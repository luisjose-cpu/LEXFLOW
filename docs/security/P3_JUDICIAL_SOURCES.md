# P3 Judicial Sources And CAPTCHA Policy

## Principle

LEXFLOW may support authorized judicial updates, but it must not evade CAPTCHA or access controls.

## CAPTCHA Rule

If a source returns `captcha_required=true`:

1. Pause the source check.
2. Mark the source status as `paused_captcha`.
3. Create a judicial update with `requires_human_intervention=true`.
4. Notify the responsible user or tenant.
5. Write an audit log.
6. Do not retry in a way that attempts to bypass CAPTCHA.

## Implemented Helper

`app.db.judicial_updates.record_judicial_update`

The helper enforces the P3 CAPTCHA behavior and stores the policy in `raw_payload` and audit metadata.

## P4 Security Work

- Add source-specific authorization configuration.
- Add rate limits.
- Add robots/legal compliance review per source.
- Add human confirmation UI.
- Add signed source credentials where applicable.
- Add operational alerting for paused judicial sources.
