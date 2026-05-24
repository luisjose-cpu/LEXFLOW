# CAPTCHA Human In The Loop

## Policy

LEXFLOW must not evade CAPTCHA, break anti-bot measures or automate CAPTCHA resolution.

When a provider asks for human verification, the system must:

1. Pause automation.
2. Create a `captcha_checkpoint`.
3. Notify an authorized user.
4. Show a human verification message.
5. Allow the authorized user to complete verification outside automated solving.
6. Record resolution metadata.
7. Continue only after human intervention.
8. Write audit logs and evidence.

## SINOE Behavior

`SinoeAdapterMock` can simulate CAPTCHA by using an external case number containing `CAPTCHA`.

The resulting flow creates:

- `JudicialUpdate` with `captcha_required=true`
- `CaptchaCheckpoint` with `provider=SINOE`
- in-app notification
- evidence payload with `policy=human_in_the_loop_no_captcha_bypass`
- audit event `sinoe_captcha_checkpoint_created`

## Forbidden

- OCR-based CAPTCHA solving
- third-party CAPTCHA solving services
- hidden browser automation to complete CAPTCHA
- aggressive scraping or bot evasion
- credential logging

## Allowed

- Authorized credential storage
- Manual user verification
- Mock adapter tests
- Official APIs, RSS, or integrations when available and permitted
- Audit and evidence capture that does not expose secrets
