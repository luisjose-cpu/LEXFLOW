from datetime import timedelta

from sqlalchemy.orm import Session

from app.db.judicial_updates import record_judicial_update
from app.db.models import (
    AiJob,
    AuditLog,
    AutomationAction,
    AutomationCondition,
    AutomationWorkflow,
    BackupRecord,
    BillingEvent,
    BillingPlan,
    CaseExpense,
    CaseFinancial,
    CaseHour,
    Case,
    CaseEvent,
    CaseSource,
    Client,
    CloudEnvironment,
    CountryConfig,
    Department,
    Document,
    CrmLead,
    DemoSnapshot,
    EnterpriseAiSwarmRun,
    EvidenceVaultItem,
    GovernancePolicy,
    Hearing,
    KnowledgeVaultItem,
    LegalDataEvent,
    LegalGraphEdge,
    LegalGraphNode,
    LegalMemoryItem,
    LegalNews,
    LegalAlert,
    LegalTag,
    LegalNewsCaseLink,
    LegalNewsSource,
    MarketplaceInstallation,
    MarketplaceItem,
    CommunicationMessage,
    CommunicationThread,
    MessageTemplate,
    Notification,
    NotificationRule,
    PlanFeature,
    Permission,
    PublicApiKey,
    Organization,
    OrganizationTenant,
    OrchestrationEvent,
    Role,
    RolePermission,
    RetentionPolicy,
    RevenueInsight,
    Task,
    Team,
    TeamMember,
    Tenant,
    TenantSubscription,
    TenantUsage,
    TelemetryMetric,
    User,
    WebhookSubscription,
    WhatsAppMessage,
    now_utc,
)
from app.services.security import hash_password


ROLE_PERMISSIONS = {
    "tenant_admin": ["users:read", "users:write", "clients:read", "clients:write", "cases:read", "cases:write", "audit:read", "communications:read", "communications:write", "templates:write", "notifications:write", "ai:read", "ai:write", "ai:review", "intelligence:read", "intelligence:write", "dashboard:read", "warroom:read", "crm:read", "crm:write", "financial:read", "financial:write", "risk:read", "demo:write", "billing:read", "billing:write", "automation:read", "automation:write", "automation:run", "legal_os:read", "legal_os:write", "knowledge:read", "knowledge:write", "memory:read", "memory:write", "graph:read", "graph:write", "copilot:read", "marketplace:read", "marketplace:write", "latam:read", "latam:write", "agents:run", "enterprise:read", "enterprise:write", "organizations:read", "organizations:write", "data_platform:read", "data_platform:write", "orchestration:read", "orchestration:write", "ai_swarm:read", "ai_swarm:run", "telemetry:read", "revenue:read", "integrations:api", "governance:read", "governance:write", "cloud:read", "cloud:write"],
    "lawyer": ["clients:read", "clients:write", "cases:read", "cases:write", "communications:read", "communications:write", "templates:write", "notifications:write", "ai:read", "ai:write", "ai:review", "intelligence:read", "intelligence:write", "dashboard:read", "warroom:read", "crm:read", "crm:write", "financial:read", "risk:read", "billing:read", "automation:read", "automation:write", "automation:run", "legal_os:read", "knowledge:read", "knowledge:write", "memory:read", "memory:write", "graph:read", "copilot:read", "marketplace:read", "latam:read", "agents:run", "enterprise:read", "organizations:read", "data_platform:read", "orchestration:read", "ai_swarm:read", "ai_swarm:run", "telemetry:read", "revenue:read", "integrations:api", "governance:read", "cloud:read"],
    "assistant": ["clients:read", "cases:read", "tasks:write", "automation:read", "automation:run", "legal_os:read", "knowledge:read", "memory:read", "graph:read", "marketplace:read", "latam:read", "enterprise:read", "data_platform:read", "telemetry:read", "governance:read"],
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

    db.add_all(
        [
            CrmLead(tenant_id=tenant.id, owner_user_id=admin.id, company="Inversiones Pacifico", person_name="Carla Rios", email="carla@pacifico.demo", phone="+5710000000", sector="corporativo", source="referido", campaign="Demo Nivel 2", expected_value_cents=1250000, probability=72, stage="proposal", next_action="Enviar propuesta piloto", score=82),
            CrmLead(tenant_id=tenant.id, owner_user_id=lawyer.id, company="Litigios Norte", person_name="Marco Silva", email="marco@litigiosnorte.demo", sector="litigios", source="web", campaign="War Room", expected_value_cents=850000, probability=48, stage="meeting", next_action="Agendar demo War Room", score=68),
        ]
    )

    for index, legal_case in enumerate(cases):
        fees = [1800000, 900000, 650000][index]
        db.add(CaseFinancial(tenant_id=tenant.id, case_id=legal_case.id, fees_cents=fees, budget_cents=round(fees * 0.55), invoiced_cents=round(fees * 0.35), pending_cents=round(fees * 0.65)))
        db.add(CaseExpense(tenant_id=tenant.id, case_id=legal_case.id, category="notificaciones", description="Gastos judiciales demo", amount_cents=[90000, 180000, 45000][index], provider="Proveedor demo"))
        db.add(CaseHour(tenant_id=tenant.id, case_id=legal_case.id, user_id=lawyer.id, minutes=[360, 720, 240][index], hourly_rate_cents=22000, description="Trabajo legal demo"))

    db.add(DemoSnapshot(tenant_id=tenant.id, demo_type="litigation", status="ready", snapshot_json={"source": "seed", "modules": ["war-room", "crm", "financial", "risk", "demo"]}))
    db.add_all(
        [
            KnowledgeVaultItem(
                tenant_id=tenant.id,
                source_type="template",
                category="demanda",
                title="Demanda ejecutiva con anexos",
                content_summary="Plantilla demo para cobro ejecutivo con checklist documental y estrategia de seguimiento.",
                tags=["cobro", "ejecutivo", "nova"],
                created_by_user_id=lawyer.id,
            ),
            KnowledgeVaultItem(
                tenant_id=tenant.id,
                source_type="precedent",
                category="laboral",
                title="Precedente interno laboral colectivo",
                content_summary="Criterios demo de control de plazos, audiencia y riesgo operativo en materia laboral colectiva.",
                tags=["laboral", "audiencia", "riesgo"],
                created_by_user_id=lawyer.id,
            ),
            LegalMemoryItem(
                tenant_id=tenant.id,
                entity_type="case",
                entity_id=cases[0].id,
                case_id=cases[0].id,
                client_id=clients[0].id,
                source_type="seed",
                title="Memoria operativa Nova",
                content="Cobro ejecutivo Nova con demanda, anexos, plazo critico y comunicacion WhatsApp mock.",
                chunk_text="Cobro ejecutivo Nova demanda anexos plazo critico comunicacion WhatsApp mock.",
                tags=["nova", "cobro", "plazo"],
                embedding_vector_json=[0.14, 0.22, 0.61, 0.33, 0.44, 0.18],
                citations_json=[{"source_type": "case", "case_id": cases[0].id, "title": cases[0].title}],
            ),
        ]
    )

    client_node = LegalGraphNode(tenant_id=tenant.id, node_type="client", entity_id=clients[0].id, label=clients[0].name, metadata_json={"risk_profile": clients[0].risk_profile})
    case_node = LegalGraphNode(tenant_id=tenant.id, node_type="case", entity_id=cases[0].id, label=cases[0].title, metadata_json={"status": cases[0].status})
    db.add_all([client_node, case_node])
    db.flush()
    db.add(LegalGraphEdge(tenant_id=tenant.id, from_node_id=client_node.id, to_node_id=case_node.id, edge_type="owns", weight=5, metadata_json={"source": "seed"}))

    marketplace_item = MarketplaceItem(
        item_key=f"deadline_risk_pack_{tenant.id[:8]}",
        name="Deadline Risk Pack",
        item_type="automation",
        description="Workflow demo para alertas de plazos, audiencias y CAPTCHA pendientes.",
        permissions_json=["automation:write", "risk:read"],
        metadata_json={"level": "N3", "review_required": True},
    )
    db.add(marketplace_item)
    db.flush()
    db.add(MarketplaceInstallation(tenant_id=tenant.id, marketplace_item_id=marketplace_item.id, installed_by_user_id=admin.id, config_json={"mode": "demo"}))
    db.add(
        CountryConfig(
            tenant_id=tenant.id,
            country_code="PE",
            name="Peru",
            currency="PEN",
            timezone="America/Lima",
            language="es",
            formats_json={"case_number": "district-instance-year-number", "date": "dd/mm/yyyy"},
            legal_sources_json=[{"key": "sinoe", "name": "SINOE", "captcha_policy": "human_in_the_loop"}],
            provider_registry_json=[{"key": "sinoe_mock", "type": "judicial", "status": "mock_ready"}],
        )
    )

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

    organization = Organization(
        name="LEXFLOW Enterprise Group",
        slug=f"lexflow-enterprise-{tenant.id[:8]}",
        org_type="holding",
        country_scope=["PE", "CO", "MX", "CL"],
        branding_json={"white_label": True, "primary_color": "#0f3b63"},
        metadata_json={"seed": True, "level": "N4"},
    )
    db.add(organization)
    db.flush()
    db.add(
        OrganizationTenant(
            organization_id=organization.id,
            tenant_id=tenant.id,
            relationship_type="headquarters",
            country_code="PE",
            brand_name="LEXFLOW Demo Studio",
            permissions_json=["cross_analytics", "cross_reporting", "cross_risk"],
        )
    )
    department = Department(organization_id=organization.id, tenant_id=tenant.id, name="Litigation Command", practice_area="litigation")
    db.add(department)
    db.flush()
    team = Team(tenant_id=tenant.id, department_id=department.id, name="Enterprise Response Team", metadata_json={"focus": ["risk", "sinoe", "automation"]})
    db.add(team)
    db.flush()
    db.add_all(
        [
            TeamMember(tenant_id=tenant.id, team_id=team.id, user_id=admin.id, role="lead"),
            TeamMember(tenant_id=tenant.id, team_id=team.id, user_id=lawyer.id, role="case_owner"),
        ]
    )
    db.add(
        LegalDataEvent(
            tenant_id=tenant.id,
            organization_id=organization.id,
            event_type="case.created",
            entity_type="case",
            entity_id=cases[0].id,
            idempotency_key=f"seed-{tenant.id}-case-created",
            payload_json={"source": "seed", "case_title": cases[0].title, "pipeline": "legal_data_platform"},
            indexed=True,
            processed_at=now_utc(),
        )
    )
    db.add(
        OrchestrationEvent(
            tenant_id=tenant.id,
            organization_id=organization.id,
            event_key="CASE_RISK_ESCALATED",
            state_json={"case_id": cases[1].id, "source": "risk_engine"},
            result_json={"actions": ["notify_partner", "prepare_ai_context", "refresh_dashboard"], "review_required": True},
        )
    )
    db.add(
        EnterpriseAiSwarmRun(
            tenant_id=tenant.id,
            organization_id=organization.id,
            objective="Evaluar riesgo multi-expediente demo",
            agents_json=[
                {"key": "legal_agent", "status": "ready"},
                {"key": "risk_agent", "status": "completed"},
                {"key": "management_agent", "status": "completed"},
            ],
            handoff_json=[
                {"from": "risk_agent", "to": "management_agent", "reason": "priorizar decisiones gerenciales"},
            ],
            actor_user_id=admin.id,
        )
    )
    db.add_all(
        [
            TelemetryMetric(tenant_id=tenant.id, organization_id=organization.id, component="api", metric_key="latency_p95_ms", metric_value=210, unit="ms", metadata_json={"target": "<500"}),
            TelemetryMetric(tenant_id=tenant.id, organization_id=organization.id, component="ai", metric_key="tokens_month", metric_value=12400, unit="tokens", metadata_json={"provider": "mock"}),
            TelemetryMetric(tenant_id=tenant.id, organization_id=organization.id, component="sinoe", metric_key="sync_success_rate", metric_value=98, unit="percent", metadata_json={"captcha_policy": "human_in_the_loop"}),
        ]
    )
    db.add(
        PublicApiKey(
            tenant_id=tenant.id,
            name="Demo Developer API Key",
            key_hash=f"seed-key-hash-{tenant.id}",
            scopes_json=["cases:read", "webhooks:write"],
        )
    )
    db.add(
        WebhookSubscription(
            tenant_id=tenant.id,
            name="Demo Enterprise Webhook",
            target_url="https://hooks.example.com/lexflow",
            event_types_json=["case.updated", "sinoe.update.approved", "automation.failed"],
            secret_hint="whsec_demo",
        )
    )
    db.add_all(
        [
            GovernancePolicy(
                tenant_id=tenant.id,
                organization_id=organization.id,
                policy_type="ai_review",
                name="Revision humana obligatoria IA",
                rules_json={"all_outputs_require_review": True, "citations_required": True},
                approved_by_user_id=admin.id,
            ),
            RetentionPolicy(tenant_id=tenant.id, record_type="documents", retention_days=3650, disposition="archive", legal_hold=True),
            EvidenceVaultItem(
                tenant_id=tenant.id,
                organization_id=organization.id,
                entity_type="judicial_update",
                entity_id=cases[0].id,
                evidence_hash=f"seed-evidence-hash-{tenant.id[:8]}",
                storage_ref=f"evidence/{tenant.id}/seed.json",
                metadata_json={"chain": "seed", "captcha_bypass": False},
            ),
            RevenueInsight(
                tenant_id=tenant.id,
                organization_id=organization.id,
                signal_type="enterprise_upgrade",
                score=84,
                recommendation="Tenant demo apto para plan Enterprise por uso de IA, SINOE, automation y data platform.",
                metadata_json={"trial_conversion": "high", "modules": ["ai", "sinoe", "automation", "api"]},
            ),
        ]
    )
    cloud_environment = CloudEnvironment(
        environment_key=f"staging-{tenant.id[:8]}",
        name="LEXFLOW Staging",
        environment_type="staging",
        region="us-east",
        config_json={"multi_region_future": True, "backup_policy": "daily", "kubernetes_future": True},
    )
    db.add(cloud_environment)
    db.flush()
    db.add(BackupRecord(environment_id=cloud_environment.id, backup_type="database", status="completed", storage_ref=f"managed-backup/{tenant.id}/seed", restore_tested_at=now_utc()))

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
