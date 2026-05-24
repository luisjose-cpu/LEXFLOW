from dataclasses import dataclass
import json
from urllib import request

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class EmailDeliveryResult:
    provider: str
    status: str


class EmailProvider:
    def send_user_invitation(self, *, to_email: str, full_name: str, invitation_url: str | None = None) -> EmailDeliveryResult:
        raise NotImplementedError

    def send_password_reset(self, *, to_email: str, reset_url: str | None = None) -> EmailDeliveryResult:
        raise NotImplementedError


class EmailPreparedProvider(EmailProvider):
    def send_user_invitation(self, *, to_email: str, full_name: str, invitation_url: str | None = None) -> EmailDeliveryResult:
        return EmailDeliveryResult(provider="email_prepared", status="prepared")

    def send_password_reset(self, *, to_email: str, reset_url: str | None = None) -> EmailDeliveryResult:
        return EmailDeliveryResult(provider="email_prepared", status="prepared")


class EmailHttpJsonProvider(EmailProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send_user_invitation(self, *, to_email: str, full_name: str, invitation_url: str | None = None) -> EmailDeliveryResult:
        return self._send(
            template="user_invitation",
            to_email=to_email,
            subject="Invitacion a LEXFLOW",
            payload={"full_name": full_name, "invitation_url": invitation_url},
        )

    def send_password_reset(self, *, to_email: str, reset_url: str | None = None) -> EmailDeliveryResult:
        return self._send(
            template="password_reset",
            to_email=to_email,
            subject="Recuperacion de acceso LEXFLOW",
            payload={"reset_url": reset_url},
        )

    def _send(self, *, template: str, to_email: str, subject: str, payload: dict[str, object]) -> EmailDeliveryResult:
        if not self.settings.email_api_url or not self.settings.email_api_key:
            return EmailDeliveryResult(provider="http_json", status="not_configured")
        body = json.dumps(
            {
                "from": self.settings.email_from,
                "to": to_email,
                "subject": subject,
                "template": template,
                "data": {key: value for key, value in payload.items() if value},
            }
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.settings.email_api_key}",
        }
        req = request.Request(self.settings.email_api_url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=10) as response:
                return EmailDeliveryResult(provider="http_json", status="sent" if 200 <= response.status < 300 else "failed")
        except Exception:
            return EmailDeliveryResult(provider="http_json", status="failed")


def get_email_provider(settings: Settings | None = None) -> EmailProvider:
    resolved = settings or get_settings()
    if resolved.email_provider.lower() == "http_json":
        return EmailHttpJsonProvider(resolved)
    return EmailPreparedProvider()
