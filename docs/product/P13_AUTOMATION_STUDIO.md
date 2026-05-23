# P13 Automation Studio

## Goal

Create a no-code legal automation engine using:

`TRIGGER -> CONDITION -> ACTION -> AUDIT -> RESULT`

## Triggers

P13 supports the requested trigger catalog, including case, hearing, document, judicial update, CAPTCHA, client message, task overdue, AI summary, and legal news alert events.

## Actions

P13 supports the requested action catalog with deterministic mock-safe behavior. Some actions create real internal records in the demo environment, including tasks, portal notifications, case events, and AI summary mock jobs.

## Frontend

`/automation` provides a step builder:

- Trigger.
- Conditions.
- Actions.
- Test.
- Activate.
- Audit/result review.

## Product Rule

Automation Studio is not allowed to bypass legal safeguards. Sensitive actions must remain permissioned, tenant scoped, auditable, and reviewable.
