from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import AuditAction, RoleName, User
from app.services.audit import audit_service


DEFAULT_MFA_REQUIRED_ROLES = [RoleName.tenant_admin.value, RoleName.partner.value]
VALID_POLICY_ROLES = {role.value for role in RoleName if role != RoleName.super_admin}


class TenantSecurityPolicyService:
    def __init__(self) -> None:
        self._memory_policies: dict[str, dict[str, object]] = {}

    def clear(self) -> None:
        self._memory_policies.clear()

    def get(self, db: Session | None, *, tenant_id: UUID) -> dict[str, object]:
        key = str(tenant_id)
        if key in self._memory_policies:
            return dict(self._memory_policies[key])
        if db is not None:
            try:
                row = db.scalar(select(dbm.TenantSecurityPolicy).where(dbm.TenantSecurityPolicy.tenant_id == key))
                if row:
                    policy = self._serialize(row)
                    self._memory_policies[key] = policy
                    return dict(policy)
            except SQLAlchemyError:
                pass
        policy = self._default_policy(tenant_id)
        self._memory_policies[key] = policy
        return dict(policy)

    def update(self, db: Session, *, tenant_id: UUID, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        current = self.get(db, tenant_id=tenant_id)
        roles = payload.get("mfa_required_roles", current["mfa_required_roles"])
        role_values = self._normalize_roles(roles)
        enforce_mfa = bool(payload.get("enforce_mfa", current["enforce_mfa"]))
        if enforce_mfa and actor.role.value in role_values and not actor.mfa_enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enable MFA before enforcing it for your own role")

        policy = {
            "tenant_id": str(tenant_id),
            "enforce_mfa": enforce_mfa,
            "mfa_required_roles": role_values,
            "grace_period_hours": int(payload.get("grace_period_hours", current["grace_period_hours"])),
            "allow_client_user_mfa_bypass": bool(payload.get("allow_client_user_mfa_bypass", current["allow_client_user_mfa_bypass"])),
        }
        self._validate_policy(policy)
        self._memory_policies[str(tenant_id)] = policy

        try:
            row = db.scalar(select(dbm.TenantSecurityPolicy).where(dbm.TenantSecurityPolicy.tenant_id == str(tenant_id)))
            if row is None:
                row = dbm.TenantSecurityPolicy(
                    tenant_id=str(tenant_id),
                    created_by=str(actor.id),
                )
                db.add(row)
            row.enforce_mfa = bool(policy["enforce_mfa"])
            row.mfa_required_roles = list(policy["mfa_required_roles"])
            row.grace_period_hours = int(policy["grace_period_hours"])
            row.allow_client_user_mfa_bypass = bool(policy["allow_client_user_mfa_bypass"])
            row.updated_by = str(actor.id)
            db.commit()
            db.refresh(row)
            policy = self._serialize(row)
            self._memory_policies[str(tenant_id)] = policy
        except SQLAlchemyError:
            db.rollback()

        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor.id,
            action=AuditAction.update,
            entity_type="tenant_security_policy",
            entity_id=tenant_id,
            request_id=request_id,
            metadata={
                "enforce_mfa": str(policy["enforce_mfa"]).lower(),
                "mfa_required_roles": ",".join(policy["mfa_required_roles"]),
                "grace_period_hours": str(policy["grace_period_hours"]),
                "allow_client_user_mfa_bypass": str(policy["allow_client_user_mfa_bypass"]).lower(),
            },
        )
        return dict(policy)

    def is_mfa_required(self, db: Session | None, *, user: User) -> bool:
        policy = self.get(db, tenant_id=user.tenant_id)
        if not policy["enforce_mfa"]:
            return False
        if user.role == RoleName.client_user and policy["allow_client_user_mfa_bypass"]:
            return False
        return user.role.value in set(policy["mfa_required_roles"])

    def _default_policy(self, tenant_id: UUID) -> dict[str, object]:
        return {
            "tenant_id": str(tenant_id),
            "enforce_mfa": False,
            "mfa_required_roles": list(DEFAULT_MFA_REQUIRED_ROLES),
            "grace_period_hours": 72,
            "allow_client_user_mfa_bypass": True,
        }

    def _serialize(self, row: dbm.TenantSecurityPolicy) -> dict[str, object]:
        return {
            "tenant_id": row.tenant_id,
            "enforce_mfa": row.enforce_mfa,
            "mfa_required_roles": list(row.mfa_required_roles or DEFAULT_MFA_REQUIRED_ROLES),
            "grace_period_hours": row.grace_period_hours,
            "allow_client_user_mfa_bypass": row.allow_client_user_mfa_bypass,
        }

    def _normalize_roles(self, roles: object) -> list[str]:
        if not isinstance(roles, list):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="mfa_required_roles must be a list")
        role_values = [str(role.value if isinstance(role, RoleName) else role) for role in roles]
        unknown = sorted(set(role_values) - VALID_POLICY_ROLES)
        if unknown:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid roles: {', '.join(unknown)}")
        return sorted(set(role_values))

    def _validate_policy(self, policy: dict[str, object]) -> None:
        grace = int(policy["grace_period_hours"])
        if grace < 0 or grace > 720:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="grace_period_hours must be between 0 and 720")


tenant_security_policy_service = TenantSecurityPolicyService()
