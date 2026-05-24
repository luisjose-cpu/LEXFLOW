from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.services.case_overview import get_case_or_404


def _tenant(tenant_id: UUID | str) -> str:
    return str(tenant_id)


def _contains(value: object, needle: str) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return any(_contains(item, needle) for item in value)
    return needle in str(value).lower()


class OperationalCoreService:
    def global_search(self, db: Session, *, tenant_id: UUID | str, query: str, limit: int = 12) -> dict[str, object]:
        needle = query.strip().lower()
        clients = self._clients(db, tenant_id=tenant_id)
        cases = self._cases(db, tenant_id=tenant_id)
        documents = self._documents(db, tenant_id=tenant_id)
        hearings = self._hearings(db, tenant_id=tenant_id)
        updates = self._judicial_updates(db, tenant_id=tenant_id)
        news = self._legal_news(db, tenant_id=tenant_id)

        buckets = {
            "clients": [
                self._quick_result("client", client.id, client.name, client.contact_email or "Sin correo", f"/clients/{client.id}", client.tags)
                for client in clients
                if self._matches_client(client, needle)
            ],
            "cases": [
                self._quick_result("case", legal_case.id, legal_case.title, legal_case.external_case_number or "Sin numero", f"/cases/{legal_case.id}", [legal_case.status])
                for legal_case in cases
                if self._matches_case(legal_case, needle)
            ],
            "documents": [
                self._quick_result("document", document.id, document.filename, document.classification or document.status, f"/cases/{document.case_id}/documents", [document.content_type])
                for document in documents
                if self._matches_document(document, needle)
            ],
            "hearings": [
                self._quick_result("hearing", hearing.id, hearing.title, hearing.location or "Sin ubicacion", f"/cases/{hearing.case_id}/hearings", [hearing.status])
                for hearing in hearings
                if self._matches_hearing(hearing, needle)
            ],
            "judicial_updates": [
                self._quick_result("judicial_update", update.id, update.title, update.summary or "Sin resumen", f"/cases/{update.case_id}/judicial", [update.status])
                for update in updates
                if self._matches_update(update, needle)
            ],
            "legal_news": [
                self._quick_result("legal_news", item.id, item.title, item.summary or "Sin resumen", "/legal-intelligence", item.tags)
                for item in news
                if _contains(item.title, needle) or _contains(item.summary, needle) or _contains(item.tags, needle)
            ],
        }
        flat = [item for bucket in buckets.values() for item in bucket][:limit]
        return {
            "query": query,
            "quick_results": flat,
            "advanced_results": buckets,
            "recent_searches": [query, "SINOE", "audiencia", "Nova Capital"],
            "favorites": [item for item in flat if item["type"] in {"client", "case"}][:3],
            "ai_future_ready": True,
        }

    def client_search(self, db: Session, *, tenant_id: UUID | str, query: str, limit: int = 20) -> list[dict[str, object]]:
        needle = query.strip().lower()
        return [self.serialize_client_summary(db, client) for client in self._clients(db, tenant_id=tenant_id) if self._matches_client(client, needle)][:limit]

    def case_search(self, db: Session, *, tenant_id: UUID | str, query: str, limit: int = 20) -> list[dict[str, object]]:
        needle = query.strip().lower()
        return [self.serialize_case_summary(db, legal_case) for legal_case in self._cases(db, tenant_id=tenant_id) if self._matches_case(legal_case, needle)][:limit]

    def client_profile(self, db: Session, *, tenant_id: UUID | str, client_id: UUID | str) -> dict[str, object]:
        client = self._client_or_404(db, tenant_id=tenant_id, client_id=client_id)
        cases = self._client_cases(db, tenant_id=tenant_id, client_id=client.id)
        documents = self._client_documents(db, tenant_id=tenant_id, client_id=client.id)
        communications = self._client_communications(db, tenant_id=tenant_id, client_id=client.id)
        updates = self._client_updates(db, tenant_id=tenant_id, case_ids=[case.id for case in cases])
        hearings = self._client_hearings(db, tenant_id=tenant_id, case_ids=[case.id for case in cases])
        timeline = self.client_timeline(db, tenant_id=tenant_id, client_id=client.id)
        return {
            "client": self.serialize_client_summary(db, client),
            "general": {
                "dni": None,
                "ruc": None,
                "business_name": client.name,
                "sector": client.tags[0] if client.tags else "legal",
                "main_matter": cases[0].title if cases else "Sin materia principal",
                "status": client.status,
                "priority": "alta" if client.risk_profile == "high" else "normal",
            },
            "metrics": self.client_metrics(db, tenant_id=tenant_id, client_id=client.id),
            "risk": self.client_risk(db, tenant_id=tenant_id, client_id=client.id),
            "cases": [self.serialize_case_summary(db, item) for item in cases],
            "documents": [self.serialize_document(item) for item in documents],
            "communications": [self.serialize_communication(item) for item in communications],
            "hearings": [self.serialize_hearing(item) for item in hearings],
            "judicial_updates": [self.serialize_update(item) for item in updates],
            "timeline": timeline,
            "notes": [{"id": f"note-{client.id}", "title": "Nota operacional", "body": "Perfil enriquecido preparado para CRM legal avanzado."}],
            "automation": [{"id": "auto-client", "name": "Alertas de audiencia y documentos", "status": "ready"}],
            "ai": {"summary": "Resumen cliente preparado. Requiere revision profesional.", "future_ready": True},
        }

    def client_timeline(self, db: Session, *, tenant_id: UUID | str, client_id: UUID | str) -> list[dict[str, object]]:
        cases = self._client_cases(db, tenant_id=tenant_id, client_id=client_id)
        case_ids = {case.id for case in cases}
        events = db.scalars(
            select(dbm.CaseEvent).where(dbm.CaseEvent.tenant_id == _tenant(tenant_id), dbm.CaseEvent.case_id.in_(case_ids)).order_by(dbm.CaseEvent.occurred_at.desc())
        ).all() if case_ids else []
        updates = self._client_updates(db, tenant_id=tenant_id, case_ids=list(case_ids))
        timeline = [
            {"id": event.id, "type": event.event_type, "title": event.title, "description": event.description, "occurred_at": event.occurred_at.isoformat()}
            for event in events
        ] + [
            {"id": update.id, "type": "judicial_update", "title": update.title, "description": update.summary, "occurred_at": update.checked_at.isoformat()}
            for update in updates
        ]
        return sorted(timeline, key=lambda item: str(item["occurred_at"]), reverse=True)

    def client_metrics(self, db: Session, *, tenant_id: UUID | str, client_id: UUID | str) -> dict[str, object]:
        cases = self._client_cases(db, tenant_id=tenant_id, client_id=client_id)
        case_ids = [case.id for case in cases]
        documents = self._client_documents(db, tenant_id=tenant_id, client_id=client_id)
        updates = self._client_updates(db, tenant_id=tenant_id, case_ids=case_ids)
        hearings = self._client_hearings(db, tenant_id=tenant_id, case_ids=case_ids)
        return {
            "active_cases": sum(1 for case in cases if case.status != "closed"),
            "documents": len(documents),
            "hearings": len(hearings),
            "judicial_updates": len(updates),
            "captcha_pending": sum(1 for update in updates if update.captcha_required),
        }

    def client_risk(self, db: Session, *, tenant_id: UUID | str, client_id: UUID | str) -> dict[str, object]:
        client = self._client_or_404(db, tenant_id=tenant_id, client_id=client_id)
        cases = self._client_cases(db, tenant_id=tenant_id, client_id=client.id)
        high_signals = sum(1 for case in cases if case.status == "risk")
        return {
            "level": "high" if client.risk_profile == "high" or high_signals else "standard",
            "signals": ["expediente en riesgo"] * high_signals + ["perfil cliente: " + client.risk_profile],
            "recommendation": "Revisar plazos, SINOE y pendientes criticos.",
        }

    def case_documents(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> list[dict[str, object]]:
        get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
        return [self.serialize_document(item) for item in db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == _tenant(tenant_id), dbm.Document.case_id == str(case_id), dbm.Document.deleted_at.is_(None))).all()]

    def case_hearings(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> list[dict[str, object]]:
        get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
        return [self.serialize_hearing(item) for item in db.scalars(select(dbm.Hearing).where(dbm.Hearing.tenant_id == _tenant(tenant_id), dbm.Hearing.case_id == str(case_id), dbm.Hearing.deleted_at.is_(None))).all()]

    def case_judicial(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> dict[str, object]:
        get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
        sources = db.scalars(select(dbm.CaseSource).where(dbm.CaseSource.tenant_id == _tenant(tenant_id), dbm.CaseSource.case_id == str(case_id), dbm.CaseSource.deleted_at.is_(None))).all()
        updates = db.scalars(select(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == _tenant(tenant_id), dbm.JudicialUpdate.case_id == str(case_id)).order_by(dbm.JudicialUpdate.checked_at.desc())).all()
        return {
            "sources": [
                {
                    "id": source.id,
                    "source_type": source.source_type,
                    "source_name": source.source_name,
                    "external_case_number": source.external_case_number,
                    "status": source.status,
                    "captcha_required": source.captcha_required,
                    "last_checked_at": source.last_checked_at.isoformat() if source.last_checked_at else None,
                    "last_result": source.last_result,
                }
                for source in sources
            ],
            "updates": [self.serialize_update(item) for item in updates],
            "sinoe_module": "consumed",
        }

    def case_automation(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> dict[str, object]:
        get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
        workflows = db.scalars(select(dbm.AutomationWorkflow).where(dbm.AutomationWorkflow.tenant_id == _tenant(tenant_id), dbm.AutomationWorkflow.deleted_at.is_(None))).all()
        return {
            "case_id": str(case_id),
            "workflows": [{"id": item.id, "name": item.name, "trigger_key": item.trigger_key, "status": item.status} for item in workflows],
            "available_triggers": ["HEARING_UPCOMING", "DOCUMENT_UPLOADED", "JUDICIAL_UPDATE_APPROVED", "CAPTCHA_REQUIRED", "AI_SUMMARY_COMPLETED"],
        }

    def case_intelligence(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> dict[str, object]:
        get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
        links = db.scalars(select(dbm.LegalNewsCaseLink).where(dbm.LegalNewsCaseLink.tenant_id == _tenant(tenant_id), dbm.LegalNewsCaseLink.case_id == str(case_id))).all()
        news_by_id = {item.id: item for item in self._legal_news(db, tenant_id=tenant_id)}
        return {
            "case_id": str(case_id),
            "linked_news": [
                {
                    "id": news_by_id[link.news_id].id,
                    "title": news_by_id[link.news_id].title,
                    "summary": news_by_id[link.news_id].summary,
                    "tags": news_by_id[link.news_id].tags,
                }
                for link in links
                if link.news_id in news_by_id
            ],
            "trend_notes": ["Inteligencia relacionada lista para decision gerencial."],
        }

    def serialize_client_summary(self, db: Session, client: dbm.Client) -> dict[str, object]:
        cases = self._client_cases(db, tenant_id=client.tenant_id, client_id=client.id)
        return {
            "id": client.id,
            "name": client.name,
            "contact_email": client.contact_email,
            "status": client.status,
            "risk_profile": client.risk_profile,
            "tags": client.tags,
            "case_count": len(cases),
            "active_case_count": sum(1 for case in cases if case.status != "closed"),
        }

    def serialize_case_summary(self, db: Session, legal_case: dbm.Case) -> dict[str, object]:
        client = db.get(dbm.Client, legal_case.client_id)
        updates = db.scalars(select(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == legal_case.tenant_id, dbm.JudicialUpdate.case_id == legal_case.id)).all()
        hearings = db.scalars(select(dbm.Hearing).where(dbm.Hearing.tenant_id == legal_case.tenant_id, dbm.Hearing.case_id == legal_case.id, dbm.Hearing.deleted_at.is_(None))).all()
        return {
            "id": legal_case.id,
            "client_id": legal_case.client_id,
            "client_name": client.name if client and client.tenant_id == legal_case.tenant_id else None,
            "title": legal_case.title,
            "matter": legal_case.description or "Materia principal",
            "external_case_number": legal_case.external_case_number,
            "status": legal_case.status,
            "priority": "alta" if legal_case.status == "risk" else "normal",
            "risk": "high" if legal_case.status == "risk" or any(update.captcha_required for update in updates) else "standard",
            "next_action": "Revisar timeline y SINOE",
            "critical_deadline": hearings[0].starts_at.isoformat() if hearings else None,
            "judicial_updates": len(updates),
            "captcha_pending": sum(1 for update in updates if update.captcha_required),
        }

    @staticmethod
    def serialize_document(document: dbm.Document) -> dict[str, object]:
        return {
            "id": document.id,
            "case_id": document.case_id,
            "filename": document.filename,
            "content_type": document.content_type,
            "classification": document.classification,
            "status": document.status,
            "is_client_visible": document.is_client_visible,
            "malware_scan_status": document.malware_scan_status,
            "created_at": document.created_at.isoformat(),
        }

    @staticmethod
    def serialize_hearing(hearing: dbm.Hearing) -> dict[str, object]:
        return {
            "id": hearing.id,
            "case_id": hearing.case_id,
            "title": hearing.title,
            "starts_at": hearing.starts_at.isoformat(),
            "location": hearing.location,
            "status": hearing.status,
        }

    @staticmethod
    def serialize_update(update: dbm.JudicialUpdate) -> dict[str, object]:
        return {
            "id": update.id,
            "case_id": update.case_id,
            "title": update.title,
            "summary": update.summary,
            "status": update.status,
            "captcha_required": update.captcha_required,
            "requires_human_intervention": update.requires_human_intervention,
            "checked_at": update.checked_at.isoformat(),
            "hash": update.raw_payload.get("external_id") if isinstance(update.raw_payload, dict) else None,
        }

    @staticmethod
    def serialize_communication(message: dbm.CommunicationMessage) -> dict[str, object]:
        return {
            "id": message.id,
            "case_id": message.case_id,
            "direction": message.direction,
            "channel": message.channel,
            "body": message.body,
            "status": message.status,
            "created_at": message.created_at.isoformat(),
        }

    def _client_or_404(self, db: Session, *, tenant_id: UUID | str, client_id: UUID | str) -> dbm.Client:
        client = db.scalar(select(dbm.Client).where(dbm.Client.tenant_id == _tenant(tenant_id), dbm.Client.id == str(client_id), dbm.Client.deleted_at.is_(None)))
        if not client:
            from fastapi import HTTPException, status

            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        return client

    @staticmethod
    def _quick_result(kind: str, item_id: str, title: str, subtitle: str, href: str, tags: list[str]) -> dict[str, object]:
        return {"type": kind, "id": item_id, "title": title, "subtitle": subtitle, "href": href, "tags": tags}

    def _clients(self, db: Session, *, tenant_id: UUID | str) -> list[dbm.Client]:
        return db.scalars(select(dbm.Client).where(dbm.Client.tenant_id == _tenant(tenant_id), dbm.Client.deleted_at.is_(None))).all()

    def _cases(self, db: Session, *, tenant_id: UUID | str) -> list[dbm.Case]:
        return db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == _tenant(tenant_id), dbm.Case.deleted_at.is_(None))).all()

    def _documents(self, db: Session, *, tenant_id: UUID | str) -> list[dbm.Document]:
        return db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == _tenant(tenant_id), dbm.Document.deleted_at.is_(None))).all()

    def _hearings(self, db: Session, *, tenant_id: UUID | str) -> list[dbm.Hearing]:
        return db.scalars(select(dbm.Hearing).where(dbm.Hearing.tenant_id == _tenant(tenant_id), dbm.Hearing.deleted_at.is_(None))).all()

    def _judicial_updates(self, db: Session, *, tenant_id: UUID | str) -> list[dbm.JudicialUpdate]:
        return db.scalars(select(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == _tenant(tenant_id))).all()

    def _legal_news(self, db: Session, *, tenant_id: UUID | str) -> list[dbm.LegalNews]:
        return db.scalars(select(dbm.LegalNews).where(dbm.LegalNews.tenant_id == _tenant(tenant_id))).all()

    def _client_cases(self, db: Session, *, tenant_id: UUID | str, client_id: UUID | str) -> list[dbm.Case]:
        return db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == _tenant(tenant_id), dbm.Case.client_id == str(client_id), dbm.Case.deleted_at.is_(None))).all()

    def _client_documents(self, db: Session, *, tenant_id: UUID | str, client_id: UUID | str) -> list[dbm.Document]:
        return db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == _tenant(tenant_id), dbm.Document.client_id == str(client_id), dbm.Document.deleted_at.is_(None))).all()

    def _client_communications(self, db: Session, *, tenant_id: UUID | str, client_id: UUID | str) -> list[dbm.CommunicationMessage]:
        return db.scalars(select(dbm.CommunicationMessage).where(dbm.CommunicationMessage.tenant_id == _tenant(tenant_id), dbm.CommunicationMessage.client_id == str(client_id))).all()

    def _client_updates(self, db: Session, *, tenant_id: UUID | str, case_ids: list[str]) -> list[dbm.JudicialUpdate]:
        return db.scalars(select(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == _tenant(tenant_id), dbm.JudicialUpdate.case_id.in_(case_ids))).all() if case_ids else []

    def _client_hearings(self, db: Session, *, tenant_id: UUID | str, case_ids: list[str]) -> list[dbm.Hearing]:
        return db.scalars(select(dbm.Hearing).where(dbm.Hearing.tenant_id == _tenant(tenant_id), dbm.Hearing.case_id.in_(case_ids), dbm.Hearing.deleted_at.is_(None))).all() if case_ids else []

    @staticmethod
    def _matches_client(client: dbm.Client, needle: str) -> bool:
        return not needle or _contains(client.name, needle) or _contains(client.contact_email, needle) or _contains(client.tags, needle) or _contains(client.risk_profile, needle)

    @staticmethod
    def _matches_case(legal_case: dbm.Case, needle: str) -> bool:
        return not needle or _contains(legal_case.title, needle) or _contains(legal_case.external_case_number, needle) or _contains(legal_case.description, needle) or _contains(legal_case.status, needle)

    @staticmethod
    def _matches_document(document: dbm.Document, needle: str) -> bool:
        return not needle or _contains(document.filename, needle) or _contains(document.classification, needle) or _contains(document.content_type, needle) or _contains(document.status, needle)

    @staticmethod
    def _matches_hearing(hearing: dbm.Hearing, needle: str) -> bool:
        return not needle or _contains(hearing.title, needle) or _contains(hearing.location, needle) or _contains(hearing.status, needle)

    @staticmethod
    def _matches_update(update: dbm.JudicialUpdate, needle: str) -> bool:
        return not needle or _contains(update.title, needle) or _contains(update.summary, needle) or _contains(update.status, needle) or _contains(update.raw_payload, needle)


operational_core_service = OperationalCoreService()
