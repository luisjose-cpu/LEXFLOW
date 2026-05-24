from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status


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


def get_owner_principal(
    x_owner_email: Annotated[str | None, Header(alias="X-Owner-Email")] = None,
    x_owner_role: Annotated[str | None, Header(alias="X-Owner-Role")] = None,
) -> OwnerPrincipal:
    if not x_owner_email or not x_owner_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner console credentials required")
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
