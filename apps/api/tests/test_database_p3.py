from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.judicial_updates import record_judicial_update
from app.db.models import (
    AiJob,
    AuditLog,
    Base,
    Case,
    CaseEvent,
    CaseSource,
    Client,
    Document,
    Hearing,
    JudicialUpdate,
    LegalNews,
    LegalNewsSource,
    Notification,
    Role,
    Task,
    Tenant,
    User,
    WhatsAppMessage,
)
from app.db.seed import seed_demo_database


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_p3_schema_contains_required_tables_and_indexes(db: Session) -> None:
    inspector = inspect(db.bind)
    tables = set(inspector.get_table_names())

    assert {
        "tenants",
        "users",
        "roles",
        "permissions",
        "role_permissions",
        "clients",
        "cases",
        "case_events",
        "case_sources",
        "judicial_updates",
        "documents",
        "hearings",
        "tasks",
        "notifications",
        "audit_logs",
        "whatsapp_messages",
        "ai_jobs",
        "legal_news_sources",
        "legal_news",
    }.issubset(tables)

    case_indexes = {index["name"] for index in inspector.get_indexes("cases")}
    source_indexes = {index["name"] for index in inspector.get_indexes("case_sources")}

    assert "ix_cases_tenant_id" in case_indexes
    assert "ix_cases_client_id" in case_indexes
    assert "ix_cases_status" in case_indexes
    assert "ix_cases_external_case_number" in case_indexes
    assert "ix_case_sources_last_checked_at" in source_indexes


def test_seed_demo_database_populates_mvp_graph(db: Session) -> None:
    result = seed_demo_database(db)

    assert result["tenant_id"]
    assert len(db.scalars(select(User)).all()) == 4
    assert len(db.scalars(select(Client)).all()) == 3
    assert len(db.scalars(select(Case)).all()) == 3
    assert len(db.scalars(select(Document)).all()) == 3
    assert len(db.scalars(select(Hearing)).all()) == 3
    assert len(db.scalars(select(Task)).all()) == 3
    assert len(db.scalars(select(CaseSource)).all()) == 3
    assert len(db.scalars(select(JudicialUpdate)).all()) == 2
    assert len(db.scalars(select(Notification)).all()) >= 4
    assert len(db.scalars(select(LegalNews)).all()) == 1


def test_tenant_isolation_queries_are_scoped(db: Session) -> None:
    seed = seed_demo_database(db)
    other_tenant = Tenant(name="Other", slug="other")
    db.add(other_tenant)
    db.flush()
    other_client = Client(tenant_id=other_tenant.id, name="Other Client")
    db.add(other_client)
    db.flush()
    db.add(Case(tenant_id=other_tenant.id, client_id=other_client.id, title="Other Case"))
    db.commit()

    demo_cases = db.scalars(select(Case).where(Case.tenant_id == seed["tenant_id"])).all()
    other_cases = db.scalars(select(Case).where(Case.tenant_id == other_tenant.id)).all()

    assert len(demo_cases) == 3
    assert len(other_cases) == 1
    assert all(case.tenant_id == seed["tenant_id"] for case in demo_cases)


def test_case_creation_events_sources_and_relationships(db: Session) -> None:
    seed = seed_demo_database(db)
    tenant_id = seed["tenant_id"]
    client = db.scalars(select(Client).where(Client.tenant_id == tenant_id)).first()
    assert client is not None

    legal_case = Case(tenant_id=tenant_id, client_id=client.id, title="Nuevo expediente", external_case_number="EXT-999")
    db.add(legal_case)
    db.flush()
    event = CaseEvent(tenant_id=tenant_id, case_id=legal_case.id, event_type="created", title="Creado")
    source = CaseSource(tenant_id=tenant_id, case_id=legal_case.id, external_case_number="EXT-999")
    db.add_all([event, source])
    db.commit()

    loaded = db.get(Case, legal_case.id)
    assert loaded is not None
    assert loaded.client.id == client.id
    assert loaded.events[0].title == "Creado"
    assert loaded.sources[0].external_case_number == "EXT-999"


def test_judicial_update_without_captcha_records_update_and_audit(db: Session) -> None:
    seed_demo_database(db)
    source = db.scalars(select(CaseSource).where(CaseSource.captcha_required.is_(False))).first()
    assert source is not None

    update = record_judicial_update(
        db,
        tenant_id=source.tenant_id,
        case_id=source.case_id,
        case_source_id=source.id,
        title="Auto nuevo",
        summary="Actualizacion sin CAPTCHA.",
    )
    db.commit()

    audit = db.scalars(select(AuditLog).where(AuditLog.entity_type == "judicial_update")).first()
    assert update.status == "recorded"
    assert update.requires_human_intervention is False
    assert audit is not None


def test_captcha_required_pauses_notifies_and_audits(db: Session) -> None:
    seed_demo_database(db)
    source = db.scalars(select(CaseSource).where(CaseSource.status == "active")).first()
    assert source is not None

    update = record_judicial_update(
        db,
        tenant_id=source.tenant_id,
        case_id=source.case_id,
        case_source_id=source.id,
        title="CAPTCHA detectado",
        summary="Debe intervenir una persona.",
        captcha_required=True,
    )
    db.commit()
    db.refresh(source)

    notification = db.scalars(select(Notification).where(Notification.case_id == source.case_id, Notification.title == "Intervencion humana requerida")).first()
    audit = db.scalars(select(AuditLog).where(AuditLog.action == "captcha_required", AuditLog.entity_id == source.id)).first()

    assert update.status == "paused"
    assert update.captcha_required is True
    assert update.requires_human_intervention is True
    assert source.status == "paused_captcha"
    assert notification is not None
    assert audit is not None
    assert audit.metadata_json["policy"] == "paused_notified_human_intervention"


def test_soft_delete_keeps_record_and_sets_deleted_at(db: Session) -> None:
    seed_demo_database(db)
    legal_case = db.scalars(select(Case)).first()
    assert legal_case is not None

    legal_case.soft_delete()
    db.commit()
    db.refresh(legal_case)

    visible_cases = db.scalars(select(Case).where(Case.deleted_at.is_(None))).all()
    stored_case = db.get(Case, legal_case.id)

    assert stored_case is not None
    assert stored_case.deleted_at is not None
    assert all(case.id != legal_case.id for case in visible_cases)


def test_mvp_relationship_tables_are_tenant_scoped(db: Session) -> None:
    seed = seed_demo_database(db)
    tenant_id = seed["tenant_id"]

    scoped_models = [
        Role,
        Client,
        Case,
        CaseEvent,
        CaseSource,
        JudicialUpdate,
        Document,
        Hearing,
        Task,
        Notification,
        AuditLog,
        WhatsAppMessage,
        AiJob,
        LegalNewsSource,
        LegalNews,
    ]

    for model in scoped_models:
        rows = db.scalars(select(model)).all()
        assert rows
        assert all(row.tenant_id == tenant_id for row in rows)
