from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.owner_dependencies import OWNER_ROLE_PERMISSIONS, OwnerPrincipal
from app.core.config import get_settings
from app.db import models as dbm
from app.db.models import now_utc
from app.services.mfa import build_otpauth_url, generate_totp_secret, verify_totp
from app.services.security import verify_password
from app.services.sinoe_integration import CredentialCipher


class OwnerAuthService:
    def login(self, db: Session, *, email: str, password: str, mfa_code: str | None = None, request_id: str | None = None) -> dict[str, object]:
        owner = self._owner_by_email(db, email)
        if not owner or owner.status != "active" or not owner.hashed_password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner credentials")
        if owner.role not in OWNER_ROLE_PERMISSIONS or not verify_password(password, owner.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner credentials")
        if self._mfa_is_enabled(owner):
            self._verify_owner_mfa(owner, mfa_code)

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

    def mfa_status(self, *, owner: dbm.OwnerUser) -> dict[str, object]:
        return {
            "mfa_enabled": self._mfa_is_enabled(owner),
            "enrollment_pending": bool(owner.mfa_secret_encrypted and not owner.mfa_enabled),
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
        self._verify_owner_mfa(owner, code)
        owner.mfa_enabled = True
        owner.mfa_confirmed_at = now_utc()
        owner.refresh_token_version += 1
        self._audit(db, owner=owner, action="owner_mfa_enabled", entity_type="owner_mfa", entity_id=owner.id, request_id=request_id)
        db.commit()
        return {
            "access_token": self._create_token(owner, token_type="access", expires_minutes=get_settings().access_token_minutes),
            "refresh_token": self._create_token(owner, token_type="refresh", expires_minutes=get_settings().refresh_token_minutes),
            "token_type": "bearer",
            "owner": self._owner_payload(owner),
        }

    def disable_mfa(self, db: Session, *, owner: dbm.OwnerUser, current_password: str, code: str | None = None, request_id: str | None = None) -> dict[str, object]:
        if not owner.hashed_password or not verify_password(current_password, owner.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner credentials")
        if self._mfa_is_enabled(owner):
            self._verify_owner_mfa(owner, code)
        owner.mfa_enabled = False
        owner.mfa_secret_encrypted = None
        owner.mfa_confirmed_at = None
        owner.refresh_token_version += 1
        self._audit(db, owner=owner, action="owner_mfa_disabled", entity_type="owner_mfa", entity_id=owner.id, request_id=request_id)
        db.commit()
        return {
            "access_token": self._create_token(owner, token_type="access", expires_minutes=get_settings().access_token_minutes),
            "refresh_token": self._create_token(owner, token_type="refresh", expires_minutes=get_settings().refresh_token_minutes),
            "token_type": "bearer",
            "owner": self._owner_payload(owner),
        }

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

    @staticmethod
    def _verify_owner_mfa(owner: dbm.OwnerUser, code: str | None) -> None:
        if not owner.mfa_secret_encrypted:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Owner MFA required")
        if not code:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Owner MFA required")
        secret = CredentialCipher().decrypt(owner.mfa_secret_encrypted)
        if not verify_totp(secret, code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner MFA code")

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


owner_auth_service = OwnerAuthService()
