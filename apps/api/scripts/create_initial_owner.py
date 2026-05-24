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
    email = require_env("INITIAL_OWNER_EMAIL").lower()
    full_name = require_env("INITIAL_OWNER_NAME")
    password = require_env("INITIAL_OWNER_PASSWORD")
    role = os.getenv("INITIAL_OWNER_ROLE", "owner_admin").strip() or "owner_admin"
    rotate_password = os.getenv("INITIAL_OWNER_ROTATE_PASSWORD", "false").lower() == "true"

    if len(password) < 14:
        raise RuntimeError("INITIAL_OWNER_PASSWORD must be at least 14 characters")
    if role not in {"owner_admin", "owner_support", "owner_sales", "owner_finance", "owner_devops", "owner_readonly"}:
        raise RuntimeError("INITIAL_OWNER_ROLE is invalid")

    with SessionLocal() as db:
        owner = db.scalars(select(dbm.OwnerUser).where(dbm.OwnerUser.email == email, dbm.OwnerUser.deleted_at.is_(None))).first()
        created_owner = False
        rotated_password = False
        if not owner:
            owner = dbm.OwnerUser(email=email, full_name=full_name, role=role, hashed_password=hash_password(password), status="active", mfa_enabled=True)
            db.add(owner)
            db.flush()
            created_owner = True
        else:
            owner.full_name = full_name
            owner.role = role
            owner.status = "active"
            owner.mfa_enabled = True
            if rotate_password:
                owner.hashed_password = hash_password(password)
                owner.refresh_token_version += 1
                rotated_password = True

        db.add(
            dbm.OwnerAuditLog(
                owner_user_id=owner.id,
                owner_email=owner.email,
                action="owner_bootstrapped",
                entity_type="owner_user",
                entity_id=owner.id,
                reason="initial owner bootstrap",
                metadata_json={"created_owner": created_owner, "rotated_password": rotated_password, "role": role},
            )
        )
        db.commit()

    print(f"Initial owner ready: email={email} role={role}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Initial owner bootstrap failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
