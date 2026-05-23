from uuid import UUID

from app.domain.models import Tenant


class TenantService:
    def __init__(self) -> None:
        self._tenants: list[Tenant] = []

    def create(self, *, name: str, slug: str) -> Tenant:
        tenant = Tenant(name=name, slug=slug)
        self._tenants.append(tenant)
        return tenant

    def get(self, tenant_id: UUID) -> Tenant | None:
        return next((tenant for tenant in self._tenants if tenant.id == tenant_id), None)

    def find_by_slug(self, slug: str) -> Tenant | None:
        return next((tenant for tenant in self._tenants if tenant.slug == slug), None)

    def list(self) -> list[Tenant]:
        return list(self._tenants)

    def clear(self) -> None:
        self._tenants.clear()


tenant_service = TenantService()
