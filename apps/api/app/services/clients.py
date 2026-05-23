from datetime import UTC, datetime
from uuid import UUID

from app.domain.models import AuditAction, Client
from app.services.audit import audit_service


class ClientService:
    def __init__(self) -> None:
        self._clients: list[Client] = []

    def create(
        self,
        *,
        tenant_id: UUID,
        name: str,
        contact_email: str | None,
        risk_profile: str,
        tags: list[str],
        actor_user_id: UUID,
        request_id: str | None = None,
    ) -> Client:
        client = Client(
            tenant_id=tenant_id,
            name=name,
            contact_email=contact_email,
            risk_profile=risk_profile,
            tags=tags,
        )
        self._clients.append(client)
        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=AuditAction.create,
            entity_type="client",
            entity_id=client.id,
            request_id=request_id,
            metadata={"name": name},
        )
        return client

    def list_for_tenant(self, tenant_id: UUID, *, search: str | None = None, tag: str | None = None) -> list[Client]:
        clients = [client for client in self._clients if client.tenant_id == tenant_id]
        if search:
            needle = search.lower()
            clients = [client for client in clients if needle in client.name.lower() or needle in (client.contact_email or "").lower()]
        if tag:
            clients = [client for client in clients if tag in client.tags]
        return clients

    def get(self, tenant_id: UUID, client_id: UUID) -> Client | None:
        return next((client for client in self._clients if client.tenant_id == tenant_id and client.id == client_id), None)

    def update(
        self,
        *,
        tenant_id: UUID,
        client_id: UUID,
        actor_user_id: UUID,
        name: str | None = None,
        contact_email: str | None = None,
        risk_profile: str | None = None,
        tags: list[str] | None = None,
        request_id: str | None = None,
    ) -> Client | None:
        client = self.get(tenant_id, client_id)
        if not client:
            return None
        update_data: dict[str, object] = {"updated_at": datetime.now(UTC)}
        if name is not None:
            update_data["name"] = name
        if contact_email is not None:
            update_data["contact_email"] = contact_email
        if risk_profile is not None:
            update_data["risk_profile"] = risk_profile
        if tags is not None:
            update_data["tags"] = tags
        updated = client.model_copy(update=update_data)
        self._clients[self._clients.index(client)] = updated
        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=AuditAction.update,
            entity_type="client",
            entity_id=client_id,
            request_id=request_id,
        )
        return updated

    def delete(self, *, tenant_id: UUID, client_id: UUID, actor_user_id: UUID, request_id: str | None = None) -> bool:
        client = self.get(tenant_id, client_id)
        if not client:
            return False
        self._clients.remove(client)
        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=AuditAction.delete,
            entity_type="client",
            entity_id=client_id,
            request_id=request_id,
        )
        return True

    def clear(self) -> None:
        self._clients.clear()


client_service = ClientService()
