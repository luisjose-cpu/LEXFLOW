# P13 Validation

## Full Check

```bash
npm run p13:check
```

## Backend Coverage

- Workflow CRUD.
- Trigger catalog.
- Workflow activation.
- Condition pass/skip behavior.
- Action execution.
- Run and run step persistence.
- Feature gate blocking.
- Permissions.
- Audit logs.

## Frontend Coverage

- `/automation`.
- Builder step sequence.
- Trigger catalog.
- Action catalog.
- Workflow preview.
- Test result.
- Audit/result chain.

## Manual QA

Verify `/automation` on desktop and mobile widths. The builder must render styled content, avoid horizontal overflow, and clearly show the chain `TRIGGER -> CONDITION -> ACTION -> AUDIT -> RESULT`.
