from datetime import timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models as dbm
from app.domain.models import AuditAction, RoleName, User
from app.services.audit import audit_service
from app.services.email_delivery import get_email_provider
from app.services.security import hash_password
from app.services.tenants import tenant_service
from app.services.users import user_service


TENANT_INVITABLE_ROLES = {RoleName.tenant_admin, RoleName.partner, RoleName.lawyer, RoleName.assistant, RoleName.client_user}


class UserInvitationService:
    def __init__(self) -> None:
        self._memory_invitations: dict[str, dict[str, object]] = {}

    def create(
        self,
        db: Session,
        *,
        tenant_id: UUID,
        email: str,
        full_name: str,
        role: RoleName,
        actor: User,
        request_id: str | None = None,
    ) -> dict[str, object]:
        if role not in TENANT_INVITABLE_ROLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role cannot be invited")
        normalized_email = email.lower()
        if user_service.find_by_email(normalized_email, tenant_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

        settings = get_settings()
        raw_token = token_urlsafe(32)
        token_hash = self._token_hash(raw_token)
        expires_at = dbm.now_utc() + timedelta(minutes=settings.user_invitation_token_minutes)

        tenant_exists_in_db = self._db_tenant_exists(db, tenant_id)
        invitation_id = uuid4()
        if tenant_exists_in_db:
            if self._db_user_exists(db, tenant_id=tenant_id, email=normalized_email):
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
            db.add(
                dbm.UserInvitation(
                    id=str(invitation_id),
                    tenant_id=str(tenant_id),
                    email=normalized_email,
                    full_name=full_name,
                    role=role.value,
                    token_hash=token_hash,
                    invited_by_user_id=str(actor.id),
                    expires_at=expires_at,
                )
            )
            try:
                db.commit()
            except IntegrityError as exc:
                db.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation already exists") from exc
            except SQLAlchemyError as exc:
                db.rollback()
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create invitation") from exc
        else:
            self._memory_invitations[token_hash] = {
                "id": invitation_id,
                "tenant_id": tenant_id,
                "email": normalized_email,
                "full_name": full_name,
                "role": role,
                "status": "pending",
                "invited_by_user_id": actor.id,
                "expires_at": expires_at,
                "accepted_at": None,
                "created_at": dbm.now_utc(),
                "updated_at": dbm.now_utc(),
            }

        delivery = self._deliver(normalized_email, full_name, token=raw_token)
        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor.id,
            action=AuditAction.create,
            entity_type="user_invitation",
            entity_id=invitation_id,
            request_id=request_id,
            metadata={"email": normalized_email, "role": role.value, "delivery": delivery.status, "provider": delivery.provider},
        )
        response = {
            "id": str(invitation_id),
            "email": normalized_email,
            "full_name": full_name,
            "role": role.value,
            "status": "pending",
            "expires_at": expires_at.isoformat(),
            "delivery": delivery.status,
        }
        if settings.app_env.lower() in {"local", "test"}:
            response["invitation_token"] = raw_token
        return response

    def list_for_tenant(self, db: Session, *, tenant_id: UUID) -> list[dict[str, object]]:
        invitations = [
            self._serialize_memory(invitation)
            for invitation in self._memory_invitations.values()
            if invitation["tenant_id"] == tenant_id
        ]
        if self._db_tenant_exists(db, tenant_id):
            rows = db.scalars(select(dbm.UserInvitation).where(dbm.UserInvitation.tenant_id == str(tenant_id)).order_by(dbm.UserInvitation.created_at.desc())).all()
            invitations.extend(self._serialize_db(row) for row in rows)
        return invitations

    def resend(self, db: Session, *, tenant_id: UUID, invitation_id: UUID, actor: User, request_id: str | None = None) -> dict[str, object]:
        settings = get_settings()
        raw_token = token_urlsafe(32)
        token_hash = self._token_hash(raw_token)
        expires_at = dbm.now_utc() + timedelta(minutes=settings.user_invitation_token_minutes)
        memory_key, memory_invitation = self._find_memory_by_id(tenant_id=tenant_id, invitation_id=invitation_id)
        if memory_invitation:
            if memory_invitation["status"] != "pending":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation is not pending")
            self._memory_invitations.pop(memory_key)
            memory_invitation["expires_at"] = expires_at
            memory_invitation["updated_at"] = dbm.now_utc()
            self._memory_invitations[token_hash] = memory_invitation
            response = self._serialize_memory(memory_invitation)
            response["delivery"] = self._deliver(memory_invitation["email"], memory_invitation["full_name"], token=raw_token).status
        else:
            invitation = self._get_db_invitation(db, tenant_id=tenant_id, invitation_id=invitation_id)
            if invitation.status != "pending":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation is not pending")
            invitation.token_hash = token_hash
            invitation.expires_at = expires_at
            invitation.updated_at = dbm.now_utc()
            db.commit()
            db.refresh(invitation)
            response = self._serialize_db(invitation)
            response["delivery"] = self._deliver(invitation.email, invitation.full_name, token=raw_token).status

        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor.id,
            action=AuditAction.update,
            entity_type="user_invitation",
            entity_id=invitation_id,
            request_id=request_id,
            metadata={"reason": "invitation_resent", "delivery": response["delivery"]},
        )
        if settings.app_env.lower() in {"local", "test"}:
            response["invitation_token"] = raw_token
        return response

    def cancel(self, db: Session, *, tenant_id: UUID, invitation_id: UUID, actor: User, request_id: str | None = None) -> dict[str, object]:
        memory_key, memory_invitation = self._find_memory_by_id(tenant_id=tenant_id, invitation_id=invitation_id)
        if memory_invitation:
            if memory_invitation["status"] != "pending":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation is not pending")
            memory_invitation["status"] = "cancelled"
            memory_invitation["updated_at"] = dbm.now_utc()
            response = self._serialize_memory(memory_invitation)
        else:
            invitation = self._get_db_invitation(db, tenant_id=tenant_id, invitation_id=invitation_id)
            if invitation.status != "pending":
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation is not pending")
            invitation.status = "cancelled"
            invitation.updated_at = dbm.now_utc()
            db.commit()
            db.refresh(invitation)
            response = self._serialize_db(invitation)

        audit_service.record(
            tenant_id=tenant_id,
            actor_user_id=actor.id,
            action=AuditAction.update,
            entity_type="user_invitation",
            entity_id=invitation_id,
            request_id=request_id,
            metadata={"reason": "invitation_cancelled"},
        )
        return response

    def accept(self, db: Session, *, invitation_token: str, password: str, request_id: str | None = None) -> dict[str, object]:
        token_hash = self._token_hash(invitation_token)
        now = dbm.now_utc()
        memory_invitation = self._memory_invitations.get(token_hash)
        if memory_invitation:
            if memory_invitation["status"] != "pending" or memory_invitation["expires_at"] <= now:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired invitation")
            user = user_service.create(
                tenant_id=memory_invitation["tenant_id"],
                email=str(memory_invitation["email"]),
                full_name=str(memory_invitation["full_name"]),
                password=password,
                role=memory_invitation["role"],
                actor_user_id=memory_invitation["invited_by_user_id"],
                request_id=request_id,
            )
            memory_invitation["status"] = "accepted"
            memory_invitation["accepted_at"] = now
            memory_invitation["updated_at"] = now
            audit_service.record(
                tenant_id=user.tenant_id,
                actor_user_id=user.id,
                action=AuditAction.update,
                entity_type="user_invitation",
                entity_id=memory_invitation["id"],
                request_id=request_id,
                metadata={"reason": "invitation_accepted", "email": user.email, "role": user.role.value},
            )
            return {"status": "accepted", "user": user}

        try:
            invitation = db.scalar(
                select(dbm.UserInvitation).where(
                    dbm.UserInvitation.token_hash == token_hash,
                    dbm.UserInvitation.status == "pending",
                    dbm.UserInvitation.expires_at > now,
                )
            )
        except SQLAlchemyError:
            invitation = None
        if not invitation:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired invitation")
        if self._db_user_exists(db, tenant_id=UUID(invitation.tenant_id), email=invitation.email):
            invitation.status = "superseded"
            invitation.updated_at = now
            db.commit()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

        role = self._ensure_role(db, tenant_id=invitation.tenant_id, role=RoleName(invitation.role))
        db_user = dbm.User(
            tenant_id=invitation.tenant_id,
            role_id=role.id,
            email=invitation.email,
            full_name=invitation.full_name,
            hashed_password=hash_password(password),
            status="active",
        )
        db.add(db_user)
        invitation.status = "accepted"
        invitation.accepted_at = now
        invitation.updated_at = now
        db.commit()
        db.refresh(db_user)
        user = user_service.upsert(self._domain_user_from_db(db_user))
        audit_service.record(
            tenant_id=user.tenant_id,
            actor_user_id=user.id,
            action=AuditAction.update,
            entity_type="user_invitation",
            entity_id=UUID(invitation.id),
            request_id=request_id,
            metadata={"reason": "invitation_accepted", "email": user.email, "role": user.role.value},
        )
        return {"status": "accepted", "user": user}

    def clear(self) -> None:
        self._memory_invitations.clear()

    def _db_tenant_exists(self, db: Session, tenant_id: UUID) -> bool:
        try:
            return db.get(dbm.Tenant, str(tenant_id)) is not None
        except SQLAlchemyError:
            return False

    def _db_user_exists(self, db: Session, *, tenant_id: UUID, email: str) -> bool:
        return (
            db.scalar(
                select(dbm.User.id).where(
                    dbm.User.tenant_id == str(tenant_id),
                    dbm.User.email == email.lower(),
                    dbm.User.deleted_at.is_(None),
                )
            )
            is not None
        )

    def _get_db_invitation(self, db: Session, *, tenant_id: UUID, invitation_id: UUID) -> dbm.UserInvitation:
        invitation = db.scalar(select(dbm.UserInvitation).where(dbm.UserInvitation.tenant_id == str(tenant_id), dbm.UserInvitation.id == str(invitation_id)))
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")
        return invitation

    def _find_memory_by_id(self, *, tenant_id: UUID, invitation_id: UUID) -> tuple[str, dict[str, object]] | tuple[None, None]:
        for token_hash, invitation in self._memory_invitations.items():
            if invitation["tenant_id"] == tenant_id and invitation["id"] == invitation_id:
                return token_hash, invitation
        return None, None

    def _deliver(self, email: object, full_name: object, *, token: str):
        settings = get_settings()
        invitation_url = f"{settings.lexflow_web_url.rstrip('/')}/login/invite?token={token}"
        return get_email_provider(settings).send_user_invitation(to_email=str(email), full_name=str(full_name), invitation_url=invitation_url)

    def _ensure_role(self, db: Session, *, tenant_id: str, role: RoleName) -> dbm.Role:
        existing = db.scalars(select(dbm.Role).where(dbm.Role.tenant_id == tenant_id, dbm.Role.name == role.value)).first()
        if existing:
            return existing
        created = dbm.Role(tenant_id=tenant_id, name=role.value, description=f"LEXFLOW role: {role.value}", is_system=True)
        db.add(created)
        db.flush()
        return created

    def _domain_user_from_db(self, db_user: dbm.User) -> User:
        role_name = db_user.role.name if db_user.role else "lawyer"
        tenant = db_user.tenant
        if tenant:
            from app.domain.models import Tenant as DomainTenant

            tenant_service.upsert(DomainTenant(id=UUID(tenant.id), name=tenant.name, slug=tenant.slug, is_active=tenant.status == "active", created_at=tenant.created_at))
        return User(
            id=UUID(db_user.id),
            tenant_id=UUID(db_user.tenant_id),
            email=db_user.email,
            full_name=db_user.full_name,
            hashed_password=db_user.hashed_password,
            role=RoleName(role_name),
            is_active=db_user.status == "active",
            mfa_enabled=db_user.mfa_enabled,
            mfa_secret_encrypted=db_user.mfa_secret_encrypted,
            refresh_token_version=db_user.refresh_token_version,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
        )

    @staticmethod
    def _serialize_memory(invitation: dict[str, object]) -> dict[str, object]:
        return {
            "id": str(invitation["id"]),
            "email": invitation["email"],
            "full_name": invitation["full_name"],
            "role": invitation["role"].value,
            "status": invitation["status"],
            "expires_at": invitation["expires_at"].isoformat(),
            "accepted_at": invitation["accepted_at"].isoformat() if invitation["accepted_at"] else None,
            "created_at": invitation["created_at"].isoformat(),
        }

    @staticmethod
    def _serialize_db(invitation: dbm.UserInvitation) -> dict[str, object]:
        return {
            "id": invitation.id,
            "email": invitation.email,
            "full_name": invitation.full_name,
            "role": invitation.role,
            "status": invitation.status,
            "expires_at": invitation.expires_at.isoformat(),
            "accepted_at": invitation.accepted_at.isoformat() if invitation.accepted_at else None,
            "created_at": invitation.created_at.isoformat(),
        }

    @staticmethod
    def _token_hash(raw_token: str) -> str:
        return sha256(raw_token.encode("utf-8")).hexdigest()


user_invitation_service = UserInvitationService()
