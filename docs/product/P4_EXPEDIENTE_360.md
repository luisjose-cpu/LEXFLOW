# P4 Expediente 360

## Goal

Create the star screen for LEXFLOW: one legal matter workspace that connects client, case, documents, hearings, tasks, judicial updates, communications, alerts, audit, and next actions.

## Backend Endpoints

- `GET /api/v1/cases/{case_id}/overview`
- `POST /api/v1/cases/{case_id}/events`
- `POST /api/v1/cases/{case_id}/tasks`
- `POST /api/v1/cases/{case_id}/documents`
- `POST /api/v1/cases/{case_id}/status`

## Frontend Route

Primary working route:

- `apps/web/app/cases/[id]/page.tsx`

Requested mirror path:

- `apps/web/src/app/cases/[id]/page.tsx`

## Components

- CaseHeader
- ClientSummaryCard
- RiskBadge
- StatusBadge
- CaseTimeline
- DocumentsPanel
- HearingsPanel
- TasksPanel
- JudicialUpdatesPanel
- CommunicationsPanel
- AlertsPanel
- AuditSummaryPanel
- NextActionsPanel

## Layout

- Desktop: 3 columns
- Tablet: 2 columns
- Mobile: 1 column

## P5 Priority

Add authorized judicial source monitoring, CAPTCHA checkpoints, evidence, notifications, and approval/rejection flows directly inside Expediente 360.
