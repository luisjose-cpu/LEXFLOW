import os
import sqlite3
import subprocess
import sys
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1]


def test_initial_admin_script_creates_persistent_tenant_and_user(tmp_path: Path) -> None:
    db_path = tmp_path / "bootstrap.db"
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite+pysqlite:///{db_path.as_posix()}",
        "INITIAL_TENANT_NAME": "LEXFLOW Pilot Studio",
        "INITIAL_TENANT_SLUG": "pilot",
        "INITIAL_ADMIN_EMAIL": "admin@pilot.lexflow.test",
        "INITIAL_ADMIN_NAME": "Pilot Admin",
        "INITIAL_ADMIN_PASSWORD": "PilotPassword123!",
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
        [sys.executable, "scripts/create_initial_admin.py"],
        cwd=API_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert migration.returncode == 0, migration.stderr
    assert bootstrap.returncode == 0, bootstrap.stderr
    assert "Initial admin ready" in bootstrap.stdout

    with sqlite3.connect(db_path) as connection:
        tenant = connection.execute("select id, name from tenants where slug = ?", ("pilot",)).fetchone()
        user = connection.execute("select email, status from users where email = ?", ("admin@pilot.lexflow.test",)).fetchone()
        audit = connection.execute("select action, entity_type from audit_logs where entity_type = ?", ("initial_admin",)).fetchone()

    assert tenant is not None
    assert tenant[1] == "LEXFLOW Pilot Studio"
    assert user == ("admin@pilot.lexflow.test", "active")
    assert audit == ("create", "initial_admin")
