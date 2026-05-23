# P13 Automation Studio Architecture

## Tables

- `automation_workflows`
- `automation_conditions`
- `automation_actions`
- `automation_runs`
- `automation_run_steps`

Every table is tenant scoped and indexed by tenant, workflow/run identifiers, status, and trigger where relevant.

## Service

`AutomationService` owns:

- Trigger/action catalog.
- Workflow CRUD.
- Workflow activation.
- Feature gate enforcement through BillingService.
- Condition evaluation.
- Action execution.
- Trigger dispatch.
- Run and run step persistence.
- Audit log persistence.

## Endpoint Boundary

All endpoints are under `/api/v1/automation/*`.

- `automation:read`: catalog, workflow list/detail, run history.
- `automation:write`: create/update/delete/activate workflows.
- `automation:run`: run workflows and trigger dispatch.

## Execution Model

P13 execution is synchronous and deterministic for QA. Future production work should move execution to Celery, add retries, idempotency keys, queue visibility, and human approval gates for sensitive actions.
