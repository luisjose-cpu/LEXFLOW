from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import User
from app.services.storage import storage_service


class DocumentLifecycleService:
    def get_document(self, db: Session, *, tenant_id: UUID | str, document_id: UUID | str) -> dbm.Document:
        document = db.get(dbm.Document, str(document_id))
        if not document or document.tenant_id != str(tenant_id) or document.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    def storage_status(self, db: Session, *, tenant_id: UUID | str, document_id: UUID | str) -> dict[str, object]:
        document = self.get_document(db, tenant_id=tenant_id, document_id=document_id)
        metadata = storage_service.object_metadata(storage_key=document.storage_key)
        return self.serialize(document, storage=metadata)

    def verify_storage(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        document_id: UUID | str,
        actor: User,
        request_id: str | None = None,
    ) -> dict[str, object]:
        document = self.get_document(db, tenant_id=tenant_id, document_id=document_id)
        metadata = storage_service.object_metadata(storage_key=document.storage_key)
        if not metadata["exists"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored object not found")
        document.file_size_bytes = int(metadata["bytes"])
        document.checksum_sha256 = str(metadata["sha256"])
        document.storage_verified_at = dbm.now_utc()
        if document.status in {"pending_upload", "missing"}:
            document.status = "uploaded"
        self.audit(
            db,
            tenant_id=tenant_id,
            actor=actor,
            action="document_storage_verified",
            document=document,
            request_id=request_id,
            metadata=metadata,
        )
        db.commit()
        db.refresh(document)
        return self.serialize(document, storage=metadata)

    def scan_mock(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        document_id: UUID | str,
        actor: User,
        verdict: str = "clean",
        request_id: str | None = None,
    ) -> dict[str, object]:
        if verdict not in {"clean", "infected"}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid scan verdict")
        document = self.get_document(db, tenant_id=tenant_id, document_id=document_id)
        metadata = storage_service.object_metadata(storage_key=document.storage_key)
        if not metadata["exists"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored object not found")
        document.file_size_bytes = int(metadata["bytes"])
        document.checksum_sha256 = str(metadata["sha256"])
        document.storage_verified_at = dbm.now_utc()
        document.malware_scan_status = verdict
        document.malware_scan_result = {
            "engine": "mock",
            "verdict": verdict,
            "scanned_at": dbm.now_utc().isoformat(),
            "sha256": metadata["sha256"],
        }
        document.status = "verified" if verdict == "clean" else "rejected"
        if verdict == "infected":
            document.is_client_visible = False
        self.audit(
            db,
            tenant_id=tenant_id,
            actor=actor,
            action="document_malware_scan_completed",
            document=document,
            request_id=request_id,
            metadata={"verdict": verdict, **metadata},
        )
        db.commit()
        db.refresh(document)
        return self.serialize(document, storage=metadata)

    def reject(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        document_id: UUID | str,
        actor: User,
        reason: str,
        request_id: str | None = None,
    ) -> dict[str, object]:
        document = self.get_document(db, tenant_id=tenant_id, document_id=document_id)
        document.status = "rejected"
        document.is_client_visible = False
        document.malware_scan_result = {**(document.malware_scan_result or {}), "rejection_reason": reason}
        self.audit(
            db,
            tenant_id=tenant_id,
            actor=actor,
            action="document_rejected",
            document=document,
            request_id=request_id,
            metadata={"reason": reason},
        )
        db.commit()
        db.refresh(document)
        return self.serialize(document, storage=storage_service.object_metadata(storage_key=document.storage_key))

    def serialize(self, document: dbm.Document, *, storage: dict[str, object] | None = None) -> dict[str, object]:
        return {
            "id": document.id,
            "tenant_id": document.tenant_id,
            "case_id": document.case_id,
            "client_id": document.client_id,
            "filename": document.filename,
            "storage_key": document.storage_key,
            "content_type": document.content_type,
            "status": document.status,
            "classification": document.classification,
            "is_client_visible": document.is_client_visible,
            "uploaded_by_client": document.uploaded_by_client,
            "file_size_bytes": document.file_size_bytes,
            "checksum_sha256": document.checksum_sha256,
            "storage_verified_at": document.storage_verified_at.isoformat() if document.storage_verified_at else None,
            "malware_scan_status": document.malware_scan_status,
            "malware_scan_result": document.malware_scan_result,
            "storage": storage or {},
        }

    def audit(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor: User,
        action: str,
        document: dbm.Document,
        request_id: str | None,
        metadata: dict[str, object],
    ) -> None:
        db.add(
            dbm.AuditLog(
                tenant_id=str(tenant_id),
                actor_user_id=str(actor.id),
                action=action,
                entity_type="document",
                entity_id=document.id,
                request_id=request_id,
                metadata_json={"case_id": document.case_id, **metadata},
            )
        )


document_lifecycle_service = DocumentLifecycleService()
