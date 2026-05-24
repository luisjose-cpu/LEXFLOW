from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.core.config import get_settings
from app.domain.models import RoleName, User
from app.services.communication import communication_service
from app.services.storage import storage_service, tenant_storage_key


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _validate_upload(filename: str, content_type: str) -> str:
    settings = get_settings()
    clean = filename.strip().replace("\\", "/").split("/")[-1]
    allowed_types = {item.strip() for item in settings.allowed_upload_content_types.split(",") if item.strip()}
    blocked_suffixes = (".exe", ".bat", ".cmd", ".ps1", ".sh", ".js", ".html", ".svg")
    if not clean or clean in {".", ".."}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid filename")
    if len(clean) > settings.max_upload_filename_length:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Filename too long")
    if clean.lower().endswith(blocked_suffixes):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="File type is not allowed")
    if content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Content type is not allowed")
    return clean


class ClientPortalService:
    def require_client_user(self, actor: User) -> None:
        if actor.role != RoleName.client_user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client portal requires a client user")

    def portal_client(self, db: Session, *, actor: User) -> dbm.Client:
        self.require_client_user(actor)
        client = db.scalars(
            select(dbm.Client).where(
                dbm.Client.tenant_id == str(actor.tenant_id),
                dbm.Client.contact_email == actor.email,
                dbm.Client.deleted_at.is_(None),
                dbm.Client.status == "active",
            )
        ).first()
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client portal profile not linked")
        return client

    def portal_db_user(self, db: Session, *, actor: User) -> dbm.User | None:
        return db.scalars(
            select(dbm.User).where(
                dbm.User.tenant_id == str(actor.tenant_id),
                dbm.User.email == actor.email,
                dbm.User.deleted_at.is_(None),
            )
        ).first()

    def get_case(self, db: Session, *, actor: User, case_id: UUID | str) -> dbm.Case:
        client = self.portal_client(db, actor=actor)
        legal_case = db.scalars(
            select(dbm.Case).where(
                dbm.Case.tenant_id == str(actor.tenant_id),
                dbm.Case.client_id == client.id,
                dbm.Case.id == str(case_id),
                dbm.Case.deleted_at.is_(None),
            )
        ).first()
        if not legal_case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        return legal_case

    def me(self, db: Session, *, actor: User) -> dict[str, object]:
        client = self.portal_client(db, actor=actor)
        return {
            "user": {"id": str(actor.id), "email": actor.email, "full_name": actor.full_name, "role": actor.role.value},
            "client": self.serialize_client(client),
            "permissions": ["portal:read", "portal:message", "portal:upload"],
        }

    def cases(self, db: Session, *, actor: User) -> list[dict[str, object]]:
        client = self.portal_client(db, actor=actor)
        rows = db.scalars(
            select(dbm.Case)
            .where(
                dbm.Case.tenant_id == str(actor.tenant_id),
                dbm.Case.client_id == client.id,
                dbm.Case.deleted_at.is_(None),
            )
            .order_by(dbm.Case.updated_at.desc())
        ).all()
        return [self.serialize_case(row) for row in rows]

    def case_detail(self, db: Session, *, actor: User, case_id: UUID | str) -> dict[str, object]:
        legal_case = self.get_case(db, actor=actor, case_id=case_id)
        return {
            "case": self.serialize_case(legal_case),
            "timeline": self.timeline(db, actor=actor, case_id=case_id),
            "documents": self.documents(db, actor=actor, case_id=case_id),
            "hearings": self.hearings(db, actor=actor, case_id=case_id),
            "messages": self.messages(db, actor=actor, case_id=case_id),
        }

    def timeline(self, db: Session, *, actor: User, case_id: UUID | str) -> list[dict[str, object]]:
        legal_case = self.get_case(db, actor=actor, case_id=case_id)
        events = db.scalars(
            select(dbm.CaseEvent).where(
                dbm.CaseEvent.tenant_id == str(actor.tenant_id),
                dbm.CaseEvent.case_id == legal_case.id,
                dbm.CaseEvent.is_client_visible.is_(True),
            )
        ).all()
        judicial_updates = db.scalars(
            select(dbm.JudicialUpdate).where(
                dbm.JudicialUpdate.tenant_id == str(actor.tenant_id),
                dbm.JudicialUpdate.case_id == legal_case.id,
                dbm.JudicialUpdate.status == "approved",
                dbm.JudicialUpdate.captcha_required.is_(False),
            )
        ).all()
        items = [
            {
                "id": event.id,
                "type": "case_event",
                "title": event.title,
                "summary": event.description,
                "occurred_at": _iso(event.occurred_at),
            }
            for event in events
        ]
        items.extend(
            {
                "id": update.id,
                "type": "judicial_update",
                "title": update.title,
                "summary": update.summary,
                "occurred_at": _iso(update.checked_at),
            }
            for update in judicial_updates
        )
        return sorted(items, key=lambda item: str(item["occurred_at"] or ""), reverse=True)

    def documents(self, db: Session, *, actor: User, case_id: UUID | str) -> list[dict[str, object]]:
        legal_case = self.get_case(db, actor=actor, case_id=case_id)
        rows = db.scalars(
            select(dbm.Document)
            .where(
                dbm.Document.tenant_id == str(actor.tenant_id),
                dbm.Document.case_id == legal_case.id,
                dbm.Document.client_id == legal_case.client_id,
                dbm.Document.is_client_visible.is_(True),
                dbm.Document.deleted_at.is_(None),
                dbm.Document.status != "private",
            )
            .order_by(dbm.Document.created_at.desc())
        ).all()
        return [self.serialize_document(row) for row in rows]

    def get_visible_document(self, db: Session, *, actor: User, document_id: UUID | str) -> dbm.Document:
        client = self.portal_client(db, actor=actor)
        document = db.scalars(
            select(dbm.Document)
            .join(dbm.Case, dbm.Case.id == dbm.Document.case_id)
            .where(
                dbm.Document.tenant_id == str(actor.tenant_id),
                dbm.Document.id == str(document_id),
                dbm.Document.client_id == client.id,
                dbm.Document.is_client_visible.is_(True),
                dbm.Document.deleted_at.is_(None),
                dbm.Document.status != "private",
                dbm.Case.client_id == client.id,
                dbm.Case.deleted_at.is_(None),
            )
        ).first()
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    def hearings(self, db: Session, *, actor: User, case_id: UUID | str) -> list[dict[str, object]]:
        legal_case = self.get_case(db, actor=actor, case_id=case_id)
        rows = db.scalars(
            select(dbm.Hearing)
            .where(
                dbm.Hearing.tenant_id == str(actor.tenant_id),
                dbm.Hearing.case_id == legal_case.id,
                dbm.Hearing.deleted_at.is_(None),
            )
            .order_by(dbm.Hearing.starts_at.asc())
        ).all()
        return [
            {"id": row.id, "title": row.title, "starts_at": _iso(row.starts_at), "location": row.location, "status": row.status}
            for row in rows
        ]

    def notifications(self, db: Session, *, actor: User) -> list[dict[str, object]]:
        client = self.portal_client(db, actor=actor)
        db_user = self.portal_db_user(db, actor=actor)
        client_case_ids = select(dbm.Case.id).where(dbm.Case.tenant_id == str(actor.tenant_id), dbm.Case.client_id == client.id)
        user_filter = dbm.Notification.user_id == db_user.id if db_user else dbm.Notification.user_id.is_(None)
        rows = db.scalars(
            select(dbm.Notification)
            .where(
                dbm.Notification.tenant_id == str(actor.tenant_id),
                dbm.Notification.case_id.in_(client_case_ids),
                or_(user_filter, and_(dbm.Notification.user_id.is_(None), dbm.Notification.channel == "portal")),
            )
            .order_by(dbm.Notification.created_at.desc())
        ).all()
        return [
            {
                "id": row.id,
                "case_id": row.case_id,
                "title": row.title,
                "body": row.body,
                "status": row.status,
                "created_at": _iso(row.created_at),
            }
            for row in rows
        ]

    def messages(self, db: Session, *, actor: User, case_id: UUID | str) -> list[dict[str, object]]:
        legal_case = self.get_case(db, actor=actor, case_id=case_id)
        rows = db.scalars(
            select(dbm.WhatsAppMessage)
            .where(
                dbm.WhatsAppMessage.tenant_id == str(actor.tenant_id),
                dbm.WhatsAppMessage.case_id == legal_case.id,
                dbm.WhatsAppMessage.client_id == legal_case.client_id,
            )
            .order_by(dbm.WhatsAppMessage.created_at.asc())
        ).all()
        return [self.serialize_message(row) for row in rows]

    def create_message(self, db: Session, *, actor: User, case_id: UUID | str, body: str, request_id: str | None = None) -> dict[str, object]:
        legal_case = self.get_case(db, actor=actor, case_id=case_id)
        message = dbm.WhatsAppMessage(
            tenant_id=str(actor.tenant_id),
            case_id=legal_case.id,
            client_id=legal_case.client_id,
            direction="inbound",
            from_number="client_portal",
            to_number="legal_team",
            body=body,
            status="received",
        )
        db.add(message)
        db.flush()
        self.audit(db, actor=actor, action="portal_message_created", entity_type="portal_message", entity_id=message.id, request_id=request_id, metadata={"case_id": legal_case.id})
        communication_service.create_message(
            db,
            tenant_id=actor.tenant_id,
            case_id=legal_case.id,
            actor_user_id=actor.id,
            body=body,
            direction="inbound",
            channel="portal",
            request_id=request_id,
            metadata={"legacy_whatsapp_message_id": message.id, "source": "client_portal"},
        )
        db.commit()
        return self.serialize_message(message)

    def upload_document(
        self,
        db: Session,
        *,
        actor: User,
        case_id: UUID | str,
        filename: str,
        content_type: str,
        request_id: str | None = None,
    ) -> dict[str, object]:
        legal_case = self.get_case(db, actor=actor, case_id=case_id)
        safe_filename = _validate_upload(filename, content_type)
        document_id = str(dbm.new_id())
        storage_key = tenant_storage_key(
            tenant_id=actor.tenant_id,
            case_id=legal_case.id,
            document_id=document_id,
            filename=safe_filename,
        )
        document = dbm.Document(
            id=document_id,
            tenant_id=str(actor.tenant_id),
            case_id=legal_case.id,
            client_id=legal_case.client_id,
            filename=safe_filename,
            storage_key=storage_key,
            content_type=content_type,
            status="pending_review",
            classification="client_upload",
            is_client_visible=True,
            uploaded_by_client=True,
        )
        db.add(document)
        db.flush()
        self.audit(db, actor=actor, action="portal_document_uploaded", entity_type="document", entity_id=document.id, request_id=request_id, metadata={"case_id": legal_case.id})
        db.commit()
        return {
            **self.serialize_document(document),
            "upload": storage_service.upload_contract(
                tenant_id=actor.tenant_id,
                case_id=legal_case.id,
                document_id=document.id,
                filename=safe_filename,
                content_type=content_type,
            )["upload"],
        }

    def download_document(self, db: Session, *, actor: User, document_id: UUID | str, request_id: str | None = None) -> dict[str, object]:
        document = self.get_visible_document(db, actor=actor, document_id=document_id)
        if get_settings().require_verified_document_downloads and (
            document.status != "verified" or document.malware_scan_status != "clean" or not document.storage_verified_at
        ):
            self.audit(
                db,
                actor=actor,
                action="portal_document_download_blocked_unverified",
                entity_type="document",
                entity_id=document.id,
                request_id=request_id,
                metadata={"case_id": document.case_id, "status": document.status, "malware_scan_status": document.malware_scan_status},
            )
            db.commit()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document is pending verification")
        self.audit(
            db,
            actor=actor,
            action="portal_document_download_link_created",
            entity_type="document",
            entity_id=document.id,
            request_id=request_id,
            metadata={"case_id": document.case_id, "storage_key": document.storage_key},
        )
        db.commit()
        return storage_service.signed_download_url(document=document, actor_user_id=actor.id, purpose="portal_download")

    def reports(self, db: Session, *, actor: User) -> dict[str, object]:
        client = self.portal_client(db, actor=actor)
        case_ids = select(dbm.Case.id).where(dbm.Case.tenant_id == str(actor.tenant_id), dbm.Case.client_id == client.id, dbm.Case.deleted_at.is_(None))
        visible_docs = db.scalar(
            select(func.count()).select_from(dbm.Document).where(dbm.Document.tenant_id == str(actor.tenant_id), dbm.Document.case_id.in_(case_ids), dbm.Document.is_client_visible.is_(True), dbm.Document.deleted_at.is_(None))
        )
        hearings = db.scalar(
            select(func.count()).select_from(dbm.Hearing).where(dbm.Hearing.tenant_id == str(actor.tenant_id), dbm.Hearing.case_id.in_(case_ids), dbm.Hearing.deleted_at.is_(None))
        )
        cases = self.cases(db, actor=actor)
        return {
            "client": self.serialize_client(client),
            "metrics": {
                "cases": len(cases),
                "visible_documents": int(visible_docs or 0),
                "hearings": int(hearings or 0),
                "open_requests": 0,
            },
            "cases": cases,
        }

    def serialize_client(self, client: dbm.Client) -> dict[str, object]:
        return {"id": client.id, "name": client.name, "contact_email": client.contact_email, "status": client.status, "tags": client.tags}

    def serialize_case(self, legal_case: dbm.Case) -> dict[str, object]:
        return {
            "id": legal_case.id,
            "title": legal_case.title,
            "external_case_number": legal_case.external_case_number,
            "status": legal_case.status,
            "description": legal_case.description,
            "updated_at": _iso(legal_case.updated_at),
        }

    def serialize_document(self, document: dbm.Document) -> dict[str, object]:
        return {
            "id": document.id,
            "case_id": document.case_id,
            "filename": document.filename,
            "content_type": document.content_type,
            "status": document.status,
            "classification": document.classification,
            "uploaded_by_client": document.uploaded_by_client,
            "download_available": bool(document.storage_key),
            "file_size_bytes": document.file_size_bytes,
            "checksum_sha256": document.checksum_sha256,
            "storage_verified_at": _iso(document.storage_verified_at),
            "malware_scan_status": document.malware_scan_status,
            "created_at": _iso(document.created_at),
        }

    def serialize_message(self, message: dbm.WhatsAppMessage) -> dict[str, object]:
        return {
            "id": message.id,
            "case_id": message.case_id,
            "direction": message.direction,
            "body": message.body,
            "status": message.status,
            "created_at": _iso(message.created_at),
        }

    def audit(
        self,
        db: Session,
        *,
        actor: User,
        action: str,
        entity_type: str,
        entity_id: str,
        request_id: str | None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        db.add(
            dbm.AuditLog(
                tenant_id=str(actor.tenant_id),
                actor_user_id=str(actor.id),
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                request_id=request_id,
                metadata_json=metadata or {},
            )
        )


client_portal_service = ClientPortalService()
