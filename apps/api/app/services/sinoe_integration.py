from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models as dbm
from app.services.case_overview import audit_case_action, get_case_or_404


SINOE_PROVIDER = "SINOE"
SINOE_LOGIN_URL = "https://casillas.pj.gob.pe/sinoe/login.xhtml"


class CredentialCipher:
    def __init__(self, secret: str | None = None) -> None:
        settings = get_settings()
        self._fernet = Fernet(self._normalize_key(secret or settings.credential_encryption_key or settings.jwt_secret))

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        try:
            return self._fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Credential encryption key is invalid") from exc

    @staticmethod
    def _normalize_key(secret: str) -> bytes:
        try:
            decoded = base64.urlsafe_b64decode(secret)
            if len(decoded) == 32:
                return secret.encode("utf-8")
        except Exception:
            pass
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)


@dataclass(frozen=True)
class SinoeSession:
    session_id: str
    captcha_required: bool = False


@dataclass(frozen=True)
class SinoeRawUpdate:
    external_id: str
    title: str
    summary: str
    occurred_at: str
    payload: dict[str, object]


class SinoeAdapter(Protocol):
    def login(self, *, username: str, password: str) -> SinoeSession:
        ...

    def detect_captcha(self, *, external_case_number: str, session: SinoeSession) -> bool:
        ...

    def fetch_updates(self, *, external_case_number: str, session: SinoeSession) -> list[SinoeRawUpdate]:
        ...

    def normalize_update(self, update: SinoeRawUpdate) -> dict[str, object]:
        ...

    def capture_evidence(self, *, external_case_number: str, update: SinoeRawUpdate | None = None, captcha_required: bool = False) -> dict[str, object]:
        ...


class SinoeAdapterMock:
    def login(self, *, username: str, password: str) -> SinoeSession:
        if not username.strip() or not password.strip() or "fail" in username.lower():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SINOE mock rejected credentials")
        return SinoeSession(session_id="sinoe-mock-session")

    def detect_captcha(self, *, external_case_number: str, session: SinoeSession) -> bool:
        return "CAPTCHA" in external_case_number.upper() or session.captcha_required

    def fetch_updates(self, *, external_case_number: str, session: SinoeSession) -> list[SinoeRawUpdate]:
        suffix = hashlib.sha1(external_case_number.encode("utf-8")).hexdigest()[:10]
        return [
            SinoeRawUpdate(
                external_id=f"sinoe-{suffix}",
                title="Notificacion SINOE registrada",
                summary=f"Adapter mock detecto una novedad autorizada para el expediente {external_case_number}.",
                occurred_at=dbm.now_utc().isoformat(),
                payload={
                    "provider": SINOE_PROVIDER,
                    "external_case_number": external_case_number,
                    "source": SINOE_LOGIN_URL,
                    "mock": True,
                },
            )
        ]

    def normalize_update(self, update: SinoeRawUpdate) -> dict[str, object]:
        return {
            "external_id": update.external_id,
            "title": update.title,
            "summary": update.summary,
            "occurred_at": update.occurred_at,
            "payload": update.payload,
        }

    def capture_evidence(self, *, external_case_number: str, update: SinoeRawUpdate | None = None, captcha_required: bool = False) -> dict[str, object]:
        return {
            "provider": SINOE_PROVIDER,
            "external_case_number": external_case_number,
            "captcha_required": captcha_required,
            "update_external_id": update.external_id if update else None,
            "source": SINOE_LOGIN_URL,
            "mock": True,
            "policy": "human_in_the_loop_no_captcha_bypass",
        }


class SinoeAutomationService:
    def __init__(self, *, adapter: SinoeAdapter | None = None, cipher: CredentialCipher | None = None) -> None:
        self.adapter = adapter or SinoeAdapterMock()
        self.cipher = cipher or CredentialCipher()

    def get_status(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        credential = self._get_credential(db, tenant_id=tenant_id)
        if not credential:
            return {"provider": SINOE_PROVIDER, "configured": False, "status": "not_configured", "last_checked_at": None, "username_hint": None}
        return {
            "id": credential.id,
            "provider": credential.provider,
            "configured": True,
            "status": credential.status,
            "last_checked_at": credential.last_checked_at.isoformat() if credential.last_checked_at else None,
            "username_hint": self._masked_username(credential.username_encrypted),
        }

    def save_credentials(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        username: str,
        password: str,
        actor_user_id: UUID | str,
        request_id: str | None = None,
    ) -> dict[str, object]:
        credential = self._get_credential(db, tenant_id=tenant_id, include_deleted=True)
        action = "sinoe_credentials_created"
        if credential:
            action = "sinoe_credentials_updated"
            credential.deleted_at = None
        else:
            credential = dbm.IntegrationCredential(tenant_id=str(tenant_id), provider=SINOE_PROVIDER, created_by=str(actor_user_id))
            db.add(credential)
        credential.username_encrypted = self.cipher.encrypt(username)
        credential.password_encrypted = self.cipher.encrypt(password)
        credential.status = "configured"
        db.flush()
        self._audit(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_id=credential.id,
            request_id=request_id,
            metadata={"provider": SINOE_PROVIDER, "status": credential.status},
        )
        db.commit()
        return self.get_status(db, tenant_id=tenant_id)

    def delete_credentials(self, db: Session, *, tenant_id: UUID | str, actor_user_id: UUID | str, request_id: str | None = None) -> dict[str, object]:
        credential = self._get_credential(db, tenant_id=tenant_id)
        if not credential:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SINOE integration not configured")
        credential.status = "disabled"
        credential.deleted_at = dbm.now_utc()
        self._audit(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="sinoe_credentials_deleted",
            entity_id=credential.id,
            request_id=request_id,
            metadata={"provider": SINOE_PROVIDER, "status": "disabled"},
        )
        db.commit()
        return {"provider": SINOE_PROVIDER, "configured": False, "status": "disabled"}

    def test_connection(self, db: Session, *, tenant_id: UUID | str, actor_user_id: UUID | str, request_id: str | None = None) -> dict[str, object]:
        credential = self._require_credentials(db, tenant_id=tenant_id)
        username, password = self._decrypt_credentials(credential)
        self.adapter.login(username=username, password=password)
        credential.status = "connected"
        credential.last_checked_at = dbm.now_utc()
        self._audit(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="sinoe_connection_tested",
            entity_id=credential.id,
            request_id=request_id,
            metadata={"provider": SINOE_PROVIDER, "status": "connected"},
        )
        db.commit()
        return self.get_status(db, tenant_id=tenant_id)

    def create_case_source(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        case_id: UUID | str,
        external_case_number: str,
        district: str | None,
        site: str | None,
        reference: str | None,
        actor_user_id: UUID | str,
        request_id: str | None = None,
    ) -> dbm.CaseSource:
        self._require_credentials(db, tenant_id=tenant_id)
        get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
        source = dbm.CaseSource(
            tenant_id=str(tenant_id),
            case_id=str(case_id),
            source_type="sinoe",
            source_name="SINOE",
            external_case_number=external_case_number,
            court_name=self._source_label(district=district, site=site, reference=reference),
            source_url=SINOE_LOGIN_URL,
            status="active",
        )
        db.add(source)
        db.flush()
        audit_case_action(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="sinoe_case_source_created",
            entity_type="case_source",
            entity_id=source.id,
            request_id=request_id,
            metadata={"case_id": str(case_id), "source_type": "sinoe"},
        )
        db.commit()
        return source

    def check_case_updates(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        source_id: UUID | str,
        actor_user_id: UUID | str,
        request_id: str | None = None,
    ) -> dict[str, object]:
        source = self._get_sinoe_source_or_404(db, tenant_id=tenant_id, source_id=source_id)
        credential = self._require_credentials(db, tenant_id=tenant_id)
        username, password = self._decrypt_credentials(credential)
        session = self.login(username=username, password=password)
        source.last_checked_at = dbm.now_utc()

        if self.detect_captcha(external_case_number=source.external_case_number, session=session):
            checkpoint = self.create_captcha_checkpoint(db, source=source, actor_user_id=actor_user_id, request_id=request_id)
            db.commit()
            return {"status": "captcha_required", "checkpoint_id": checkpoint.id, "source_id": source.id}

        raw_updates = self.extract_updates_after_login(source=source, session=session)
        normalized = [self.normalize_updates(update) for update in raw_updates]
        new_updates = self.compare_with_previous_updates(db, source=source, normalized_updates=normalized)
        created_update_ids: list[str] = []
        for raw_update, normalized_update in zip(raw_updates, normalized, strict=False):
            if normalized_update not in new_updates:
                continue
            judicial_update = self.save_judicial_update(db, source=source, normalized_update=normalized_update)
            created_update_ids.append(judicial_update.id)
            self.create_case_event(db, source=source, judicial_update=judicial_update)
            self.create_notification(db, source=source, judicial_update=judicial_update, actor_user_id=actor_user_id)
            self.create_evidence(db, source=source, judicial_update=judicial_update, raw_update=raw_update)

        source.status = "active"
        source.captcha_required = False
        source.last_result = "updates_found" if created_update_ids else "no_new_updates"
        credential.status = "connected"
        credential.last_checked_at = source.last_checked_at
        self.create_audit_log(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="sinoe_case_source_checked",
            entity_type="case_source",
            entity_id=source.id,
            request_id=request_id,
            metadata={"case_id": source.case_id, "updates_created": len(created_update_ids), "result": source.last_result},
        )
        db.commit()
        return {"status": source.last_result, "source_id": source.id, "update_ids": created_update_ids}

    def list_updates(self, db: Session, *, tenant_id: UUID | str, source_id: UUID | str) -> list[dbm.JudicialUpdate]:
        source = self._get_sinoe_source_or_404(db, tenant_id=tenant_id, source_id=source_id)
        return db.scalars(
            select(dbm.JudicialUpdate)
            .where(dbm.JudicialUpdate.tenant_id == str(tenant_id), dbm.JudicialUpdate.case_source_id == source.id)
            .order_by(dbm.JudicialUpdate.checked_at.desc())
        ).all()

    def login(self, *, username: str, password: str) -> SinoeSession:
        return self.adapter.login(username=username, password=password)

    def detect_captcha(self, *, external_case_number: str, session: SinoeSession) -> bool:
        return self.adapter.detect_captcha(external_case_number=external_case_number, session=session)

    def create_captcha_checkpoint(
        self,
        db: Session,
        *,
        source: dbm.CaseSource,
        actor_user_id: UUID | str,
        request_id: str | None,
    ) -> dbm.CaptchaCheckpoint:
        source.status = "paused_captcha"
        source.captcha_required = True
        source.last_result = "captcha_required"
        evidence_payload = self.adapter.capture_evidence(external_case_number=source.external_case_number, captcha_required=True)
        checkpoint = dbm.CaptchaCheckpoint(
            tenant_id=source.tenant_id,
            case_id=source.case_id,
            case_source_id=source.id,
            provider=SINOE_PROVIDER,
            status="pending",
            reason="SINOE requiere verificacion humana para continuar.",
            screenshot_url=None,
            expires_at=dbm.now_utc() + timedelta(minutes=30),
        )
        update = dbm.JudicialUpdate(
            tenant_id=source.tenant_id,
            case_id=source.case_id,
            case_source_id=source.id,
            update_type="sinoe_captcha_required",
            title="SINOE requiere verificacion humana",
            summary="La automatizacion fue pausada. No se evadira CAPTCHA ni medidas anti-bot.",
            status="paused",
            captcha_required=True,
            requires_human_intervention=True,
            raw_payload=evidence_payload,
        )
        db.add_all([checkpoint, update])
        db.flush()
        self.create_evidence(db, source=source, judicial_update=update, evidence_payload=evidence_payload)
        self.create_notification(
            db,
            source=source,
            title="SINOE requiere verificacion humana",
            body="La revision del expediente fue pausada por CAPTCHA. Un usuario autorizado debe resolverlo manualmente.",
            actor_user_id=actor_user_id,
        )
        self.create_audit_log(
            db,
            tenant_id=source.tenant_id,
            actor_user_id=actor_user_id,
            action="sinoe_captcha_checkpoint_created",
            entity_type="captcha_checkpoint",
            entity_id=checkpoint.id,
            request_id=request_id,
            metadata={"case_id": source.case_id, "case_source_id": source.id, "policy": "human_in_the_loop"},
        )
        return checkpoint

    def extract_updates_after_login(self, *, source: dbm.CaseSource, session: SinoeSession) -> list[SinoeRawUpdate]:
        return self.adapter.fetch_updates(external_case_number=source.external_case_number, session=session)

    def normalize_updates(self, update: SinoeRawUpdate) -> dict[str, object]:
        return self.adapter.normalize_update(update)

    def compare_with_previous_updates(self, db: Session, *, source: dbm.CaseSource, normalized_updates: list[dict[str, object]]) -> list[dict[str, object]]:
        existing_ids = {
            item.raw_payload.get("external_id")
            for item in db.scalars(
                select(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == source.tenant_id, dbm.JudicialUpdate.case_source_id == source.id)
            ).all()
            if isinstance(item.raw_payload, dict)
        }
        return [item for item in normalized_updates if item.get("external_id") not in existing_ids]

    def save_judicial_update(self, db: Session, *, source: dbm.CaseSource, normalized_update: dict[str, object]) -> dbm.JudicialUpdate:
        update = dbm.JudicialUpdate(
            tenant_id=source.tenant_id,
            case_id=source.case_id,
            case_source_id=source.id,
            update_type="sinoe_update",
            title=str(normalized_update["title"]),
            summary=str(normalized_update["summary"]),
            status="recorded",
            captcha_required=False,
            requires_human_intervention=False,
            raw_payload=normalized_update,
        )
        db.add(update)
        db.flush()
        return update

    def create_case_event(self, db: Session, *, source: dbm.CaseSource, judicial_update: dbm.JudicialUpdate) -> dbm.CaseEvent:
        event = dbm.CaseEvent(
            tenant_id=source.tenant_id,
            case_id=source.case_id,
            event_type="sinoe_update",
            title=judicial_update.title,
            description=judicial_update.summary,
            is_client_visible=False,
        )
        db.add(event)
        return event

    def create_notification(
        self,
        db: Session,
        *,
        source: dbm.CaseSource,
        actor_user_id: UUID | str | None,
        judicial_update: dbm.JudicialUpdate | None = None,
        title: str | None = None,
        body: str | None = None,
    ) -> dbm.Notification:
        notification = dbm.Notification(
            tenant_id=source.tenant_id,
            user_id=str(actor_user_id) if actor_user_id else None,
            case_id=source.case_id,
            title=title or "Nueva actualizacion SINOE",
            body=body or (judicial_update.summary if judicial_update else "SINOE registro una novedad del expediente."),
            channel="in_app",
            status="pending",
        )
        db.add(notification)
        return notification

    def create_evidence(
        self,
        db: Session,
        *,
        source: dbm.CaseSource,
        judicial_update: dbm.JudicialUpdate,
        raw_update: SinoeRawUpdate | None = None,
        evidence_payload: dict[str, object] | None = None,
    ) -> dbm.JudicialEvidence:
        payload = evidence_payload or self.adapter.capture_evidence(external_case_number=source.external_case_number, update=raw_update)
        evidence = dbm.JudicialEvidence(
            tenant_id=source.tenant_id,
            case_id=source.case_id,
            case_source_id=source.id,
            judicial_update_id=judicial_update.id,
            evidence_type="sinoe_mock_payload",
            metadata_json=payload,
        )
        db.add(evidence)
        return evidence

    def create_audit_log(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor_user_id: UUID | str | None,
        action: str,
        entity_type: str,
        entity_id: UUID | str,
        request_id: str | None,
        metadata: dict[str, object],
    ) -> dbm.AuditLog:
        audit = dbm.AuditLog(
            tenant_id=str(tenant_id),
            actor_user_id=str(actor_user_id) if actor_user_id else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            request_id=request_id,
            metadata_json=metadata,
        )
        db.add(audit)
        return audit

    def _get_credential(self, db: Session, *, tenant_id: UUID | str, include_deleted: bool = False) -> dbm.IntegrationCredential | None:
        query = select(dbm.IntegrationCredential).where(
            dbm.IntegrationCredential.tenant_id == str(tenant_id),
            dbm.IntegrationCredential.provider == SINOE_PROVIDER,
        )
        if not include_deleted:
            query = query.where(dbm.IntegrationCredential.deleted_at.is_(None))
        return db.scalar(query)

    def _require_credentials(self, db: Session, *, tenant_id: UUID | str) -> dbm.IntegrationCredential:
        credential = self._get_credential(db, tenant_id=tenant_id)
        if not credential or credential.status == "disabled":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SINOE integration is not configured")
        return credential

    def _decrypt_credentials(self, credential: dbm.IntegrationCredential) -> tuple[str, str]:
        return self.cipher.decrypt(credential.username_encrypted), self.cipher.decrypt(credential.password_encrypted)

    def _get_sinoe_source_or_404(self, db: Session, *, tenant_id: UUID | str, source_id: UUID | str) -> dbm.CaseSource:
        source = db.scalar(
            select(dbm.CaseSource).where(
                dbm.CaseSource.tenant_id == str(tenant_id),
                dbm.CaseSource.id == str(source_id),
                dbm.CaseSource.source_type == "sinoe",
                dbm.CaseSource.deleted_at.is_(None),
            )
        )
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SINOE case source not found")
        return source

    def _masked_username(self, encrypted_username: str) -> str:
        username = self.cipher.decrypt(encrypted_username)
        if "@" in username:
            name, domain = username.split("@", 1)
            return f"{name[:2]}***@{domain}"
        return f"{username[:2]}***"

    def _audit(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor_user_id: UUID | str,
        action: str,
        entity_id: UUID | str,
        request_id: str | None,
        metadata: dict[str, object],
    ) -> dbm.AuditLog:
        return self.create_audit_log(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type="integration_credentials",
            entity_id=entity_id,
            request_id=request_id,
            metadata=metadata,
        )

    @staticmethod
    def _source_label(*, district: str | None, site: str | None, reference: str | None) -> str:
        parts = [part for part in [district, site, reference] if part]
        return " / ".join(parts) if parts else "SINOE"


sinoe_automation_service = SinoeAutomationService()
