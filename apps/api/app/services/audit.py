from uuid import UUID

from app.domain.models import AuditAction, AuditLog


class AuditService:
    def __init__(self) -> None:
        self._entries: list[AuditLog] = []

    def record(
        self,
        *,
        tenant_id: UUID,
        action: AuditAction,
        entity_type: str,
        entity_id: UUID,
        actor_user_id: UUID | None = None,
        metadata: dict[str, str] | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata or {},
            request_id=request_id,
        )
        self._entries.append(entry)
        return entry

    def list_for_tenant(
        self,
        tenant_id: UUID,
        *,
        action: AuditAction | None = None,
        entity_type: str | None = None,
        actor_user_id: UUID | None = None,
    ) -> list[AuditLog]:
        entries = [entry for entry in self._entries if entry.tenant_id == tenant_id]
        if action:
            entries = [entry for entry in entries if entry.action == action]
        if entity_type:
            entries = [entry for entry in entries if entry.entity_type == entity_type]
        if actor_user_id:
            entries = [entry for entry in entries if entry.actor_user_id == actor_user_id]
        return entries

    def clear(self) -> None:
        self._entries.clear()


audit_service = AuditService()
