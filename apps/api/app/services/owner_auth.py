from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_hex

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.owner_dependencies import OWNER_ROLE_PERMISSIONS, OwnerPrincipal
from app.core.config import get_settings
from app.db import models as dbm
from app.db.models import now_utc
from app.services.mfa import build_otpauth_url, generate_totp_secret, verify_totp
from app.services.security import verify_password
from app.services.security_alerts import security_alert_service
from app.services.sinoe_integration import CredentialCipher


class OwnerAuthService:
    def __init__(self) -> None:
        self._failed_logins: dict[str, list[datetime]] = {}

    def login(self, db: Session, *, email: str, password: str, mfa_code: str | None = None, request_id: str | None = None) -> dict[str, object]:
        failure_key = self._failure_key(email)
        self._raise_if_too_many_failures(failure_key)
        owner = self._owner_by_email(db, email)
        if not owner or owner.status != "active" or not owner.hashed_password:
            self._record_failed_login(failure_key)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner credentials")
        if owner.role not in OWNER_ROLE_PERMISSIONS or not verify_password(password, owner.hashed_password):
            self._record_failed_login(failure_key)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner credentials")
        if get_settings().require_owner_mfa and not self._mfa_is_enabled(owner):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner MFA enrollment required")
        if self._mfa_is_enabled(owner):
            self._verify_owner_mfa(db, owner=owner, code=mfa_code, request_id=request_id)

        self._clear_failed_logins(failure_key)
        owner.last_login_at = now_utc()
        self._audit(db, owner=owner, action="owner_login", entity_type="owner_user", entity_id=owner.id, request_id=request_id)
        db.commit()
        return {
            "access_token": self._create_token(owner, token_type="access", expires_minutes=get_settings().access_token_minutes),
            "refresh_token": self._create_token(owner, token_type="refresh", expires_minutes=get_settings().refresh_token_minutes),
            "token_type": "bearer",
            "owner": self._owner_payload(owner),
        }

    def refresh(self, db: Session, *, refresh_token: str, request_id: str | None = None) -> dict[str, object]:
        owner = self.owner_from_token(db, refresh_token, expected_type="refresh")
        self._audit(db, owner=owner, action="owner_refresh", entity_type="owner_user", entity_id=owner.id, request_id=request_id)
        db.commit()
        return {"access_token": self._create_token(owner, token_type="access", expires_minutes=get_settings().access_token_minutes), "token_type": "bearer"}

    def logout(self, db: Session, *, owner: dbm.OwnerUser, request_id: str | None = None) -> None:
        owner.refresh_token_version += 1
        self._audit(db, owner=owner, action="owner_logout", entity_type="owner_user", entity_id=owner.id, request_id=request_id)
        db.commit()

    def mfa_status(self, db: Session, *, owner: dbm.OwnerUser) -> dict[str, object]:
        return {
            "mfa_enabled": self._mfa_is_enabled(owner),
            "enrollment_pending": bool(owner.mfa_secret_encrypted and not owner.mfa_enabled),
            "recovery_codes_remaining": self._recovery_codes_remaining(db, owner=owner),
        }

    def start_mfa_enrollment(self, db: Session, *, owner: dbm.OwnerUser, request_id: str | None = None) -> dict[str, object]:
        secret = generate_totp_secret()
        owner.mfa_secret_encrypted = CredentialCipher().encrypt(secret)
        owner.mfa_enabled = False
        owner.mfa_confirmed_at = None
        self._audit(db, owner=owner, action="owner_mfa_enrollment_started", entity_type="owner_mfa", entity_id=owner.id, request_id=request_id)
        db.commit()
        return {
            "status": "pending",
            "secret": secret,
            "otpauth_url": build_otpauth_url(issuer="LEXFLOW Owner", account=owner.email, secret=secret),
        }

    def confirm_mfa_enrollment(self, db: Session, *, owner: dbm.OwnerUser, code: str, request_id: str | None = None) -> dict[str, object]:
        if not owner.mfa_secret_encrypted:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner MFA enrollment has not started")
        self._verify_owner_totp(owner, code)
        owner.mfa_enabled = True
        owner.mfa_confirmed_at = now_utc()
        owner.refresh_token_version += 1
        recovery_codes = self._replace_recovery_codes(db, owner=owner)
        self._audit(db, owner=owner, action="owner_mfa_enabled", entity_type="owner_mfa", entity_id=owner.id, request_id=request_id)
        db.commit()
        return {
            "access_token": self._create_token(owner, token_type="access", expires_minutes=get_settings().access_token_minutes),
            "refresh_token": self._create_token(owner, token_type="refresh", expires_minutes=get_settings().refresh_token_minutes),
            "token_type": "bearer",
            "owner": self._owner_payload(owner),
            "recovery_codes": recovery_codes,
        }

    def disable_mfa(self, db: Session, *, owner: dbm.OwnerUser, current_password: str, code: str | None = None, request_id: str | None = None) -> dict[str, object]:
        if not owner.hashed_password or not verify_password(current_password, owner.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner credentials")
        if self._mfa_is_enabled(owner):
            self._verify_owner_mfa(db, owner=owner, code=code, request_id=request_id)
        owner.mfa_enabled = False
        owner.mfa_secret_encrypted = None
        owner.mfa_confirmed_at = None
        db.execute(delete(dbm.OwnerMfaRecoveryCode).where(dbm.OwnerMfaRecoveryCode.owner_user_id == owner.id))
        owner.refresh_token_version += 1
        self._audit(db, owner=owner, action="owner_mfa_disabled", entity_type="owner_mfa", entity_id=owner.id, request_id=request_id)
        db.commit()
        return {
            "access_token": self._create_token(owner, token_type="access", expires_minutes=get_settings().access_token_minutes),
            "refresh_token": self._create_token(owner, token_type="refresh", expires_minutes=get_settings().refresh_token_minutes),
            "token_type": "bearer",
            "owner": self._owner_payload(owner),
        }

    def regenerate_recovery_codes(self, db: Session, *, owner: dbm.OwnerUser, current_password: str, code: str | None = None, request_id: str | None = None) -> dict[str, object]:
        if not self._mfa_is_enabled(owner):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner MFA is not enabled")
        if not owner.hashed_password or not verify_password(current_password, owner.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner credentials")
        self._verify_owner_mfa(db, owner=owner, code=code, request_id=request_id)
        codes = self._replace_recovery_codes(db, owner=owner)
        self._audit(db, owner=owner, action="owner_mfa_recovery_codes_regenerated", entity_type="owner_mfa", entity_id=owner.id, request_id=request_id)
        db.commit()
        return {"status": "recovery_codes_regenerated", "recovery_codes": codes}

    def principal_from_token(self, db: Session, token: str, *, expected_type: str = "access") -> OwnerPrincipal:
        owner = self.owner_from_token(db, token, expected_type=expected_type)
        return OwnerPrincipal(email=owner.email, role=owner.role, user_id=owner.id)

    def owner_from_token(self, db: Session, token: str, *, expected_type: str = "access") -> dbm.OwnerUser:
        try:
            payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[get_settings().jwt_algorithm])
        except InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner token") from exc

        if payload.get("scope") != "owner" or payload.get("type") != expected_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner token type")

        owner = db.get(dbm.OwnerUser, str(payload.get("sub")))
        if not owner or owner.status != "active" or owner.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner token subject")
        if owner.role not in OWNER_ROLE_PERMISSIONS:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid owner role")
        if int(payload.get("version", -1)) != owner.refresh_token_version:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Owner token revoked")
        return owner

    @staticmethod
    def _owner_payload(owner: dbm.OwnerUser) -> dict[str, object]:
        return {
            "id": owner.id,
            "email": owner.email,
            "full_name": owner.full_name,
            "role": owner.role,
            "mfa_enabled": bool(owner.mfa_enabled and owner.mfa_secret_encrypted),
            "last_login_at": owner.last_login_at.isoformat() if owner.last_login_at else None,
        }

    def _create_token(self, owner: dbm.OwnerUser, *, token_type: str, expires_minutes: int) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": owner.id,
            "email": owner.email,
            "role": owner.role,
            "scope": "owner",
            "type": token_type,
            "version": owner.refresh_token_version,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        }
        settings = get_settings()
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def _owner_by_email(db: Session, email: str) -> dbm.OwnerUser | None:
        return db.scalar(select(dbm.OwnerUser).where(dbm.OwnerUser.email == email.strip().lower(), dbm.OwnerUser.deleted_at.is_(None)))

    @staticmethod
    def _mfa_is_enabled(owner: dbm.OwnerUser) -> bool:
        return bool(owner.mfa_enabled and owner.mfa_secret_encrypted)

    def _verify_owner_mfa(self, db: Session, *, owner: dbm.OwnerUser, code: str | None, request_id: str | None = None) -> None:
        if not owner.mfa_secret_encrypted:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Owner MFA required")
        if not code:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Owner MFA required")
        if self._consume_recovery_code(db, owner=owner, code=code):
            self._audit(db, owner=owner, action="owner_mfa_recovery_code_used", entity_type="owner_mfa", entity_id=owner.id, request_id=request_id)
            return
        secret = CredentialCipher().decrypt(owner.mfa_secret_encrypted)
        if not verify_totp(secret, code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner MFA code")

    @staticmethod
    def _verify_owner_totp(owner: dbm.OwnerUser, code: str | None) -> None:
        if not owner.mfa_secret_encrypted or not code:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Owner MFA required")
        secret = CredentialCipher().decrypt(owner.mfa_secret_encrypted)
        if not verify_totp(secret, code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner MFA code")

    def _replace_recovery_codes(self, db: Session, *, owner: dbm.OwnerUser) -> list[str]:
        db.execute(delete(dbm.OwnerMfaRecoveryCode).where(dbm.OwnerMfaRecoveryCode.owner_user_id == owner.id))
        codes = [self._new_recovery_code() for _ in range(10)]
        for code in codes:
            db.add(dbm.OwnerMfaRecoveryCode(owner_user_id=owner.id, code_hash=self._recovery_code_hash(code)))
        return codes

    def _consume_recovery_code(self, db: Session, *, owner: dbm.OwnerUser, code: str) -> bool:
        normalized_hash = self._recovery_code_hash(code)
        rows = db.scalars(select(dbm.OwnerMfaRecoveryCode).where(dbm.OwnerMfaRecoveryCode.owner_user_id == owner.id, dbm.OwnerMfaRecoveryCode.used_at.is_(None))).all()
        for row in rows:
            if row.code_hash == normalized_hash:
                row.used_at = now_utc()
                return True
        return False

    def _recovery_codes_remaining(self, db: Session, *, owner: dbm.OwnerUser) -> int:
        return int(
            db.scalar(
                select(func.count())
                .select_from(dbm.OwnerMfaRecoveryCode)
                .where(dbm.OwnerMfaRecoveryCode.owner_user_id == owner.id, dbm.OwnerMfaRecoveryCode.used_at.is_(None))
            )
            or 0
        )

    @staticmethod
    def _new_recovery_code() -> str:
        raw = token_hex(6).upper()
        return f"LF-{raw[:4]}-{raw[4:8]}-{raw[8:]}"

    @staticmethod
    def _recovery_code_hash(code: str) -> str:
        normalized = code.strip().upper().replace(" ", "")
        return sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _audit(db: Session, *, owner: dbm.OwnerUser, action: str, entity_type: str, entity_id: str | None = None, request_id: str | None = None) -> None:
        db.add(
            dbm.OwnerAuditLog(
                owner_user_id=owner.id,
                owner_email=owner.email,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                reason="owner auth",
                request_id=request_id,
            )
        )
        alert_titles = {
            "owner_login": ("Owner login", "Una cuenta owner inicio sesion.", "medium"),
            "owner_mfa_enabled": ("MFA owner activado", "Una cuenta owner activo MFA.", "medium"),
            "owner_mfa_disabled": ("MFA owner desactivado", "Una cuenta owner desactivo MFA. Revisar si fue esperado.", "critical"),
            "owner_mfa_recovery_code_used": ("Recovery code owner usado", "Una cuenta owner uso un codigo de recuperacion MFA.", "high"),
            "owner_mfa_recovery_codes_regenerated": ("Recovery codes owner regenerados", "Una cuenta owner regenero codigos de recuperacion.", "high"),
        }
        if action in alert_titles:
            title, body, severity = alert_titles[action]
            security_alert_service.create_owner_alert(
                db,
                owner=owner,
                event_type=f"owner.{action}",
                title=title,
                body=body,
                severity=severity,
                request_id=request_id,
                metadata={"owner_role": owner.role},
            )

    @staticmethod
    def _failure_key(email: str) -> str:
        return email.strip().lower()

    def _recent_failures(self, key: str) -> list[datetime]:
        settings = get_settings()
        cutoff = now_utc() - timedelta(minutes=settings.failed_login_window_minutes)
        recent = [item for item in self._failed_logins.get(key, []) if item > cutoff]
        self._failed_logins[key] = recent
        return recent

    def _raise_if_too_many_failures(self, key: str) -> None:
        settings = get_settings()
        if settings.failed_login_limit <= 0:
            return
        if len(self._recent_failures(key)) >= settings.failed_login_limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many failed login attempts")

    def _record_failed_login(self, key: str) -> None:
        self._failed_logins[key] = [*self._recent_failures(key), now_utc()]

    def _clear_failed_logins(self, key: str) -> None:
        self._failed_logins.pop(key, None)


owner_auth_service = OwnerAuthService()
