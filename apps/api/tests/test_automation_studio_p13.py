from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, AutomationRun, AutomationRunStep, Base, Task
from app.db.seed import seed_demo_database
from app.main import app
from app.services.seed import DEMO_SEED, seed_demo_data


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def api(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def login(api: TestClient, email: str) -> dict[str, str]:
    response = api.post(
        "/api/v1/auth/login",
        json={"email": email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_for_automation(api: TestClient, db_session: Session) -> str:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    return tenant_id


def workflow_payload() -> dict[str, object]:
    return {
        "name": "Audiencia proxima -> tareas y aviso",
        "description": "Prepara al equipo ante audiencia cercana.",
        "trigger_key": "HEARING_UPCOMING",
        "conditions": [{"condition_type": "CASE_STATUS_EQUALS", "config": {"status": "active"}}],
        "actions": [
            {"action_type": "CREATE_TASK", "config": {"title": "Preparar audiencia"}},
            {"action_type": "SEND_PORTAL_NOTIFICATION", "config": {"title": "Audiencia proxima", "body": "Revisar agenda"}},
            {"action_type": "RUN_AI_SUMMARY_MOCK", "config": {"title": "Resumen previo"}},
        ],
    }


def test_workflow_crud_activate_and_run(api: TestClient, db_session: Session) -> None:
    tenant_id = seed_for_automation(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)
    case_id = db_session.execute(select(Task.case_id).where(Task.tenant_id == tenant_id)).scalars().first()

    catalog = api.get("/api/v1/automation/catalog", headers=headers)
    created = api.post("/api/v1/automation/workflows", headers=headers, json=workflow_payload())
    workflow_id = created.json()["id"]
    activated = api.post(f"/api/v1/automation/workflows/{workflow_id}/activate", headers=headers)
    run = api.post(
        f"/api/v1/automation/workflows/{workflow_id}/run",
        headers=headers,
        json={"event_payload": {"case_id": case_id, "case_status": "active"}, "dry_run": False},
    )

    assert catalog.status_code == 200
    assert "CAPTCHA_REQUIRED" in catalog.json()["triggers"]
    assert created.status_code == 201
    assert activated.json()["status"] == "active"
    assert run.status_code == 200
    assert run.json()["status"] == "succeeded"
    assert len(run.json()["steps"]) == 4
    assert db_session.scalar(select(AutomationRun).where(AutomationRun.tenant_id == tenant_id)) is not None
    assert db_session.scalar(select(AutomationRunStep).where(AutomationRunStep.tenant_id == tenant_id, AutomationRunStep.step_type == "action")) is not None
    assert db_session.scalar(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.action == "automation.run_workflow")) is not None


def test_trigger_conditions_errors_and_permissions(api: TestClient, db_session: Session) -> None:
    seed_for_automation(api, db_session)
    admin_headers = login(api, DEMO_SEED.admin_email)
    client_headers = login(api, DEMO_SEED.client_email)

    created = api.post("/api/v1/automation/workflows", headers=admin_headers, json=workflow_payload())
    workflow_id = created.json()["id"]
    api.post(f"/api/v1/automation/workflows/{workflow_id}/activate", headers=admin_headers)
    skipped = api.post(
        f"/api/v1/automation/workflows/{workflow_id}/run",
        headers=admin_headers,
        json={"event_payload": {"case_status": "closed"}, "dry_run": False},
    )
    invalid = api.post(
        "/api/v1/automation/workflows",
        headers=admin_headers,
        json={**workflow_payload(), "trigger_key": "BAD_TRIGGER"},
    )
    client_blocked = api.get("/api/v1/automation/workflows", headers=client_headers)
    triggered = api.post("/api/v1/automation/triggers/run", headers=admin_headers, json={"trigger_key": "HEARING_UPCOMING", "event_payload": {"case_status": "active"}})

    assert skipped.json()["status"] == "skipped"
    assert invalid.status_code == 422
    assert client_blocked.status_code == 403
    assert len(triggered.json()) == 1


def test_automation_feature_gate_blocks_start_plan(api: TestClient, db_session: Session) -> None:
    seed_for_automation(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)
    changed = api.post("/api/v1/billing/change-plan", headers=headers, json={"plan_code": "START", "seats": 3})
    blocked = api.post("/api/v1/automation/workflows", headers=headers, json=workflow_payload())

    assert changed.status_code == 200
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "Automation Studio requires plan upgrade"
