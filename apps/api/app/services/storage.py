from __future__ import annotations

import base64
import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db import models as dbm


SAFE_SEGMENT = re.compile(r"[^a-zA-Z0-9._=-]+")


@dataclass(frozen=True)
class SignedStorageToken:
    action: str
    tenant_id: str
    document_id: str
    storage_key: str
    expires_at: datetime
    case_id: str | None = None
    actor_user_id: str | None = None
    purpose: str | None = None


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign(payload: str) -> str:
    settings = get_settings()
    signature = hmac.new(settings.jwt_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64(payload.encode("utf-8")) + "." + _b64(signature)


def sanitize_storage_filename(filename: str) -> str:
    clean = filename.strip().replace("\\", "/").split("/")[-1]
    clean = SAFE_SEGMENT.sub("-", clean).strip(".-")
    if not clean:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid filename")
    return clean


def tenant_storage_key(*, tenant_id: UUID | str, case_id: UUID | str, document_id: UUID | str, filename: str) -> str:
    clean = sanitize_storage_filename(filename)
    return f"tenants/{tenant_id}/cases/{case_id}/documents/{document_id}/{clean}"


def _safe_local_path(storage_key: str) -> Path:
    settings = get_settings()
    parts = [sanitize_storage_filename(part) for part in storage_key.split("/") if part]
    if not parts or parts[0] != "tenants":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid storage key")
    root = Path(settings.storage_local_root).resolve()
    path = root.joinpath(*parts).resolve()
    if root != path and root not in path.parents:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid storage path")
    return path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _s3_client(settings: Settings):
    try:
        import boto3
    except ImportError as exc:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="S3 backend requires boto3") from exc
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )


def _s3_not_found(exc: Exception) -> bool:
    response = getattr(exc, "response", {}) or {}
    code = str(response.get("Error", {}).get("Code", "")).lower()
    status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    return code in {"404", "nosuchkey", "notfound"} or status_code == 404


class StorageService:
    def provider_status(self) -> dict[str, object]:
        settings = get_settings()
        return {
            "provider": "s3-compatible",
            "backend": settings.storage_backend,
            "mode": "local-bytes" if settings.storage_backend == "local" else "api-proxy-s3-compatible",
            "bucket": settings.s3_bucket,
            "endpoint_configured": bool(settings.s3_endpoint),
            "access_key_configured": bool(settings.s3_access_key),
            "public_base_url": settings.storage_public_base_url,
            "signed_url_minutes": settings.storage_signed_url_minutes,
            "max_upload_bytes": settings.max_upload_bytes,
            "local_root": settings.storage_local_root if settings.storage_backend == "local" else None,
        }

    def signed_download_url(self, *, document: dbm.Document, actor_user_id: UUID | str, purpose: str = "download") -> dict[str, object]:
        settings = get_settings()
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.storage_signed_url_minutes)
        payload = f"{document.tenant_id}|{document.id}|{document.storage_key}|{actor_user_id}|{purpose}|{int(expires_at.timestamp())}"
        token = _sign(payload)
        return {
            "document_id": document.id,
            "filename": document.filename,
            "content_type": document.content_type,
            "storage_key": document.storage_key,
            "expires_at": expires_at.isoformat(),
            "url": f"{settings.storage_public_base_url}/{document.id}?token={token}",
            "method": "GET",
        }

    def upload_contract(self, *, tenant_id: UUID | str, case_id: UUID | str, document_id: UUID | str, filename: str, content_type: str) -> dict[str, object]:
        settings = get_settings()
        storage_key = tenant_storage_key(tenant_id=tenant_id, case_id=case_id, document_id=document_id, filename=filename)
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.storage_signed_url_minutes)
        payload = f"{tenant_id}|{case_id}|{document_id}|{storage_key}|upload|{int(expires_at.timestamp())}"
        token = _sign(payload)
        return {
            "storage_key": storage_key,
            "upload": {
                "url": f"{settings.storage_public_base_url}/{document_id}?token={token}",
                "method": "PUT",
                "headers": {"Content-Type": content_type},
                "max_bytes": settings.max_upload_bytes,
                "expires_at": expires_at.isoformat(),
            },
        }

    def verify_token(self, token: str) -> SignedStorageToken:
        try:
            payload_b64, signature_b64 = token.split(".", 1)
            payload = _unb64(payload_b64).decode("utf-8")
            expected = _sign(payload).split(".", 1)[1]
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid storage token") from exc
        if not hmac.compare_digest(signature_b64, expected):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid storage token")

        parts = payload.split("|")
        if len(parts) != 6:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid storage token")
        try:
            expires_at = datetime.fromtimestamp(int(parts[5]), tz=UTC)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid storage token") from exc
        if expires_at < datetime.now(UTC):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Storage token expired")

        if parts[4] == "upload":
            return SignedStorageToken(
                action="upload",
                tenant_id=parts[0],
                case_id=parts[1],
                document_id=parts[2],
                storage_key=parts[3],
                expires_at=expires_at,
            )
        return SignedStorageToken(
            action="download",
            tenant_id=parts[0],
            document_id=parts[1],
            storage_key=parts[2],
            actor_user_id=parts[3],
            purpose=parts[4],
            expires_at=expires_at,
        )

    def store_signed_upload(self, db: Session, *, document_id: UUID | str, token: str, body: bytes, content_type: str | None, request_id: str | None = None) -> dict[str, object]:
        settings = get_settings()
        signed = self.verify_token(token)
        if signed.action != "upload" or signed.document_id != str(document_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Storage token does not allow upload")
        if len(body) > settings.max_upload_bytes:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Upload exceeds max size")

        document = self._document_or_404(db, document_id=document_id, tenant_id=signed.tenant_id)
        if document.storage_key != signed.storage_key:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Storage key mismatch")
        if content_type and content_type.split(";", 1)[0].strip() != document.content_type:
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Content type mismatch")

        checksum = hashlib.sha256(body).hexdigest()
        if settings.storage_backend == "local":
            path = _safe_local_path(document.storage_key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        else:
            _s3_client(settings).put_object(
                Bucket=settings.s3_bucket,
                Key=document.storage_key,
                Body=body,
                ContentType=document.content_type,
                Metadata={"sha256": checksum, "tenant_id": document.tenant_id, "document_id": document.id},
            )
        document.status = "pending_review" if document.uploaded_by_client else "uploaded"
        document.file_size_bytes = len(body)
        document.checksum_sha256 = checksum
        document.storage_verified_at = dbm.now_utc()
        document.malware_scan_status = "pending"
        document.malware_scan_result = {"engine": "pending", "status": "pending"}
        self._audit(
            db,
            tenant_id=document.tenant_id,
            actor_user_id=None,
            action="storage_object_uploaded",
            entity_id=document.id,
            request_id=request_id,
            metadata={"storage_key": document.storage_key, "bytes": len(body), "sha256": checksum},
        )
        db.commit()
        return {
            "document_id": document.id,
            "storage_key": document.storage_key,
            "bytes": len(body),
            "sha256": checksum,
            "status": document.status,
        }

    def object_metadata(self, *, storage_key: str) -> dict[str, object]:
        settings = get_settings()
        if settings.storage_backend == "local":
            path = _safe_local_path(storage_key)
            if not path.exists():
                return {"exists": False, "bytes": 0, "sha256": None}
            return {"exists": True, "bytes": path.stat().st_size, "sha256": _sha256_file(path)}
        try:
            response = _s3_client(settings).head_object(Bucket=settings.s3_bucket, Key=storage_key)
        except Exception as exc:
            if _s3_not_found(exc):
                return {"exists": False, "bytes": 0, "sha256": None}
            raise
        metadata = response.get("Metadata", {}) or {}
        etag = str(response.get("ETag", "")).strip('"') or None
        return {"exists": True, "bytes": response.get("ContentLength", 0), "sha256": metadata.get("sha256") or etag}

    def read_object_bytes(self, *, storage_key: str) -> bytes:
        settings = get_settings()
        if settings.storage_backend == "local":
            path = _safe_local_path(storage_key)
            if not path.exists():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored object not found")
            return path.read_bytes()
        try:
            response = _s3_client(settings).get_object(Bucket=settings.s3_bucket, Key=storage_key)
        except Exception as exc:
            if _s3_not_found(exc):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored object not found") from exc
            raise
        stream = response.get("Body", BytesIO())
        return stream.read()

    def read_signed_download(self, db: Session, *, document_id: UUID | str, token: str, request_id: str | None = None) -> tuple[bytes, dict[str, object]]:
        settings = get_settings()
        signed = self.verify_token(token)
        if signed.action != "download" or signed.document_id != str(document_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Storage token does not allow download")
        document = self._document_or_404(db, document_id=document_id, tenant_id=signed.tenant_id)
        if document.storage_key != signed.storage_key or document.deleted_at is not None or document.status == "private":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Storage key mismatch")
        if settings.storage_backend == "local":
            path = _safe_local_path(document.storage_key)
            if not path.exists():
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored object not found")
            body = path.read_bytes()
        else:
            try:
                response = _s3_client(settings).get_object(Bucket=settings.s3_bucket, Key=document.storage_key)
            except Exception as exc:
                if _s3_not_found(exc):
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored object not found") from exc
                raise
            stream = response.get("Body", BytesIO())
            body = stream.read()
        checksum = hashlib.sha256(body).hexdigest()
        self._audit(
            db,
            tenant_id=document.tenant_id,
            actor_user_id=signed.actor_user_id,
            action="storage_object_downloaded",
            entity_id=document.id,
            request_id=request_id,
            metadata={"storage_key": document.storage_key, "bytes": len(body), "sha256": checksum, "purpose": signed.purpose},
        )
        db.commit()
        return body, {
            "filename": document.filename,
            "content_type": document.content_type,
            "sha256": checksum,
            "bytes": len(body),
        }

    def _document_or_404(self, db: Session, *, document_id: UUID | str, tenant_id: UUID | str) -> dbm.Document:
        document = db.get(dbm.Document, str(document_id))
        if not document or document.tenant_id != str(tenant_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    def _audit(
        self,
        db: Session,
        *,
        tenant_id: str,
        actor_user_id: str | None,
        action: str,
        entity_id: str,
        request_id: str | None,
        metadata: dict[str, object],
    ) -> None:
        db.add(
            dbm.AuditLog(
                tenant_id=tenant_id,
                actor_user_id=actor_user_id,
                action=action,
                entity_type="storage_object",
                entity_id=entity_id,
                request_id=request_id,
                metadata_json=metadata,
            )
        )


storage_service = StorageService()
