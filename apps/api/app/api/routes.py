from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_request_tenant, require_permission
from app.api.owner_dependencies import OwnerPrincipal, require_owner_permission
from app.core.config import get_settings
from app.core.readiness import production_readiness_report
from app.db import models as dbm
from app.db.database import get_db
from app.domain.models import AuditAction, AuditLog, Client, LegalCase, Matter, MatterStatus, Role, RoleName, User
from app.services.automation import automation_service
from app.services.auth import auth_service
from app.services.audit import audit_service
from app.services.billing import billing_service
from app.services.ai_practical import ai_service
from app.services.case_overview import audit_case_action, build_case_overview, get_case_or_404, now
from app.services.cases import case_service
from app.services.client_portal import client_portal_service
from app.services.clients import client_service
from app.services.communication import communication_service, message_template_service, notification_service
from app.services.command_center import (
    ai_analytics_service,
    command_center_service,
    communication_analytics_service,
    dashboard_service,
    judicial_monitoring_service,
    kpi_service,
    legal_trend_analytics_service,
    productivity_service,
    risk_service,
)
from app.services.document_lifecycle import document_lifecycle_service
from app.services.judicial_automation import captcha_checkpoint_service, judicial_source_service, judicial_update_service
from app.services.legal_intelligence import (
    legal_alert_service,
    legal_news_service,
    legal_news_source_service,
    legal_trend_service,
    serialize_alert,
    serialize_news,
    serialize_source,
    tag_service,
)
from app.services.lexflow_os import lexflow_os_service
from app.services.matters import matter_service
from app.services.mobile import mobile_client_service, mobile_lawyer_service
from app.services.ops_center import ops_center_service
from app.services.ops_import import ops_import_service
from app.services.operational_core import operational_core_service
from app.services.owner_auth import owner_auth_service
from app.services.owner_console import owner_console_service
from app.services.roles import role_service
from app.services.seed import DEMO_SEED
from app.services.sinoe_integration import sinoe_automation_service
from app.services.storage import storage_service
from app.services.users import user_service

router = APIRouter()


class MatterCreate(BaseModel):
    client_id: UUID
    title: str
    next_action: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_slug: str | None = None
    mfa_code: str | None = Field(default=None, min_length=6, max_length=12)


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=500)
    new_password: str = Field(min_length=10, max_length=500)


class PasswordResetRequest(BaseModel):
    email: EmailStr
    tenant_slug: str = Field(min_length=2, max_length=120)


class PasswordResetConfirmRequest(BaseModel):
    reset_token: str = Field(min_length=20, max_length=500)
    new_password: str = Field(min_length=10, max_length=500)


class MfaCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=12)


class MfaDisableRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=500)
    code: str | None = Field(default=None, min_length=6, max_length=12)


class UserOut(BaseModel):
    id: UUID
    tenant_id: UUID
    email: EmailStr
    full_name: str
    role: RoleName
    is_active: bool
    mfa_enabled: bool


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserOut


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class OwnerLoginRequest(BaseModel):
    email: EmailStr
    password: str


class OwnerOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    mfa_enabled: bool
    last_login_at: str | None = None


class OwnerLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    owner: OwnerOut


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=10)
    role: RoleName


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: RoleName | None = None
    is_active: bool | None = None


class ClientCreate(BaseModel):
    name: str
    contact_email: EmailStr | None = None
    risk_profile: str = "standard"
    tags: list[str] = Field(default_factory=list)


class ClientUpdate(BaseModel):
    name: str | None = None
    contact_email: EmailStr | None = None
    risk_profile: str | None = None
    tags: list[str] | None = None


class CaseCreate(BaseModel):
    client_id: UUID
    title: str
    description: str | None = None
    next_action: str
    assigned_user_ids: list[UUID] = Field(default_factory=list)


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    next_action: str | None = None


class CaseAssign(BaseModel):
    assigned_user_ids: list[UUID]


class CaseStatusChange(BaseModel):
    status: MatterStatus


class CaseEventCreate(BaseModel):
    event_type: str = "note"
    title: str
    description: str | None = None


class CaseTaskCreate(BaseModel):
    title: str
    assigned_user_id: UUID | None = None
    due_at: str | None = None


class CaseDocumentCreate(BaseModel):
    filename: str
    storage_key: str
    content_type: str = "application/pdf"
    classification: str | None = None


class CaseSourceCreate(BaseModel):
    source_type: str = Field(pattern="^(poder_judicial|cej|sinoe|mpfn)$")
    external_case_number: str
    court_name: str | None = None
    source_url: str | None = None


class SinoeCredentialsRequest(BaseModel):
    username: str = Field(min_length=1, max_length=240)
    password: str = Field(min_length=1, max_length=500)


class SinoeCaseSourceRequest(BaseModel):
    external_case_number: str = Field(min_length=1, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    site: str | None = Field(default=None, max_length=120)
    reference: str | None = Field(default=None, max_length=180)


class CaptchaResolveRequest(BaseModel):
    resolution_note: str


class JudicialDecisionRequest(BaseModel):
    note: str | None = None


class ClientPortalMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class ClientPortalDocumentUpload(BaseModel):
    filename: str = Field(min_length=1, max_length=240)
    content_type: str = "application/pdf"


class DocumentScanMockRequest(BaseModel):
    verdict: str = Field(default="clean", pattern="^(clean|infected)$")


class DocumentRejectRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class CommunicationCreate(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    channel: str = Field(default="portal", pattern="^(portal|whatsapp|email|push)$")
    direction: str = Field(default="outbound", pattern="^(inbound|outbound)$")
    template_id: UUID | None = None
    to_number: str | None = None


class MessageTemplateCreate(BaseModel):
    code: str = Field(min_length=2, max_length=120)
    name: str = Field(min_length=2, max_length=180)
    channel: str = Field(default="whatsapp", pattern="^(portal|whatsapp|email|push)$")
    body: str = Field(min_length=1, max_length=4000)
    subject: str | None = None


class MessageTemplateUpdate(BaseModel):
    name: str | None = None
    channel: str | None = Field(default=None, pattern="^(portal|whatsapp|email|push)$")
    body: str | None = None
    subject: str | None = None
    status: str | None = None


class NotificationSendRequest(BaseModel):
    case_id: UUID
    title: str
    body: str = ""
    channel: str = Field(default="portal", pattern="^(portal|whatsapp|email|push|in_app)$")
    user_id: UUID | None = None
    template_id: UUID | None = None
    variables: dict[str, object] = Field(default_factory=dict)


class OwnerTenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    slug: str = Field(min_length=2, max_length=120)
    plan: str = Field(default="START", max_length=40)
    trial: bool = True
    demo_data: bool = False
    demo_type: str = "general"


class OwnerReasonRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class OwnerPlanChangeRequest(BaseModel):
    plan: str = Field(min_length=2, max_length=40)
    reason: str = Field(min_length=3, max_length=500)


class OwnerPlanCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    monthly_price_cents: int = Field(default=0, ge=0)
    status: str = Field(default="active", max_length=40)
    trial_days: int = Field(default=14, ge=0, le=365)
    limits: dict[str, object] = Field(default_factory=dict)
    features: list[str] = Field(default_factory=list)


class OwnerPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    monthly_price_cents: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, max_length=40)
    trial_days: int | None = Field(default=None, ge=0, le=365)
    limits: dict[str, object] | None = None
    features: list[str] | None = None
    reason: str = Field(default="Actualizacion de plan desde Owner Console", min_length=3, max_length=500)


class OwnerFeatureUpdateRequest(BaseModel):
    features: dict[str, bool]
    reason: str = Field(min_length=3, max_length=500)


class OwnerTenantLimitUpdateRequest(BaseModel):
    limits: dict[str, int] = Field(default_factory=dict)
    hard_limit: bool = True
    reason: str = Field(default="Actualizacion de limites desde Owner Console", min_length=3, max_length=500)


class OwnerTicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    tenant_id: UUID | None = None
    category: str = "support"
    priority: str = "medium"
    body: str = "Ticket creado"


class OwnerTicketResolve(BaseModel):
    resolution: str = Field(min_length=3, max_length=1000)


class OwnerDemoCreate(BaseModel):
    name: str = "LEXFLOW Demo Tenant"
    slug: str | None = None
    plan: str = "AI"
    demo_type: str = "general"


class OwnerInterventionCreate(BaseModel):
    tenant_id: UUID
    reason: str = Field(min_length=5, max_length=1000)
    duration_minutes: int = Field(default=60, ge=5, le=480)
    scopes: list[str] = Field(default_factory=lambda: ["metadata:read"])


class OwnerIncidentCreate(BaseModel):
    component: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=3, max_length=240)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    summary: str = Field(default="", max_length=2000)


class NotificationTestRequest(BaseModel):
    template_id: UUID
    variables: dict[str, object] = Field(default_factory=dict)


class AISearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class AIReviewRequest(BaseModel):
    note: str | None = None


class LegalNewsSourceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    source_url: str = Field(min_length=4, max_length=500)
    category: str = Field(default="news", max_length=80)
    adapter_key: str = Field(default="mock", max_length=120)


class LegalNewsLinkCaseRequest(BaseModel):
    case_id: UUID
    note: str | None = None


class BillingSubscribeRequest(BaseModel):
    plan_code: str = Field(pattern="^(START|PRO|AI|ENTERPRISE)$")
    seats: int = Field(default=3, ge=1, le=1000)


class BillingChangePlanRequest(BaseModel):
    plan_code: str = Field(pattern="^(START|PRO|AI|ENTERPRISE)$")
    seats: int | None = Field(default=None, ge=1, le=1000)


class BillingWebhookMockRequest(BaseModel):
    event_type: str = Field(min_length=3, max_length=120)
    payload: dict[str, object] = Field(default_factory=dict)


class AutomationConditionIn(BaseModel):
    condition_type: str = "ALWAYS"
    config: dict[str, object] = Field(default_factory=dict)


class AutomationActionIn(BaseModel):
    action_type: str
    config: dict[str, object] = Field(default_factory=dict)


class AutomationWorkflowCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str = ""
    trigger_key: str
    conditions: list[AutomationConditionIn] = Field(default_factory=list)
    actions: list[AutomationActionIn] = Field(min_length=1)


class AutomationWorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_key: str | None = None
    conditions: list[AutomationConditionIn] | None = None
    actions: list[AutomationActionIn] | None = None


class AutomationRunRequest(BaseModel):
    event_payload: dict[str, object] = Field(default_factory=dict)
    dry_run: bool = False


class AutomationTriggerRequest(BaseModel):
    trigger_key: str
    event_payload: dict[str, object] = Field(default_factory=dict)


class LexflowOSQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class LexflowOSCopilotRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)


class TenantBootstrapRequest(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    slug: str = Field(min_length=2, max_length=120)
    plan: str = Field(default="pilot", max_length=80)


class CSVImportRequest(BaseModel):
    csv_text: str = Field(min_length=3)
    dry_run: bool = True


def resolve_tenant(x_tenant_id: str | None = Header(default=None)) -> UUID:
    return UUID(x_tenant_id) if x_tenant_id else UUID("00000000-0000-0000-0000-000000000001")


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "service": settings.app_name, "version": settings.api_version}


@router.get("/status")
def api_status() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ready",
        "phase": settings.release_phase,
        "service": settings.app_name,
        "version": settings.api_version,
        "capabilities": [
            "multitenant",
            "jwt-auth",
            "rbac",
            "audit",
            "core-crud",
            "expediente-360",
            "judicial-automation",
            "client-portal",
            "communication",
            "whatsapp-mock",
            "practical-legal-ai",
            "legal-intelligence",
            "legal-command-center",
            "pwa-mobile",
            "billing-saas",
            "automation-studio",
            "hardening-rc1",
            "lexflow-os-final",
            "legal-memory",
            "rag-legal",
            "global-search",
            "legal-copilot",
            "ai-agents",
            "legal-graph",
            "demo-mode",
            "production-readiness",
            "document-storage",
            "storage-bytes",
            "document-trust-lifecycle",
            "tenant-bootstrap",
            "csv-import",
            "pilot-ops-center",
            "production-gate",
            "owner-console",
        ],
        "release": settings.release_name,
    }


@router.get("/readiness")
def api_readiness() -> dict[str, object]:
    return production_readiness_report(get_settings())


@router.post("/owner/auth/login", response_model=OwnerLoginResponse)
def owner_login(payload: OwnerLoginRequest, db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_auth_service.login(db, email=payload.email, password=payload.password, request_id=getattr(request.state, "request_id", None))


@router.post("/owner/auth/refresh", response_model=TokenResponse)
def owner_refresh(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_auth_service.refresh(db, refresh_token=payload.refresh_token, request_id=getattr(request.state, "request_id", None))


@router.post("/owner/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def owner_logout(
    owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> Response:
    if not owner.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner token required")
    db_owner = db.get(dbm.OwnerUser, owner.user_id)
    if not db_owner:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner token subject")
    owner_auth_service.logout(db, owner=db_owner, request_id=getattr(request.state, "request_id", None))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/owner/auth/me")
def owner_me(owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))]) -> dict[str, object]:
    return {"email": owner.email, "role": owner.role, "id": owner.user_id}


@router.get("/owner/dashboard")
def owner_dashboard(_: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    return owner_console_service.dashboard(db)


@router.get("/owner/tenants")
def owner_tenants(_: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, object]]:
    return owner_console_service.list_tenants(db)


@router.post("/owner/tenants", status_code=status.HTTP_201_CREATED)
def owner_create_tenant(payload: OwnerTenantCreate, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("tenants:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.create_tenant(db, owner=owner, payload=payload.model_dump(exclude_none=True), request_id=getattr(request.state, "request_id", None))


@router.get("/owner/tenants/{tenant_id}")
def owner_tenant_detail(tenant_id: UUID, _: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    return owner_console_service.tenant_detail(db, tenant_id=tenant_id)


@router.post("/owner/tenants/{tenant_id}/suspend")
def owner_suspend_tenant(tenant_id: UUID, payload: OwnerReasonRequest, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("tenants:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.suspend_tenant(db, owner=owner, tenant_id=tenant_id, reason=payload.reason, request_id=getattr(request.state, "request_id", None))


@router.post("/owner/tenants/{tenant_id}/reactivate")
def owner_reactivate_tenant(tenant_id: UUID, payload: OwnerReasonRequest, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("tenants:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.reactivate_tenant(db, owner=owner, tenant_id=tenant_id, reason=payload.reason, request_id=getattr(request.state, "request_id", None))


@router.post("/owner/tenants/{tenant_id}/change-plan")
def owner_change_plan(tenant_id: UUID, payload: OwnerPlanChangeRequest, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("billing:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.change_plan(db, owner=owner, tenant_id=tenant_id, plan=payload.plan, reason=payload.reason, request_id=getattr(request.state, "request_id", None))


@router.get("/owner/tenants/{tenant_id}/features")
def owner_get_features(tenant_id: UUID, _: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, object]]:
    return owner_console_service.features(db, tenant_id=tenant_id)


@router.post("/owner/tenants/{tenant_id}/features")
def owner_update_features(tenant_id: UUID, payload: OwnerFeatureUpdateRequest, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("tenants:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> list[dict[str, object]]:
    return owner_console_service.update_features(db, owner=owner, tenant_id=tenant_id, features=payload.features, reason=payload.reason, request_id=getattr(request.state, "request_id", None))


@router.get("/owner/tenants/{tenant_id}/usage")
def owner_tenant_usage(tenant_id: UUID, _: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    return owner_console_service.usage(db, tenant_id=tenant_id)


@router.get("/owner/tenants/{tenant_id}/limits")
def owner_tenant_limits(tenant_id: UUID, _: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, object]]:
    return owner_console_service.limits(db, tenant_id=tenant_id)


@router.post("/owner/tenants/{tenant_id}/limits")
def owner_update_tenant_limits(tenant_id: UUID, payload: OwnerTenantLimitUpdateRequest, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("tenants:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> list[dict[str, object]]:
    return owner_console_service.update_limits(db, owner=owner, tenant_id=tenant_id, limits=payload.limits, hard_limit=payload.hard_limit, reason=payload.reason, request_id=getattr(request.state, "request_id", None))


@router.get("/owner/tenants/{tenant_id}/health-score")
def owner_tenant_health_score(tenant_id: UUID, _: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    return owner_console_service.health_score(db, tenant_id=tenant_id)


@router.get("/owner/plans")
def owner_plans(_: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, object]]:
    return owner_console_service.plans(db)


@router.post("/owner/plans", status_code=status.HTTP_201_CREATED)
def owner_create_plan(payload: OwnerPlanCreate, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("plans:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.create_plan(db, owner=owner, payload=payload.model_dump(), request_id=getattr(request.state, "request_id", None))


@router.patch("/owner/plans/{plan_code}")
def owner_update_plan(plan_code: str, payload: OwnerPlanUpdate, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("plans:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.update_plan(db, owner=owner, plan_code=plan_code, payload=payload.model_dump(exclude_none=True), request_id=getattr(request.state, "request_id", None))


@router.get("/owner/billing")
def owner_billing(_: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    return owner_console_service.billing(db)


@router.get("/owner/support/tickets")
def owner_support_tickets(_: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, object]]:
    return owner_console_service.tickets(db)


@router.post("/owner/support/tickets", status_code=status.HTTP_201_CREATED)
def owner_create_ticket(payload: OwnerTicketCreate, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("support:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.create_ticket(db, owner=owner, payload=payload.model_dump(exclude_none=True), request_id=getattr(request.state, "request_id", None))


@router.post("/owner/support/tickets/{ticket_id}/resolve")
def owner_resolve_ticket(ticket_id: UUID, payload: OwnerTicketResolve, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("support:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.resolve_ticket(db, owner=owner, ticket_id=ticket_id, resolution=payload.resolution, request_id=getattr(request.state, "request_id", None))


@router.get("/owner/system/health")
def owner_system_health(_: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> dict[str, object]:
    return owner_console_service.system_health(db)


@router.get("/owner/system/incidents")
def owner_system_incidents(_: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, object]]:
    return owner_console_service.incidents(db)


@router.post("/owner/system/incidents", status_code=status.HTTP_201_CREATED)
def owner_create_system_incident(payload: OwnerIncidentCreate, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("system:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.create_incident(db, owner=owner, payload=payload.model_dump(), request_id=getattr(request.state, "request_id", None))


@router.post("/owner/system/incidents/{incident_id}/resolve")
def owner_resolve_system_incident(incident_id: UUID, payload: OwnerReasonRequest, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("system:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.resolve_incident(db, owner=owner, incident_id=incident_id, reason=payload.reason, request_id=getattr(request.state, "request_id", None))


@router.get("/owner/demos")
def owner_demo_tenants(_: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, object]]:
    return owner_console_service.demos(db)


@router.post("/owner/demos", status_code=status.HTTP_201_CREATED)
def owner_create_demo_tenant(payload: OwnerDemoCreate, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("demos:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.create_demo(db, owner=owner, payload=payload.model_dump(exclude_none=True), request_id=getattr(request.state, "request_id", None))


@router.post("/owner/demos/{demo_id}/reset")
def owner_reset_demo_tenant(demo_id: UUID, payload: OwnerReasonRequest, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("demos:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.reset_demo(db, owner=owner, demo_id=demo_id, reason=payload.reason, request_id=getattr(request.state, "request_id", None))


@router.get("/owner/interventions")
def owner_interventions(_: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, object]]:
    return owner_console_service.interventions(db)


@router.post("/owner/interventions", status_code=status.HTTP_201_CREATED)
def owner_create_intervention(payload: OwnerInterventionCreate, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("interventions:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.create_intervention(db, owner=owner, payload=payload.model_dump(), request_id=getattr(request.state, "request_id", None))


@router.post("/owner/interventions/{intervention_id}/close")
def owner_close_intervention(intervention_id: UUID, payload: OwnerReasonRequest, owner: Annotated[OwnerPrincipal, Depends(require_owner_permission("interventions:write"))], db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return owner_console_service.close_intervention(db, owner=owner, intervention_id=intervention_id, reason=payload.reason, request_id=getattr(request.state, "request_id", None))


@router.get("/owner/audit-logs")
def owner_audit_logs(_: Annotated[OwnerPrincipal, Depends(require_owner_permission("owner:read"))], db: Annotated[Session, Depends(get_db)]) -> list[dict[str, object]]:
    return owner_console_service.audit_logs(db)


@router.get("/storage/status")
def storage_status(
    actor: Annotated[User, Depends(require_permission("dashboard:read"))],
) -> dict[str, object]:
    return storage_service.provider_status()


@router.post("/ops/bootstrap/current-tenant")
def ops_bootstrap_current_tenant(
    payload: TenantBootstrapRequest,
    actor: Annotated[User, Depends(require_permission("users:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return ops_import_service.bootstrap_current_tenant(
        db,
        tenant_id=tenant_id,
        actor=actor,
        name=payload.name,
        slug=payload.slug,
        plan=payload.plan,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/ops/import/clients")
def ops_import_clients(
    payload: CSVImportRequest,
    actor: Annotated[User, Depends(require_permission("clients:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return ops_import_service.import_clients(
        db,
        tenant_id=tenant_id,
        actor=actor,
        csv_text=payload.csv_text,
        dry_run=payload.dry_run,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/ops/import/cases")
def ops_import_cases(
    payload: CSVImportRequest,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return ops_import_service.import_cases(
        db,
        tenant_id=tenant_id,
        actor=actor,
        csv_text=payload.csv_text,
        dry_run=payload.dry_run,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/ops/import/documents")
def ops_import_documents(
    payload: CSVImportRequest,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return ops_import_service.import_documents(
        db,
        tenant_id=tenant_id,
        actor=actor,
        csv_text=payload.csv_text,
        dry_run=payload.dry_run,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/ops/import/templates")
def ops_import_templates(
    actor: Annotated[User, Depends(require_permission("clients:read"))],
) -> dict[str, object]:
    return ops_center_service.import_templates()


@router.get("/ops/pilot/readiness")
def ops_pilot_readiness(
    actor: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return ops_center_service.pilot_readiness(db, tenant_id=tenant_id)


@router.get("/ops/production-gate")
def ops_production_gate(
    actor: Annotated[User, Depends(require_permission("dashboard:read"))],
) -> dict[str, object]:
    return ops_center_service.production_gate()


@router.put("/storage/mock/{document_id}")
async def storage_mock_upload(
    document_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    token: str = Query(min_length=16),
) -> dict[str, object]:
    body = await request.body()
    return storage_service.store_signed_upload(
        db,
        document_id=document_id,
        token=token,
        body=body,
        content_type=request.headers.get("content-type"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/documents/{document_id}/storage")
def document_storage_status(
    document_id: UUID,
    actor: Annotated[User, Depends(require_permission("cases:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return document_lifecycle_service.storage_status(db, tenant_id=tenant_id, document_id=document_id)


@router.post("/documents/{document_id}/verify-storage")
def document_verify_storage(
    document_id: UUID,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return document_lifecycle_service.verify_storage(
        db,
        tenant_id=tenant_id,
        document_id=document_id,
        actor=actor,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/documents/{document_id}/scan-mock")
def document_scan_mock(
    document_id: UUID,
    payload: DocumentScanMockRequest,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return document_lifecycle_service.scan_mock(
        db,
        tenant_id=tenant_id,
        document_id=document_id,
        actor=actor,
        verdict=payload.verdict,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/documents/{document_id}/reject")
def document_reject(
    document_id: UUID,
    payload: DocumentRejectRequest,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return document_lifecycle_service.reject(
        db,
        tenant_id=tenant_id,
        document_id=document_id,
        actor=actor,
        reason=payload.reason,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/storage/mock/{document_id}")
def storage_mock_download(
    document_id: UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    token: str = Query(min_length=16),
) -> Response:
    body, metadata = storage_service.read_signed_download(
        db,
        document_id=document_id,
        token=token,
        request_id=getattr(request.state, "request_id", None),
    )
    return Response(
        content=body,
        media_type=str(metadata["content_type"]),
        headers={
            "Content-Disposition": f'attachment; filename="{metadata["filename"]}"',
            "X-Content-SHA256": str(metadata["sha256"]),
            "X-Content-Length": str(metadata["bytes"]),
        },
    )


@router.get("/seed/demo")
def seed_demo() -> dict[str, str]:
    return {
        "tenant_slug": DEMO_SEED.tenant_slug,
        "admin_email": DEMO_SEED.admin_email,
        "lawyer_email": DEMO_SEED.lawyer_email,
        "client_email": DEMO_SEED.client_email,
        "password": "configured-for-local-seed",
    }


@router.get("/lexflow-os/memory")
def lexflow_os_memory(
    actor: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return lexflow_os_service.memory(db, tenant_id=tenant_id)


@router.post("/lexflow-os/rag/query")
def lexflow_os_rag_query(
    payload: LexflowOSQueryRequest,
    actor: Annotated[User, Depends(require_permission("ai:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return lexflow_os_service.rag_query(
        db,
        tenant_id=tenant_id,
        actor=actor,
        query=payload.query,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/lexflow-os/search")
def lexflow_os_global_search(
    payload: LexflowOSQueryRequest,
    actor: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return lexflow_os_service.global_search(
        db,
        tenant_id=tenant_id,
        actor=actor,
        query=payload.query,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/lexflow-os/copilot")
def lexflow_os_copilot(
    payload: LexflowOSCopilotRequest,
    actor: Annotated[User, Depends(require_permission("ai:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return lexflow_os_service.copilot(
        db,
        tenant_id=tenant_id,
        actor=actor,
        prompt=payload.prompt,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/lexflow-os/agents")
def lexflow_os_agents(
    actor: Annotated[User, Depends(require_permission("ai:read"))],
) -> dict[str, object]:
    return lexflow_os_service.agents()


@router.get("/lexflow-os/graph")
def lexflow_os_graph(
    actor: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return lexflow_os_service.graph(db, tenant_id=tenant_id)


@router.get("/lexflow-os/marketplace")
def lexflow_os_marketplace(
    actor: Annotated[User, Depends(require_permission("dashboard:read"))],
) -> dict[str, object]:
    return lexflow_os_service.marketplace()


@router.get("/lexflow-os/demo")
def lexflow_os_demo(
    actor: Annotated[User, Depends(require_permission("dashboard:read"))],
) -> dict[str, object]:
    return lexflow_os_service.demo_mode()


@router.get("/lexflow-os/release-status")
def lexflow_os_release_status(
    actor: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return lexflow_os_service.release_status(db, tenant_id=tenant_id)


@router.get("/automation/catalog")
def automation_catalog(
    actor: Annotated[User, Depends(require_permission("automation:read"))],
) -> dict[str, object]:
    return automation_service.catalog()


@router.get("/automation/workflows")
def automation_workflows(
    actor: Annotated[User, Depends(require_permission("automation:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return automation_service.list_workflows(db, tenant_id=tenant_id)


@router.post("/automation/workflows", status_code=status.HTTP_201_CREATED)
def automation_create_workflow(
    payload: AutomationWorkflowCreate,
    actor: Annotated[User, Depends(require_permission("automation:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return automation_service.create_workflow(
        db,
        tenant_id=tenant_id,
        actor=actor,
        name=payload.name,
        trigger_key=payload.trigger_key,
        description=payload.description,
        conditions=[item.model_dump() for item in payload.conditions],
        actions=[item.model_dump() for item in payload.actions],
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/automation/workflows/{workflow_id}")
def automation_get_workflow(
    workflow_id: UUID,
    actor: Annotated[User, Depends(require_permission("automation:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return automation_service.serialize_workflow(automation_service.workflow_or_404(db, tenant_id=tenant_id, workflow_id=workflow_id))


@router.patch("/automation/workflows/{workflow_id}")
def automation_update_workflow(
    workflow_id: UUID,
    payload: AutomationWorkflowUpdate,
    actor: Annotated[User, Depends(require_permission("automation:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return automation_service.update_workflow(
        db,
        tenant_id=tenant_id,
        workflow_id=workflow_id,
        actor=actor,
        name=payload.name,
        description=payload.description,
        trigger_key=payload.trigger_key,
        conditions=[item.model_dump() for item in payload.conditions] if payload.conditions is not None else None,
        actions=[item.model_dump() for item in payload.actions] if payload.actions is not None else None,
        request_id=getattr(request.state, "request_id", None),
    )


@router.delete("/automation/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def automation_delete_workflow(
    workflow_id: UUID,
    actor: Annotated[User, Depends(require_permission("automation:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> None:
    automation_service.delete(db, tenant_id=tenant_id, workflow_id=workflow_id, actor=actor, request_id=getattr(request.state, "request_id", None))


@router.post("/automation/workflows/{workflow_id}/activate")
def automation_activate_workflow(
    workflow_id: UUID,
    actor: Annotated[User, Depends(require_permission("automation:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return automation_service.activate(db, tenant_id=tenant_id, workflow_id=workflow_id, actor=actor, request_id=getattr(request.state, "request_id", None))


@router.post("/automation/workflows/{workflow_id}/run")
def automation_run_workflow(
    workflow_id: UUID,
    payload: AutomationRunRequest,
    actor: Annotated[User, Depends(require_permission("automation:run"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return automation_service.run_workflow(db, tenant_id=tenant_id, workflow_id=workflow_id, actor=actor, event_payload=payload.event_payload, dry_run=payload.dry_run, request_id=getattr(request.state, "request_id", None))


@router.post("/automation/triggers/run")
def automation_trigger_run(
    payload: AutomationTriggerRequest,
    actor: Annotated[User, Depends(require_permission("automation:run"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> list[dict[str, object]]:
    return automation_service.trigger(db, tenant_id=tenant_id, trigger_key=payload.trigger_key, actor=actor, event_payload=payload.event_payload, request_id=getattr(request.state, "request_id", None))


@router.get("/automation/runs")
def automation_runs(
    actor: Annotated[User, Depends(require_permission("automation:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    workflow_id: UUID | None = Query(default=None),
) -> list[dict[str, object]]:
    return automation_service.list_runs(db, tenant_id=tenant_id, workflow_id=workflow_id)


@router.get("/billing/plans")
def billing_plans(
    actor: Annotated[User, Depends(require_permission("billing:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return billing_service.list_plans(db, tenant_id=tenant_id)


@router.get("/billing/current")
def billing_current(
    actor: Annotated[User, Depends(require_permission("billing:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return billing_service.current(db, tenant_id=tenant_id)


@router.post("/billing/subscribe-mock", status_code=status.HTTP_201_CREATED)
def billing_subscribe_mock(
    payload: BillingSubscribeRequest,
    actor: Annotated[User, Depends(require_permission("billing:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return billing_service.subscribe_mock(
        db,
        tenant_id=tenant_id,
        actor=actor,
        plan_code=payload.plan_code,
        seats=payload.seats,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/billing/change-plan")
def billing_change_plan(
    payload: BillingChangePlanRequest,
    actor: Annotated[User, Depends(require_permission("billing:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return billing_service.change_plan(
        db,
        tenant_id=tenant_id,
        actor=actor,
        plan_code=payload.plan_code,
        seats=payload.seats,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/billing/usage")
def billing_usage(
    actor: Annotated[User, Depends(require_permission("billing:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return billing_service.usage(db, tenant_id=tenant_id)


@router.get("/billing/features")
def billing_features(
    actor: Annotated[User, Depends(require_permission("billing:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return billing_service.features(db, tenant_id=tenant_id)


@router.post("/billing/webhook/mock")
def billing_webhook_mock(
    payload: BillingWebhookMockRequest,
    actor: Annotated[User, Depends(require_permission("billing:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return billing_service.webhook_mock(
        db,
        tenant_id=tenant_id,
        actor=actor,
        event_type=payload.event_type,
        payload=payload.payload,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request) -> dict[str, object]:
    return auth_service.login(
        email=payload.email,
        password=payload.password,
        tenant_slug=payload.tenant_slug,
        mfa_code=payload.mfa_code,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, request: Request) -> dict[str, str]:
    return auth_service.refresh(refresh_token=payload.refresh_token, request_id=getattr(request.state, "request_id", None))


@router.post("/auth/password-reset/request")
def request_password_reset(payload: PasswordResetRequest, db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return auth_service.request_password_reset(
        db,
        email=payload.email,
        tenant_slug=payload.tenant_slug,
        request_id=getattr(request.state, "request_id", None),
        requested_ip=request.client.host if request.client else None,
    )


@router.post("/auth/password-reset/confirm")
def confirm_password_reset(payload: PasswordResetConfirmRequest, db: Annotated[Session, Depends(get_db)], request: Request) -> dict[str, object]:
    return auth_service.confirm_password_reset(db, reset_token=payload.reset_token, new_password=payload.new_password, request_id=getattr(request.state, "request_id", None))


@router.post("/auth/logout")
def logout(current_user: Annotated[User, Depends(get_current_user)], request: Request) -> dict[str, str]:
    auth_service.logout(user=current_user, request_id=getattr(request.state, "request_id", None))
    return {"status": "logged_out"}


@router.post("/auth/change-password", response_model=LoginResponse)
def change_password(payload: ChangePasswordRequest, current_user: Annotated[User, Depends(get_current_user)], request: Request) -> dict[str, object]:
    return auth_service.change_password(user=current_user, current_password=payload.current_password, new_password=payload.new_password, request_id=getattr(request.state, "request_id", None))


@router.get("/auth/mfa/status")
def mfa_status(current_user: Annotated[User, Depends(get_current_user)]) -> dict[str, object]:
    return auth_service.mfa_status(user=current_user)


@router.post("/auth/mfa/enroll")
def enroll_mfa(current_user: Annotated[User, Depends(get_current_user)], request: Request) -> dict[str, object]:
    return auth_service.start_mfa_enrollment(user=current_user, request_id=getattr(request.state, "request_id", None))


@router.post("/auth/mfa/verify", response_model=LoginResponse)
def verify_mfa(payload: MfaCodeRequest, current_user: Annotated[User, Depends(get_current_user)], request: Request) -> dict[str, object]:
    return auth_service.confirm_mfa_enrollment(user=current_user, code=payload.code, request_id=getattr(request.state, "request_id", None))


@router.post("/auth/mfa/disable", response_model=LoginResponse)
def disable_mfa(payload: MfaDisableRequest, current_user: Annotated[User, Depends(get_current_user)], request: Request) -> dict[str, object]:
    return auth_service.disable_mfa(user=current_user, current_password=payload.current_password, code=payload.code, request_id=getattr(request.state, "request_id", None))


@router.get("/auth/me", response_model=UserOut)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user


@router.get("/client-portal/me")
def client_portal_me(
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return client_portal_service.me(db, actor=actor)


@router.get("/client-portal/cases")
def client_portal_cases(
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return client_portal_service.cases(db, actor=actor)


@router.get("/client-portal/cases/{case_id}")
def client_portal_case_detail(
    case_id: UUID,
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return client_portal_service.case_detail(db, actor=actor, case_id=case_id)


@router.get("/client-portal/cases/{case_id}/timeline")
def client_portal_case_timeline(
    case_id: UUID,
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return client_portal_service.timeline(db, actor=actor, case_id=case_id)


@router.get("/client-portal/cases/{case_id}/documents")
def client_portal_case_documents(
    case_id: UUID,
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return client_portal_service.documents(db, actor=actor, case_id=case_id)


@router.get("/client-portal/cases/{case_id}/hearings")
def client_portal_case_hearings(
    case_id: UUID,
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return client_portal_service.hearings(db, actor=actor, case_id=case_id)


@router.get("/client-portal/notifications")
def client_portal_notifications(
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return client_portal_service.notifications(db, actor=actor)


@router.post("/client-portal/cases/{case_id}/messages", status_code=status.HTTP_201_CREATED)
def client_portal_create_message(
    case_id: UUID,
    payload: ClientPortalMessageCreate,
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return client_portal_service.create_message(
        db,
        actor=actor,
        case_id=case_id,
        body=payload.body,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/client-portal/cases/{case_id}/documents", status_code=status.HTTP_201_CREATED)
def client_portal_upload_document(
    case_id: UUID,
    payload: ClientPortalDocumentUpload,
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return client_portal_service.upload_document(
        db,
        actor=actor,
        case_id=case_id,
        filename=payload.filename,
        content_type=payload.content_type,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/client-portal/documents/{document_id}/download")
def client_portal_download_document(
    document_id: UUID,
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return client_portal_service.download_document(
        db,
        actor=actor,
        document_id=document_id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/client-portal/reports")
def client_portal_reports(
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return client_portal_service.reports(db, actor=actor)


def serialize_template(template: dbm.MessageTemplate) -> dict[str, object]:
    return {
        "id": template.id,
        "code": template.code,
        "name": template.name,
        "channel": template.channel,
        "subject": template.subject,
        "body": template.body,
        "status": template.status,
    }


def serialize_notification(notification: dbm.Notification) -> dict[str, object]:
    return {
        "id": notification.id,
        "case_id": notification.case_id,
        "user_id": notification.user_id,
        "title": notification.title,
        "body": notification.body,
        "channel": notification.channel,
        "status": notification.status,
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
        "created_at": notification.created_at.isoformat(),
    }


@router.get("/cases/{case_id}/communications")
def list_case_communications(
    case_id: UUID,
    _: Annotated[User, Depends(require_permission("communications:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return communication_service.list_case_communications(db, tenant_id=tenant_id, case_id=case_id)


@router.post("/cases/{case_id}/communications", status_code=status.HTTP_201_CREATED)
def create_case_communication(
    case_id: UUID,
    payload: CommunicationCreate,
    actor: Annotated[User, Depends(require_permission("communications:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    body = payload.body
    if payload.template_id:
        template = message_template_service.get(db, tenant_id=tenant_id, template_id=payload.template_id)
        body = message_template_service.render(template, {"case_id": str(case_id)})
    message = communication_service.create_message(
        db,
        tenant_id=tenant_id,
        case_id=case_id,
        actor_user_id=actor.id,
        body=body,
        direction=payload.direction,
        channel=payload.channel,
        template_id=payload.template_id,
        to_number=payload.to_number,
        request_id=getattr(request.state, "request_id", None),
    )
    return communication_service.serialize_message(message)


@router.get("/message-templates")
def list_message_templates(
    _: Annotated[User, Depends(require_permission("communications:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return [serialize_template(template) for template in message_template_service.list(db, tenant_id=tenant_id)]


@router.post("/message-templates", status_code=status.HTTP_201_CREATED)
def create_message_template(
    payload: MessageTemplateCreate,
    _: Annotated[User, Depends(require_permission("templates:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    template = message_template_service.create(
        db,
        tenant_id=tenant_id,
        code=payload.code,
        name=payload.name,
        channel=payload.channel,
        body=payload.body,
        subject=payload.subject,
    )
    return serialize_template(template)


@router.patch("/message-templates/{template_id}")
def update_message_template(
    template_id: UUID,
    payload: MessageTemplateUpdate,
    _: Annotated[User, Depends(require_permission("templates:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    template = message_template_service.update(
        db,
        tenant_id=tenant_id,
        template_id=template_id,
        name=payload.name,
        channel=payload.channel,
        body=payload.body,
        subject=payload.subject,
        status_value=payload.status,
    )
    return serialize_template(template)


@router.delete("/message-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message_template(
    template_id: UUID,
    _: Annotated[User, Depends(require_permission("templates:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    message_template_service.delete(db, tenant_id=tenant_id, template_id=template_id)


@router.get("/notifications")
def list_notifications(
    _: Annotated[User, Depends(require_permission("communications:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return [serialize_notification(notification) for notification in notification_service.list(db, tenant_id=tenant_id)]


@router.post("/notifications/send", status_code=status.HTTP_201_CREATED)
def send_notification(
    payload: NotificationSendRequest,
    actor: Annotated[User, Depends(require_permission("notifications:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    notification = notification_service.send(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        case_id=payload.case_id,
        title=payload.title,
        body=payload.body,
        channel=payload.channel,
        user_id=payload.user_id,
        template_id=payload.template_id,
        variables=payload.variables,
        request_id=getattr(request.state, "request_id", None),
    )
    return serialize_notification(notification)


@router.post("/notifications/test")
def test_notification(
    payload: NotificationTestRequest,
    _: Annotated[User, Depends(require_permission("communications:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return notification_service.test(db, tenant_id=tenant_id, template_id=payload.template_id, variables=payload.variables)


@router.post("/notifications/{notification_id}/mark-read")
def mark_notification_read(
    notification_id: UUID,
    actor: Annotated[User, Depends(require_permission("communications:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    notification = notification_service.mark_read(db, tenant_id=tenant_id, notification_id=notification_id, actor=actor)
    return serialize_notification(notification)


@router.post("/ai/documents/{document_id}/ocr", status_code=status.HTTP_201_CREATED)
def ai_document_ocr(
    document_id: UUID,
    actor: Annotated[User, Depends(require_permission("ai:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    document = ai_service.document_or_404(db, tenant_id=tenant_id, document_id=document_id)
    job = ai_service.ocr_service.run(db, tenant_id=tenant_id, document=document, actor_user_id=actor.id, request_id=getattr(request.state, "request_id", None))
    return ai_service.serialize_job(job)


@router.post("/ai/documents/{document_id}/summarize", status_code=status.HTTP_201_CREATED)
def ai_document_summarize(
    document_id: UUID,
    actor: Annotated[User, Depends(require_permission("ai:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    document = ai_service.document_or_404(db, tenant_id=tenant_id, document_id=document_id)
    job = ai_service.document_service.analyze(db, tenant_id=tenant_id, document=document, actor_user_id=actor.id, operation="summarize", request_id=getattr(request.state, "request_id", None))
    return ai_service.serialize_job(job)


@router.post("/ai/documents/{document_id}/classify", status_code=status.HTTP_201_CREATED)
def ai_document_classify(
    document_id: UUID,
    actor: Annotated[User, Depends(require_permission("ai:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    document = ai_service.document_or_404(db, tenant_id=tenant_id, document_id=document_id)
    job = ai_service.document_service.analyze(db, tenant_id=tenant_id, document=document, actor_user_id=actor.id, operation="classify", request_id=getattr(request.state, "request_id", None))
    return ai_service.serialize_job(job)


@router.post("/ai/documents/{document_id}/extract", status_code=status.HTTP_201_CREATED)
def ai_document_extract(
    document_id: UUID,
    actor: Annotated[User, Depends(require_permission("ai:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    document = ai_service.document_or_404(db, tenant_id=tenant_id, document_id=document_id)
    job = ai_service.document_service.analyze(db, tenant_id=tenant_id, document=document, actor_user_id=actor.id, operation="extract", request_id=getattr(request.state, "request_id", None))
    return ai_service.serialize_job(job)


@router.post("/ai/cases/{case_id}/summary", status_code=status.HTTP_201_CREATED)
def ai_case_summary(
    case_id: UUID,
    actor: Annotated[User, Depends(require_permission("ai:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    legal_case = ai_service.case_or_404(db, tenant_id=tenant_id, case_id=case_id)
    job = ai_service.case_service.summarize(db, tenant_id=tenant_id, legal_case=legal_case, actor_user_id=actor.id, request_id=getattr(request.state, "request_id", None))
    return ai_service.serialize_job(job)


@router.post("/ai/cases/{case_id}/search", status_code=status.HTTP_201_CREATED)
def ai_case_search(
    case_id: UUID,
    payload: AISearchRequest,
    actor: Annotated[User, Depends(require_permission("ai:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    legal_case = ai_service.case_or_404(db, tenant_id=tenant_id, case_id=case_id)
    job = ai_service.case_service.search(db, tenant_id=tenant_id, legal_case=legal_case, actor_user_id=actor.id, query=payload.query, request_id=getattr(request.state, "request_id", None))
    return ai_service.serialize_job(job)


@router.get("/ai/jobs/{job_id}")
def ai_job_detail(
    job_id: UUID,
    _: Annotated[User, Depends(require_permission("ai:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return ai_service.serialize_job(ai_service.job_service.get(db, tenant_id=tenant_id, job_id=job_id))


@router.post("/ai/jobs/{job_id}/approve")
def ai_job_approve(
    job_id: UUID,
    payload: AIReviewRequest,
    actor: Annotated[User, Depends(require_permission("ai:review"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    job = ai_service.job_service.decide(db, tenant_id=tenant_id, job_id=job_id, actor=actor, decision="approve", note=payload.note, request_id=getattr(request.state, "request_id", None))
    return ai_service.serialize_job(job)


@router.post("/ai/jobs/{job_id}/reject")
def ai_job_reject(
    job_id: UUID,
    payload: AIReviewRequest,
    actor: Annotated[User, Depends(require_permission("ai:review"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    job = ai_service.job_service.decide(db, tenant_id=tenant_id, job_id=job_id, actor=actor, decision="reject", note=payload.note, request_id=getattr(request.state, "request_id", None))
    return ai_service.serialize_job(job)


@router.get("/legal-intelligence/sources")
def legal_intelligence_sources(
    _: Annotated[User, Depends(require_permission("intelligence:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return [serialize_source(source) for source in legal_news_source_service.list(db, tenant_id=tenant_id)]


@router.post("/legal-intelligence/sources", status_code=status.HTTP_201_CREATED)
def legal_intelligence_create_source(
    payload: LegalNewsSourceCreate,
    actor: Annotated[User, Depends(require_permission("intelligence:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    source = legal_news_source_service.create(
        db,
        tenant_id=tenant_id,
        name=payload.name,
        source_url=payload.source_url,
        category=payload.category,
        adapter_key=payload.adapter_key,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )
    return serialize_source(source)


@router.post("/legal-intelligence/sources/{source_id}/sync")
def legal_intelligence_sync_source(
    source_id: UUID,
    actor: Annotated[User, Depends(require_permission("intelligence:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return legal_news_source_service.sync(db, tenant_id=tenant_id, source_id=source_id, actor_user_id=actor.id, request_id=getattr(request.state, "request_id", None))


@router.get("/legal-intelligence/news")
def legal_intelligence_news(
    actor: Annotated[User, Depends(require_permission("intelligence:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    search: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    category: str | None = Query(default=None),
) -> list[dict[str, object]]:
    favorites = {
        favorite.news_id
        for favorite in db.query(dbm.LegalNewsFavorite).filter(
            dbm.LegalNewsFavorite.tenant_id == str(tenant_id),
            dbm.LegalNewsFavorite.user_id == str(actor.id),
        )
    }
    return [serialize_news(news, favorite=news.id in favorites) for news in legal_news_service.list(db, tenant_id=tenant_id, search=search, tag=tag, category=category)]


@router.get("/legal-intelligence/news/{news_id}")
def legal_intelligence_news_detail(
    news_id: UUID,
    actor: Annotated[User, Depends(require_permission("intelligence:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    favorite = db.query(dbm.LegalNewsFavorite).filter(
        dbm.LegalNewsFavorite.tenant_id == str(tenant_id),
        dbm.LegalNewsFavorite.news_id == str(news_id),
        dbm.LegalNewsFavorite.user_id == str(actor.id),
    ).first()
    return serialize_news(legal_news_service.get(db, tenant_id=tenant_id, news_id=news_id), favorite=bool(favorite))


@router.post("/legal-intelligence/news/{news_id}/summarize")
def legal_intelligence_summarize_news(
    news_id: UUID,
    actor: Annotated[User, Depends(require_permission("intelligence:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    news = legal_news_service.summarize(db, tenant_id=tenant_id, news_id=news_id, actor_user_id=actor.id, request_id=getattr(request.state, "request_id", None))
    return serialize_news(news, favorite=False)


@router.post("/legal-intelligence/news/{news_id}/favorite")
def legal_intelligence_favorite_news(
    news_id: UUID,
    actor: Annotated[User, Depends(require_permission("intelligence:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return legal_news_service.favorite(db, tenant_id=tenant_id, news_id=news_id, actor_user_id=actor.id, request_id=getattr(request.state, "request_id", None))


@router.post("/legal-intelligence/news/{news_id}/link-case")
def legal_intelligence_link_news_to_case(
    news_id: UUID,
    payload: LegalNewsLinkCaseRequest,
    actor: Annotated[User, Depends(require_permission("intelligence:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return legal_news_service.link_case(
        db,
        tenant_id=tenant_id,
        news_id=news_id,
        case_id=payload.case_id,
        actor_user_id=actor.id,
        note=payload.note,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/legal-intelligence/alerts")
def legal_intelligence_alerts(
    _: Annotated[User, Depends(require_permission("intelligence:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return [serialize_alert(alert) for alert in legal_alert_service.list(db, tenant_id=tenant_id)]


@router.get("/legal-intelligence/tags")
def legal_intelligence_tags(
    _: Annotated[User, Depends(require_permission("intelligence:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return [{"id": tag.id, "name": tag.name, "color": tag.color} for tag in tag_service.list(db, tenant_id=tenant_id)]


@router.get("/legal-intelligence/trends")
def legal_intelligence_trends(
    _: Annotated[User, Depends(require_permission("intelligence:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return legal_trend_service.trends(db, tenant_id=tenant_id)


@router.get("/dashboard/overview")
def dashboard_overview(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return dashboard_service.overview(db, tenant_id=tenant_id)


@router.get("/dashboard/search")
def dashboard_search(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    q: str = Query(default=""),
    limit: int = Query(default=12, ge=1, le=50),
) -> dict[str, object]:
    return operational_core_service.global_search(db, tenant_id=tenant_id, query=q, limit=limit)


@router.get("/dashboard/kpis")
def dashboard_kpis(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return kpi_service.kpis(db, tenant_id=tenant_id)


@router.get("/dashboard/risks")
def dashboard_risks(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return risk_service.risks(db, tenant_id=tenant_id)


@router.get("/dashboard/productivity")
def dashboard_productivity(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return productivity_service.productivity(db, tenant_id=tenant_id)


@router.get("/dashboard/judicial-monitoring")
def dashboard_judicial_monitoring(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return judicial_monitoring_service.monitoring(db, tenant_id=tenant_id)


@router.get("/dashboard/communications")
def dashboard_communications(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return communication_analytics_service.analytics(db, tenant_id=tenant_id)


@router.get("/dashboard/ai")
def dashboard_ai(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return ai_analytics_service.analytics(db, tenant_id=tenant_id)


@router.get("/dashboard/legal-intelligence")
def dashboard_legal_intelligence(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return legal_trend_analytics_service.analytics(db, tenant_id=tenant_id)


@router.get("/dashboard/trends")
def dashboard_trends(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return legal_trend_analytics_service.analytics(db, tenant_id=tenant_id)


@router.get("/dashboard/snapshot")
def dashboard_snapshot(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return command_center_service.snapshot(db, tenant_id=tenant_id)


@router.get("/mobile/client/home")
def mobile_client_home(
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return mobile_client_service.home(db, actor=actor)


@router.get("/mobile/client/cases")
def mobile_client_cases(
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return mobile_client_service.cases(db, actor=actor)


@router.get("/mobile/client/cases/{case_id}")
def mobile_client_case_detail(
    case_id: UUID,
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return mobile_client_service.case_detail(db, actor=actor, case_id=case_id)


@router.get("/mobile/client/documents")
def mobile_client_documents(
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return mobile_client_service.documents(db, actor=actor)


@router.get("/mobile/client/messages")
def mobile_client_messages(
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return mobile_client_service.messages(db, actor=actor)


@router.get("/mobile/client/notifications")
def mobile_client_notifications(
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return mobile_client_service.notifications(db, actor=actor)


@router.get("/mobile/lawyer/home")
def mobile_lawyer_home(
    actor: Annotated[User, Depends(require_permission("cases:read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return mobile_lawyer_service.home(db, actor=actor)


@router.get("/mobile/lawyer/cases")
def mobile_lawyer_cases(
    actor: Annotated[User, Depends(require_permission("cases:read"))],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return mobile_lawyer_service.cases(db, actor=actor)


@router.get("/mobile/lawyer/cases/{case_id}")
def mobile_lawyer_case_detail(
    case_id: UUID,
    actor: Annotated[User, Depends(require_permission("cases:read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return mobile_lawyer_service.case_detail(db, actor=actor, case_id=case_id)


@router.get("/mobile/lawyer/tasks")
def mobile_lawyer_tasks(
    actor: Annotated[User, Depends(require_permission("cases:read"))],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return mobile_lawyer_service.tasks(db, actor=actor)


@router.get("/mobile/lawyer/hearings")
def mobile_lawyer_hearings(
    actor: Annotated[User, Depends(require_permission("cases:read"))],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return mobile_lawyer_service.hearings(db, actor=actor)


@router.get("/mobile/lawyer/notifications")
def mobile_lawyer_notifications(
    actor: Annotated[User, Depends(require_permission("cases:read"))],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return mobile_lawyer_service.notifications(db, actor=actor)


@router.get("/roles", response_model=list[Role])
def list_roles(_: Annotated[User, Depends(require_permission("roles:read"))]) -> list[Role]:
    return role_service.list_roles()


@router.get("/users", response_model=list[UserOut])
def list_users(
    _: Annotated[User, Depends(require_permission("users:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
) -> list[User]:
    return user_service.list_for_tenant(tenant_id)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    actor: Annotated[User, Depends(require_permission("users:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    request: Request,
) -> User:
    return user_service.create(
        tenant_id=tenant_id,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role=payload.role,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(
    user_id: UUID,
    _: Annotated[User, Depends(require_permission("users:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
) -> User:
    user = user_service.get(tenant_id, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    actor: Annotated[User, Depends(require_permission("users:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    request: Request,
) -> User:
    user = user_service.update(
        tenant_id=tenant_id,
        user_id=user_id,
        actor_user_id=actor.id,
        full_name=payload.full_name,
        role=payload.role,
        is_active=payload.is_active,
        request_id=getattr(request.state, "request_id", None),
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    actor: Annotated[User, Depends(require_permission("users:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    request: Request,
) -> None:
    deleted = user_service.delete(
        tenant_id=tenant_id,
        user_id=user_id,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/clients", response_model=list[Client])
def list_clients(
    _: Annotated[User, Depends(require_permission("clients:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    search: str | None = Query(default=None),
    tag: str | None = Query(default=None),
) -> list[Client]:
    return client_service.list_for_tenant(tenant_id, search=search, tag=tag)


@router.get("/clients/search")
def search_clients(
    _: Annotated[User, Depends(require_permission("clients:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    q: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict[str, object]]:
    return operational_core_service.client_search(db, tenant_id=tenant_id, query=q, limit=limit)


@router.post("/clients", response_model=Client, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    actor: Annotated[User, Depends(require_permission("clients:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    request: Request,
) -> Client:
    return client_service.create(
        tenant_id=tenant_id,
        name=payload.name,
        contact_email=payload.contact_email,
        risk_profile=payload.risk_profile,
        tags=payload.tags,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/clients/{client_id}/profile")
def get_client_profile(
    client_id: UUID,
    _: Annotated[User, Depends(require_permission("clients:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return operational_core_service.client_profile(db, tenant_id=tenant_id, client_id=client_id)


@router.get("/clients/{client_id}", response_model=Client)
def get_client(
    client_id: UUID,
    _: Annotated[User, Depends(require_permission("clients:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
) -> Client:
    client = client_service.get(tenant_id, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.get("/clients/{client_id}/timeline")
def get_client_timeline(
    client_id: UUID,
    _: Annotated[User, Depends(require_permission("clients:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return operational_core_service.client_timeline(db, tenant_id=tenant_id, client_id=client_id)


@router.get("/clients/{client_id}/documents")
def get_client_documents(
    client_id: UUID,
    _: Annotated[User, Depends(require_permission("clients:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return operational_core_service.client_profile(db, tenant_id=tenant_id, client_id=client_id)["documents"]


@router.get("/clients/{client_id}/communications")
def get_client_communications(
    client_id: UUID,
    _: Annotated[User, Depends(require_permission("communications:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return operational_core_service.client_profile(db, tenant_id=tenant_id, client_id=client_id)["communications"]


@router.get("/clients/{client_id}/metrics")
def get_client_metrics(
    client_id: UUID,
    _: Annotated[User, Depends(require_permission("clients:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return operational_core_service.client_metrics(db, tenant_id=tenant_id, client_id=client_id)


@router.get("/clients/{client_id}/risk")
def get_client_risk(
    client_id: UUID,
    _: Annotated[User, Depends(require_permission("clients:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return operational_core_service.client_risk(db, tenant_id=tenant_id, client_id=client_id)


@router.patch("/clients/{client_id}", response_model=Client)
def update_client(
    client_id: UUID,
    payload: ClientUpdate,
    actor: Annotated[User, Depends(require_permission("clients:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    request: Request,
) -> Client:
    client = client_service.update(
        tenant_id=tenant_id,
        client_id=client_id,
        actor_user_id=actor.id,
        name=payload.name,
        contact_email=payload.contact_email,
        risk_profile=payload.risk_profile,
        tags=payload.tags,
        request_id=getattr(request.state, "request_id", None),
    )
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: UUID,
    actor: Annotated[User, Depends(require_permission("clients:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    request: Request,
) -> None:
    deleted = client_service.delete(
        tenant_id=tenant_id,
        client_id=client_id,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")


@router.get("/cases", response_model=list[LegalCase])
def list_cases(
    _: Annotated[User, Depends(require_permission("cases:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    status_filter: MatterStatus | None = Query(default=None, alias="status"),
) -> list[LegalCase]:
    return case_service.list_for_tenant(tenant_id, status=status_filter)


@router.get("/cases/search")
def search_cases(
    _: Annotated[User, Depends(require_permission("cases:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    q: str = Query(default=""),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict[str, object]]:
    return operational_core_service.case_search(db, tenant_id=tenant_id, query=q, limit=limit)


@router.post("/cases", response_model=LegalCase, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    request: Request,
) -> LegalCase:
    if not client_service.get(tenant_id, payload.client_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return case_service.create(
        tenant_id=tenant_id,
        client_id=payload.client_id,
        title=payload.title,
        description=payload.description,
        next_action=payload.next_action,
        assigned_user_ids=payload.assigned_user_ids,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/cases/{case_id}/overview")
def case_overview(
    case_id: UUID,
    _: Annotated[User, Depends(require_permission("cases:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return build_case_overview(db, tenant_id=tenant_id, case_id=case_id)


@router.get("/cases/{case_id}/documents")
def list_case_documents(
    case_id: UUID,
    _: Annotated[User, Depends(require_permission("cases:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return operational_core_service.case_documents(db, tenant_id=tenant_id, case_id=case_id)


@router.get("/cases/{case_id}/hearings")
def list_case_hearings(
    case_id: UUID,
    _: Annotated[User, Depends(require_permission("cases:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    return operational_core_service.case_hearings(db, tenant_id=tenant_id, case_id=case_id)


@router.get("/cases/{case_id}/judicial")
def list_case_judicial(
    case_id: UUID,
    _: Annotated[User, Depends(require_permission("cases:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return operational_core_service.case_judicial(db, tenant_id=tenant_id, case_id=case_id)


@router.get("/cases/{case_id}/automation")
def list_case_automation(
    case_id: UUID,
    _: Annotated[User, Depends(require_permission("automation:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return operational_core_service.case_automation(db, tenant_id=tenant_id, case_id=case_id)


@router.get("/cases/{case_id}/intelligence")
def list_case_intelligence(
    case_id: UUID,
    _: Annotated[User, Depends(require_permission("intelligence:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return operational_core_service.case_intelligence(db, tenant_id=tenant_id, case_id=case_id)


@router.post("/cases/{case_id}/events", status_code=status.HTTP_201_CREATED)
def create_case_event(
    case_id: UUID,
    payload: CaseEventCreate,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
    event = dbm.CaseEvent(
        tenant_id=str(tenant_id),
        case_id=str(case_id),
        event_type=payload.event_type,
        title=payload.title,
        description=payload.description,
    )
    db.add(event)
    db.flush()
    audit_case_action(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="create",
        entity_type="case_event",
        entity_id=event.id,
        request_id=getattr(request.state, "request_id", None),
        metadata={"case_id": str(case_id)},
    )
    db.commit()
    return {"id": event.id, "case_id": event.case_id, "title": event.title, "event_type": event.event_type}


@router.post("/cases/{case_id}/tasks", status_code=status.HTTP_201_CREATED)
def create_case_task(
    case_id: UUID,
    payload: CaseTaskCreate,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
    task = dbm.Task(
        tenant_id=str(tenant_id),
        case_id=str(case_id),
        assigned_user_id=str(payload.assigned_user_id) if payload.assigned_user_id else None,
        title=payload.title,
        status="open",
    )
    db.add(task)
    db.flush()
    audit_case_action(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="create",
        entity_type="task",
        entity_id=task.id,
        request_id=getattr(request.state, "request_id", None),
        metadata={"case_id": str(case_id)},
    )
    db.commit()
    return {"id": task.id, "case_id": task.case_id, "title": task.title, "status": task.status}


@router.post("/cases/{case_id}/documents", status_code=status.HTTP_201_CREATED)
def create_case_document(
    case_id: UUID,
    payload: CaseDocumentCreate,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    legal_case = get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
    document = dbm.Document(
        tenant_id=str(tenant_id),
        case_id=str(case_id),
        client_id=legal_case.client_id,
        filename=payload.filename,
        storage_key=payload.storage_key,
        content_type=payload.content_type,
        classification=payload.classification,
    )
    db.add(document)
    db.flush()
    audit_case_action(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="create",
        entity_type="document",
        entity_id=document.id,
        request_id=getattr(request.state, "request_id", None),
        metadata={"case_id": str(case_id)},
    )
    db.commit()
    return {"id": document.id, "case_id": document.case_id, "filename": document.filename, "status": document.status}


@router.post("/cases/{case_id}/status")
def update_case_status_p4(
    case_id: UUID,
    payload: CaseStatusChange,
    actor: Annotated[User, Depends(require_permission("cases:change_status"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    legal_case = get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
    legal_case.status = payload.status.value
    legal_case.updated_at = now()
    event = dbm.CaseEvent(
        tenant_id=str(tenant_id),
        case_id=str(case_id),
        event_type="status_change",
        title=f"Estado actualizado a {payload.status.value}",
    )
    db.add(event)
    db.flush()
    audit_case_action(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        action="change_status",
        entity_type="case",
        entity_id=legal_case.id,
        request_id=getattr(request.state, "request_id", None),
        metadata={"case_id": str(case_id), "status": payload.status.value},
    )
    db.commit()
    return {"id": legal_case.id, "status": legal_case.status}


@router.get("/cases/{case_id}/sources")
def list_case_sources(
    case_id: UUID,
    _: Annotated[User, Depends(require_permission("cases:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    sources = judicial_source_service.list_sources(db, tenant_id=tenant_id, case_id=case_id)
    return [
        {
            "id": source.id,
            "case_id": source.case_id,
            "source_type": source.source_type,
            "source_name": source.source_name,
            "external_case_number": source.external_case_number,
            "court_name": source.court_name,
            "status": source.status,
            "captcha_required": source.captcha_required,
            "last_checked_at": source.last_checked_at.isoformat() if source.last_checked_at else None,
            "last_result": source.last_result,
        }
        for source in sources
    ]


@router.post("/settings/integrations/sinoe")
def save_sinoe_credentials(
    payload: SinoeCredentialsRequest,
    actor: Annotated[User, Depends(require_permission("integrations:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return sinoe_automation_service.save_credentials(
        db,
        tenant_id=tenant_id,
        username=payload.username,
        password=payload.password,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/settings/integrations/sinoe")
def get_sinoe_integration(
    _: Annotated[User, Depends(require_permission("integrations:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return sinoe_automation_service.get_status(db, tenant_id=tenant_id)


@router.delete("/settings/integrations/sinoe")
def delete_sinoe_credentials(
    actor: Annotated[User, Depends(require_permission("integrations:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return sinoe_automation_service.delete_credentials(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/settings/integrations/sinoe/test")
def test_sinoe_connection(
    actor: Annotated[User, Depends(require_permission("integrations:run"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return sinoe_automation_service.test_connection(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/cases/{case_id}/sources", status_code=status.HTTP_201_CREATED)
def create_case_source(
    case_id: UUID,
    payload: CaseSourceCreate,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    source = judicial_source_service.create_source(
        db,
        tenant_id=tenant_id,
        case_id=case_id,
        source_type=payload.source_type,
        external_case_number=payload.external_case_number,
        court_name=payload.court_name,
        source_url=payload.source_url,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )
    return {"id": source.id, "case_id": source.case_id, "source_type": source.source_type, "status": source.status}


@router.post("/cases/{case_id}/sources/sinoe", status_code=status.HTTP_201_CREATED)
def create_sinoe_case_source(
    case_id: UUID,
    payload: SinoeCaseSourceRequest,
    actor: Annotated[User, Depends(require_permission("integrations:run"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    source = sinoe_automation_service.create_case_source(
        db,
        tenant_id=tenant_id,
        case_id=case_id,
        external_case_number=payload.external_case_number,
        district=payload.district,
        site=payload.site,
        reference=payload.reference,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )
    return {
        "id": source.id,
        "case_id": source.case_id,
        "source_type": source.source_type,
        "source_name": source.source_name,
        "external_case_number": source.external_case_number,
        "status": source.status,
        "last_checked_at": source.last_checked_at.isoformat() if source.last_checked_at else None,
        "last_result": source.last_result,
    }


@router.post("/case-sources/{source_id}/check")
def check_case_source(
    source_id: UUID,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return judicial_update_service.check_source(
        db,
        tenant_id=tenant_id,
        source_id=source_id,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/case-sources/{source_id}/sinoe/check")
def check_sinoe_case_source(
    source_id: UUID,
    actor: Annotated[User, Depends(require_permission("integrations:run"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    return sinoe_automation_service.check_case_updates(
        db,
        tenant_id=tenant_id,
        source_id=source_id,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/case-sources/{source_id}/updates")
def list_case_source_updates(
    source_id: UUID,
    _: Annotated[User, Depends(require_permission("cases:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    updates = judicial_update_service.list_updates(db, tenant_id=tenant_id, source_id=source_id)
    return [
        {
            "id": update.id,
            "case_id": update.case_id,
            "case_source_id": update.case_source_id,
            "title": update.title,
            "summary": update.summary,
            "status": update.status,
            "captcha_required": update.captcha_required,
            "requires_human_intervention": update.requires_human_intervention,
        }
        for update in updates
    ]


@router.get("/case-sources/{source_id}/sinoe/updates")
def list_sinoe_case_source_updates(
    source_id: UUID,
    _: Annotated[User, Depends(require_permission("integrations:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict[str, object]]:
    updates = sinoe_automation_service.list_updates(db, tenant_id=tenant_id, source_id=source_id)
    return [
        {
            "id": update.id,
            "case_id": update.case_id,
            "case_source_id": update.case_source_id,
            "title": update.title,
            "summary": update.summary,
            "status": update.status,
            "captcha_required": update.captcha_required,
            "requires_human_intervention": update.requires_human_intervention,
            "checked_at": update.checked_at.isoformat() if update.checked_at else None,
        }
        for update in updates
    ]


@router.post("/captcha-checkpoints/{checkpoint_id}/resolve")
def resolve_captcha_checkpoint(
    checkpoint_id: UUID,
    payload: CaptchaResolveRequest,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    checkpoint = captcha_checkpoint_service.resolve_checkpoint(
        db,
        tenant_id=tenant_id,
        checkpoint_id=checkpoint_id,
        actor_user_id=actor.id,
        resolution_note=payload.resolution_note,
        request_id=getattr(request.state, "request_id", None),
    )
    return {"id": checkpoint.id, "status": checkpoint.status, "resolved_at": checkpoint.resolved_at.isoformat() if checkpoint.resolved_at else None}


@router.post("/judicial-updates/{update_id}/approve")
def approve_judicial_update(
    update_id: UUID,
    payload: JudicialDecisionRequest,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    update = judicial_update_service.decide_update(
        db,
        tenant_id=tenant_id,
        update_id=update_id,
        actor_user_id=actor.id,
        decision="approve",
        note=payload.note,
        request_id=getattr(request.state, "request_id", None),
    )
    return {"id": update.id, "status": update.status}


@router.post("/judicial-updates/{update_id}/reject")
def reject_judicial_update(
    update_id: UUID,
    payload: JudicialDecisionRequest,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, object]:
    update = judicial_update_service.decide_update(
        db,
        tenant_id=tenant_id,
        update_id=update_id,
        actor_user_id=actor.id,
        decision="reject",
        note=payload.note,
        request_id=getattr(request.state, "request_id", None),
    )
    return {"id": update.id, "status": update.status}


@router.get("/cases/{case_id}", response_model=LegalCase)
def get_case(
    case_id: UUID,
    _: Annotated[User, Depends(require_permission("cases:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
) -> LegalCase:
    legal_case = case_service.get(tenant_id, case_id)
    if not legal_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return legal_case


@router.patch("/cases/{case_id}", response_model=LegalCase)
def update_case(
    case_id: UUID,
    payload: CaseUpdate,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    request: Request,
) -> LegalCase:
    legal_case = case_service.update(
        tenant_id=tenant_id,
        case_id=case_id,
        actor_user_id=actor.id,
        title=payload.title,
        description=payload.description,
        next_action=payload.next_action,
        request_id=getattr(request.state, "request_id", None),
    )
    if not legal_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return legal_case


@router.post("/cases/{case_id}/assign", response_model=LegalCase)
def assign_case(
    case_id: UUID,
    payload: CaseAssign,
    actor: Annotated[User, Depends(require_permission("cases:assign"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    request: Request,
) -> LegalCase:
    legal_case = case_service.assign(
        tenant_id=tenant_id,
        case_id=case_id,
        assigned_user_ids=payload.assigned_user_ids,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )
    if not legal_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return legal_case


@router.post("/cases/{case_id}/change-status", response_model=LegalCase)
def change_case_status(
    case_id: UUID,
    payload: CaseStatusChange,
    actor: Annotated[User, Depends(require_permission("cases:change_status"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    request: Request,
) -> LegalCase:
    legal_case = case_service.change_status(
        tenant_id=tenant_id,
        case_id=case_id,
        status=payload.status,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )
    if not legal_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return legal_case


@router.delete("/cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id: UUID,
    actor: Annotated[User, Depends(require_permission("cases:write"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    request: Request,
) -> None:
    deleted = case_service.delete(
        tenant_id=tenant_id,
        case_id=case_id,
        actor_user_id=actor.id,
        request_id=getattr(request.state, "request_id", None),
    )
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")


@router.get("/audit", response_model=list[AuditLog])
def list_audit(
    _: Annotated[User, Depends(require_permission("audit:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    action: AuditAction | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    actor_user_id: UUID | None = Query(default=None),
) -> list[AuditLog]:
    return audit_service.list_for_tenant(
        tenant_id,
        action=action,
        entity_type=entity_type,
        actor_user_id=actor_user_id,
    )


@router.get("/command-center")
def command_center(
    _: Annotated[User, Depends(require_permission("dashboard:read"))],
    tenant_id: Annotated[UUID, Depends(get_request_tenant)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return command_center_service.snapshot(db, tenant_id=tenant_id)


@router.post("/matters", response_model=Matter)
def create_matter(payload: MatterCreate, tenant_id: UUID = Header(default=UUID("00000000-0000-0000-0000-000000000001"), alias="X-Tenant-Id")) -> Matter:
    return matter_service.create(
        tenant_id=tenant_id,
        client_id=payload.client_id,
        title=payload.title,
        next_action=payload.next_action,
    )


@router.get("/matters", response_model=list[Matter])
def list_matters(tenant_id: UUID = Header(default=UUID("00000000-0000-0000-0000-000000000001"), alias="X-Tenant-Id")) -> list[Matter]:
    return matter_service.list_for_tenant(tenant_id)


@router.get("/audit-log", response_model=list[AuditLog])
def list_audit_log(tenant_id: UUID = Header(default=UUID("00000000-0000-0000-0000-000000000001"), alias="X-Tenant-Id")) -> list[AuditLog]:
    return audit_service.list_for_tenant(tenant_id)


@router.get("/demo/client-id")
def demo_client_id() -> dict[str, str]:
    return {"client_id": str(uuid4())}
