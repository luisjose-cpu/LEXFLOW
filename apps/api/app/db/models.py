from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def new_id() -> str:
    return str(uuid4())


def now_utc() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def soft_delete(self) -> None:
        self.deleted_at = now_utc()


class Tenant(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    plan: Mapped[str] = mapped_column(String(80), default="demo", nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    clients: Mapped[list["Client"]] = relationship(back_populates="tenant")
    cases: Mapped[list["Case"]] = relationship(back_populates="tenant")


class Role(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
        Index("ix_roles_tenant_id", "tenant_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    permissions: Mapped[list["RolePermission"]] = relationship(back_populates="role", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship(back_populates="role")


class Permission(Base, TimestampMixin):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(String(240), default="", nullable=False)


class RolePermission(Base, TimestampMixin):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
        Index("ix_role_permissions_tenant_id", "tenant_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id"), nullable=False)
    permission_id: Mapped[str] = mapped_column(String(36), ForeignKey("permissions.id"), nullable=False)

    role: Mapped[Role] = relationship(back_populates="permissions")
    permission: Mapped[Permission] = relationship()


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        Index("ix_users_tenant_id", "tenant_id"),
        Index("ix_users_status", "status"),
        Index("ix_users_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(240), nullable=False)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="users")
    role: Mapped[Role] = relationship(back_populates="users")
    tasks: Mapped[list["Task"]] = relationship(back_populates="assigned_user")


class Client(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "clients"
    __table_args__ = (
        Index("ix_clients_tenant_id", "tenant_id"),
        Index("ix_clients_status", "status"),
        Index("ix_clients_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(240), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    risk_profile: Mapped[str] = mapped_column(String(80), default="standard", nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="clients")
    cases: Mapped[list["Case"]] = relationship(back_populates="client")


class Case(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "cases"
    __table_args__ = (
        Index("ix_cases_tenant_id", "tenant_id"),
        Index("ix_cases_client_id", "client_id"),
        Index("ix_cases_status", "status"),
        Index("ix_cases_created_at", "created_at"),
        Index("ix_cases_external_case_number", "external_case_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    external_case_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="cases")
    client: Mapped[Client] = relationship(back_populates="cases")
    events: Mapped[list["CaseEvent"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    sources: Mapped[list["CaseSource"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    judicial_updates: Mapped[list["JudicialUpdate"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="case")
    hearings: Mapped[list["Hearing"]] = relationship(back_populates="case")
    tasks: Mapped[list["Task"]] = relationship(back_populates="case")


class CaseEvent(Base, TimestampMixin):
    __tablename__ = "case_events"
    __table_args__ = (
        Index("ix_case_events_tenant_id", "tenant_id"),
        Index("ix_case_events_case_id", "case_id"),
        Index("ix_case_events_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_client_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

    case: Mapped[Case] = relationship(back_populates="events")


class CaseSource(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "case_sources"
    __table_args__ = (
        Index("ix_case_sources_tenant_id", "tenant_id"),
        Index("ix_case_sources_case_id", "case_id"),
        Index("ix_case_sources_status", "status"),
        Index("ix_case_sources_external_case_number", "external_case_number"),
        Index("ix_case_sources_last_checked_at", "last_checked_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), default="judicial", nullable=False)
    external_case_number: Mapped[str] = mapped_column(String(120), nullable=False)
    court_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    captcha_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped[Case] = relationship(back_populates="sources")
    judicial_updates: Mapped[list["JudicialUpdate"]] = relationship(back_populates="case_source")


class JudicialUpdate(Base, TimestampMixin):
    __tablename__ = "judicial_updates"
    __table_args__ = (
        Index("ix_judicial_updates_tenant_id", "tenant_id"),
        Index("ix_judicial_updates_case_id", "case_id"),
        Index("ix_judicial_updates_status", "status"),
        Index("ix_judicial_updates_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    case_source_id: Mapped[str] = mapped_column(String(36), ForeignKey("case_sources.id"), nullable=False)
    update_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="recorded", nullable=False)
    captcha_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_human_intervention: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    raw_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    case: Mapped[Case] = relationship(back_populates="judicial_updates")
    case_source: Mapped[CaseSource] = relationship(back_populates="judicial_updates")


class CaptchaCheckpoint(Base, TimestampMixin):
    __tablename__ = "captcha_checkpoints"
    __table_args__ = (
        Index("ix_captcha_checkpoints_tenant_id", "tenant_id"),
        Index("ix_captcha_checkpoints_case_id", "case_id"),
        Index("ix_captcha_checkpoints_status", "status"),
        Index("ix_captcha_checkpoints_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    case_source_id: Mapped[str] = mapped_column(String(36), ForeignKey("case_sources.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    reason: Mapped[str] = mapped_column(String(240), default="captcha_required", nullable=False)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class JudicialEvidence(Base, TimestampMixin):
    __tablename__ = "judicial_evidence"
    __table_args__ = (
        Index("ix_judicial_evidence_tenant_id", "tenant_id"),
        Index("ix_judicial_evidence_case_id", "case_id"),
        Index("ix_judicial_evidence_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    case_source_id: Mapped[str] = mapped_column(String(36), ForeignKey("case_sources.id"), nullable=False)
    judicial_update_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("judicial_updates.id"), nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(80), default="adapter_payload", nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)


class Document(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_tenant_id", "tenant_id"),
        Index("ix_documents_case_id", "case_id"),
        Index("ix_documents_client_id", "client_id"),
        Index("ix_documents_status", "status"),
        Index("ix_documents_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(240), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), default="application/pdf", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="uploaded", nullable=False)
    classification: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_client_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    uploaded_by_client: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(96), nullable=True)
    storage_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    malware_scan_status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    malware_scan_result: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    case: Mapped[Case] = relationship(back_populates="documents")


class Hearing(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "hearings"
    __table_args__ = (
        Index("ix_hearings_tenant_id", "tenant_id"),
        Index("ix_hearings_case_id", "case_id"),
        Index("ix_hearings_status", "status"),
        Index("ix_hearings_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(240), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="scheduled", nullable=False)

    case: Mapped[Case] = relationship(back_populates="hearings")


class Task(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_tenant_id", "tenant_id"),
        Index("ix_tasks_case_id", "case_id"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    assigned_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped[Case] = relationship(back_populates="tasks")
    assigned_user: Mapped[User | None] = relationship(back_populates="tasks")


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_tenant_id", "tenant_id"),
        Index("ix_notifications_case_id", "case_id"),
        Index("ix_notifications_status", "status"),
        Index("ix_notifications_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cases.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(80), default="in_app", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_tenant_id", "tenant_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)


class WhatsAppMessage(Base, TimestampMixin):
    __tablename__ = "whatsapp_messages"
    __table_args__ = (
        Index("ix_whatsapp_messages_tenant_id", "tenant_id"),
        Index("ix_whatsapp_messages_case_id", "case_id"),
        Index("ix_whatsapp_messages_client_id", "client_id"),
        Index("ix_whatsapp_messages_status", "status"),
        Index("ix_whatsapp_messages_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cases.id"), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("clients.id"), nullable=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    from_number: Mapped[str] = mapped_column(String(80), nullable=False)
    to_number: Mapped[str] = mapped_column(String(80), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(String(160), nullable=True)


class CommunicationThread(Base, TimestampMixin):
    __tablename__ = "communication_threads"
    __table_args__ = (
        Index("ix_communication_threads_tenant_id", "tenant_id"),
        Index("ix_communication_threads_case_id", "case_id"),
        Index("ix_communication_threads_client_id", "client_id"),
        Index("ix_communication_threads_status", "status"),
        Index("ix_communication_threads_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String(240), nullable=False)
    channel: Mapped[str] = mapped_column(String(80), default="portal", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)

    messages: Mapped[list["CommunicationMessage"]] = relationship(back_populates="thread")


class CommunicationMessage(Base, TimestampMixin):
    __tablename__ = "communication_messages"
    __table_args__ = (
        Index("ix_communication_messages_tenant_id", "tenant_id"),
        Index("ix_communication_messages_thread_id", "thread_id"),
        Index("ix_communication_messages_case_id", "case_id"),
        Index("ix_communication_messages_client_id", "client_id"),
        Index("ix_communication_messages_status", "status"),
        Index("ix_communication_messages_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    thread_id: Mapped[str] = mapped_column(String(36), ForeignKey("communication_threads.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id"), nullable=False)
    sender_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    channel: Mapped[str] = mapped_column(String(80), default="portal", nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(180), nullable=True)
    template_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("message_templates.id"), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    thread: Mapped[CommunicationThread] = relationship(back_populates="messages")


class MessageTemplate(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "message_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_message_templates_tenant_code"),
        Index("ix_message_templates_tenant_id", "tenant_id"),
        Index("ix_message_templates_channel", "channel"),
        Index("ix_message_templates_status", "status"),
        Index("ix_message_templates_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    channel: Mapped[str] = mapped_column(String(80), default="whatsapp", nullable=False)
    subject: Mapped[str | None] = mapped_column(String(240), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)


class NotificationRule(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "notification_rules"
    __table_args__ = (
        Index("ix_notification_rules_tenant_id", "tenant_id"),
        Index("ix_notification_rules_event_type", "event_type"),
        Index("ix_notification_rules_channel", "channel"),
        Index("ix_notification_rules_status", "status"),
        Index("ix_notification_rules_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    channel: Mapped[str] = mapped_column(String(80), default="portal", nullable=False)
    template_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("message_templates.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    config_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)


class AiJob(Base, TimestampMixin):
    __tablename__ = "ai_jobs"
    __table_args__ = (
        Index("ix_ai_jobs_tenant_id", "tenant_id"),
        Index("ix_ai_jobs_case_id", "case_id"),
        Index("ix_ai_jobs_status", "status"),
        Index("ix_ai_jobs_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("cases.id"), nullable=True)
    document_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("documents.id"), nullable=True)
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="queued", nullable=False)
    input_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    output_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)


class LegalNewsSource(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "legal_news_sources"
    __table_args__ = (
        Index("ix_legal_news_sources_tenant_id", "tenant_id"),
        Index("ix_legal_news_sources_status", "status"),
        Index("ix_legal_news_sources_last_checked_at", "last_checked_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="judicial", nullable=False)
    adapter_key: Mapped[str] = mapped_column(String(120), default="mock", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    news: Mapped[list["LegalNews"]] = relationship(back_populates="source")


class LegalNews(Base, TimestampMixin):
    __tablename__ = "legal_news"
    __table_args__ = (
        Index("ix_legal_news_tenant_id", "tenant_id"),
        Index("ix_legal_news_created_at", "created_at"),
        Index("ix_legal_news_status", "status"),
        Index("ix_legal_news_category", "category"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("legal_news_sources.id"), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(180), nullable=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="news", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="published", nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    trend_score: Mapped[str] = mapped_column(String(40), default="normal", nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    source: Mapped[LegalNewsSource] = relationship(back_populates="news")


class LegalNewsFavorite(Base, TimestampMixin):
    __tablename__ = "legal_news_favorites"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "news_id", name="uq_legal_news_favorites_user_news"),
        Index("ix_legal_news_favorites_tenant_id", "tenant_id"),
        Index("ix_legal_news_favorites_news_id", "news_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    news_id: Mapped[str] = mapped_column(String(36), ForeignKey("legal_news.id"), nullable=False)


class LegalNewsCaseLink(Base, TimestampMixin):
    __tablename__ = "legal_news_case_links"
    __table_args__ = (
        UniqueConstraint("tenant_id", "case_id", "news_id", name="uq_legal_news_case_links_case_news"),
        Index("ix_legal_news_case_links_tenant_id", "tenant_id"),
        Index("ix_legal_news_case_links_case_id", "case_id"),
        Index("ix_legal_news_case_links_news_id", "news_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id"), nullable=False)
    news_id: Mapped[str] = mapped_column(String(36), ForeignKey("legal_news.id"), nullable=False)
    linked_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class LegalAlert(Base, TimestampMixin):
    __tablename__ = "legal_alerts"
    __table_args__ = (
        Index("ix_legal_alerts_tenant_id", "tenant_id"),
        Index("ix_legal_alerts_status", "status"),
        Index("ix_legal_alerts_severity", "severity"),
        Index("ix_legal_alerts_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    news_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("legal_news.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(40), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="open", nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)


class LegalTag(Base, TimestampMixin):
    __tablename__ = "legal_tags"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_legal_tags_tenant_name"),
        Index("ix_legal_tags_tenant_id", "tenant_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    color: Mapped[str] = mapped_column(String(40), default="blue", nullable=False)


class BillingPlan(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "billing_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_billing_plans_tenant_code"),
        Index("ix_billing_plans_tenant_id", "tenant_id"),
        Index("ix_billing_plans_code", "code"),
        Index("ix_billing_plans_status", "status"),
        Index("ix_billing_plans_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    monthly_price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    trial_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    limits_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    features: Mapped[list["PlanFeature"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    subscriptions: Mapped[list["TenantSubscription"]] = relationship(back_populates="plan")


class PlanFeature(Base, TimestampMixin):
    __tablename__ = "plan_features"
    __table_args__ = (
        UniqueConstraint("tenant_id", "plan_id", "feature_key", name="uq_plan_features_plan_feature"),
        Index("ix_plan_features_tenant_id", "tenant_id"),
        Index("ix_plan_features_plan_id", "plan_id"),
        Index("ix_plan_features_feature_key", "feature_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("billing_plans.id"), nullable=False)
    feature_key: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    limit_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    plan: Mapped[BillingPlan] = relationship(back_populates="features")


class TenantSubscription(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "tenant_subscriptions"
    __table_args__ = (
        Index("ix_tenant_subscriptions_tenant_id", "tenant_id"),
        Index("ix_tenant_subscriptions_plan_id", "plan_id"),
        Index("ix_tenant_subscriptions_status", "status"),
        Index("ix_tenant_subscriptions_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("billing_plans.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="trialing", nullable=False)
    seats: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider: Mapped[str] = mapped_column(String(80), default="mock", nullable=False)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(180), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    plan: Mapped[BillingPlan] = relationship(back_populates="subscriptions")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="subscription")


class TenantUsage(Base, TimestampMixin):
    __tablename__ = "tenant_usage"
    __table_args__ = (
        UniqueConstraint("tenant_id", "feature_key", "period_key", name="uq_tenant_usage_feature_period"),
        Index("ix_tenant_usage_tenant_id", "tenant_id"),
        Index("ix_tenant_usage_feature_key", "feature_key"),
        Index("ix_tenant_usage_period_key", "period_key"),
        Index("ix_tenant_usage_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    feature_key: Mapped[str] = mapped_column(String(120), nullable=False)
    period_key: Mapped[str] = mapped_column(String(40), nullable=False)
    used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    limit_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)


class BillingEvent(Base, TimestampMixin):
    __tablename__ = "billing_events"
    __table_args__ = (
        Index("ix_billing_events_tenant_id", "tenant_id"),
        Index("ix_billing_events_subscription_id", "subscription_id"),
        Index("ix_billing_events_event_type", "event_type"),
        Index("ix_billing_events_status", "status"),
        Index("ix_billing_events_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    subscription_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tenant_subscriptions.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="processed", nullable=False)
    payload_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "invoice_number", name="uq_invoices_tenant_number"),
        Index("ix_invoices_tenant_id", "tenant_id"),
        Index("ix_invoices_subscription_id", "subscription_id"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    subscription_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tenant_subscriptions.id"), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)
    amount_due_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(12), default="USD", nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    subscription: Mapped[TenantSubscription | None] = relationship(back_populates="invoices")


class AutomationWorkflow(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "automation_workflows"
    __table_args__ = (
        Index("ix_automation_workflows_tenant_id", "tenant_id"),
        Index("ix_automation_workflows_trigger_key", "trigger_key"),
        Index("ix_automation_workflows_status", "status"),
        Index("ix_automation_workflows_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    trigger_key: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    conditions: Mapped[list["AutomationCondition"]] = relationship(back_populates="workflow", cascade="all, delete-orphan")
    actions: Mapped[list["AutomationAction"]] = relationship(back_populates="workflow", cascade="all, delete-orphan")
    runs: Mapped[list["AutomationRun"]] = relationship(back_populates="workflow")


class AutomationCondition(Base, TimestampMixin):
    __tablename__ = "automation_conditions"
    __table_args__ = (
        Index("ix_automation_conditions_tenant_id", "tenant_id"),
        Index("ix_automation_conditions_workflow_id", "workflow_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("automation_workflows.id"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    condition_type: Mapped[str] = mapped_column(String(120), default="ALWAYS", nullable=False)
    config_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    workflow: Mapped[AutomationWorkflow] = relationship(back_populates="conditions")


class AutomationAction(Base, TimestampMixin):
    __tablename__ = "automation_actions"
    __table_args__ = (
        Index("ix_automation_actions_tenant_id", "tenant_id"),
        Index("ix_automation_actions_workflow_id", "workflow_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("automation_workflows.id"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    action_type: Mapped[str] = mapped_column(String(120), nullable=False)
    config_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)

    workflow: Mapped[AutomationWorkflow] = relationship(back_populates="actions")


class AutomationRun(Base, TimestampMixin):
    __tablename__ = "automation_runs"
    __table_args__ = (
        Index("ix_automation_runs_tenant_id", "tenant_id"),
        Index("ix_automation_runs_workflow_id", "workflow_id"),
        Index("ix_automation_runs_trigger_key", "trigger_key"),
        Index("ix_automation_runs_status", "status"),
        Index("ix_automation_runs_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("automation_workflows.id"), nullable=False)
    trigger_key: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="running", nullable=False)
    event_payload_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    result_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow: Mapped[AutomationWorkflow] = relationship(back_populates="runs")
    steps: Mapped[list["AutomationRunStep"]] = relationship(back_populates="run", cascade="all, delete-orphan")


class AutomationRunStep(Base, TimestampMixin):
    __tablename__ = "automation_run_steps"
    __table_args__ = (
        Index("ix_automation_run_steps_tenant_id", "tenant_id"),
        Index("ix_automation_run_steps_run_id", "run_id"),
        Index("ix_automation_run_steps_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("automation_runs.id"), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    step_type: Mapped[str] = mapped_column(String(40), nullable=False)
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    result_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    run: Mapped[AutomationRun] = relationship(back_populates="steps")
