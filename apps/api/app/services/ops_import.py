from __future__ import annotations

import csv
from io import StringIO
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import User
from app.services.storage import tenant_storage_key


def _rows(csv_text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(StringIO(csv_text.strip()))
    if not reader.fieldnames:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="CSV header is required")
    return [{str(key or "").strip(): str(value or "").strip() for key, value in row.items()} for row in reader]


def _tags(value: str) -> list[str]:
    return [item.strip() for item in value.replace(",", ";").split(";") if item.strip()]


def _bool(value: str, *, default: bool = False) -> bool:
    if not value:
        return default
    return value.strip().lower() in {"1", "true", "yes", "si", "visible"}


class OpsImportService:
    def bootstrap_current_tenant(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor: User,
        name: str,
        slug: str,
        plan: str,
        request_id: str | None = None,
    ) -> dict[str, object]:
        tenant = db.get(dbm.Tenant, str(tenant_id))
        created = False
        if tenant is None:
            tenant = dbm.Tenant(id=str(tenant_id), name=name, slug=slug, plan=plan)
            db.add(tenant)
            created = True
        else:
            tenant.name = name
            tenant.slug = slug
            tenant.plan = plan
            tenant.status = "active"
        self._audit(db, tenant_id=tenant_id, actor=actor, action="tenant_bootstrapped", entity_type="tenant", entity_id=tenant.id, request_id=request_id, metadata={"created": created, "slug": slug, "plan": plan})
        db.commit()
        return {"tenant_id": tenant.id, "name": tenant.name, "slug": tenant.slug, "plan": tenant.plan, "created": created}

    def import_clients(self, db: Session, *, tenant_id: UUID | str, actor: User, csv_text: str, dry_run: bool, request_id: str | None = None) -> dict[str, object]:
        rows = _rows(csv_text)
        errors: list[dict[str, object]] = []
        created: list[dict[str, object]] = []
        skipped = 0
        for index, row in enumerate(rows, start=2):
            name = row.get("name", "")
            if not name:
                errors.append({"line": index, "error": "name is required"})
                continue
            email = row.get("contact_email") or None
            existing = self._find_client(db, tenant_id=tenant_id, name=name, contact_email=email)
            if existing:
                skipped += 1
                continue
            item = {
                "name": name,
                "contact_email": email,
                "risk_profile": row.get("risk_profile") or "standard",
                "tags": _tags(row.get("tags", "")),
            }
            created.append(item)
            if not dry_run:
                db.add(dbm.Client(tenant_id=str(tenant_id), **item))
        if not dry_run and not errors:
            self._audit(db, tenant_id=tenant_id, actor=actor, action="clients_imported", entity_type="import_batch", entity_id=tenant_id, request_id=request_id, metadata={"created": len(created), "skipped": skipped})
            db.commit()
        return {"kind": "clients", "dry_run": dry_run, "created": len(created), "skipped": skipped, "errors": errors, "preview": created[:10]}

    def import_cases(self, db: Session, *, tenant_id: UUID | str, actor: User, csv_text: str, dry_run: bool, request_id: str | None = None) -> dict[str, object]:
        rows = _rows(csv_text)
        errors: list[dict[str, object]] = []
        created: list[dict[str, object]] = []
        skipped = 0
        for index, row in enumerate(rows, start=2):
            title = row.get("title", "")
            client = self._find_client(db, tenant_id=tenant_id, name=row.get("client_name", ""), contact_email=row.get("client_email") or None)
            if not title:
                errors.append({"line": index, "error": "title is required"})
                continue
            if not client:
                errors.append({"line": index, "error": "client not found"})
                continue
            external = row.get("external_case_number") or None
            existing = self._find_case(db, tenant_id=tenant_id, client_id=client.id, title=title, external_case_number=external)
            if existing:
                skipped += 1
                continue
            status_value = row.get("status") or "active"
            item = {
                "client_id": client.id,
                "title": title,
                "external_case_number": external,
                "status": status_value,
                "description": row.get("description") or None,
            }
            created.append({**item, "client_name": client.name})
            if not dry_run:
                db.add(dbm.Case(tenant_id=str(tenant_id), **item))
        if not dry_run and not errors:
            self._audit(db, tenant_id=tenant_id, actor=actor, action="cases_imported", entity_type="import_batch", entity_id=tenant_id, request_id=request_id, metadata={"created": len(created), "skipped": skipped})
            db.commit()
        return {"kind": "cases", "dry_run": dry_run, "created": len(created), "skipped": skipped, "errors": errors, "preview": created[:10]}

    def import_documents(self, db: Session, *, tenant_id: UUID | str, actor: User, csv_text: str, dry_run: bool, request_id: str | None = None) -> dict[str, object]:
        rows = _rows(csv_text)
        errors: list[dict[str, object]] = []
        created: list[dict[str, object]] = []
        skipped = 0
        for index, row in enumerate(rows, start=2):
            filename = row.get("filename", "")
            legal_case = self._find_case_by_ref(db, tenant_id=tenant_id, external_case_number=row.get("case_external_case_number", ""), title=row.get("case_title", ""))
            if not filename:
                errors.append({"line": index, "error": "filename is required"})
                continue
            if not legal_case:
                errors.append({"line": index, "error": "case not found"})
                continue
            existing = db.scalars(
                select(dbm.Document).where(
                    dbm.Document.tenant_id == str(tenant_id),
                    dbm.Document.case_id == legal_case.id,
                    dbm.Document.filename == filename,
                    dbm.Document.deleted_at.is_(None),
                )
            ).first()
            if existing:
                skipped += 1
                continue
            document_id = dbm.new_id()
            storage_key = tenant_storage_key(tenant_id=tenant_id, case_id=legal_case.id, document_id=document_id, filename=filename)
            item = {
                "id": document_id,
                "case_id": legal_case.id,
                "client_id": legal_case.client_id,
                "filename": filename,
                "storage_key": storage_key,
                "content_type": row.get("content_type") or "application/pdf",
                "status": "pending_upload",
                "classification": row.get("classification") or None,
                "is_client_visible": _bool(row.get("is_client_visible", ""), default=False),
                "uploaded_by_client": False,
            }
            created.append({**item, "case_title": legal_case.title})
            if not dry_run:
                db.add(dbm.Document(tenant_id=str(tenant_id), **item))
        if not dry_run and not errors:
            self._audit(db, tenant_id=tenant_id, actor=actor, action="documents_manifest_imported", entity_type="import_batch", entity_id=tenant_id, request_id=request_id, metadata={"created": len(created), "skipped": skipped})
            db.commit()
        return {"kind": "documents", "dry_run": dry_run, "created": len(created), "skipped": skipped, "errors": errors, "preview": created[:10]}

    def _find_client(self, db: Session, *, tenant_id: UUID | str, name: str, contact_email: str | None) -> dbm.Client | None:
        if contact_email:
            found = db.scalars(select(dbm.Client).where(dbm.Client.tenant_id == str(tenant_id), dbm.Client.contact_email == contact_email, dbm.Client.deleted_at.is_(None))).first()
            if found:
                return found
        if name:
            return db.scalars(select(dbm.Client).where(dbm.Client.tenant_id == str(tenant_id), dbm.Client.name == name, dbm.Client.deleted_at.is_(None))).first()
        return None

    def _find_case(self, db: Session, *, tenant_id: UUID | str, client_id: str, title: str, external_case_number: str | None) -> dbm.Case | None:
        if external_case_number:
            found = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == str(tenant_id), dbm.Case.external_case_number == external_case_number, dbm.Case.deleted_at.is_(None))).first()
            if found:
                return found
        return db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == str(tenant_id), dbm.Case.client_id == client_id, dbm.Case.title == title, dbm.Case.deleted_at.is_(None))).first()

    def _find_case_by_ref(self, db: Session, *, tenant_id: UUID | str, external_case_number: str, title: str) -> dbm.Case | None:
        if external_case_number:
            found = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == str(tenant_id), dbm.Case.external_case_number == external_case_number, dbm.Case.deleted_at.is_(None))).first()
            if found:
                return found
        if title:
            return db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == str(tenant_id), dbm.Case.title == title, dbm.Case.deleted_at.is_(None))).first()
        return None

    def _audit(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor: User,
        action: str,
        entity_type: str,
        entity_id: UUID | str,
        request_id: str | None,
        metadata: dict[str, object],
    ) -> None:
        db.add(
            dbm.AuditLog(
                tenant_id=str(tenant_id),
                actor_user_id=str(actor.id),
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id),
                request_id=request_id,
                metadata_json=metadata,
            )
        )


ops_import_service = OpsImportService()
