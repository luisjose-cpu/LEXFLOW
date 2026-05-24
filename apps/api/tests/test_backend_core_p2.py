from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.domain.models import RoleName
from app.main import app
from app.services import auth as auth_module
from app.services import login_throttle as login_throttle_module
from app.services.mfa import totp_code
from app.services.seed import DEMO_SEED, seed_demo_data
from app.services.tenants import tenant_service
from app.services.users import user_service


client = TestClient(app)


def login(email: str = DEMO_SEED.admin_email, password: str = DEMO_SEED.password, tenant_slug: str = DEMO_SEED.tenant_slug) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "tenant_slug": tenant_slug},
    )
    assert response.status_code == 200
    body = response.json()
    return {"Authorization": f"Bearer {body['access_token']}"}


def test_auth_login_me_refresh_and_logout() -> None:
    seed_demo_data()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    assert response.status_code == 200
    body = response.json()
    headers = {"Authorization": f"Bearer {body['access_token']}"}

    me = client.get("/api/v1/auth/me", headers=headers)
    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})
    logout = client.post("/api/v1/auth/logout", headers=headers)
    revoked = client.post("/api/v1/auth/refresh", json={"refresh_token": body["refresh_token"]})

    assert me.status_code == 200
    assert me.json()["email"] == DEMO_SEED.admin_email
    assert refresh.status_code == 200
    assert logout.status_code == 200
    assert revoked.status_code == 401


def test_rbac_blocks_lawyer_from_user_admin() -> None:
    seed_demo_data()
    lawyer_headers = login(DEMO_SEED.lawyer_email)

    response = client.get("/api/v1/users", headers=lawyer_headers)

    assert response.status_code == 403


def test_clients_crud_search_tags_and_audit() -> None:
    seed_demo_data()
    headers = login()

    created = client.post(
        "/api/v1/clients",
        headers=headers,
        json={"name": "Andes Health", "contact_email": "legal@andes.demo", "tags": ["health", "priority"]},
    )
    assert created.status_code == 201
    client_id = created.json()["id"]

    listed = client.get("/api/v1/clients?search=andes&tag=health", headers=headers)
    updated = client.patch(
        f"/api/v1/clients/{client_id}",
        headers=headers,
        json={"risk_profile": "high", "tags": ["health", "litigation"]},
    )
    audit = client.get("/api/v1/audit?entity_type=client&action=create", headers=headers)

    assert len(listed.json()) == 1
    assert updated.status_code == 200
    assert updated.json()["risk_profile"] == "high"
    assert any(entry["entity_id"] == client_id for entry in audit.json())


def test_cases_crud_assign_change_status_and_permissions() -> None:
    seed_demo_data()
    headers = login()
    clients = client.get("/api/v1/clients", headers=headers).json()
    users = client.get("/api/v1/users", headers=headers).json()
    lawyer_id = next(user["id"] for user in users if user["role"] == "lawyer")

    created = client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "client_id": clients[0]["id"],
            "title": "Laboral colectivo",
            "next_action": "Clasificar pruebas",
        },
    )
    case_id = created.json()["id"]
    assigned = client.post(f"/api/v1/cases/{case_id}/assign", headers=headers, json={"assigned_user_ids": [lawyer_id]})
    changed = client.post(f"/api/v1/cases/{case_id}/change-status", headers=headers, json={"status": "risk"})
    filtered = client.get("/api/v1/cases?status=risk", headers=headers)

    assert created.status_code == 201
    assert assigned.json()["assigned_user_ids"] == [lawyer_id]
    assert changed.json()["status"] == "risk"
    assert any(item["id"] == case_id for item in filtered.json())


def test_tenant_isolation_blocks_cross_tenant_header() -> None:
    seed_demo_data()
    headers = login()
    other_tenant = tenant_service.create(name="Other Studio", slug="other")
    user_service.create(
        tenant_id=other_tenant.id,
        email="admin@other.demo",
        full_name="Other Admin",
        password=DEMO_SEED.password,
        role=RoleName.tenant_admin,
    )

    blocked = client.get("/api/v1/clients", headers={**headers, "X-Tenant-Id": str(other_tenant.id)})

    assert blocked.status_code == 403


def test_auth_rejects_bad_password() -> None:
    seed_demo_data()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": "wrong-password", "tenant_slug": DEMO_SEED.tenant_slug},
    )

    assert response.status_code == 401


def test_auth_temporarily_blocks_repeated_failed_logins(monkeypatch) -> None:
    seed_demo_data()
    login_throttle_module.login_throttle.clear_all()
    monkeypatch.setattr(auth_module, "get_settings", lambda: Settings(failed_login_limit=2, failed_login_window_minutes=15))
    monkeypatch.setattr(login_throttle_module.login_throttle, "_settings_provider", lambda: Settings(failed_login_limit=2, failed_login_window_minutes=15))
    payload = {"email": DEMO_SEED.admin_email, "password": "wrong-password", "tenant_slug": DEMO_SEED.tenant_slug}

    first = client.post("/api/v1/auth/login", json=payload)
    second = client.post("/api/v1/auth/login", json=payload)
    blocked = client.post("/api/v1/auth/login", json={**payload, "password": DEMO_SEED.password})

    assert first.status_code == 401
    assert second.status_code == 401
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Too many failed login attempts"


def test_auth_change_password_revokes_old_tokens_and_allows_new_password() -> None:
    seed_demo_data()
    logged = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    old_access = logged.json()["access_token"]
    old_refresh = logged.json()["refresh_token"]

    changed = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {old_access}"},
        json={"current_password": DEMO_SEED.password, "new_password": "NewPilotPassword123!"},
    )
    old_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {old_access}"})
    old_refresh_response = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": "NewPilotPassword123!", "tenant_slug": DEMO_SEED.tenant_slug},
    )

    assert changed.status_code == 200
    assert changed.json()["refresh_token"]
    assert old_me.status_code == 401
    assert old_refresh_response.status_code == 401
    assert new_login.status_code == 200


def test_auth_password_reset_flow_does_not_expose_unknown_accounts_and_revokes_sessions() -> None:
    seed_demo_data()
    unknown = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "missing@lexflow.demo", "tenant_slug": DEMO_SEED.tenant_slug},
    )
    logged = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    old_access = logged.json()["access_token"]
    requested = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": DEMO_SEED.admin_email, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    reset_token = requested.json()["reset_token"]
    confirmed = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"reset_token": reset_token, "new_password": "ResetPilotPassword123!"},
    )
    reused = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"reset_token": reset_token, "new_password": "ResetPilotPassword456!"},
    )
    old_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {old_access}"})
    old_password = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    new_password = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": "ResetPilotPassword123!", "tenant_slug": DEMO_SEED.tenant_slug},
    )

    assert unknown.status_code == 200
    assert "reset_token" not in unknown.json()
    assert requested.status_code == 200
    assert confirmed.json()["status"] == "password_reset_complete"
    assert reused.status_code == 401
    assert old_me.status_code == 401
    assert old_password.status_code == 401
    assert new_password.status_code == 200


def test_auth_mfa_enrollment_requires_totp_and_can_be_disabled() -> None:
    seed_demo_data()
    logged = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    access = logged.json()["access_token"]
    enrollment = client.post("/api/v1/auth/mfa/enroll", headers={"Authorization": f"Bearer {access}"})
    secret = enrollment.json()["secret"]
    code = totp_code(secret, int(datetime.now(UTC).timestamp() // 30))
    verified = client.post("/api/v1/auth/mfa/verify", headers={"Authorization": f"Bearer {access}"}, json={"code": code})
    rotated_access = verified.json()["access_token"]
    no_mfa_login = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    bad_mfa_login = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug, "mfa_code": "000000"},
    )
    good_mfa_login = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug, "mfa_code": code},
    )
    disabled = client.post(
        "/api/v1/auth/mfa/disable",
        headers={"Authorization": f"Bearer {rotated_access}"},
        json={"current_password": DEMO_SEED.password, "code": code},
    )
    no_code_after_disable = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )

    assert enrollment.status_code == 200
    assert enrollment.json()["status"] == "pending"
    assert enrollment.json()["otpauth_url"].startswith("otpauth://totp/")
    assert verified.status_code == 200
    assert no_mfa_login.status_code == 401
    assert bad_mfa_login.status_code == 401
    assert good_mfa_login.status_code == 200
    assert disabled.status_code == 200
    assert no_code_after_disable.status_code == 200


def test_user_invitation_flow_accepts_once_and_blocks_low_permission() -> None:
    seed_demo_data()
    admin_headers = login()
    lawyer_headers = login(DEMO_SEED.lawyer_email)

    blocked = client.post(
        "/api/v1/users/invitations",
        headers=lawyer_headers,
        json={"email": "invited.blocked@lexflow.com", "full_name": "Blocked Invite", "role": "lawyer"},
    )
    invited = client.post(
        "/api/v1/users/invitations",
        headers=admin_headers,
        json={"email": "newlawyer@lexflow.com", "full_name": "New Lawyer", "role": "lawyer"},
    )
    token = invited.json()["invitation_token"]
    listed = client.get("/api/v1/users/invitations", headers=admin_headers)
    accepted = client.post(
        "/api/v1/auth/invitations/accept",
        json={"invitation_token": token, "password": "InvitedLawyer123!"},
    )
    reused = client.post(
        "/api/v1/auth/invitations/accept",
        json={"invitation_token": token, "password": "InvitedLawyer456!"},
    )
    invited_login = client.post(
        "/api/v1/auth/login",
        json={"email": "newlawyer@lexflow.com", "password": "InvitedLawyer123!", "tenant_slug": DEMO_SEED.tenant_slug},
    )
    audit = client.get("/api/v1/audit?entity_type=user_invitation&action=create", headers=admin_headers)

    assert blocked.status_code == 403
    assert invited.status_code == 201
    assert invited.json()["delivery"] == "prepared"
    assert "invitation_token" not in listed.json()[0]
    assert listed.json()[0]["email"] == "newlawyer@lexflow.com"
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    assert accepted.json()["user"]["role"] == "lawyer"
    assert reused.status_code == 401
    assert invited_login.status_code == 200
    assert any(entry["entity_type"] == "user_invitation" for entry in audit.json())


def test_user_invitation_resend_rotates_token_and_cancel_blocks_acceptance() -> None:
    seed_demo_data()
    admin_headers = login()
    invited = client.post(
        "/api/v1/users/invitations",
        headers=admin_headers,
        json={"email": "rotated@lexflow.com", "full_name": "Rotated Invite", "role": "assistant"},
    )
    invitation_id = invited.json()["id"]
    old_token = invited.json()["invitation_token"]
    resent = client.post(f"/api/v1/users/invitations/{invitation_id}/resend", headers=admin_headers)
    new_token = resent.json()["invitation_token"]
    old_accept = client.post(
        "/api/v1/auth/invitations/accept",
        json={"invitation_token": old_token, "password": "RotatedInvite123!"},
    )
    cancelled = client.post(f"/api/v1/users/invitations/{invitation_id}/cancel", headers=admin_headers)
    new_accept = client.post(
        "/api/v1/auth/invitations/accept",
        json={"invitation_token": new_token, "password": "RotatedInvite123!"},
    )
    listed = client.get("/api/v1/users/invitations", headers=admin_headers)

    assert resent.status_code == 200
    assert resent.json()["delivery"] == "prepared"
    assert old_token != new_token
    assert old_accept.status_code == 401
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert new_accept.status_code == 401
    assert listed.json()[0]["status"] == "cancelled"


def test_tenant_security_policy_enforces_mfa_for_configured_roles() -> None:
    seed_demo_data()
    admin_headers = login()
    updated = client.patch(
        "/api/v1/settings/security-policy",
        headers=admin_headers,
        json={"enforce_mfa": True, "mfa_required_roles": ["lawyer"], "grace_period_hours": 24},
    )
    status_response = client.get("/api/v1/auth/mfa/status", headers=admin_headers)
    lawyer_login = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.lawyer_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    audit = client.get("/api/v1/audit?entity_type=tenant_security_policy&action=update", headers=admin_headers)

    assert updated.status_code == 200
    assert updated.json()["enforce_mfa"] is True
    assert updated.json()["mfa_required_roles"] == ["lawyer"]
    assert status_response.json()["policy_required"] is False
    assert lawyer_login.status_code == 403
    assert lawyer_login.json()["detail"] == "MFA enrollment required"
    assert admin_login.status_code == 200
    assert any(entry["entity_type"] == "tenant_security_policy" for entry in audit.json())


def test_tenant_security_policy_blocks_self_lockout_without_mfa() -> None:
    seed_demo_data()
    admin_headers = login()

    blocked = client.patch(
        "/api/v1/settings/security-policy",
        headers=admin_headers,
        json={"enforce_mfa": True, "mfa_required_roles": ["tenant_admin"]},
    )

    assert blocked.status_code == 400
    assert blocked.json()["detail"] == "Enable MFA before enforcing it for your own role"
