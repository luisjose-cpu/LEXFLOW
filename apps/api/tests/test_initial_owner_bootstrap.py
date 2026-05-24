import os
import sqlite3
import subprocess
import sys
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1]


def test_initial_owner_script_creates_owner_admin(tmp_path: Path) -> None:
    db_path = tmp_path / "owner_bootstrap.db"
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite+pysqlite:///{db_path.as_posix()}",
        "INITIAL_OWNER_EMAIL": "owner@lexflow.com",
        "INITIAL_OWNER_NAME": "Owner Admin",
        "INITIAL_OWNER_PASSWORD": "OwnerPassword123!",
        "INITIAL_OWNER_ROLE": "owner_admin",
    }

    migration = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=API_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    bootstrap = subprocess.run(
        [sys.executable, "scripts/create_initial_owner.py"],
        cwd=API_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert migration.returncode == 0, migration.stderr
    assert bootstrap.returncode == 0, bootstrap.stderr
    assert "Initial owner ready" in bootstrap.stdout

    with sqlite3.connect(db_path) as connection:
        owner = connection.execute("select email, role, status, hashed_password from owner_users where email = ?", ("owner@lexflow.com",)).fetchone()
        audit = connection.execute("select action, entity_type from owner_audit_logs where entity_type = ?", ("owner_user",)).fetchone()

    assert owner is not None
    assert owner[0:3] == ("owner@lexflow.com", "owner_admin", "active")
    assert owner[3] != "OwnerPassword123!"
    assert audit == ("owner_bootstrapped", "owner_user")
