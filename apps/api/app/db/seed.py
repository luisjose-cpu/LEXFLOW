from datetime import timedelta

from sqlalchemy.orm import Session

from app.db.judicial_updates import record_judicial_update
from app.db.models import (
    AiJob,
    AuditLog,
    AutomationAction,
    AutomationCondition,
    AutomationWorkflow,
    BillingEvent,
    BillingPlan,
    Case,
    CaseEvent,
    CaseSource,
    Client,
    Document,
    Hearing,
    LegalNews,
    LegalAlert,
    LegalTag,
    LegalNewsCaseLink,
    LegalNewsSource,
    CommunicationMessage,
    CommunicationThread,
    MessageTemplate,
    Notification,
    NotificationRule,
    PlanFeature,
    Permission,
    Role,
    RolePermission,
    Task,
    Tenant,
    TenantSubscription,
    TenantUsage,
    User,
    WhatsAppMessage,
    now_utc,
)
from app.services.security import hash_password


ROLE_PERMISSIONS = {
    "tenant_admin": ["users:read", "users:write", "clients:read", "clients:write", "cases:read", "cases:write", "audit:read", "communications:read", "communications:write", "templates:write", "notifications:write", "ai:read", "ai:write", "ai:review", "intelligence:read", "intelligence:write", "dashboard:read", "billing:read", "billing:write", "automation:read", "automation:write", "automation:run"],
    "lawyer": ["clients:read", "clients:write", "cases:read", "cases:write", "communications:read", "communications:write", "templates:write", "notifications:write", "ai:read", "ai:write", "ai:review", "intelligence:read", "intelligence:write", "dashboard:read", "billing:read", "automation:read", "automation:write", "automation:run"],
    "assistant": ["clients:read", "cases:read", "tasks:write", "automation:read", "automation:run"],
    "client_user": ["portal:read", "cases:read"],
}


def seed_demo_database(db: Session, *, tenant_id: str | None = None) -> dict[str, str]:
    tenant = Tenant(id=tenant_id, name="LEXFLOW Demo Studio", slug="demo", plan="trial") if tenant_id else Tenant(name="LEXFLOW Demo Studio", slug="demo", plan="trial")
    db.add(tenant)
    db.flush()

    permission_rows: dict[str, Permission] = {}
    for permission_code in sorted({code for permissions in ROLE_PERMISSIONS.values() for code in permissions}):
        permission = Permission(code=permission_code, description=f"Permission {permission_code}")
        db.add(permission)
        permission_rows[permission_code] = permission
    db.flush()

    roles: dict[str, Role] = {}
    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = Role(tenant_id=tenant.id, name=role_name, description=f"Demo {role_name}", is_system=True)
        db.add(role)
        db.flush()
        roles[role_name] = role
        for permission_code in permission_codes:
            db.add(RolePermission(tenant_id=tenant.id, role_id=role.id, permission_id=permission_rows[permission_code].id))

    admin = User(
        tenant_id=tenant.id,
        role_id=roles["tenant_admin"].id,
        email="admin@lexflow.demo",
        full_name="Demo Admin",
        hashed_password=hash_password("LexflowDemo123!"),
    )
    lawyer = User(
        tenant_id=tenant.id,
        role_id=roles["lawyer"].id,
        email="lawyer@lexflow.demo",
        full_name="Demo Lawyer",
        hashed_password=hash_password("LexflowDemo123!"),
    )
    assistant = User(
        tenant_id=tenant.id,
        role_id=roles["assistant"].id,
        email="assistant@lexflow.demo",
        full_name="Demo Assistant",
        hashed_password=hash_password("LexflowDemo123!"),
    )
    client_user = User(
        tenant_id=tenant.id,
        role_id=roles["client_user"].id,
        email="client@lexflow.demo",
        full_name="Demo Client",
        hashed_password=hash_password("LexflowDemo123!"),
    )
    db.add_all([admin, lawyer, assistant, client_user])
    db.flush()

    clients = [
        Client(tenant_id=tenant.id, name="Nova Capital", contact_email="client@lexflow.demo", tags=["corporate", "priority", "portal"]),
        Client(tenant_id=tenant.id, name="Andes Health", contact_email="legal@andes.demo", risk_profile="high", tags=["health"]),
        Client(tenant_id=tenant.id, name="Mercurio Retail", contact_email="legal@mercurio.demo", tags=["contracts"]),
    ]
    db.add_all(clients)
    db.flush()

    cases = [
        Case(
            tenant_id=tenant.id,
            client_id=clients[0].id,
            title="Cobro ejecutivo Nova",
            external_case_number="11001-31-03-001-2026-00001",
            status="active",
            description="Expediente demo de cobro ejecutivo.",
        ),
        Case(
            tenant_id=tenant.id,
            client_id=clients[1].id,
            title="Laboral colectivo Andes",
            external_case_number="11001-05-02-002-2026-00002",
            status="risk",
            description="Expediente demo laboral.",
        ),
        Case(
            tenant_id=tenant.id,
            client_id=clients[2].id,
            title="Contrato marco Mercurio",
            external_case_number="11001-40-03-003-2026-00003",
            status="active",
            description="Expediente demo contractual.",
        ),
    ]
    db.add_all(cases)
    db.flush()

    for legal_case in cases:
        thread = CommunicationThread(
            tenant_id=tenant.id,
            case_id=legal_case.id,
            client_id=legal_case.client_id,
            subject=f"Comunicacion {legal_case.title}",
            channel="whatsapp",
        )
        db.add(thread)
        db.flush()
        db.add(
            CommunicationMessage(
                tenant_id=tenant.id,
                thread_id=thread.id,
                case_id=legal_case.id,
                client_id=legal_case.client_id,
                sender_user_id=lawyer.id,
                direction="outbound",
                channel="whatsapp",
                body="Actualizacion demo del expediente.",
                status="sent",
                provider_message_id=f"mock-seed-{legal_case.id}",
            )
        )
        db.add(
            CaseEvent(
                tenant_id=tenant.id,
                case_id=legal_case.id,
                event_type="created",
                title="Expediente creado",
                description="Seed inicial del expediente.",
                is_client_visible=True,
            )
        )
        db.add(
            CaseSource(
                tenant_id=tenant.id,
                case_id=legal_case.id,
                external_case_number=legal_case.external_case_number or legal_case.id,
                court_name="Juzgado Demo",
                source_url="https://consulta.demo/judicial",
                last_checked_at=now_utc(),
            )
        )
        db.add(
            Document(
                tenant_id=tenant.id,
                case_id=legal_case.id,
                client_id=legal_case.client_id,
                filename=f"{legal_case.title}.pdf",
                storage_key=f"demo/{legal_case.id}/documento.pdf",
                classification="seed",
                is_client_visible=legal_case.client_id == clients[0].id,
            )
        )
        db.add(
            Hearing(
                tenant_id=tenant.id,
                case_id=legal_case.id,
                title="Audiencia inicial",
                starts_at=now_utc() + timedelta(days=14),
                location="Virtual",
            )
        )
        db.add(
            Task(
                tenant_id=tenant.id,
                case_id=legal_case.id,
                assigned_user_id=lawyer.id,
                title="Revisar expediente y preparar proxima actuacion",
                due_at=now_utc() + timedelta(days=3),
            )
        )
        db.add(
            WhatsAppMessage(
                tenant_id=tenant.id,
                case_id=legal_case.id,
                client_id=legal_case.client_id,
                direction="outbound",
                from_number="+570000000000",
                to_number="+571111111111",
                body="Actualizacion demo del expediente.",
                status="sent",
            )
        )
    db.flush()

    template_specs = [
        ("audiencia_proxima", "Audiencia proxima", "whatsapp", "Recordatorio de audiencia: {{case_title}} tiene audiencia el {{hearing_date}}."),
        ("documento_requerido", "Documento requerido", "whatsapp", "Necesitamos el documento {{document_name}} para continuar con {{case_title}}."),
        ("informe_disponible", "Informe disponible", "portal", "Ya esta disponible el informe de {{case_title}} en tu portal."),
        ("actualizacion_expediente", "Actualizacion expediente", "whatsapp", "Hay una actualizacion aprobada en {{case_title}}: {{update_summary}}."),
        ("proximo_paso", "Proximo paso", "portal", "El proximo paso de {{case_title}} es {{next_action}}."),
    ]
    templates: dict[str, MessageTemplate] = {}
    for code, name, channel, body in template_specs:
        template = MessageTemplate(tenant_id=tenant.id, code=code, name=name, channel=channel, body=body)
        db.add(template)
        templates[code] = template
    db.flush()
    db.add_all(
        [
            NotificationRule(tenant_id=tenant.id, name="Audiencia proxima", event_type="hearing.upcoming", channel="whatsapp", template_id=templates["audiencia_proxima"].id),
            NotificationRule(tenant_id=tenant.id, name="Documento requerido", event_type="document.required", channel="whatsapp", template_id=templates["documento_requerido"].id),
            NotificationRule(tenant_id=tenant.id, name="Informe disponible", event_type="report.available", channel="portal", template_id=templates["informe_disponible"].id),
        ]
    )

    sources = db.query(CaseSource).filter(CaseSource.tenant_id == tenant.id).all()
    record_judicial_update(
        db,
        tenant_id=tenant.id,
        case_id=cases[0].id,
        case_source_id=sources[0].id,
        title="Auto reconoce personeria",
        summary="Actualizacion judicial simulada.",
        actor_user_id=lawyer.id,
    )
    record_judicial_update(
        db,
        tenant_id=tenant.id,
        case_id=cases[1].id,
        case_source_id=sources[1].id,
        title="Fuente requiere CAPTCHA",
        summary="Se pausa la actualizacion para intervencion humana.",
        actor_user_id=assistant.id,
        captcha_required=True,
    )

    for legal_case in cases:
        db.add(Notification(tenant_id=tenant.id, user_id=lawyer.id, case_id=legal_case.id, title="Tarea pendiente", body="Revisar siguiente actuacion."))
        db.add(AiJob(tenant_id=tenant.id, case_id=legal_case.id, job_type="summary", status="queued", input_ref=f"case:{legal_case.id}", result_json={}))

    db.add(
        Notification(
            tenant_id=tenant.id,
            user_id=client_user.id,
            case_id=cases[0].id,
            title="Resumen disponible",
            body="Tu expediente tiene una actualizacion visible en el portal.",
            channel="portal",
            status="sent",
        )
    )

    news_source = LegalNewsSource(
        tenant_id=tenant.id,
        name="Corte Constitucional Demo",
        source_url="https://noticias.demo/legal",
        category="jurisprudence",
        adapter_key="poder_judicial",
        last_checked_at=now_utc(),
        config_json={"policy": "mock_only"},
    )
    db.add(news_source)
    db.flush()
    db.add(
        LegalNews(
            tenant_id=tenant.id,
            source_id=news_source.id,
            title="Sentencia demo sobre debido proceso",
            url="https://noticias.demo/legal/sentencia-demo",
            category="jurisprudence",
            summary="Noticia legal simulada para dashboard.",
            ai_summary="Resumen IA: criterio procesal relevante para revisar expedientes con notificaciones pendientes. Requiere revisión profesional.",
            tags=["jurisprudencia", "debido-proceso"],
            trend_score="rising",
            published_at=now_utc(),
            metadata_json={"adapter": "seed"},
        )
    )
    db.flush()
    db.add_all(
        [
            LegalTag(tenant_id=tenant.id, name="jurisprudencia"),
            LegalTag(tenant_id=tenant.id, name="debido-proceso"),
            LegalAlert(
                tenant_id=tenant.id,
                title="Tendencia jurisprudencial",
                body="Nueva decision demo vinculada a debido proceso.",
                severity="medium",
                tags=["jurisprudencia", "debido-proceso"],
            ),
            LegalNewsCaseLink(tenant_id=tenant.id, case_id=cases[0].id, news_id=db.query(LegalNews).filter(LegalNews.tenant_id == tenant.id).first().id, linked_by_user_id=lawyer.id),
        ]
    )

    billing_specs = [
        ("START", "Start", 4900, {"cases": 50, "users": 3}, {"expediente360": 50, "client_portal": 50, "mobile_pwa": 50, "dashboard": 1}),
        ("PRO", "Pro", 14900, {"cases": 300, "users": 12}, {"expediente360": 300, "client_portal": 300, "whatsapp": 1000, "judicial_automation": 300, "dashboard": 1, "mobile_pwa": 300, "automation_studio": 25}),
        ("AI", "AI", 29900, {"cases": 1000, "users": 30, "ai_jobs": 500}, {"expediente360": 1000, "client_portal": 1000, "whatsapp": 5000, "ai": 500, "legal_intelligence": 1, "judicial_automation": 1000, "dashboard": 1, "mobile_pwa": 1000, "automation_studio": 100, "custom_branding": 1}),
        ("ENTERPRISE", "Enterprise", 0, {"cases": None, "users": None}, {"expediente360": None, "client_portal": None, "whatsapp": None, "ai": None, "legal_intelligence": None, "judicial_automation": None, "dashboard": None, "mobile_pwa": None, "automation_studio": None, "custom_branding": None, "custom_domain": None, "api_access": None}),
    ]
    billing_features = ["expediente360", "client_portal", "whatsapp", "ai", "legal_intelligence", "judicial_automation", "dashboard", "mobile_pwa", "automation_studio", "custom_branding", "custom_domain", "api_access"]
    plans: dict[str, BillingPlan] = {}
    for code, name, price, limits, enabled_features in billing_specs:
        plan = BillingPlan(
            tenant_id=tenant.id,
            code=code,
            name=name,
            description=f"Plan {name} demo para SaaS vendible.",
            monthly_price_cents=price,
            trial_days=14 if code != "ENTERPRISE" else 30,
            limits_json=limits,
        )
        db.add(plan)
        db.flush()
        plans[code] = plan
        for feature_key in billing_features:
            limit_value = enabled_features.get(feature_key)
            db.add(
                PlanFeature(
                    tenant_id=tenant.id,
                    plan_id=plan.id,
                    feature_key=feature_key,
                    enabled=feature_key in enabled_features,
                    limit_value=limit_value if isinstance(limit_value, int) else None,
                    metadata_json={"unlimited": feature_key in enabled_features and limit_value is None},
                )
            )
    subscription = TenantSubscription(
        tenant_id=tenant.id,
        plan_id=plans["AI"].id,
        status="trialing",
        seats=8,
        trial_ends_at=now_utc() + timedelta(days=14),
        current_period_ends_at=now_utc() + timedelta(days=30),
        provider_subscription_id=f"mock-sub-{tenant.id[:8]}",
        metadata_json={"source": "seed_demo"},
    )
    db.add(subscription)
    db.flush()
    db.add_all(
        [
            TenantUsage(tenant_id=tenant.id, feature_key="expediente360", period_key=now_utc().strftime("%Y-%m"), used=3, limit_value=1000),
            TenantUsage(tenant_id=tenant.id, feature_key="ai", period_key=now_utc().strftime("%Y-%m"), used=6, limit_value=500),
            TenantUsage(tenant_id=tenant.id, feature_key="whatsapp", period_key=now_utc().strftime("%Y-%m"), used=8, limit_value=5000),
            BillingEvent(tenant_id=tenant.id, subscription_id=subscription.id, event_type="trial_started", status="processed", payload_json={"plan_code": "AI"}),
        ]
    )

    workflow = AutomationWorkflow(
        tenant_id=tenant.id,
        name="CAPTCHA requerido -> alerta interna",
        description="Pausa automatizacion judicial y notifica al equipo cuando una fuente requiere intervencion humana.",
        trigger_key="CAPTCHA_REQUIRED",
        status="active",
        metadata_json={"phase": "P13"},
    )
    db.add(workflow)
    db.flush()
    db.add_all(
        [
            AutomationCondition(tenant_id=tenant.id, workflow_id=workflow.id, order_index=0, condition_type="ALWAYS", config_json={}),
            AutomationAction(
                tenant_id=tenant.id,
                workflow_id=workflow.id,
                order_index=0,
                action_type="CREATE_INTERNAL_ALERT",
                config_json={"title": "CAPTCHA requiere intervencion"},
            ),
            AutomationAction(
                tenant_id=tenant.id,
                workflow_id=workflow.id,
                order_index=1,
                action_type="CREATE_TASK",
                config_json={"title": "Resolver CAPTCHA de fuente judicial"},
            ),
        ]
    )

    db.add(
        AuditLog(
            tenant_id=tenant.id,
            actor_user_id=admin.id,
            action="seed",
            entity_type="tenant",
            entity_id=tenant.id,
            metadata_json={"phase": "P3"},
        )
    )
    db.commit()
    return {
        "tenant_id": tenant.id,
        "admin_id": admin.id,
        "lawyer_id": lawyer.id,
        "assistant_id": assistant.id,
        "client_user_id": client_user.id,
    }
