from datetime import UTC, datetime
from uuid import UUID

from app.domain.models import AuditAction, RoleName, User
from app.services.audit import audit_service
from app.services.security import hash_password


class UserService:
    def __init__(self) -> None:
        self._users: list[User] = []

    def create(
        self,
        *,
        tenant_id: UUID,
        email: str,
        full_name: str,
        password: str,
        role: RoleName,
        actor_user_id: UUID | None = None,
        request_id: str | None = None,
    ) -> User:
        user = User(
            tenant_id=tenant_id,
            email=email.lower(),
            full_name=full_name,
            hashed_password=hash_password(password),
            role=role,
        )
        self._users.append(user)
        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=AuditAction.create,
            entity_type="user",
            entity_id=user.id,
            request_id=request_id,
            metadata={"email": user.email, "role": role.value},
        )
        return user

    def list_for_tenant(self, tenant_id: UUID) -> list[User]:
        return [user for user in self._users if user.tenant_id == tenant_id and user.is_active]

    def get(self, tenant_id: UUID, user_id: UUID) -> User | None:
        return next((user for user in self._users if user.tenant_id == tenant_id and user.id == user_id), None)

    def find_by_email(self, email: str, tenant_id: UUID | None = None) -> User | None:
        return next(
            (
                user
                for user in self._users
                if user.email == email.lower() and user.is_active and (tenant_id is None or user.tenant_id == tenant_id)
            ),
            None,
        )

    def update(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        actor_user_id: UUID,
        full_name: str | None = None,
        role: RoleName | None = None,
        is_active: bool | None = None,
        request_id: str | None = None,
    ) -> User | None:
        user = self.get(tenant_id, user_id)
        if not user:
            return None
        update_data: dict[str, object] = {"updated_at": datetime.now(UTC)}
        if full_name is not None:
            update_data["full_name"] = full_name
        if role is not None:
            update_data["role"] = role
        if is_active is not None:
            update_data["is_active"] = is_active
        updated = user.model_copy(update=update_data)
        self._users[self._users.index(user)] = updated
        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=AuditAction.update,
            entity_type="user",
            entity_id=user_id,
            request_id=request_id,
        )
        return updated

    def delete(self, *, tenant_id: UUID, user_id: UUID, actor_user_id: UUID, request_id: str | None = None) -> bool:
        user = self.update(
            tenant_id=tenant_id,
            user_id=user_id,
            actor_user_id=actor_user_id,
            is_active=False,
            request_id=request_id,
        )
        if user:
            audit_service.record(
                tenant_id=tenant_id,
                actor_user_id=actor_user_id,
                action=AuditAction.delete,
                entity_type="user",
                entity_id=user_id,
                request_id=request_id,
            )
        return user is not None

    def bump_refresh_version(self, user: User) -> User:
        updated = user.model_copy(update={"refresh_token_version": user.refresh_token_version + 1})
        self._users[self._users.index(user)] = updated
        return updated

    def clear(self) -> None:
        self._users.clear()


user_service = UserService()
