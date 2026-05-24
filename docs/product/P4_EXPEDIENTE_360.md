# P4 Expediente 360

## Goal

Create the star screen for LEXFLOW: one legal matter workspace that connects client, case, documents, hearings, tasks, judicial updates, communications, alerts, audit, and next actions.

## Backend Endpoints

- `GET /api/v1/cases/{case_id}/overview`
- `POST /api/v1/cases/{case_id}/events`
- `POST /api/v1/cases/{case_id}/tasks`
- `PATCH /api/v1/cases/{case_id}/tasks/{task_id}`
- `POST /api/v1/cases/{case_id}/documents`
- `PATCH /api/v1/cases/{case_id}/documents/{document_id}`
- `POST /api/v1/cases/{case_id}/hearings`
- `PATCH /api/v1/cases/{case_id}/hearings/{hearing_id}`
- `POST /api/v1/cases/{case_id}/status`
- `POST /api/v1/cases/{case_id}/communications`
- `POST /api/v1/ai/cases/{case_id}/summary`
- `POST /api/v1/case-sources/{source_id}/sinoe/check`

## Frontend Route

Primary working route:

- `apps/web/app/cases/[id]/page.tsx`

Requested mirror path:

- `apps/web/src/app/cases/[id]/page.tsx`

## Components

- CaseHeader
- Case360Workspace
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

- Desktop: workspace 2 columns with primary timeline/resources and right operational rail
- Tablet: 2 columns
- Mobile: 1 column

## Functional Workspace

The route now uses `Case360Workspace`:

- Loads live `GET /cases/{case_id}/overview` when a tenant session exists.
- Falls back to safe demo data when no session/API is available.
- Creates timeline notes, tasks with due dates, documents, hearings and portal communications.
- Advances the lifecycle of tasks, hearings and documents from the right operational rail.
- Runs case AI summary with the mandatory professional review disclaimer.
- Consumes the existing SINOE module for manual source checks and CAPTCHA human-in-the-loop flow.
- Refreshes the case overview after each successful action.
- Keeps all critical mutations audited server-side.

## P5/P26 Priority

Continue tightening document byte upload UX, hearing result/acta capture, task checklist versioning and production E2E coverage.
