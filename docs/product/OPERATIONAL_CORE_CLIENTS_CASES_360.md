# Operational Core: Clients, Cases And Expediente 360

Date: 2026-05-24

## Objective

Create the operational nucleus of LEXFLOW:

`CLIENTE -> EXPEDIENTE -> EXPEDIENTE 360 -> DOCUMENTOS -> AUDIENCIAS -> SINOE -> COMUNICACIONES -> IA -> AUTOMATIZACIONES -> INTELIGENCIA -> DECISIONES`

## Product Scope

The module adds a global search layer, richer client management, case management and advanced case resource views. Judicial updates are not reimplemented here; they consume the existing SINOE Automation Module.

## Frontend Surfaces

- `/clients`
- `/clients/create`
- `/clients/[id]`
- `/clients/[id]/edit`
- `/cases`
- `/cases/create`
- `/cases/[id]/edit`
- `/cases/[id]/documents`
- `/cases/[id]/hearings`
- `/cases/[id]/communications`
- `/cases/[id]/judicial`
- `/cases/[id]/automation`
- `/cases/[id]/intelligence`

## Core Components

- `SearchGlobalBar`
- `ClientList`
- `ClientSearch`
- `ClientCard`
- `ClientDetail`
- `ClientEditForm`
- `ClientOnboardingWizard`
- `ClientDocuments`
- `ClientCasesGrid`
- `ClientTimeline`
- `ClientTags`
- `ClientRiskPanel`
- `ClientNotes`
- `ClientCommunications`
- `ClientMetrics`
- `CasesDashboard`
- `CaseCreateWizard`
- `CaseEditForm`
- `CaseResourcePage`

## Backend Contracts

- `GET /api/v1/dashboard/search`
- `GET /api/v1/clients/search`
- `GET /api/v1/clients/{client_id}/profile`
- `GET /api/v1/clients/{client_id}/timeline`
- `GET /api/v1/clients/{client_id}/documents`
- `GET /api/v1/clients/{client_id}/communications`
- `GET /api/v1/clients/{client_id}/metrics`
- `GET /api/v1/clients/{client_id}/risk`
- `GET /api/v1/cases/search`
- `GET /api/v1/cases/{case_id}/documents`
- `GET /api/v1/cases/{case_id}/hearings`
- `GET /api/v1/cases/{case_id}/judicial`
- `GET /api/v1/cases/{case_id}/automation`
- `GET /api/v1/cases/{case_id}/intelligence`

## SINOE Integration Rule

The judicial case panel uses existing `case_sources`, `judicial_updates` and CAPTCHA checkpoint concepts. It reports SINOE status, last synchronization, evidence hash, pending human verification and update history without duplicating SINOE login, CAPTCHA or adapter logic.

## Current Limitations

- Some frontend operational details use deterministic demo data until the web app consumes the new backend endpoints directly.
- Real document upload, OCR and AI execution remain delegated to existing document and AI modules.
- E2E browser validation should be run after the next cloud deployment against Vercel and Render.
