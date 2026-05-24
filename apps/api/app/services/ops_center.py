from __future__ import annotations

from collections import Counter
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import deployment_revision, get_settings
from app.core.readiness import production_readiness_report
from app.db import models as dbm
from app.services.storage import storage_service


CLIENTS_CSV = "name,contact_email,risk_profile,tags\nAcme Legal,legal@acme.test,high,corporate;pilot\n"
CASES_CSV = "client_email,title,external_case_number,status,description\nlegal@acme.test,Cobro Acme,ACME-001,active,Expediente piloto\n"
DOCUMENTS_CSV = "case_external_case_number,filename,content_type,classification,is_client_visible\nACME-001,demanda-acme.pdf,application/pdf,pleading,true\n"


class OpsCenterService:
    def import_templates(self) -> dict[str, object]:
        return {
            "templates": [
                {"kind": "clients", "required": ["name"], "optional": ["contact_email", "risk_profile", "tags"], "csv": CLIENTS_CSV},
                {"kind": "cases", "required": ["client_email", "title"], "optional": ["external_case_number", "status", "description"], "csv": CASES_CSV},
                {"kind": "documents", "required": ["case_external_case_number", "filename"], "optional": ["content_type", "classification", "is_client_visible"], "csv": DOCUMENTS_CSV},
            ],
            "flow": ["bootstrap tenant", "import clients dry-run", "import clients", "import cases", "import document manifest", "upload bytes", "verify and scan"],
        }

    def pilot_readiness(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = db.get(dbm.Tenant, str(tenant_id))
        clients = db.scalars(select(dbm.Client).where(dbm.Client.tenant_id == str(tenant_id), dbm.Client.deleted_at.is_(None))).all()
        cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == str(tenant_id), dbm.Case.deleted_at.is_(None))).all()
        documents = db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == str(tenant_id), dbm.Document.deleted_at.is_(None))).all()
        users = db.scalars(select(dbm.User).where(dbm.User.tenant_id == str(tenant_id), dbm.User.deleted_at.is_(None))).all()
        audits = db.scalars(select(dbm.AuditLog).where(dbm.AuditLog.tenant_id == str(tenant_id))).all()
        document_status = Counter(document.status for document in documents)
        scan_status = Counter(document.malware_scan_status for document in documents)
        import_audits = [audit for audit in audits if audit.action in {"clients_imported", "cases_imported", "documents_manifest_imported"}]
        checklist = [
            {"key": "tenant", "label": "Tenant configurado", "ok": tenant is not None},
            {"key": "users", "label": "Usuarios internos creados", "ok": len([user for user in users if user.role.name != "client_user"]) >= 2},
            {"key": "clients", "label": "Clientes cargados", "ok": len(clients) >= 1},
            {"key": "cases", "label": "Expedientes cargados", "ok": len(cases) >= 1},
            {"key": "documents", "label": "Manifiesto documental cargado", "ok": len(documents) >= 1},
            {"key": "storage", "label": "Storage listo", "ok": storage_service.provider_status()["backend"] == "local"},
            {"key": "verified_docs", "label": "Documentos verificados", "ok": document_status.get("verified", 0) >= 1},
            {"key": "imports_audited", "label": "Imports auditados", "ok": len(import_audits) >= 1},
        ]
        ready = all(item["ok"] for item in checklist[:6])
        return {
            "tenant_id": str(tenant_id),
            "ready_for_controlled_pilot": ready,
            "metrics": {
                "users": len(users),
                "clients": len(clients),
                "cases": len(cases),
                "documents": len(documents),
                "verified_documents": document_status.get("verified", 0),
                "pending_upload_documents": document_status.get("pending_upload", 0),
                "rejected_documents": document_status.get("rejected", 0),
                "clean_scans": scan_status.get("clean", 0),
                "pending_scans": scan_status.get("pending", 0),
                "audit_events": len(audits),
            },
            "checklist": checklist,
            "next_actions": [
                "Completar imports dry-run antes de commit.",
                "Subir bytes de documentos pending_upload.",
                "Verificar storage y ejecutar scan mock.",
                "Ejecutar demo E2E con sponsor socio.",
            ],
        }

    def production_gate(self) -> dict[str, object]:
        settings = get_settings()
        readiness = production_readiness_report(settings)
        blockers = len(readiness["blockers"])
        warnings = len(readiness["warnings"])
        external_providers = {
            "ai": "live" if settings.openai_api_key else "mock",
            "whatsapp": "live" if settings.whatsapp_business_token else "mock",
            "billing": "live" if settings.billing_provider_secret else "mock",
            "email": "live" if settings.email_provider == "http_json" and settings.email_api_key else settings.email_provider,
            "malware_scanner": settings.malware_scanner_provider,
            "storage": storage_service.provider_status()["provider"],
        }
        static_requirements = [
            "APP_ENV=production",
            "REQUIRE_PRODUCTION_READY=true",
            "SEED_DEMO_ON_STARTUP=false",
            "PostgreSQL production database",
            "Strong JWT/S3 secrets",
            "No localhost CORS origins",
            "HTTPS-only public origins",
            "External pentest and monitoring",
        ]
        readiness_requirements = [
            f"{item['key']}: {item['message']}"
            for item in [*readiness["blockers"], *readiness["warnings"]]
        ]
        return {
            "gate": "P23 Production Gate",
            "status": "pass" if readiness["production_ready"] else "blocked",
            "public_production_status": "pass" if readiness["public_production_ready"] else "blocked",
            "revision": deployment_revision(settings),
            "external_providers": external_providers,
            "readiness": readiness,
            "summary": {"blockers": blockers, "warnings": warnings},
            "commands": [
                "npm run lint",
                "npm run test",
                "npm run build",
                "npm run test:api",
                "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/production-gate.ps1",
                "npm run cloud:wait-revision",
                "npm run cloud:smoke",
                "npm run cloud:evidence",
                "npm run cloud:public-ready",
            ],
            "required_before_public_production": [*static_requirements, *readiness_requirements],
        }


ops_center_service = OpsCenterService()
