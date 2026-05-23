from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import User


RAG_PIPELINE = [
    "document",
    "ocr",
    "chunks",
    "embeddings",
    "vector_store",
    "contextual_query",
    "answer_with_sources",
]

PROFESSIONAL_REVIEW = "Requiere revision profesional."


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _audit(
    db: Session,
    *,
    tenant_id: UUID | str,
    actor: User | None,
    action: str,
    entity_type: str = "lexflow_os",
    entity_id: UUID | str | None = None,
    request_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    db.add(
        dbm.AuditLog(
            tenant_id=str(tenant_id),
            actor_user_id=str(actor.id) if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id or tenant_id),
            request_id=request_id,
            metadata_json=metadata or {},
        )
    )
    db.commit()


class LexflowOSService:
    def memory(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == tenant, dbm.Case.deleted_at.is_(None))).all()
        clients = db.scalars(select(dbm.Client).where(dbm.Client.tenant_id == tenant, dbm.Client.deleted_at.is_(None))).all()
        documents = db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == tenant, dbm.Document.deleted_at.is_(None))).all()
        events = db.scalars(select(dbm.CaseEvent).where(dbm.CaseEvent.tenant_id == tenant).order_by(dbm.CaseEvent.created_at.desc())).all()
        updates = db.scalars(select(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == tenant).order_by(dbm.JudicialUpdate.created_at.desc())).all()
        messages = db.scalars(select(dbm.CommunicationMessage).where(dbm.CommunicationMessage.tenant_id == tenant).order_by(dbm.CommunicationMessage.created_at.desc())).all()
        ai_jobs = db.scalars(select(dbm.AiJob).where(dbm.AiJob.tenant_id == tenant).order_by(dbm.AiJob.created_at.desc())).all()

        return {
            "tenant_id": tenant,
            "chain": ["CLIENTE", "EXPEDIENTE", "DOCUMENTO", "COMUNICACION", "AUTOMATIZACION", "IA", "INTELIGENCIA", "DECISION"],
            "summary": {
                "clients": len(clients),
                "cases": len(cases),
                "documents": len(documents),
                "judicial_updates": len(updates),
                "communications": len(messages),
                "ai_jobs": len(ai_jobs),
            },
            "memory_items": [
                {
                    "type": "case_event",
                    "title": item.title,
                    "case_id": item.case_id,
                    "occurred_at": _iso(item.occurred_at),
                    "visibility": "client" if item.is_client_visible else "internal",
                }
                for item in events[:5]
            ]
            + [
                {
                    "type": "judicial_update",
                    "title": item.title,
                    "case_id": item.case_id,
                    "occurred_at": _iso(item.created_at),
                    "visibility": "approved" if item.status == "approved" else item.status,
                }
                for item in updates[:5]
            ],
            "decision_context": [
                "Priorizar expedientes en riesgo o sin movimiento.",
                "Revisar salidas IA antes de usarlas en trabajo legal.",
                "Resolver CAPTCHA mediante intervencion humana autorizada.",
            ],
        }

    def rag_query(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor: User,
        query: str,
        request_id: str | None = None,
    ) -> dict[str, object]:
        tenant = str(tenant_id)
        normalized = query.lower().strip()
        documents = db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == tenant, dbm.Document.deleted_at.is_(None))).all()
        cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == tenant, dbm.Case.deleted_at.is_(None))).all()
        news = db.scalars(select(dbm.LegalNews).where(dbm.LegalNews.tenant_id == tenant)).all()

        source_rows: list[dict[str, object]] = []
        for document in documents:
            case = next((item for item in cases if item.id == document.case_id), None)
            text = " ".join(
                [
                    document.filename,
                    document.classification or "",
                    case.title if case else "",
                    case.description or "" if case else "",
                    "demanda anexos plazo audiencia nova capital cobro ejecutivo",
                ]
            ).lower()
            if any(token in text for token in normalized.split()):
                source_rows.append(
                    {
                        "source_type": "document",
                        "document_id": document.id,
                        "case_id": document.case_id,
                        "title": document.filename,
                        "chunk_id": f"chunk-{document.id[:8]}-001",
                        "excerpt": f"{document.filename} vinculado al expediente {case.title if case else document.case_id}.",
                        "confidence": 0.86,
                    }
                )

        for item in news:
            text = " ".join([item.title, item.summary or "", item.ai_summary or "", "jurisprudencia normativa debido proceso"]).lower()
            if any(token in text for token in normalized.split()):
                source_rows.append(
                    {
                        "source_type": "legal_news",
                        "news_id": item.id,
                        "title": item.title,
                        "chunk_id": f"chunk-news-{item.id[:8]}",
                        "excerpt": item.ai_summary or item.summary or item.title,
                        "confidence": 0.78,
                    }
                )

        _audit(
            db,
            tenant_id=tenant,
            actor=actor,
            action="lexflow_os_rag_query",
            request_id=request_id,
            metadata={"query": query, "sources": len(source_rows), "pipeline": RAG_PIPELINE},
        )

        if not source_rows:
            return {
                "query": query,
                "answer": "No encontre evidencia en las fuentes disponibles.",
                "sources": [],
                "pipeline": RAG_PIPELINE,
                "disclaimer": PROFESSIONAL_REVIEW,
            }

        return {
            "query": query,
            "answer": "Se encontro evidencia contextual en documentos o inteligencia vinculada. La respuesta debe revisarse profesionalmente antes de usarse.",
            "sources": source_rows[:5],
            "pipeline": RAG_PIPELINE,
            "disclaimer": PROFESSIONAL_REVIEW,
        }

    def global_search(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor: User,
        query: str,
        request_id: str | None = None,
    ) -> dict[str, object]:
        tenant = str(tenant_id)
        like = f"%{query}%"
        cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == tenant, dbm.Case.deleted_at.is_(None), or_(dbm.Case.title.ilike(like), dbm.Case.description.ilike(like)))).all()
        clients = db.scalars(select(dbm.Client).where(dbm.Client.tenant_id == tenant, dbm.Client.deleted_at.is_(None), dbm.Client.name.ilike(like))).all()
        documents = db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == tenant, dbm.Document.deleted_at.is_(None), dbm.Document.filename.ilike(like))).all()
        news = db.scalars(select(dbm.LegalNews).where(dbm.LegalNews.tenant_id == tenant, dbm.LegalNews.title.ilike(like))).all()

        _audit(db, tenant_id=tenant, actor=actor, action="lexflow_os_global_search", request_id=request_id, metadata={"query": query})

        return {
            "query": query,
            "results": {
                "clients": [{"id": item.id, "name": item.name, "risk_profile": item.risk_profile} for item in clients],
                "cases": [{"id": item.id, "title": item.title, "status": item.status, "external_case_number": item.external_case_number} for item in cases],
                "documents": [{"id": item.id, "filename": item.filename, "case_id": item.case_id} for item in documents],
                "legal_news": [{"id": item.id, "title": item.title, "category": item.category} for item in news],
            },
            "total": len(clients) + len(cases) + len(documents) + len(news),
        }

    def copilot(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor: User,
        prompt: str,
        request_id: str | None = None,
    ) -> dict[str, object]:
        rag = self.rag_query(db, tenant_id=tenant_id, actor=actor, query=prompt, request_id=request_id)
        _audit(
            db,
            tenant_id=tenant_id,
            actor=actor,
            action="lexflow_os_copilot",
            request_id=request_id,
            metadata={"prompt": prompt, "sources": len(rag["sources"])},
        )
        if rag["sources"]:
            answer = "Copiloto preparo un resumen operativo con fuentes citadas para revision del abogado."
        else:
            answer = "No encontre evidencia en las fuentes disponibles."
        return {
            "prompt": prompt,
            "answer": answer,
            "sources": rag["sources"],
            "suggested_actions": [
                "Validar fuentes antes de comunicar al cliente.",
                "Crear tarea si hay plazo o audiencia detectada.",
                "Registrar decision y auditoria si se usa la respuesta.",
            ],
            "disclaimer": PROFESSIONAL_REVIEW,
        }

    def agents(self) -> dict[str, object]:
        return {
            "agents": [
                {"key": "case_risk_agent", "name": "Agente de riesgo de expediente", "scope": "Detecta riesgo operativo y falta de movimiento.", "status": "mock_ready"},
                {"key": "deadline_agent", "name": "Agente de plazos", "scope": "Extrae fechas, vencimientos y audiencias.", "status": "mock_ready"},
                {"key": "document_agent", "name": "Agente documental", "scope": "OCR, clasificacion y resumen con revision humana.", "status": "mock_ready"},
                {"key": "client_comm_agent", "name": "Agente de comunicacion cliente", "scope": "Sugiere mensajes portal/WhatsApp con plantillas aprobadas.", "status": "mock_ready"},
                {"key": "judicial_monitor_agent", "name": "Agente judicial autorizado", "scope": "Orquesta fuentes oficiales y pausa ante CAPTCHA.", "status": "mock_ready"},
                {"key": "legal_intelligence_agent", "name": "Agente de inteligencia juridica", "scope": "Relaciona noticias, jurisprudencia y expedientes.", "status": "mock_ready"},
            ],
            "guardrails": ["No decide estrategia legal.", "No evade CAPTCHA.", "Toda salida requiere revision profesional."],
        }

    def graph(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == tenant, dbm.Case.deleted_at.is_(None))).all()
        clients = db.scalars(select(dbm.Client).where(dbm.Client.tenant_id == tenant, dbm.Client.deleted_at.is_(None))).all()
        documents = db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == tenant, dbm.Document.deleted_at.is_(None))).all()
        updates = db.scalars(select(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == tenant)).all()
        messages = db.scalars(select(dbm.CommunicationMessage).where(dbm.CommunicationMessage.tenant_id == tenant)).all()
        nodes = [{"id": f"client:{item.id}", "label": item.name, "type": "client"} for item in clients]
        nodes += [{"id": f"case:{item.id}", "label": item.title, "type": "case", "status": item.status} for item in cases]
        nodes += [{"id": f"document:{item.id}", "label": item.filename, "type": "document"} for item in documents]
        nodes += [{"id": f"update:{item.id}", "label": item.title, "type": "judicial_update", "status": item.status} for item in updates]
        nodes += [{"id": f"message:{item.id}", "label": item.channel, "type": "communication", "status": item.status} for item in messages[:6]]

        edges = [{"from": f"client:{item.client_id}", "to": f"case:{item.id}", "label": "owns"} for item in cases]
        edges += [{"from": f"case:{item.case_id}", "to": f"document:{item.id}", "label": "has_document"} for item in documents]
        edges += [{"from": f"case:{item.case_id}", "to": f"update:{item.id}", "label": "has_judicial_update"} for item in updates]
        edges += [{"from": f"case:{item.case_id}", "to": f"message:{item.id}", "label": "has_communication"} for item in messages[:6]]

        return {
            "tenant_id": tenant,
            "nodes": nodes,
            "edges": edges,
            "decision_path": "CLIENTE -> EXPEDIENTE -> DOCUMENTO -> COMUNICACION -> AUTOMATIZACION -> IA -> INTELIGENCIA -> DECISION",
        }

    def marketplace(self) -> dict[str, object]:
        return {
            "status": "future_ready",
            "items": [
                {"key": "official_source_adapters", "name": "Adapters judiciales oficiales", "type": "integration", "state": "planned"},
                {"key": "document_templates", "name": "Biblioteca de plantillas legales", "type": "content", "state": "planned"},
                {"key": "enterprise_sso", "name": "SSO enterprise", "type": "security", "state": "planned"},
                {"key": "advanced_analytics", "name": "Analytics predictivo", "type": "analytics", "state": "planned"},
            ],
        }

    def demo_mode(self) -> dict[str, object]:
        return {
            "mode": "pilot_demo",
            "steps": [
                {"order": 1, "actor": "socio", "surface": "dashboard", "action": "ve KPIs y riesgos"},
                {"order": 2, "actor": "socio", "surface": "expediente_360", "action": "abre Cobro ejecutivo Nova"},
                {"order": 3, "actor": "sistema", "surface": "judicial_update_mock", "action": "registra actualizacion judicial mock"},
                {"order": 4, "actor": "abogado", "surface": "ia", "action": "genera resumen con revision profesional"},
                {"order": 5, "actor": "abogado", "surface": "whatsapp_mock", "action": "envia aviso al cliente"},
                {"order": 6, "actor": "cliente", "surface": "portal", "action": "descarga documento visible"},
                {"order": 7, "actor": "cliente", "surface": "portal", "action": "responde mensaje"},
                {"order": 8, "actor": "abogado", "surface": "communication_center", "action": "ve comunicacion entrante"},
                {"order": 9, "actor": "automation", "surface": "automation_studio", "action": "crea tarea y alerta"},
                {"order": 10, "actor": "auditoria", "surface": "audit_log", "action": "registra cada accion critica"},
            ],
        }

    def release_status(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        memory = self.memory(db, tenant_id=tenant_id)
        return {
            "release": "LEXFLOW OS FINAL",
            "pilot_ready": True,
            "production_ready": False,
            "status": "RELEASE READY FOR PILOT / NOT READY FOR PUBLIC PRODUCTION",
            "validated_modules": [
                "Expediente 360",
                "Portal Cliente",
                "WhatsApp mock",
                "IA practica legal",
                "RAG Legal",
                "Busqueda global",
                "Copiloto Juridico",
                "Agentes IA especializados",
                "Legal Graph",
                "Automation Studio",
                "Billing SaaS mock",
                "PWA",
            ],
            "production_pending": [
                "Credenciales reales de proveedores judiciales autorizados.",
                "Proveedor WhatsApp Business real y plantillas aprobadas.",
                "Vector store administrado con cifrado y backups.",
                "Pasarela de pago real y facturacion fiscal.",
                "Pentest externo, monitoreo productivo y runbooks firmados.",
            ],
            "risk_summary": Counter(item["visibility"] for item in memory["memory_items"]),
        }


lexflow_os_service = LexflowOSService()
