from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, Base, Case, CrmLead, Tenant
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


def seed_level2(api: TestClient, db_session: Session) -> tuple[dict[str, str], str]:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    return headers, tenant_id


def test_war_room_risk_financial_and_demo_endpoints(api: TestClient, db_session: Session) -> None:
    headers, tenant_id = seed_level2(api, db_session)
    case_id = db_session.scalars(select(Case.id).where(Case.tenant_id == tenant_id)).first()

    war_room = api.get("/api/v1/war-room", headers=headers)
    risk = api.get("/api/v1/risk", headers=headers)
    case_risk = api.get(f"/api/v1/risk/cases/{case_id}", headers=headers)
    financial = api.get("/api/v1/financial/overview", headers=headers)
    case_financial = api.get(f"/api/v1/financial/cases/{case_id}", headers=headers)
    demo = api.post("/api/v1/demo/level2/reset", headers=headers, json={"demo_type": "litigation"})

    assert war_room.status_code == 200
    assert war_room.json()["study_health"]["score"] >= 0
    assert war_room.json()["critical_cases"]
    assert risk.json()["study_score"] >= 0
    assert case_risk.json()["case_id"] == case_id
    assert financial.json()["summary"]["fees"]["cents"] > 0
    assert case_financial.json()["margin"]["cents"] != 0
    assert demo.json()["status"] == "ready"


def test_crm_create_move_convert_and_audit(api: TestClient, db_session: Session) -> None:
    headers, tenant_id = seed_level2(api, db_session)

    created = api.post(
        "/api/v1/crm/leads",
        headers=headers,
        json={
            "company": "Cliente Nivel 2",
            "person_name": "Socia Comercial",
            "email": "socia@n2.example.com",
            "sector": "retail",
            "expected_value_cents": 750000,
            "probability": 45,
            "next_action": "Enviar propuesta",
        },
    )
    lead_id = created.json()["id"]
    moved = api.patch(f"/api/v1/crm/leads/{lead_id}/stage", headers=headers, json={"stage": "won"})
    converted = api.post(f"/api/v1/crm/leads/{lead_id}/convert", headers=headers)

    assert created.status_code == 201
    assert moved.json()["stage"] == "won"
    assert converted.json()["client_id"]
    assert converted.json()["case_id"]
    assert db_session.scalars(select(CrmLead).where(CrmLead.tenant_id == tenant_id, CrmLead.id == lead_id)).first().converted_case_id
    assert db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.action == "crm.lead_converted")).all()


def test_financial_hours_expenses_permissions_and_tenant_isolation(api: TestClient, db_session: Session) -> None:
    headers, tenant_id = seed_level2(api, db_session)
    case_id = db_session.scalars(select(Case.id).where(Case.tenant_id == tenant_id)).first()
    client_headers = login(api, DEMO_SEED.client_email)
    other_tenant = Tenant(name="N2 Other", slug="n2-other")
    db_session.add(other_tenant)
    db_session.commit()

    expense = api.post(f"/api/v1/financial/cases/{case_id}/expenses", headers=headers, json={"description": "Perito", "amount_cents": 50000, "category": "peritos"})
    hours = api.post(f"/api/v1/financial/cases/{case_id}/hours", headers=headers, json={"minutes": 90, "hourly_rate_cents": 30000, "description": "Audiencia"})
    blocked_client = api.get("/api/v1/financial/overview", headers=client_headers)
    blocked_cross_tenant = api.get("/api/v1/risk", headers={**headers, "X-Tenant-Id": other_tenant.id})

    assert expense.status_code == 201
    assert hours.status_code == 201
    assert blocked_client.status_code == 403
    assert blocked_cross_tenant.status_code == 403
