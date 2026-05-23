from uuid import UUID

from fastapi import HTTPException, status
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.domain.models import AuditAction, User
from app.services.audit import audit_service
from app.services.security import create_token, decode_token, verify_password
from app.services.tenants import tenant_service
from app.services.users import user_service


class AuthService:
    def login(self, *, email: str, password: str, tenant_slug: str | None = None, request_id: str | None = None) -> dict[str, object]:
        tenant_id: UUID | None = None
        if tenant_slug:
            tenant = tenant_service.find_by_slug(tenant_slug)
            if not tenant:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
            tenant_id = tenant.id

        user = user_service.find_by_email(email, tenant_id)
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
        audit_service.record(
            tenant_id=user.tenant_id,
            actor_user_id=user.id,
            action=AuditAction.logout,
            entity_type="user",
            entity_id=user.id,
            request_id=request_id,
        )

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
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
        if int(payload.get("version", -1)) != user.refresh_token_version:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
        return user


auth_service = AuthService()
