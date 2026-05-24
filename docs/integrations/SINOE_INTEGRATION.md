# SINOE Integration

## Scope

LEXFLOW supports a governed SINOE integration surface for tenants that have authorized credentials for `https://casillas.pj.gob.pe/sinoe/login.xhtml`.

The first implementation uses `SinoeAdapterMock`. It does not connect to the real SINOE site, does not bypass CAPTCHA, and does not automate human verification.

## Product Flow

1. A tenant admin or partner opens `Settings -> Integraciones -> SINOE`.
2. The user saves authorized SINOE credentials.
3. The backend encrypts username and password before persistence.
4. A case is linked to a SINOE source from Expediente 360.
5. A manual or scheduled check runs through `SinoeAutomationService`.
6. Mock updates become `judicial_updates`, `case_events`, notifications, evidence and audit logs.
7. If CAPTCHA is detected, automation pauses and creates a `captcha_checkpoint`.

## Backend

Endpoints:

- `POST /api/v1/settings/integrations/sinoe`
- `GET /api/v1/settings/integrations/sinoe`
- `DELETE /api/v1/settings/integrations/sinoe`
- `POST /api/v1/settings/integrations/sinoe/test`
- `POST /api/v1/cases/{case_id}/sources/sinoe`
- `POST /api/v1/case-sources/{source_id}/sinoe/check`
- `GET /api/v1/case-sources/{source_id}/sinoe/updates`
- `POST /api/v1/captcha-checkpoints/{checkpoint_id}/resolve`

Core service:

- `SinoeAutomationService`
- `SinoeAdapter`
- `SinoeAdapterMock`
- `CredentialCipher`

## Frontend

Routes and components:

- `/settings/integrations/sinoe`
- `SettingsSinoeIntegration`
- `SinoeCredentialsForm`
- `SinoeConnectionStatus`
- `SinoeCaseSourceForm`
- `SinoeUpdatePanel`
- `CaptchaCheckpointModal`
- `SinoeUpdateHistory`

Expediente 360 shows SINOE sources, last review, last result, CAPTCHA status, review action and history.

## Current Limitations

- Real SINOE adapter is intentionally not implemented.
- Global bulk update button is represented in Settings, while actual checks run per case source.
- CAPTCHA resolution is recorded after manual intervention; LEXFLOW does not solve it.
