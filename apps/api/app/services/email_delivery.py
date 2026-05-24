from dataclasses import dataclass


@dataclass(frozen=True)
class EmailDeliveryResult:
    provider: str
    status: str


class EmailProvider:
    def send_user_invitation(self, *, to_email: str, full_name: str, invitation_url: str | None = None) -> EmailDeliveryResult:
        raise NotImplementedError


class EmailPreparedProvider(EmailProvider):
    def send_user_invitation(self, *, to_email: str, full_name: str, invitation_url: str | None = None) -> EmailDeliveryResult:
        return EmailDeliveryResult(provider="email_prepared", status="prepared")


email_provider: EmailProvider = EmailPreparedProvider()
