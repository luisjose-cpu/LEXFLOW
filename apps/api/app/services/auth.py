from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

from fastapi import HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models as dbm
from app.db.database import SessionLocal
from app.domain.models import AuditAction, User
from app.services.audit import audit_service
from app.services.email_delivery import get_email_provider
from app.services.mfa import build_otpauth_url, generate_totp_secret, verify_totp
from app.services.security import create_token, decode_token, hash_password, verify_password
from app.services.sinoe_integration import CredentialCipher
from app.services.tenants import tenant_service
from app.services.users import user_service


class AuthService:
    def __init__(self) -> None:
        self._memory_password_resets: dict[str, dict[str, object]] = {}

    def login(self, *, email: str, password: str, tenant_slug: str | None = None, mfa_code: str | None = None, request_id: str | None = None) -> dict[str, object]:
        tenant_id: UUID | None = None
        if tenant_slug:
            tenant = tenant_service.find_by_slug(tenant_slug)
            if not tenant:
                tenant = self._load_tenant_by_slug(tenant_slug)
            if not tenant:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
            tenant_id = tenant.id

        user = user_service.find_by_email(email, tenant_id)
        if not user:
            user = self._load_user_by_email(email=email, tenant_id=tenant_id)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        if user.mfa_enabled:
            self._verify_user_mfa(user, mfa_code)

        tokens = self._issue_session(user)
        audit_service.record(
            tenant_id=user.tenant_id,
            actor_user_id=user.id,
            action=AuditAction.login,
            entity_type="user",
            entity_id=user.id,
            request_id=request_id,
        )
        return {**tokens, "user": user}

    def refresh(self, *, refresh_token: str, request_id: str | None = None) -> dict[str, str]:
        user = self.user_from_token(refresh_token, expected_type="refresh")
        settings = get_settings()
        access_token = create_token(
            subject=user.id,
            tenant_id=user.tenant_id,
            role=user.role,
            token_type="access",
            expires_minutes=settings.access_token_minutes,
            version=user.refresh_token_version,
        )
        audit_service.record(
            tenant_id=user.tenant_id,
            actor_user_id=user.id,
            action=AuditAction.refresh,
            entity_type="user",
            entity_id=user.id,
            request_id=request_id,
        )
        return {"access_token": access_token, "token_type": "bearer"}

    def logout(self, *, user: User, request_id: str | None = None) -> None:
        user_service.bump_refresh_version(user)
        self._sync_user_refresh_version(user)
        audit_service.record(
            tenant_id=user.tenant_id,
            actor_user_id=user.id,
            action=AuditAction.logout,
            entity_type="user",
            entity_id=user.id,
            request_id=request_id,
        )

    def change_password(self, *, user: User, current_password: str, new_password: str, request_id: str | None = None) -> dict[str, object]:
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password")
        new_hash = hash_password(new_password)
        updated = user_service.change_password(user, new_hash)
        self._sync_user_password(updated)
        audit_service.record(
            tenant_id=updated.tenant_id,
            actor_user_id=updated.id,
            action=AuditAction.update,
            entity_type="auth_password",
            entity_id=updated.id,
            request_id=request_id,
            metadata={"reason": "user_password_changed"},
        )
        tokens = self._issue_session(updated)
        return {**tokens, "user": updated}

    def mfa_status(self, *, user: User) -> dict[str, object]:
        return {"mfa_enabled": user.mfa_enabled, "enrollment_pending": bool(user.mfa_secret_encrypted and not user.mfa_enabled)}

    def start_mfa_enrollment(self, *, user: User, request_id: str | None = None) -> dict[str, object]:
        secret = generate_totp_secret()
        encrypted = CredentialCipher().encrypt(secret)
        updated = user.model_copy(update={"mfa_secret_encrypted": encrypted, "mfa_enabled": False})
        user_service.upsert(updated)
        self._sync_user_mfa(updated, confirmed=False)
        audit_service.record(
            tenant_id=updated.tenant_id,
            actor_user_id=updated.id,
            action=AuditAction.update,
            entity_type="auth_mfa",
            entity_id=updated.id,
            request_id=request_id,
            metadata={"reason": "mfa_enrollment_started"},
        )
        return {
            "status": "pending",
            "secret": secret,
            "otpauth_url": build_otpauth_url(issuer="LEXFLOW", account=updated.email, secret=secret),
        }

    def confirm_mfa_enrollment(self, *, user: User, code: str, request_id: str | None = None) -> dict[str, object]:
        if not user.mfa_secret_encrypted:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA enrollment has not started")
        secret = CredentialCipher().decrypt(user.mfa_secret_encrypted)
        if not verify_totp(secret, code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")
        updated = user.model_copy(
            update={
                "mfa_enabled": True,
                "refresh_token_version": user.refresh_token_version + 1,
                "updated_at": dbm.now_utc(),
            }
        )
        user_service.upsert(updated)
        self._sync_user_mfa(updated, confirmed=True)
        audit_service.record(
            tenant_id=updated.tenant_id,
            actor_user_id=updated.id,
            action=AuditAction.update,
            entity_type="auth_mfa",
            entity_id=updated.id,
            request_id=request_id,
            metadata={"reason": "mfa_enabled"},
        )
        return {**self._issue_session(updated), "user": updated}

    def disable_mfa(self, *, user: User, current_password: str, code: str | None = None, request_id: str | None = None) -> dict[str, object]:
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password")
        if user.mfa_enabled:
            self._verify_user_mfa(user, code)
        updated = user.model_copy(
            update={
                "mfa_enabled": False,
                "mfa_secret_encrypted": None,
                "refresh_token_version": user.refresh_token_version + 1,
                "updated_at": dbm.now_utc(),
            }
        )
        user_service.upsert(updated)
        self._sync_user_mfa(updated, confirmed=False, clear_secret=True)
        audit_service.record(
            tenant_id=updated.tenant_id,
            actor_user_id=updated.id,
            action=AuditAction.update,
            entity_type="auth_mfa",
            entity_id=updated.id,
            request_id=request_id,
            metadata={"reason": "mfa_disabled"},
        )
        return {**self._issue_session(updated), "user": updated}

    def _issue_session(self, user: User) -> dict[str, str]:
        settings = get_settings()
        access_token = create_token(
            subject=user.id,
            tenant_id=user.tenant_id,
            role=user.role,
            token_type="access",
            expires_minutes=settings.access_token_minutes,
            version=user.refresh_token_version,
        )
        refresh_token = create_token(
            subject=user.id,
            tenant_id=user.tenant_id,
            role=user.role,
            token_type="refresh",
            expires_minutes=settings.refresh_token_minutes,
            version=user.refresh_token_version,
        )
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    def request_password_reset(self, db: Session, *, email: str, tenant_slug: str, request_id: str | None = None, requested_ip: str | None = None) -> dict[str, object]:
        settings = get_settings()
        tenant = tenant_service.find_by_slug(tenant_slug) or self._load_tenant_by_slug(tenant_slug)
        response: dict[str, object] = {"status": "reset_requested", "delivery": "email_prepared"}
        if not tenant:
            return response

        raw_token = token_urlsafe(32)
        token_hash = self._token_hash(raw_token)
        expires_at = dbm.now_utc() + timedelta(minutes=settings.password_reset_token_minutes)

        user = user_service.find_by_email(email, tenant.id)
        if user:
            self._memory_password_resets[token_hash] = {
                "tenant_id": str(user.tenant_id),
                "user_id": str(user.id),
                "expires_at": expires_at,
                "used": False,
            }
            audit_service.record(
                tenant_id=user.tenant_id,
                actor_user_id=user.id,
                action=AuditAction.update,
                entity_type="auth_password_reset",
                entity_id=user.id,
                request_id=request_id,
                metadata={"reason": "password_reset_requested"},
            )
            delivery = self._deliver_password_reset(email=user.email, token=raw_token)
            response["delivery"] = delivery.provider if delivery.status == "prepared" else delivery.status
            if settings.app_env.lower() in {"local", "test"}:
                response["reset_token"] = raw_token
            return response

        try:
            db_user = db.scalars(
                select(dbm.User)
                .join(dbm.Tenant)
                .where(
                    dbm.Tenant.slug == tenant_slug,
                    dbm.Tenant.deleted_at.is_(None),
                    dbm.User.email == email.lower(),
                    dbm.User.status == "active",
                    dbm.User.deleted_at.is_(None),
                )
            ).first()
        except SQLAlchemyError:
            return response
        if not db_user:
            return response

        db.add(
            dbm.PasswordResetToken(
                tenant_id=db_user.tenant_id,
                user_id=db_user.id,
                token_hash=token_hash,
                requested_ip=requested_ip,
                expires_at=expires_at,
            )
        )
        db.commit()
        audit_service.record(
            tenant_id=UUID(db_user.tenant_id),
            actor_user_id=UUID(db_user.id),
            action=AuditAction.update,
            entity_type="auth_password_reset",
            entity_id=UUID(db_user.id),
            request_id=request_id,
            metadata={"reason": "password_reset_requested"},
        )
        delivery = self._deliver_password_reset(email=db_user.email, token=raw_token)
        response["delivery"] = delivery.provider if delivery.status == "prepared" else delivery.status
        if settings.app_env.lower() in {"local", "test"}:
            response["reset_token"] = raw_token
        return response

    def confirm_password_reset(self, db: Session, *, reset_token: str, new_password: str, request_id: str | None = None) -> dict[str, object]:
        token_hash = self._token_hash(reset_token)
        now = dbm.now_utc()
        memory_token = self._memory_password_resets.get(token_hash)
        if memory_token:
            if memory_token["used"] or memory_token["expires_at"] <= now:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired reset token")
            user = user_service.get(UUID(str(memory_token["tenant_id"])), UUID(str(memory_token["user_id"])))
            if not user or not user.is_active:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reset token subject")
            memory_token["used"] = True
            updated = user_service.change_password(user, hash_password(new_password))
            self._sync_user_password(updated)
            audit_service.record(
                tenant_id=updated.tenant_id,
                actor_user_id=updated.id,
                action=AuditAction.update,
                entity_type="auth_password_reset",
                entity_id=updated.id,
                request_id=request_id,
                metadata={"reason": "password_reset_completed"},
            )
            return {"status": "password_reset_complete"}

        reset_row = db.scalar(
            select(dbm.PasswordResetToken).where(
                dbm.PasswordResetToken.token_hash == token_hash,
                dbm.PasswordResetToken.used_at.is_(None),
                dbm.PasswordResetToken.expires_at > now,
            )
        )
        if not reset_row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired reset token")
        db_user = db.get(dbm.User, reset_row.user_id)
        if not db_user or db_user.status != "active" or db_user.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid reset token subject")
        db_user.hashed_password = hash_password(new_password)
        db_user.refresh_token_version += 1
        reset_row.used_at = now
        reset_row.status = "used"
        db.commit()
        user_service.upsert(self._domain_user_from_db(db_user))
        audit_service.record(
            tenant_id=UUID(db_user.tenant_id),
            actor_user_id=UUID(db_user.id),
            action=AuditAction.update,
            entity_type="auth_password_reset",
            entity_id=UUID(db_user.id),
            request_id=request_id,
            metadata={"reason": "password_reset_completed"},
        )
        return {"status": "password_reset_complete"}

    def user_from_token(self, token: str, *, expected_type: str = "access") -> User:
        try:
            payload = decode_token(token)
        except InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

        if payload.get("type") != expected_type:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        tenant_id = UUID(str(payload["tenant_id"]))
        user_id = UUID(str(payload["sub"]))
        user = user_service.get(tenant_id, user_id)
        if not user:
            user = self._load_user_by_id(tenant_id=tenant_id, user_id=user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
        if int(payload.get("version", -1)) != user.refresh_token_version:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
        return user

    def _load_tenant_by_slug(self, slug: str):
        try:
            with SessionLocal() as db:
                tenant = db.scalars(
                    select(dbm.Tenant).where(
                        dbm.Tenant.slug == slug,
                        dbm.Tenant.status == "active",
                        dbm.Tenant.deleted_at.is_(None),
                    )
                ).first()
                if not tenant:
                    return None
                from app.domain.models import Tenant as DomainTenant

                return tenant_service.upsert(
                    DomainTenant(
                        id=UUID(tenant.id),
                        name=tenant.name,
                        slug=tenant.slug,
                        is_active=tenant.status == "active",
                        created_at=tenant.created_at,
                    )
                )
        except SQLAlchemyError:
            return None

    def _load_user_by_email(self, *, email: str, tenant_id: UUID | None) -> User | None:
        try:
            with SessionLocal() as db:
                query = (
                    select(dbm.User)
                    .join(dbm.Role)
                    .where(
                        dbm.User.email == email.lower(),
                        dbm.User.status == "active",
                        dbm.User.deleted_at.is_(None),
                    )
                )
                if tenant_id:
                    query = query.where(dbm.User.tenant_id == str(tenant_id))
                db_user = db.scalars(query).first()
                return self._domain_user_from_db(db_user) if db_user else None
        except SQLAlchemyError:
            return None

    def _load_user_by_id(self, *, tenant_id: UUID, user_id: UUID) -> User | None:
        try:
            with SessionLocal() as db:
                db_user = db.scalars(
                    select(dbm.User)
                    .join(dbm.Role)
                    .where(
                        dbm.User.id == str(user_id),
                        dbm.User.tenant_id == str(tenant_id),
                        dbm.User.status == "active",
                        dbm.User.deleted_at.is_(None),
                    )
                ).first()
                return self._domain_user_from_db(db_user) if db_user else None
        except SQLAlchemyError:
            return None

    def _domain_user_from_db(self, db_user: dbm.User) -> User:
        from app.domain.models import RoleName

        return user_service.upsert(
            User(
                id=UUID(db_user.id),
                tenant_id=UUID(db_user.tenant_id),
                email=db_user.email,
                full_name=db_user.full_name,
                hashed_password=db_user.hashed_password,
                role=RoleName(db_user.role.name),
                is_active=db_user.status == "active",
                mfa_enabled=db_user.mfa_enabled,
                mfa_secret_encrypted=db_user.mfa_secret_encrypted,
                refresh_token_version=db_user.refresh_token_version,
                created_at=db_user.created_at,
                updated_at=db_user.updated_at,
            )
        )

    def _sync_user_password(self, user: User) -> None:
        try:
            with SessionLocal() as db:
                db_user = db.get(dbm.User, str(user.id))
                if not db_user:
                    return
                db_user.hashed_password = user.hashed_password
                db_user.refresh_token_version = user.refresh_token_version
                db.commit()
        except SQLAlchemyError:
            return

    def _sync_user_refresh_version(self, user: User) -> None:
        try:
            with SessionLocal() as db:
                db_user = db.get(dbm.User, str(user.id))
                if not db_user:
                    return
                db_user.refresh_token_version = user.refresh_token_version + 1
                db.commit()
        except SQLAlchemyError:
            return

    def _sync_user_mfa(self, user: User, *, confirmed: bool, clear_secret: bool = False) -> None:
        try:
            with SessionLocal() as db:
                db_user = db.get(dbm.User, str(user.id))
                if not db_user:
                    return
                db_user.mfa_enabled = user.mfa_enabled
                db_user.mfa_secret_encrypted = None if clear_secret else user.mfa_secret_encrypted
                db_user.mfa_confirmed_at = dbm.now_utc() if confirmed else None
                db_user.refresh_token_version = user.refresh_token_version
                db.commit()
        except SQLAlchemyError:
            return

    def _verify_user_mfa(self, user: User, code: str | None) -> None:
        if not code:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA code required")
        if not user.mfa_secret_encrypted:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="MFA is enabled but not configured")
        secret = CredentialCipher().decrypt(user.mfa_secret_encrypted)
        if not verify_totp(secret, code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")

    @staticmethod
    def _token_hash(raw_token: str) -> str:
        return sha256(raw_token.encode("utf-8")).hexdigest()

    def _deliver_password_reset(self, *, email: str, token: str):
        settings = get_settings()
        reset_url = f"{settings.lexflow_web_url.rstrip('/')}/login/reset/confirm?token={token}"
        return get_email_provider(settings).send_password_reset(to_email=email, reset_url=reset_url)


auth_service = AuthService()
