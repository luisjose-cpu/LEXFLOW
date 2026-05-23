from datetime import UTC, datetime
from uuid import UUID

from app.domain.models import AuditAction, LegalCase, MatterStatus
from app.services.audit import audit_service


class CaseService:
    def __init__(self) -> None:
        self._cases: list[LegalCase] = []

    def create(
        self,
        *,
        tenant_id: UUID,
        client_id: UUID,
        title: str,
        next_action: str,
        actor_user_id: UUID,
        description: str | None = None,
        assigned_user_ids: list[UUID] | None = None,
        request_id: str | None = None,
    ) -> LegalCase:
        legal_case = LegalCase(
            tenant_id=tenant_id,
            client_id=client_id,
            title=title,
            description=description,
            next_action=next_action,
            assigned_user_ids=assigned_user_ids or [],
        )
        self._cases.append(legal_case)
        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=AuditAction.create,
            entity_type="case",
            entity_id=legal_case.id,
            request_id=request_id,
            metadata={"title": title},
        )
        return legal_case

    def list_for_tenant(self, tenant_id: UUID, *, status: MatterStatus | None = None) -> list[LegalCase]:
        cases = [legal_case for legal_case in self._cases if legal_case.tenant_id == tenant_id]
        if status:
            cases = [legal_case for legal_case in cases if legal_case.status == status]
        return cases

    def get(self, tenant_id: UUID, case_id: UUID) -> LegalCase | None:
        return next((legal_case for legal_case in self._cases if legal_case.tenant_id == tenant_id and legal_case.id == case_id), None)

    def update(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        actor_user_id: UUID,
        title: str | None = None,
        description: str | None = None,
        next_action: str | None = None,
        request_id: str | None = None,
    ) -> LegalCase | None:
        legal_case = self.get(tenant_id, case_id)
        if not legal_case:
            return None
        update_data: dict[str, object] = {"updated_at": datetime.now(UTC)}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if next_action is not None:
            update_data["next_action"] = next_action
        updated = legal_case.model_copy(update=update_data)
        self._cases[self._cases.index(legal_case)] = updated
        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=AuditAction.update,
            entity_type="case",
            entity_id=case_id,
            request_id=request_id,
        )
        return updated

    def assign(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        assigned_user_ids: list[UUID],
        actor_user_id: UUID,
        request_id: str | None = None,
    ) -> LegalCase | None:
        legal_case = self.get(tenant_id, case_id)
        if not legal_case:
            return None
        updated = legal_case.model_copy(update={"assigned_user_ids": assigned_user_ids, "updated_at": datetime.now(UTC)})
        self._cases[self._cases.index(legal_case)] = updated
        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=AuditAction.assign,
            entity_type="case",
            entity_id=case_id,
            request_id=request_id,
        )
        return updated

    def change_status(
        self,
        *,
        tenant_id: UUID,
        case_id: UUID,
        status: MatterStatus,
        actor_user_id: UUID,
        request_id: str | None = None,
    ) -> LegalCase | None:
        legal_case = self.get(tenant_id, case_id)
        if not legal_case:
            return None
        updated = legal_case.model_copy(update={"status": status, "updated_at": datetime.now(UTC)})
        self._cases[self._cases.index(legal_case)] = updated
        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=AuditAction.change_status,
            entity_type="case",
            entity_id=case_id,
            request_id=request_id,
            metadata={"status": status.value},
        )
        return updated

    def delete(self, *, tenant_id: UUID, case_id: UUID, actor_user_id: UUID, request_id: str | None = None) -> bool:
        legal_case = self.get(tenant_id, case_id)
        if not legal_case:
            return False
        self._cases.remove(legal_case)
        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=AuditAction.delete,
            entity_type="case",
            entity_id=case_id,
            request_id=request_id,
        )
        return True

    def clear(self) -> None:
        self._cases.clear()


case_service = CaseService()
