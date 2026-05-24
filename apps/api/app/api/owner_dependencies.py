from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.config import get_settings
from app.db.database import get_db
from sqlalchemy.orm import Session


OWNER_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner_admin": {"*"},
    "owner_support": {"owner:read", "support:write", "interventions:write"},
    "owner_sales": {"owner:read", "tenants:write", "demos:write"},
    "owner_finance": {"owner:read", "billing:write", "plans:write"},
    "owner_devops": {"owner:read", "system:write"},
    "owner_readonly": {"owner:read"},
}


@dataclass(frozen=True)
class OwnerPrincipal:
    email: str
    role: str
    user_id: str | None = None


def get_owner_principal(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
    x_owner_email: Annotated[str | None, Header(alias="X-Owner-Email")] = None,
    x_owner_role: Annotated[str | None, Header(alias="X-Owner-Role")] = None,
) -> OwnerPrincipal:
    if authorization and authorization.lower().startswith("bearer "):
        from app.services.owner_auth import owner_auth_service

        return owner_auth_service.principal_from_token(db, authorization.split(" ", 1)[1])

    if not x_owner_email or not x_owner_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner console credentials required")
    if get_settings().app_env.lower() not in {"local", "test"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner header fallback is disabled")
    if x_owner_role not in OWNER_ROLE_PERMISSIONS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid owner role")
    return OwnerPrincipal(email=x_owner_email.strip().lower(), role=x_owner_role)


def require_owner_permission(permission: str):
    def dependency(owner: Annotated[OwnerPrincipal, Depends(get_owner_principal)]) -> OwnerPrincipal:
        permissions = OWNER_ROLE_PERMISSIONS[owner.role]
        if "*" not in permissions and permission not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient owner permissions")
        return owner

    return dependency
