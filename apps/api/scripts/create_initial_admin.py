from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import models as dbm
from app.db.database import SessionLocal
from app.services.security import hash_password


def require_env(key: str) -> str:
    value = os.getenv(key, "").strip()
    if not value:
        raise RuntimeError(f"{key} is required")
    return value


def main() -> int:
    tenant_name = require_env("INITIAL_TENANT_NAME")
    tenant_slug = require_env("INITIAL_TENANT_SLUG")
    admin_email = require_env("INITIAL_ADMIN_EMAIL").lower()
    admin_name = require_env("INITIAL_ADMIN_NAME")
    admin_password = require_env("INITIAL_ADMIN_PASSWORD")
    rotate_password = os.getenv("INITIAL_ADMIN_ROTATE_PASSWORD", "false").lower() == "true"

    if len(admin_password) < 12:
        raise RuntimeError("INITIAL_ADMIN_PASSWORD must be at least 12 characters")

    with SessionLocal() as db:
        tenant = db.scalars(select(dbm.Tenant).where(dbm.Tenant.slug == tenant_slug)).first()
        created_tenant = False
        if not tenant:
            tenant = dbm.Tenant(name=tenant_name, slug=tenant_slug, plan="pilot", status="active")
            db.add(tenant)
            db.flush()
            created_tenant = True
        else:
            tenant.name = tenant_name
            tenant.status = "active"
            tenant.plan = tenant.plan or "pilot"

        role = db.scalars(
            select(dbm.Role).where(
                dbm.Role.tenant_id == tenant.id,
                dbm.Role.name == "tenant_admin",
                dbm.Role.deleted_at.is_(None),
            )
        ).first()
        if not role:
            role = dbm.Role(tenant_id=tenant.id, name="tenant_admin", description="Tenant administrator", is_system=True)
            db.add(role)
            db.flush()

        user = db.scalars(
            select(dbm.User).where(
                dbm.User.tenant_id == tenant.id,
                dbm.User.email == admin_email,
                dbm.User.deleted_at.is_(None),
            )
        ).first()
        created_user = False
        rotated_password = False
        if not user:
            user = dbm.User(
                tenant_id=tenant.id,
                role_id=role.id,
                email=admin_email,
                full_name=admin_name,
                hashed_password=hash_password(admin_password),
                status="active",
            )
            db.add(user)
            db.flush()
            created_user = True
        else:
            user.role_id = role.id
            user.full_name = admin_name
            user.status = "active"
            if rotate_password:
                user.hashed_password = hash_password(admin_password)
                rotated_password = True

        db.add(
            dbm.AuditLog(
                tenant_id=tenant.id,
                actor_user_id=user.id,
                action="create",
                entity_type="initial_admin",
                entity_id=user.id,
                metadata_json={
                    "tenant_slug": tenant_slug,
                    "created_tenant": created_tenant,
                    "created_user": created_user,
                    "rotated_password": rotated_password,
                },
            )
        )
        db.commit()

    print(f"Initial admin ready: tenant={tenant_slug} email={admin_email}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Initial admin bootstrap failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
