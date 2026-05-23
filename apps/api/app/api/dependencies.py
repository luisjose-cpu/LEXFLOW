from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status

from app.domain.models import RoleName, User
from app.services.auth import auth_service
from app.services.roles import role_service


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return auth_service.user_from_token(authorization.split(" ", 1)[1])


def get_request_tenant(
    current_user: Annotated[User, Depends(get_current_user)],
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-Id")] = None,
) -> UUID:
    if x_tenant_id:
        requested_tenant_id = UUID(x_tenant_id)
        if current_user.role != RoleName.super_admin and requested_tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant access denied")
        return requested_tenant_id
    return current_user.tenant_id


def require_permission(permission: str):
    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if not role_service.has_permission(current_user.role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency


def request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)
