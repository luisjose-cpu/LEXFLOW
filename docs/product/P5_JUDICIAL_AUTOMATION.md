# P5 Actualizacion Judicial Automatizada

## Goal

Register, monitor, and update case records from official or authorized judicial sources while preserving legal compliance, auditability, tenant isolation, and human intervention when a CAPTCHA or access-control checkpoint appears.

## Supported Source Adapters

- PoderJudicialAdapterMock
- CEJAdapterMock
- SINOEAdapterMock
- MPFNAdapterMock

These adapters are mocks for P5. They define the operational contract without touching real judicial systems or bypassing any protection.

## Backend Services

- JudicialSourceService
- JudicialUpdateService
- CaptchaCheckpointService
- JudicialEvidenceService
- JudicialNotificationService

## API Endpoints

- `GET /api/v1/cases/{case_id}/sources`
- `POST /api/v1/cases/{case_id}/sources`
- `POST /api/v1/case-sources/{source_id}/check`
- `GET /api/v1/case-sources/{source_id}/updates`
- `POST /api/v1/captcha-checkpoints/{checkpoint_id}/resolve`
- `POST /api/v1/judicial-updates/{update_id}/approve`
- `POST /api/v1/judicial-updates/{update_id}/reject`

## Frontend Components

- JudicialSourcesPanel
- JudicialUpdateStatusCard
- CaptchaCheckpointModal
- JudicialUpdateTimelineItem
- SourceConfigurationForm
- JudicialUpdatesList

## Human-In-The-Loop Flow

1. A source is checked through an authorized adapter.
2. If the adapter returns `captcha_required=true`, LEXFLOW pauses the source.
3. A judicial update is stored as paused and requires human intervention.
4. Evidence, notification, and audit records are created.
5. A user resolves the CAPTCHA checkpoint manually.
6. The source can return to active monitoring after the checkpoint is audited.

## Product Boundary

P5 does not connect to live judicial portals. Real connectors require source-by-source legal review, rate limits, authorization handling, monitoring, and operational approvals before production use.
