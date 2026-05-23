from uuid import UUID

from app.domain.models import AuditAction, Matter
from app.services.audit import audit_service


class MatterService:
    def __init__(self) -> None:
        self._matters: list[Matter] = []

    def create(self, *, tenant_id: UUID, client_id: UUID, title: str, next_action: str) -> Matter:
        matter = Matter(
            tenant_id=tenant_id,
            client_id=client_id,
            title=title,
            next_action=next_action,
        )
        self._matters.append(matter)
        audit_service.record(
            tenant_id=tenant_id,
            action=AuditAction.create,
            entity_type="matter",
            entity_id=matter.id,
            metadata={"title": title},
        )
        return matter

    def list_for_tenant(self, tenant_id: UUID) -> list[Matter]:
        return [matter for matter in self._matters if matter.tenant_id == tenant_id]


matter_service = MatterService()
