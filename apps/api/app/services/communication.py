from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import User


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


@dataclass(frozen=True)
class WhatsAppSendResult:
    provider_message_id: str
    status: str
    provider: str


class WhatsAppProvider(Protocol):
    def send_message(self, *, to_number: str, body: str, metadata: dict[str, object] | None = None) -> WhatsAppSendResult:
        ...


class WhatsAppMockProvider:
    def send_message(self, *, to_number: str, body: str, metadata: dict[str, object] | None = None) -> WhatsAppSendResult:
        return WhatsAppSendResult(provider_message_id=f"mock-whatsapp-{abs(hash((to_number, body))) % 1000000}", status="sent", provider="mock")


class WhatsAppBusinessProvider:
    def send_message(self, *, to_number: str, body: str, metadata: dict[str, object] | None = None) -> WhatsAppSendResult:
        return WhatsAppSendResult(provider_message_id="placeholder-whatsapp-business", status="queued_placeholder", provider="whatsapp_business_placeholder")


class CommunicationAuditService:
    def record(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor_user_id: UUID | str | None,
        action: str,
        entity_type: str,
        entity_id: UUID | str,
        request_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> dbm.AuditLog:
        audit = dbm.AuditLog(
            tenant_id=str(tenant_id),
            actor_user_id=str(actor_user_id) if actor_user_id else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            request_id=request_id,
            metadata_json=metadata or {},
        )
        db.add(audit)
        return audit


class MessageTemplateService:
    default_templates = [
        ("audiencia_proxima", "Audiencia proxima", "whatsapp", "Recordatorio de audiencia: {{case_title}} tiene audiencia el {{hearing_date}}."),
        ("documento_requerido", "Documento requerido", "whatsapp", "Necesitamos el documento {{document_name}} para continuar con {{case_title}}."),
        ("informe_disponible", "Informe disponible", "portal", "Ya esta disponible el informe de {{case_title}} en tu portal."),
        ("actualizacion_expediente", "Actualizacion expediente", "whatsapp", "Hay una actualizacion aprobada en {{case_title}}: {{update_summary}}."),
        ("proximo_paso", "Proximo paso", "portal", "El proximo paso de {{case_title}} es {{next_action}}."),
    ]

    def ensure_defaults(self, db: Session, *, tenant_id: UUID | str) -> None:
        existing_codes = set(db.scalars(select(dbm.MessageTemplate.code).where(dbm.MessageTemplate.tenant_id == str(tenant_id))).all())
        for code, name, channel, body in self.default_templates:
            if code not in existing_codes:
                db.add(dbm.MessageTemplate(tenant_id=str(tenant_id), code=code, name=name, channel=channel, body=body))
        db.flush()

    def list(self, db: Session, *, tenant_id: UUID | str) -> list[dbm.MessageTemplate]:
        self.ensure_defaults(db, tenant_id=tenant_id)
        return db.scalars(
            select(dbm.MessageTemplate)
            .where(dbm.MessageTemplate.tenant_id == str(tenant_id), dbm.MessageTemplate.deleted_at.is_(None))
            .order_by(dbm.MessageTemplate.created_at.asc())
        ).all()

    def get(self, db: Session, *, tenant_id: UUID | str, template_id: UUID | str) -> dbm.MessageTemplate:
        template = db.scalars(
            select(dbm.MessageTemplate).where(
                dbm.MessageTemplate.tenant_id == str(tenant_id),
                dbm.MessageTemplate.id == str(template_id),
                dbm.MessageTemplate.deleted_at.is_(None),
            )
        ).first()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return template

    def create(self, db: Session, *, tenant_id: UUID | str, code: str, name: str, channel: str, body: str, subject: str | None = None) -> dbm.MessageTemplate:
        template = dbm.MessageTemplate(tenant_id=str(tenant_id), code=code, name=name, channel=channel, body=body, subject=subject)
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    def update(self, db: Session, *, tenant_id: UUID | str, template_id: UUID | str, name: str | None = None, channel: str | None = None, body: str | None = None, subject: str | None = None, status_value: str | None = None) -> dbm.MessageTemplate:
        template = self.get(db, tenant_id=tenant_id, template_id=template_id)
        if name is not None:
            template.name = name
        if channel is not None:
            template.channel = channel
        if body is not None:
            template.body = body
        if subject is not None:
            template.subject = subject
        if status_value is not None:
            template.status = status_value
        db.commit()
        db.refresh(template)
        return template

    def delete(self, db: Session, *, tenant_id: UUID | str, template_id: UUID | str) -> None:
        template = self.get(db, tenant_id=tenant_id, template_id=template_id)
        template.soft_delete()
        db.commit()

    def render(self, template: dbm.MessageTemplate, variables: dict[str, object] | None = None) -> str:
        body = template.body
        for key, value in (variables or {}).items():
            body = body.replace("{{" + key + "}}", str(value))
        return body


class WhatsAppService:
    def __init__(self, provider: WhatsAppProvider | None = None) -> None:
        self.provider = provider or WhatsAppMockProvider()

    def send(self, *, to_number: str, body: str, metadata: dict[str, object] | None = None) -> WhatsAppSendResult:
        return self.provider.send_message(to_number=to_number, body=body, metadata=metadata)


class CommunicationService:
    def __init__(self, *, audit_service: CommunicationAuditService, whatsapp_service: WhatsAppService) -> None:
        self.audit_service = audit_service
        self.whatsapp_service = whatsapp_service

    def get_case(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> dbm.Case:
        legal_case = db.scalars(
            select(dbm.Case).where(
                dbm.Case.tenant_id == str(tenant_id),
                dbm.Case.id == str(case_id),
                dbm.Case.deleted_at.is_(None),
            )
        ).first()
        if not legal_case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        return legal_case

    def get_or_create_thread(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str, channel: str = "portal", subject: str | None = None) -> dbm.CommunicationThread:
        legal_case = self.get_case(db, tenant_id=tenant_id, case_id=case_id)
        thread = db.scalars(
            select(dbm.CommunicationThread).where(
                dbm.CommunicationThread.tenant_id == str(tenant_id),
                dbm.CommunicationThread.case_id == legal_case.id,
                dbm.CommunicationThread.channel == channel,
                dbm.CommunicationThread.status == "open",
            )
        ).first()
        if thread:
            return thread
        thread = dbm.CommunicationThread(
            tenant_id=str(tenant_id),
            case_id=legal_case.id,
            client_id=legal_case.client_id,
            subject=subject or f"Comunicacion {legal_case.title}",
            channel=channel,
        )
        db.add(thread)
        db.flush()
        return thread

    def list_case_communications(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> list[dict[str, object]]:
        self.get_case(db, tenant_id=tenant_id, case_id=case_id)
        threads = db.scalars(
            select(dbm.CommunicationThread)
            .where(dbm.CommunicationThread.tenant_id == str(tenant_id), dbm.CommunicationThread.case_id == str(case_id))
            .order_by(dbm.CommunicationThread.updated_at.desc())
        ).all()
        return [self.serialize_thread(db, thread) for thread in threads]

    def create_message(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        case_id: UUID | str,
        actor_user_id: UUID | str | None,
        body: str,
        direction: str,
        channel: str,
        template_id: UUID | str | None = None,
        to_number: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> dbm.CommunicationMessage:
        thread = self.get_or_create_thread(db, tenant_id=tenant_id, case_id=case_id, channel=channel)
        provider_message_id = None
        message_status = "received" if direction == "inbound" else "queued"
        if channel == "whatsapp" and direction == "outbound":
            result = self.whatsapp_service.send(to_number=to_number or "mock-client", body=body, metadata=metadata)
            provider_message_id = result.provider_message_id
            message_status = result.status
        elif direction == "outbound":
            message_status = "sent"

        message = dbm.CommunicationMessage(
            tenant_id=str(tenant_id),
            thread_id=thread.id,
            case_id=thread.case_id,
            client_id=thread.client_id,
            sender_user_id=str(actor_user_id) if actor_user_id else None,
            direction=direction,
            channel=channel,
            body=body,
            status=message_status,
            provider_message_id=provider_message_id,
            template_id=str(template_id) if template_id else None,
            metadata_json=metadata or {},
        )
        db.add(message)
        db.flush()
        self.audit_service.record(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="communication_message_created",
            entity_type="communication_message",
            entity_id=message.id,
            request_id=request_id,
            metadata={"case_id": thread.case_id, "channel": channel, "direction": direction},
        )
        db.commit()
        db.refresh(message)
        return message

    def serialize_message(self, message: dbm.CommunicationMessage) -> dict[str, object]:
        return {
            "id": message.id,
            "thread_id": message.thread_id,
            "case_id": message.case_id,
            "client_id": message.client_id,
            "direction": message.direction,
            "channel": message.channel,
            "body": message.body,
            "status": message.status,
            "provider_message_id": message.provider_message_id,
            "created_at": _iso(message.created_at),
        }

    def serialize_thread(self, db: Session, thread: dbm.CommunicationThread) -> dict[str, object]:
        messages = db.scalars(
            select(dbm.CommunicationMessage)
            .where(dbm.CommunicationMessage.tenant_id == thread.tenant_id, dbm.CommunicationMessage.thread_id == thread.id)
            .order_by(dbm.CommunicationMessage.created_at.asc())
        ).all()
        return {
            "id": thread.id,
            "case_id": thread.case_id,
            "client_id": thread.client_id,
            "subject": thread.subject,
            "channel": thread.channel,
            "status": thread.status,
            "messages": [self.serialize_message(message) for message in messages],
        }


class NotificationService:
    def __init__(self, *, audit_service: CommunicationAuditService, template_service: MessageTemplateService, communication_service: CommunicationService) -> None:
        self.audit_service = audit_service
        self.template_service = template_service
        self.communication_service = communication_service

    def list(self, db: Session, *, tenant_id: UUID | str) -> list[dbm.Notification]:
        return db.scalars(
            select(dbm.Notification).where(dbm.Notification.tenant_id == str(tenant_id)).order_by(dbm.Notification.created_at.desc())
        ).all()

    def send(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor_user_id: UUID | str | None,
        case_id: UUID | str,
        title: str,
        body: str,
        channel: str,
        user_id: UUID | str | None = None,
        template_id: UUID | str | None = None,
        variables: dict[str, object] | None = None,
        request_id: str | None = None,
    ) -> dbm.Notification:
        legal_case = self.communication_service.get_case(db, tenant_id=tenant_id, case_id=case_id)
        rendered_body = body
        if template_id:
            template = self.template_service.get(db, tenant_id=tenant_id, template_id=template_id)
            rendered_body = self.template_service.render(template, variables)
        notification = dbm.Notification(
            tenant_id=str(tenant_id),
            user_id=str(user_id) if user_id else None,
            case_id=legal_case.id,
            title=title,
            body=rendered_body,
            channel=channel,
            status="sent",
        )
        db.add(notification)
        db.flush()
        if channel in {"portal", "whatsapp", "email"}:
            self.communication_service.create_message(
                db,
                tenant_id=tenant_id,
                case_id=legal_case.id,
                actor_user_id=actor_user_id,
                body=rendered_body,
                direction="outbound",
                channel=channel,
                template_id=template_id,
                request_id=request_id,
                metadata={"notification_id": notification.id},
            )
        self.audit_service.record(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="notification_sent",
            entity_type="notification",
            entity_id=notification.id,
            request_id=request_id,
            metadata={"case_id": legal_case.id, "channel": channel},
        )
        db.commit()
        db.refresh(notification)
        return notification

    def test(self, db: Session, *, tenant_id: UUID | str, template_id: UUID | str, variables: dict[str, object] | None = None) -> dict[str, object]:
        template = self.template_service.get(db, tenant_id=tenant_id, template_id=template_id)
        return {"template_id": template.id, "channel": template.channel, "body": self.template_service.render(template, variables), "status": "rendered"}

    def mark_read(self, db: Session, *, tenant_id: UUID | str, notification_id: UUID | str, actor: User | None = None) -> dbm.Notification:
        notification = db.scalars(
            select(dbm.Notification).where(dbm.Notification.tenant_id == str(tenant_id), dbm.Notification.id == str(notification_id))
        ).first()
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        notification.status = "read"
        notification.read_at = dbm.now_utc()
        self.audit_service.record(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor.id if actor else None,
            action="notification_marked_read",
            entity_type="notification",
            entity_id=notification.id,
            metadata={"case_id": notification.case_id},
        )
        db.commit()
        db.refresh(notification)
        return notification


communication_audit_service = CommunicationAuditService()
message_template_service = MessageTemplateService()
whatsapp_service = WhatsAppService()
communication_service = CommunicationService(audit_service=communication_audit_service, whatsapp_service=whatsapp_service)
notification_service = NotificationService(
    audit_service=communication_audit_service,
    template_service=message_template_service,
    communication_service=communication_service,
)
