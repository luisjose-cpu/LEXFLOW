from uuid import UUID

from fastapi import HTTPException, status
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db import models as dbm
from app.db.database import SessionLocal
from app.domain.models import AuditAction, User
from app.services.audit import audit_service
from app.services.security import create_token, decode_token, hash_password, verify_password
from app.services.tenants import tenant_service
from app.services.users import user_service


class AuthService:
    def login(self, *, email: str, password: str, tenant_slug: str | None = None, request_id: str | None = None) -> dict[str, object]:
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
        audit_service.record(
            tenant_id=user.tenant_id,
            actor_user_id=user.id,
            action=AuditAction.login,
            entity_type="user",
            entity_id=user.id,
            request_id=request_id,
        )
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user": user}

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
        settings = get_settings()
        access_token = create_token(
            subject=updated.id,
            tenant_id=updated.tenant_id,
            role=updated.role,
            token_type="access",
            expires_minutes=settings.access_token_minutes,
            version=updated.refresh_token_version,
        )
        refresh_token = create_token(
            subject=updated.id,
            tenant_id=updated.tenant_id,
            role=updated.role,
            token_type="refresh",
            expires_minutes=settings.refresh_token_minutes,
            version=updated.refresh_token_version,
        )
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user": updated}

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


auth_service = AuthService()
