from dataclasses import dataclass

from app.domain.models import RoleName
from app.services.audit import audit_service
from app.services.cases import case_service
from app.services.clients import client_service
from app.services.tenants import tenant_service
from app.services.user_invitations import user_invitation_service
from app.services.users import user_service


@dataclass(frozen=True)
class SeedResult:
    tenant_slug: str
    admin_email: str
    lawyer_email: str
    client_email: str
    password: str


DEMO_SEED = SeedResult(
    tenant_slug="demo",
    admin_email="admin@lexflow.demo",
    lawyer_email="lawyer@lexflow.demo",
    client_email="client@lexflow.demo",
    password="LexflowDemo123!",
)


def seed_demo_data() -> SeedResult:
    audit_service.clear()
    case_service.clear()
    client_service.clear()
    user_service.clear()
    tenant_service.clear()
    user_invitation_service.clear()

    tenant = tenant_service.create(name="LEXFLOW Demo Studio", slug=DEMO_SEED.tenant_slug)
    admin = user_service.create(
        tenant_id=tenant.id,
        email=DEMO_SEED.admin_email,
        full_name="Demo Tenant Admin",
        password=DEMO_SEED.password,
        role=RoleName.tenant_admin,
    )
    lawyer = user_service.create(
        tenant_id=tenant.id,
        email=DEMO_SEED.lawyer_email,
        full_name="Demo Lawyer",
        password=DEMO_SEED.password,
        role=RoleName.lawyer,
        actor_user_id=admin.id,
    )
    user_service.create(
        tenant_id=tenant.id,
        email=DEMO_SEED.client_email,
        full_name="Demo Client User",
        password=DEMO_SEED.password,
        role=RoleName.client_user,
        actor_user_id=admin.id,
    )
    client = client_service.create(
        tenant_id=tenant.id,
        name="Nova Capital",
        contact_email="legal@novacapital.demo",
        risk_profile="standard",
        tags=["demo", "corporate"],
        actor_user_id=admin.id,
    )
    case_service.create(
        tenant_id=tenant.id,
        client_id=client.id,
        title="Cobro ejecutivo demo",
        description="Seed case for P2 backend core.",
        next_action="Preparar memorial",
        assigned_user_ids=[lawyer.id],
        actor_user_id=admin.id,
    )
    return DEMO_SEED
