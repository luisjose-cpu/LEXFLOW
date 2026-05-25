from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import RoleName, User
from app.services.level2 import financial_engine_service, risk_engine_service, war_room_service
from app.services.lexflow_os import PROFESSIONAL_REVIEW, RAG_PIPELINE, lexflow_os_service


def _now() -> datetime:
    return datetime.now(UTC)


def _audit(db: Session, *, tenant_id: UUID | str, actor: User, action: str, entity_type: str, entity_id: str, request_id: str | None = None, metadata: dict[str, object] | None = None) -> None:
    db.add(
        dbm.AuditLog(
            tenant_id=str(tenant_id),
            actor_user_id=str(actor.id),
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            request_id=request_id,
            metadata_json=metadata or {},
        )
    )


def _tokens(value: str) -> set[str]:
    return {token for token in "".join(char.lower() if char.isalnum() else " " for char in value).split() if len(token) > 2}


def _score_text(query: str, text: str) -> int:
    query_tokens = _tokens(query)
    if not query_tokens:
        return 0
    overlap = query_tokens.intersection(_tokens(text))
    return round((len(overlap) / len(query_tokens)) * 100)


def _embedding(text: str) -> list[float]:
    digest = sha256(text.encode("utf-8")).digest()
    return [round(byte / 255, 4) for byte in digest[:8]]


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class DigitalTwinService:
    def dashboard(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        war_room = war_room_service.dashboard(db, tenant_id=tenant_id, mode="partner")
        risk = risk_engine_service.dashboard(db, tenant_id=tenant_id)
        financial = financial_engine_service.overview(db, tenant_id=tenant_id)
        cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == tenant, dbm.Case.deleted_at.is_(None))).all()
        documents = db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == tenant, dbm.Document.deleted_at.is_(None))).all()
        messages = db.scalars(select(dbm.CommunicationMessage).where(dbm.CommunicationMessage.tenant_id == tenant)).all()
        automations = db.scalars(select(dbm.AutomationRun).where(dbm.AutomationRun.tenant_id == tenant)).all()
        users = db.scalars(select(dbm.User).where(dbm.User.tenant_id == tenant, dbm.User.deleted_at.is_(None))).all()
        clients = db.scalars(select(dbm.Client).where(dbm.Client.tenant_id == tenant, dbm.Client.deleted_at.is_(None))).all()
        task_load = Counter(task.assigned_user_id or "unassigned" for task in db.scalars(select(dbm.Task).where(dbm.Task.tenant_id == tenant, dbm.Task.deleted_at.is_(None), dbm.Task.status != "done")).all())
        complexity = []
        for legal_case in cases:
            risk_row = next((item for item in risk["cases"] if item["case_id"] == legal_case.id), {"score": 20, "factors": []})
            doc_count = len([item for item in documents if item.case_id == legal_case.id])
            msg_count = len([item for item in messages if item.case_id == legal_case.id])
            complexity.append(
                {
                    "case_id": legal_case.id,
                    "title": legal_case.title,
                    "score": min(100, int(risk_row["score"]) + doc_count * 4 + msg_count * 2),
                    "drivers": [factor["key"] for factor in risk_row.get("factors", [])] + ["documents", "communications"],
                }
            )
        return {
            "generated_at": _now().isoformat(),
            "study_health": war_room["study_health"],
            "operational_map": {
                "clients": len(clients),
                "cases": len(cases),
                "documents": len(documents),
                "communications": len(messages),
                "automation_runs": len(automations),
            },
            "lawyer_load": [
                {
                    "user_id": user.id,
                    "name": user.full_name,
                    "open_tasks": task_load.get(user.id, 0),
                    "load_score": min(100, task_load.get(user.id, 0) * 18),
                    "status": "saturated" if task_load.get(user.id, 0) >= 5 else "balanced",
                }
                for user in users
            ],
            "case_complexity": sorted(complexity, key=lambda item: item["score"], reverse=True),
            "risk_propagation": risk["critical_cases"][:5],
            "simulation": {
                "question": "Que podria pasar si no se atienden los riesgos?",
                "projection": "Aumentarian plazos vencidos, carga de abogados y alertas de cliente sin respuesta.",
                "recommended_controls": ["resolver CAPTCHA pendientes", "revisar IA pendiente", "reasignar tareas saturadas"],
            },
            "financial_signal": financial["summary"],
        }


class KnowledgeVaultService:
    def create_item(self, db: Session, *, tenant_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        item = dbm.KnowledgeVaultItem(
            tenant_id=str(tenant_id),
            source_type=str(payload.get("source_type") or "template"),
            category=str(payload.get("category") or "knowledge"),
            title=str(payload.get("title") or "Nuevo item"),
            content_summary=str(payload.get("content_summary") or ""),
            tags=list(payload.get("tags") or []),
            visibility=str(payload.get("visibility") or "internal"),
            case_id=payload.get("case_id"),
            client_id=payload.get("client_id"),
            document_id=payload.get("document_id"),
            created_by_user_id=str(actor.id),
            metadata_json={"level": "N3"},
        )
        db.add(item)
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="knowledge.item_created", entity_type="knowledge_vault_item", entity_id=item.id, request_id=request_id)
        db.commit()
        return self._serialize(item)

    def search(self, db: Session, *, tenant_id: UUID | str, query: str, source_type: str | None = None) -> dict[str, object]:
        filters = [dbm.KnowledgeVaultItem.tenant_id == str(tenant_id), dbm.KnowledgeVaultItem.deleted_at.is_(None)]
        if source_type:
            filters.append(dbm.KnowledgeVaultItem.source_type == source_type)
        items = db.scalars(select(dbm.KnowledgeVaultItem).where(*filters).order_by(dbm.KnowledgeVaultItem.created_at.desc())).all()
        if not query.strip():
            return {"query": query, "results": [self._serialize(item) for item in items], "total": len(items)}
        results = []
        for item in items:
            score = _score_text(query, f"{item.title} {item.content_summary} {' '.join(item.tags)}")
            if score:
                row = self._serialize(item)
                row["similarity"] = score
                results.append(row)
        return {"query": query, "results": sorted(results, key=lambda item: item["similarity"], reverse=True), "total": len(results)}

    def list_by_type(self, db: Session, *, tenant_id: UUID | str, source_type: str) -> list[dict[str, object]]:
        items = db.scalars(select(dbm.KnowledgeVaultItem).where(dbm.KnowledgeVaultItem.tenant_id == str(tenant_id), dbm.KnowledgeVaultItem.source_type == source_type, dbm.KnowledgeVaultItem.deleted_at.is_(None)).order_by(dbm.KnowledgeVaultItem.created_at.desc())).all()
        return [self._serialize(item) for item in items]

    def _serialize(self, item: dbm.KnowledgeVaultItem) -> dict[str, object]:
        return {
            "id": item.id,
            "source_type": item.source_type,
            "category": item.category,
            "title": item.title,
            "content_summary": item.content_summary,
            "tags": item.tags,
            "visibility": item.visibility,
            "case_id": item.case_id,
            "client_id": item.client_id,
            "document_id": item.document_id,
            "created_at": item.created_at.isoformat(),
        }


class LegalMemoryService:
    def index_tenant(self, db: Session, *, tenant_id: UUID | str, actor: User, request_id: str | None = None) -> dict[str, object]:
        tenant = str(tenant_id)
        created = 0
        documents = db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == tenant, dbm.Document.deleted_at.is_(None))).all()
        for document in documents:
            case = db.scalar(select(dbm.Case).where(dbm.Case.id == document.case_id, dbm.Case.tenant_id == tenant))
            text = f"{document.filename} {document.classification or ''} {case.title if case else ''} {case.description if case else ''}"
            created += self._upsert(db, tenant_id=tenant, entity_type="document", entity_id=document.id, case_id=document.case_id, client_id=document.client_id, source_type="document", title=document.filename, content=text, tags=["document", document.classification or "uploaded"])
        events = db.scalars(select(dbm.CaseEvent).where(dbm.CaseEvent.tenant_id == tenant)).all()
        for event in events:
            case = db.scalar(select(dbm.Case).where(dbm.Case.id == event.case_id, dbm.Case.tenant_id == tenant))
            created += self._upsert(db, tenant_id=tenant, entity_type="case_event", entity_id=event.id, case_id=event.case_id, client_id=case.client_id if case else None, source_type="timeline", title=event.title, content=f"{event.title} {event.description or ''}", tags=["timeline", event.event_type])
        messages = db.scalars(select(dbm.CommunicationMessage).where(dbm.CommunicationMessage.tenant_id == tenant)).all()
        for message in messages:
            created += self._upsert(db, tenant_id=tenant, entity_type="communication", entity_id=message.id, case_id=message.case_id, client_id=message.client_id, source_type="communication", title=f"Mensaje {message.channel}", content=message.body, tags=["communication", message.channel])
        _audit(db, tenant_id=tenant, actor=actor, action="memory.indexed", entity_type="legal_memory", entity_id=tenant, request_id=request_id, metadata={"created": created})
        db.commit()
        return {"tenant_id": tenant, "created": created, "status": "indexed"}

    def search(self, db: Session, *, tenant_id: UUID | str, query: str) -> dict[str, object]:
        items = db.scalars(select(dbm.LegalMemoryItem).where(dbm.LegalMemoryItem.tenant_id == str(tenant_id), dbm.LegalMemoryItem.deleted_at.is_(None), dbm.LegalMemoryItem.index_status == "indexed")).all()
        results = []
        for item in items:
            score = _score_text(query, f"{item.title} {item.chunk_text} {' '.join(item.tags)}")
            if score:
                results.append(self._serialize(item, score=score))
        return {"query": query, "results": sorted(results, key=lambda item: item["score"], reverse=True), "total": len(results)}

    def _upsert(self, db: Session, *, tenant_id: str, entity_type: str, entity_id: str, case_id: str | None, client_id: str | None, source_type: str, title: str, content: str, tags: list[str]) -> int:
        existing = db.scalar(select(dbm.LegalMemoryItem).where(dbm.LegalMemoryItem.tenant_id == tenant_id, dbm.LegalMemoryItem.source_type == source_type, dbm.LegalMemoryItem.entity_type == entity_type, dbm.LegalMemoryItem.entity_id == entity_id))
        if existing:
            return 0
        chunk = content[:1200]
        db.add(
            dbm.LegalMemoryItem(
                tenant_id=tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                case_id=case_id,
                client_id=client_id,
                source_type=source_type,
                title=title,
                content=content,
                chunk_text=chunk,
                tags=tags,
                embedding_vector_json=_embedding(chunk),
                citations_json=[{"source_type": source_type, "entity_type": entity_type, "entity_id": entity_id, "title": title}],
            )
        )
        return 1

    def _serialize(self, item: dbm.LegalMemoryItem, *, score: int | None = None) -> dict[str, object]:
        row: dict[str, object] = {
            "id": item.id,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "case_id": item.case_id,
            "client_id": item.client_id,
            "source_type": item.source_type,
            "title": item.title,
            "chunk_text": item.chunk_text,
            "tags": item.tags,
            "citations": item.citations_json,
            "index_status": item.index_status,
        }
        if score is not None:
            row["score"] = score
        return row


class LegalGraphService:
    def build(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        self._sync_core_graph(db, tenant_id=tenant)
        nodes = db.scalars(select(dbm.LegalGraphNode).where(dbm.LegalGraphNode.tenant_id == tenant, dbm.LegalGraphNode.deleted_at.is_(None))).all()
        edges = db.scalars(select(dbm.LegalGraphEdge).where(dbm.LegalGraphEdge.tenant_id == tenant)).all()
        return {
            "tenant_id": tenant,
            "nodes": [{"id": item.id, "type": item.node_type, "entity_id": item.entity_id, "label": item.label, "metadata": item.metadata_json} for item in nodes],
            "edges": [{"id": item.id, "from": item.from_node_id, "to": item.to_node_id, "relationship": item.edge_type, "weight": item.weight, "metadata": item.metadata_json} for item in edges],
        }

    def create_relationship(self, db: Session, *, tenant_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        tenant = str(tenant_id)
        from_node = self._node_or_404(db, tenant_id=tenant, node_id=str(payload["from_node_id"]))
        to_node = self._node_or_404(db, tenant_id=tenant, node_id=str(payload["to_node_id"]))
        edge = dbm.LegalGraphEdge(tenant_id=tenant, from_node_id=from_node.id, to_node_id=to_node.id, edge_type=str(payload.get("relationship") or "related"), weight=int(payload.get("weight") or 1), metadata_json=dict(payload.get("metadata") or {}))
        db.add(edge)
        db.flush()
        _audit(db, tenant_id=tenant, actor=actor, action="graph.relationship_created", entity_type="legal_graph_edge", entity_id=edge.id, request_id=request_id)
        db.commit()
        return {"id": edge.id, "from": edge.from_node_id, "to": edge.to_node_id, "relationship": edge.edge_type, "weight": edge.weight}

    def search(self, db: Session, *, tenant_id: UUID | str, query: str) -> dict[str, object]:
        like = f"%{query}%"
        nodes = db.scalars(select(dbm.LegalGraphNode).where(dbm.LegalGraphNode.tenant_id == str(tenant_id), dbm.LegalGraphNode.deleted_at.is_(None), or_(dbm.LegalGraphNode.label.ilike(like), dbm.LegalGraphNode.node_type.ilike(like)))).all()
        return {"query": query, "results": [{"id": item.id, "type": item.node_type, "entity_id": item.entity_id, "label": item.label} for item in nodes], "total": len(nodes)}

    def _sync_core_graph(self, db: Session, *, tenant_id: str) -> None:
        clients = db.scalars(select(dbm.Client).where(dbm.Client.tenant_id == tenant_id, dbm.Client.deleted_at.is_(None))).all()
        cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == tenant_id, dbm.Case.deleted_at.is_(None))).all()
        documents = db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == tenant_id, dbm.Document.deleted_at.is_(None))).all()
        node_ids: dict[tuple[str, str], str] = {}
        for node_type, rows in [("client", clients), ("case", cases), ("document", documents)]:
            for row in rows:
                label = row.name if node_type == "client" else row.title if node_type == "case" else row.filename
                node = self._ensure_node(db, tenant_id=tenant_id, node_type=node_type, entity_id=row.id, label=label, metadata={"status": getattr(row, "status", None)})
                node_ids[(node_type, row.id)] = node.id
        for legal_case in cases:
            self._ensure_edge(db, tenant_id=tenant_id, from_node_id=node_ids.get(("client", legal_case.client_id)), to_node_id=node_ids.get(("case", legal_case.id)), relationship="owns")
        for document in documents:
            self._ensure_edge(db, tenant_id=tenant_id, from_node_id=node_ids.get(("case", document.case_id)), to_node_id=node_ids.get(("document", document.id)), relationship="has_document")
        db.flush()

    def _ensure_node(self, db: Session, *, tenant_id: str, node_type: str, entity_id: str, label: str, metadata: dict[str, object]) -> dbm.LegalGraphNode:
        node = db.scalar(select(dbm.LegalGraphNode).where(dbm.LegalGraphNode.tenant_id == tenant_id, dbm.LegalGraphNode.node_type == node_type, dbm.LegalGraphNode.entity_id == entity_id))
        if node:
            node.label = label
            node.metadata_json = metadata
            return node
        node = dbm.LegalGraphNode(tenant_id=tenant_id, node_type=node_type, entity_id=entity_id, label=label, metadata_json=metadata)
        db.add(node)
        db.flush()
        return node

    def _ensure_edge(self, db: Session, *, tenant_id: str, from_node_id: str | None, to_node_id: str | None, relationship: str) -> None:
        if not from_node_id or not to_node_id:
            return
        edge = db.scalar(select(dbm.LegalGraphEdge).where(dbm.LegalGraphEdge.tenant_id == tenant_id, dbm.LegalGraphEdge.from_node_id == from_node_id, dbm.LegalGraphEdge.to_node_id == to_node_id, dbm.LegalGraphEdge.edge_type == relationship))
        if not edge:
            db.add(dbm.LegalGraphEdge(tenant_id=tenant_id, from_node_id=from_node_id, to_node_id=to_node_id, edge_type=relationship, weight=3))

    def _node_or_404(self, db: Session, *, tenant_id: str, node_id: str) -> dbm.LegalGraphNode:
        node = db.scalar(select(dbm.LegalGraphNode).where(dbm.LegalGraphNode.id == node_id, dbm.LegalGraphNode.tenant_id == tenant_id, dbm.LegalGraphNode.deleted_at.is_(None)))
        if not node:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Graph node not found")
        return node


class ContextEngine:
    def build(self, db: Session, *, tenant_id: UUID | str, query: str, case_id: UUID | str | None = None, client_id: UUID | str | None = None) -> dict[str, object]:
        tenant = str(tenant_id)
        memory_filters = [dbm.LegalMemoryItem.tenant_id == tenant, dbm.LegalMemoryItem.deleted_at.is_(None)]
        if case_id:
            memory_filters.append(dbm.LegalMemoryItem.case_id == str(case_id))
        if client_id:
            memory_filters.append(dbm.LegalMemoryItem.client_id == str(client_id))
        memory = db.scalars(select(dbm.LegalMemoryItem).where(*memory_filters).order_by(dbm.LegalMemoryItem.created_at.desc())).all()
        scored = [(item, _score_text(query, f"{item.title} {item.chunk_text}")) for item in memory]
        selected = [item for item, score in sorted(scored, key=lambda pair: pair[1], reverse=True) if score > 0][:6]
        if not selected:
            return lexflow_os_service.rag_query(db, tenant_id=tenant_id, actor=self._system_actor(db, tenant), query=query)
        return {
            "query": query,
            "context_window": [{"title": item.title, "chunk": item.chunk_text, "citations": item.citations_json} for item in selected],
            "sources": [citation for item in selected for citation in item.citations_json],
        }

    def _system_actor(self, db: Session, tenant_id: str) -> User:
        user = db.scalars(select(dbm.User).where(dbm.User.tenant_id == tenant_id, dbm.User.deleted_at.is_(None))).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant actor not found")
        role = db.scalar(select(dbm.Role).where(dbm.Role.id == user.role_id))
        return User(id=UUID(user.id), tenant_id=UUID(user.tenant_id), email=user.email, full_name=user.full_name, role=RoleName(role.name if role else "tenant_admin"), is_active=user.status == "active", hashed_password=user.hashed_password, mfa_enabled=user.mfa_enabled)


class RAGPipelineService:
    def query(self, db: Session, *, tenant_id: UUID | str, actor: User, query: str, case_id: UUID | str | None = None, client_id: UUID | str | None = None, request_id: str | None = None) -> dict[str, object]:
        context = context_engine.build(db, tenant_id=tenant_id, query=query, case_id=case_id, client_id=client_id)
        sources = context.get("sources", [])
        _audit(db, tenant_id=tenant_id, actor=actor, action="rag.context_query", entity_type="rag_pipeline", entity_id=str(tenant_id), request_id=request_id, metadata={"query": query, "sources": len(sources)})
        db.commit()
        if not sources:
            return {"query": query, "answer": "No encontre evidencia en las fuentes disponibles.", "sources": [], "pipeline": RAG_PIPELINE, "disclaimer": PROFESSIONAL_REVIEW}
        return {
            "query": query,
            "answer": "Se encontro contexto legal del tenant con fuentes citadas. La respuesta es explicativa y requiere revision profesional.",
            "sources": sources[:6],
            "context_window": context.get("context_window", []),
            "pipeline": RAG_PIPELINE,
            "disclaimer": PROFESSIONAL_REVIEW,
        }


class ManagementCopilotService:
    def ask(self, db: Session, *, tenant_id: UUID | str, actor: User, question: str, request_id: str | None = None) -> dict[str, object]:
        twin = digital_twin_service.dashboard(db, tenant_id=tenant_id)
        rag = rag_pipeline_service.query(db, tenant_id=tenant_id, actor=actor, query=question, request_id=request_id)
        overloaded = [item for item in twin["lawyer_load"] if item["status"] == "saturated"]
        critical = twin["risk_propagation"]
        insight = "El estudio esta operativamente estable, con focos que requieren seguimiento."
        if critical or overloaded:
            insight = "Hay riesgo operativo visible: priorizar casos criticos, carga saturada y revision de fuentes citadas."
        _audit(db, tenant_id=tenant_id, actor=actor, action="copilot.management_asked", entity_type="management_copilot", entity_id=str(tenant_id), request_id=request_id, metadata={"question": question})
        db.commit()
        return {
            "question": question,
            "insight": insight,
            "risk_context": critical[:3],
            "sources": rag["sources"],
            "recommendations": [
                "Revisar los expedientes con mayor propagacion de riesgo.",
                "Reasignar tareas si un abogado supera carga balanceada.",
                "Usar la respuesta como apoyo operativo, no como decision juridica automatica.",
            ],
            "disclaimer": PROFESSIONAL_REVIEW,
        }


class MarketplaceService:
    defaults = [
        ("sinoe_checkpoint_pack", "SINOE Human Checkpoint Pack", "integration", "Plantillas de intervencion humana y auditoria para CAPTCHA."),
        ("document_precedent_pack", "Precedent Template Pack", "template", "Plantillas, checklists y prompts para Knowledge Vault."),
        ("risk_warroom_widgets", "Risk War Room Widgets", "dashboard", "Widgets gerenciales de carga, riesgo y alertas."),
    ]

    def catalog(self, db: Session) -> dict[str, object]:
        self.ensure_defaults(db)
        items = db.scalars(select(dbm.MarketplaceItem).where(dbm.MarketplaceItem.deleted_at.is_(None)).order_by(dbm.MarketplaceItem.created_at.desc())).all()
        return {"items": [self._item(item) for item in items], "payments": "not_enabled", "permissions_model": "tenant_install_with_audit"}

    def install(self, db: Session, *, tenant_id: UUID | str, actor: User, item_id: UUID | str, request_id: str | None = None) -> dict[str, object]:
        item = db.scalar(select(dbm.MarketplaceItem).where(dbm.MarketplaceItem.id == str(item_id), dbm.MarketplaceItem.deleted_at.is_(None)))
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Marketplace item not found")
        installation = db.scalar(select(dbm.MarketplaceInstallation).where(dbm.MarketplaceInstallation.tenant_id == str(tenant_id), dbm.MarketplaceInstallation.marketplace_item_id == item.id))
        if not installation:
            installation = dbm.MarketplaceInstallation(tenant_id=str(tenant_id), marketplace_item_id=item.id, installed_by_user_id=str(actor.id), config_json={"review_required": True})
            db.add(installation)
        installation.status = "installed"
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="marketplace.item_installed", entity_type="marketplace_installation", entity_id=installation.id, request_id=request_id, metadata={"item_key": item.item_key})
        db.commit()
        return {"installation_id": installation.id, "item": self._item(item), "status": installation.status}

    def ensure_defaults(self, db: Session) -> None:
        for key, name, item_type, description in self.defaults:
            existing = db.scalar(select(dbm.MarketplaceItem).where(dbm.MarketplaceItem.item_key == key))
            if not existing:
                db.add(dbm.MarketplaceItem(item_key=key, name=name, item_type=item_type, description=description, permissions_json=["legal_os:read"], metadata_json={"level": "N3"}))
        db.commit()

    def _item(self, item: dbm.MarketplaceItem) -> dict[str, object]:
        return {"id": item.id, "item_key": item.item_key, "name": item.name, "item_type": item.item_type, "description": item.description, "permissions": item.permissions_json, "status": item.status}


class LatamReadyService:
    countries = [
        {"country_code": "PE", "name": "Peru", "currency": "PEN", "timezone": "America/Lima", "sources": ["SINOE", "Poder Judicial", "El Peruano"]},
        {"country_code": "CO", "name": "Colombia", "currency": "COP", "timezone": "America/Bogota", "sources": ["Rama Judicial", "SUIN"]},
        {"country_code": "MX", "name": "Mexico", "currency": "MXN", "timezone": "America/Mexico_City", "sources": ["CJF", "DOF"]},
        {"country_code": "CL", "name": "Chile", "currency": "CLP", "timezone": "America/Santiago", "sources": ["Poder Judicial", "Diario Oficial"]},
    ]

    def ensure_defaults(self, db: Session, *, tenant_id: UUID | str, actor: User, request_id: str | None = None) -> dict[str, object]:
        created = 0
        for country in self.countries:
            existing = db.scalar(select(dbm.CountryConfig).where(dbm.CountryConfig.tenant_id == str(tenant_id), dbm.CountryConfig.country_code == country["country_code"]))
            if not existing:
                db.add(
                    dbm.CountryConfig(
                        tenant_id=str(tenant_id),
                        country_code=country["country_code"],
                        name=country["name"],
                        currency=country["currency"],
                        timezone=country["timezone"],
                        legal_sources_json=[{"name": source, "status": "registry_ready"} for source in country["sources"]],
                        provider_registry_json=[{"key": source.lower().replace(" ", "_"), "status": "adapter_mock_ready"} for source in country["sources"]],
                    )
                )
                created += 1
        _audit(db, tenant_id=tenant_id, actor=actor, action="latam.defaults_created", entity_type="country_config", entity_id=str(tenant_id), request_id=request_id, metadata={"created": created})
        db.commit()
        return {"created": created, "configs": self.list_configs(db, tenant_id=tenant_id)}

    def list_configs(self, db: Session, *, tenant_id: UUID | str) -> list[dict[str, object]]:
        configs = db.scalars(select(dbm.CountryConfig).where(dbm.CountryConfig.tenant_id == str(tenant_id), dbm.CountryConfig.deleted_at.is_(None)).order_by(dbm.CountryConfig.country_code.asc())).all()
        return [{"id": item.id, "country_code": item.country_code, "name": item.name, "currency": item.currency, "timezone": item.timezone, "language": item.language, "legal_sources": item.legal_sources_json, "providers": item.provider_registry_json} for item in configs]


class AiAgentsFramework:
    catalog = [
        {"key": "case_agent", "name": "CaseAgent", "scope": "expediente, riesgo, timeline", "review_required": True},
        {"key": "document_agent", "name": "DocumentAgent", "scope": "documentos, OCR, clasificacion", "review_required": True},
        {"key": "hearing_agent", "name": "HearingAgent", "scope": "audiencias y plazos", "review_required": True},
        {"key": "client_agent", "name": "ClientAgent", "scope": "portal, comunicaciones, solicitudes", "review_required": True},
        {"key": "news_agent", "name": "NewsAgent", "scope": "noticias y jurisprudencia", "review_required": True},
        {"key": "management_agent", "name": "ManagementAgent", "scope": "insights gerenciales", "review_required": True},
        {"key": "automation_agent", "name": "AutomationAgent", "scope": "triggers, acciones, errores", "review_required": True},
    ]

    def list_catalog(self) -> dict[str, object]:
        return {"agents": self.catalog, "guardrails": ["output_json", "permissions", "audit", "review_required", "no_decision_automation"]}

    def run(self, db: Session, *, tenant_id: UUID | str, actor: User, agent_key: str, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        agent = next((item for item in self.catalog if item["key"] == agent_key), None)
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        output = {
            "agent_key": agent_key,
            "status": "completed",
            "finding": "Analisis contextual mock con permisos y auditoria aplicada.",
            "context_used": sorted(payload.keys()),
            "sources_required": True,
            "review_required": True,
            "disclaimer": PROFESSIONAL_REVIEW,
        }
        run = dbm.AiAgentRun(tenant_id=str(tenant_id), agent_key=agent_key, status="completed", input_json=payload, output_json=output, review_required=True, actor_user_id=str(actor.id))
        db.add(run)
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="agent.run_completed", entity_type="ai_agent_run", entity_id=run.id, request_id=request_id, metadata={"agent_key": agent_key})
        db.commit()
        return {"run_id": run.id, "output": output}


digital_twin_service = DigitalTwinService()
knowledge_vault_service = KnowledgeVaultService()
legal_memory_service = LegalMemoryService()
legal_graph_service = LegalGraphService()
context_engine = ContextEngine()
rag_pipeline_service = RAGPipelineService()
management_copilot_service = ManagementCopilotService()
marketplace_service = MarketplaceService()
latam_ready_service = LatamReadyService()
ai_agents_framework = AiAgentsFramework()
