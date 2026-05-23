from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import User


AI_REVIEW_DISCLAIMER = "Requiere revisión profesional."


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _document_text(document: dbm.Document) -> str:
    return (
        f"Documento {document.filename}. Clasificacion previa {document.classification or 'sin clasificar'}. "
        f"Expediente {document.case_id}. Cliente {document.client_id}. Contiene fecha 2026-05-28, parte Nova Capital, "
        "plazo de 5 dias y obligacion de presentar anexos."
    )


class OCRProvider(Protocol):
    def extract_text(self, *, document: dbm.Document) -> str:
        ...


class MockOCRProvider:
    def extract_text(self, *, document: dbm.Document) -> str:
        return _document_text(document)


class FutureCloudOCRProvider:
    def extract_text(self, *, document: dbm.Document) -> str:
        return _document_text(document)


class LLMProvider(Protocol):
    def complete(self, *, prompt_name: str, text: str, context: dict[str, object] | None = None) -> dict[str, object]:
        ...


class MockLLMProvider:
    def complete(self, *, prompt_name: str, text: str, context: dict[str, object] | None = None) -> dict[str, object]:
        if prompt_name == "summarize_document":
            return {"summary": f"Resumen operativo de {context.get('filename') if context else 'documento'}: documento revisado y puntos relevantes identificados."}
        if prompt_name == "classify_document":
            return {"classification": "evidence", "confidence": 0.86}
        if prompt_name == "extract_dates":
            return {"dates": [{"label": "audiencia", "value": "2026-05-28"}]}
        if prompt_name == "extract_parties":
            return {"parties": ["Nova Capital", "Equipo legal"]}
        if prompt_name == "extract_deadlines":
            return {"deadlines": [{"label": "presentar anexos", "days": 5}]}
        if prompt_name == "extract_obligations":
            return {"obligations": ["Presentar anexos", "Revisar poder faltante"]}
        if prompt_name == "case_summary":
            return {"summary": "Resumen de expediente con estado, documentos, audiencias, comunicaciones y proximos pasos visibles para revision profesional."}
        if prompt_name == "smart_search":
            return {"answer": "Resultados relevantes encontrados en documentos, timeline y comunicaciones."}
        return {"draft": "Borrador asistido preparado para revision profesional."}


class OpenAILLMProvider:
    def complete(self, *, prompt_name: str, text: str, context: dict[str, object] | None = None) -> dict[str, object]:
        return MockLLMProvider().complete(prompt_name=prompt_name, text=text, context=context)


class AIUsageAuditService:
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


class AIJobService:
    def __init__(self, *, audit_service: AIUsageAuditService) -> None:
        self.audit_service = audit_service

    def create_completed_job(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor_user_id: UUID | str | None,
        job_type: str,
        result: dict[str, object],
        case_id: UUID | str | None = None,
        document_id: UUID | str | None = None,
        input_ref: str | None = None,
        request_id: str | None = None,
    ) -> dbm.AiJob:
        job = dbm.AiJob(
            tenant_id=str(tenant_id),
            case_id=str(case_id) if case_id else None,
            document_id=str(document_id) if document_id else None,
            job_type=job_type,
            status="pending_review",
            input_ref=input_ref,
            output_ref=f"ai-job:{job_type}",
            result_json={**result, "disclaimer": AI_REVIEW_DISCLAIMER},
            completed_at=dbm.now_utc(),
        )
        db.add(job)
        db.flush()
        self.audit_service.record(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="ai_job_created",
            entity_type="ai_job",
            entity_id=job.id,
            request_id=request_id,
            metadata={"job_type": job_type, "case_id": str(case_id) if case_id else None, "document_id": str(document_id) if document_id else None},
        )
        db.commit()
        db.refresh(job)
        return job

    def get(self, db: Session, *, tenant_id: UUID | str, job_id: UUID | str) -> dbm.AiJob:
        job = db.scalars(select(dbm.AiJob).where(dbm.AiJob.tenant_id == str(tenant_id), dbm.AiJob.id == str(job_id))).first()
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI job not found")
        return job

    def decide(self, db: Session, *, tenant_id: UUID | str, job_id: UUID | str, actor: User, decision: str, note: str | None = None, request_id: str | None = None) -> dbm.AiJob:
        job = self.get(db, tenant_id=tenant_id, job_id=job_id)
        if job.status not in {"pending_review", "completed"}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="AI job is not reviewable")
        job.status = "approved" if decision == "approve" else "rejected"
        job.reviewed_by_user_id = str(actor.id)
        job.review_note = note
        self.audit_service.record(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor.id,
            action=f"ai_job_{job.status}",
            entity_type="ai_job",
            entity_id=job.id,
            request_id=request_id,
            metadata={"job_type": job.job_type},
        )
        db.commit()
        db.refresh(job)
        return job


class OCRService:
    def __init__(self, *, provider: OCRProvider, job_service: AIJobService) -> None:
        self.provider = provider
        self.job_service = job_service

    def run(self, db: Session, *, tenant_id: UUID | str, document: dbm.Document, actor_user_id: UUID | str, request_id: str | None = None) -> dbm.AiJob:
        text = self.provider.extract_text(document=document)
        return self.job_service.create_completed_job(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            job_type="ocr",
            document_id=document.id,
            case_id=document.case_id,
            input_ref=document.storage_key,
            result={"text": text, "provider": "mock_ocr"},
            request_id=request_id,
        )


class DocumentAnalysisService:
    def __init__(self, *, llm_provider: LLMProvider, job_service: AIJobService, ocr_provider: OCRProvider) -> None:
        self.llm_provider = llm_provider
        self.job_service = job_service
        self.ocr_provider = ocr_provider

    def analyze(self, db: Session, *, tenant_id: UUID | str, document: dbm.Document, actor_user_id: UUID | str, operation: str, request_id: str | None = None) -> dbm.AiJob:
        text = self.ocr_provider.extract_text(document=document)
        prompt_name = {
            "summarize": "summarize_document",
            "classify": "classify_document",
            "extract": "extract_dates",
        }[operation]
        result = self.llm_provider.complete(prompt_name=prompt_name, text=text, context={"filename": document.filename})
        if operation == "extract":
            result.update(self.llm_provider.complete(prompt_name="extract_parties", text=text))
            result.update(self.llm_provider.complete(prompt_name="extract_deadlines", text=text))
            result.update(self.llm_provider.complete(prompt_name="extract_obligations", text=text))
        return self.job_service.create_completed_job(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            job_type=f"document_{operation}",
            document_id=document.id,
            case_id=document.case_id,
            input_ref=document.storage_key,
            result={"prompt": prompt_name, **result},
            request_id=request_id,
        )


class CaseSummaryService:
    def __init__(self, *, llm_provider: LLMProvider, job_service: AIJobService) -> None:
        self.llm_provider = llm_provider
        self.job_service = job_service

    def summarize(self, db: Session, *, tenant_id: UUID | str, legal_case: dbm.Case, actor_user_id: UUID | str, request_id: str | None = None) -> dbm.AiJob:
        documents = db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == str(tenant_id), dbm.Document.case_id == legal_case.id, dbm.Document.deleted_at.is_(None))).all()
        events = db.scalars(select(dbm.CaseEvent).where(dbm.CaseEvent.tenant_id == str(tenant_id), dbm.CaseEvent.case_id == legal_case.id)).all()
        text = f"Caso {legal_case.title}. Documentos {len(documents)}. Eventos {len(events)}. Estado {legal_case.status}."
        result = self.llm_provider.complete(prompt_name="case_summary", text=text, context={"case_title": legal_case.title})
        result["inputs"] = {"documents": len(documents), "events": len(events)}
        return self.job_service.create_completed_job(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            job_type="case_summary",
            case_id=legal_case.id,
            input_ref=f"case:{legal_case.id}",
            result=result,
            request_id=request_id,
        )

    def search(self, db: Session, *, tenant_id: UUID | str, legal_case: dbm.Case, actor_user_id: UUID | str, query: str, request_id: str | None = None) -> dbm.AiJob:
        like = f"%{query.lower()}%"
        documents = db.scalars(
            select(dbm.Document).where(
                dbm.Document.tenant_id == str(tenant_id),
                dbm.Document.case_id == legal_case.id,
                dbm.Document.deleted_at.is_(None),
                or_(dbm.Document.filename.ilike(like), dbm.Document.classification.ilike(like)),
            )
        ).all()
        events = db.scalars(
            select(dbm.CaseEvent).where(
                dbm.CaseEvent.tenant_id == str(tenant_id),
                dbm.CaseEvent.case_id == legal_case.id,
                or_(dbm.CaseEvent.title.ilike(like), dbm.CaseEvent.description.ilike(like)),
            )
        ).all()
        result = self.llm_provider.complete(prompt_name="smart_search", text=query, context={"case_title": legal_case.title})
        result["query"] = query
        result["matches"] = {
            "documents": [{"id": item.id, "filename": item.filename} for item in documents],
            "events": [{"id": item.id, "title": item.title} for item in events],
        }
        return self.job_service.create_completed_job(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            job_type="case_search",
            case_id=legal_case.id,
            input_ref=f"case:{legal_case.id}:search",
            result=result,
            request_id=request_id,
        )


class AIService:
    def __init__(self, *, ocr_service: OCRService, document_service: DocumentAnalysisService, case_service: CaseSummaryService, job_service: AIJobService) -> None:
        self.ocr_service = ocr_service
        self.document_service = document_service
        self.case_service = case_service
        self.job_service = job_service

    def document_or_404(self, db: Session, *, tenant_id: UUID | str, document_id: UUID | str) -> dbm.Document:
        document = db.scalars(
            select(dbm.Document).where(dbm.Document.tenant_id == str(tenant_id), dbm.Document.id == str(document_id), dbm.Document.deleted_at.is_(None))
        ).first()
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    def case_or_404(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> dbm.Case:
        legal_case = db.scalars(
            select(dbm.Case).where(dbm.Case.tenant_id == str(tenant_id), dbm.Case.id == str(case_id), dbm.Case.deleted_at.is_(None))
        ).first()
        if not legal_case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        return legal_case

    def serialize_job(self, job: dbm.AiJob) -> dict[str, object]:
        return {
            "id": job.id,
            "tenant_id": job.tenant_id,
            "case_id": job.case_id,
            "document_id": job.document_id,
            "job_type": job.job_type,
            "status": job.status,
            "input_ref": job.input_ref,
            "output_ref": job.output_ref,
            "result": job.result_json,
            "error_message": job.error_message,
            "completed_at": _iso(job.completed_at),
            "reviewed_by_user_id": job.reviewed_by_user_id,
            "review_note": job.review_note,
        }


ai_usage_audit_service = AIUsageAuditService()
ai_job_service = AIJobService(audit_service=ai_usage_audit_service)
mock_ocr_provider = MockOCRProvider()
mock_llm_provider = MockLLMProvider()
ocr_service = OCRService(provider=mock_ocr_provider, job_service=ai_job_service)
document_analysis_service = DocumentAnalysisService(llm_provider=mock_llm_provider, job_service=ai_job_service, ocr_provider=mock_ocr_provider)
case_summary_service = CaseSummaryService(llm_provider=mock_llm_provider, job_service=ai_job_service)
ai_service = AIService(
    ocr_service=ocr_service,
    document_service=document_analysis_service,
    case_service=case_summary_service,
    job_service=ai_job_service,
)
