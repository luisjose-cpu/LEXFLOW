from __future__ import annotations

import base64
import hmac
import struct
from datetime import UTC, datetime
from hashlib import sha1
from secrets import token_bytes
from urllib.parse import quote


def generate_totp_secret() -> str:
    return base64.b32encode(token_bytes(20)).decode("utf-8").rstrip("=")


def build_otpauth_url(*, issuer: str, account: str, secret: str) -> str:
    label = quote(f"{issuer}:{account}")
    issuer_q = quote(issuer)
    return f"otpauth://totp/{label}?secret={secret}&issuer={issuer_q}&algorithm=SHA1&digits=6&period=30"


def verify_totp(secret: str, code: str, *, at: datetime | None = None, window: int = 1) -> bool:
    normalized = "".join(character for character in code if character.isdigit())
    if len(normalized) != 6:
        return False
    now = at or datetime.now(UTC)
    counter = int(now.timestamp() // 30)
    return any(hmac.compare_digest(totp_code(secret, counter + offset), normalized) for offset in range(-window, window + 1))


def totp_code(secret: str, counter: int) -> str:
    padded_secret = secret.upper() + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded_secret, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"
