from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MatterStatus(StrEnum):
    active = "active"
    paused = "paused"
    closed = "closed"
    risk = "risk"


class RoleName(StrEnum):
    super_admin = "super_admin"
    tenant_admin = "tenant_admin"
    partner = "partner"
    lawyer = "lawyer"
    assistant = "assistant"
    client_user = "client_user"


class AuditAction(StrEnum):
    create = "create"
    update = "update"
    delete = "delete"
    read = "read"
    login = "login"
    logout = "logout"
    refresh = "refresh"
    assign = "assign"
    change_status = "change_status"
    send = "send"
    automate = "automate"
    ai_run = "ai_run"


class Tenant(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    slug: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Role(BaseModel):
    name: RoleName
    permissions: list[str]
    description: str


class TenantScopedModel(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Client(TenantScopedModel):
    name: str
    contact_email: str | None = None
    risk_profile: str = "standard"
    tags: list[str] = Field(default_factory=list)


class User(TenantScopedModel):
    email: str
    full_name: str
    hashed_password: str
    role: RoleName
    is_active: bool = True
    mfa_enabled: bool = False
    refresh_token_version: int = 0


class Matter(TenantScopedModel):
    client_id: UUID
    title: str
    status: MatterStatus = MatterStatus.active
    next_action: str


class LegalCase(TenantScopedModel):
    client_id: UUID
    title: str
    description: str | None = None
    status: MatterStatus = MatterStatus.active
    assigned_user_ids: list[UUID] = Field(default_factory=list)
    next_action: str


class Document(TenantScopedModel):
    matter_id: UUID
    filename: str
    storage_key: str
    classification: str | None = None


class Communication(TenantScopedModel):
    matter_id: UUID
    channel: str
    external_ref: str | None = None
    summary: str


class AutomationRun(TenantScopedModel):
    matter_id: UUID
    workflow_name: str
    authorized_by_user_id: UUID
    status: str


class AiInsight(TenantScopedModel):
    matter_id: UUID
    insight_type: str
    summary: str
    confidence: float = Field(ge=0, le=1)


class AuditLog(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    actor_user_id: UUID | None = None
    action: AuditAction
    entity_type: str
    entity_id: UUID
    request_id: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
