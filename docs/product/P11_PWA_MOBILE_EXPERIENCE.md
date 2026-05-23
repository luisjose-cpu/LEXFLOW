# P11 PWA y experiencia movil

## Goal

Create the first mobile experience as a responsive PWA for clients and lawyers, prepared for a future React Native + Expo app without duplicating product logic.

## Client Experience

- `/m/client`
- `/m/client/cases`
- `/m/client/cases/[id]`
- `/m/client/documents`
- `/m/client/messages`
- `/m/client/notifications`

The client mobile surface focuses on authorized cases, status, public timeline, approved documents, hearings, messages, notifications, requests, and next steps.

## Lawyer Experience

- `/m/lawyer`
- `/m/lawyer/cases`
- `/m/lawyer/cases/[id]`
- `/m/lawyer/tasks`
- `/m/lawyer/hearings`
- `/m/lawyer/notifications`

The lawyer mobile surface focuses on assigned cases, alerts, hearings, tasks, communications, documents, judicial updates, AI case summary, and personal dashboard.

## PWA Scope

- Manifest with `/m/client` start URL.
- Service worker with offline fallback.
- Install prompt.
- Mobile bottom tabs.
- Responsive layouts for 375px phone and tablet widths.

## Product Rule

P11 does not create isolated mobile screens. The mobile experience follows the LEXFLOW chain:

`CLIENTE -> EXPEDIENTE -> DOCUMENTO -> COMUNICACION -> AUTOMATIZACION -> IA -> INTELIGENCIA -> DECISION`
