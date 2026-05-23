# P4 QA Checklist

## Backend

- [x] Overview endpoint returns complete Expediente 360 data.
- [x] Case events can be created.
- [x] Case tasks can be created.
- [x] Case documents can be created.
- [x] Case status can be changed.
- [x] Mutations create persistent audit logs.
- [x] Tenant isolation blocks cross-tenant access.
- [x] Permissions block unauthorized writes.
- [x] Missing cases return 404.

## Frontend

- [x] CaseHeader renders status, risk, responsible, priority, and next actions.
- [x] Timeline renders case activity.
- [x] Documents, hearings, tasks, judicial updates, communications, alerts, audit, and next actions panels render.
- [x] Layout uses 1 column mobile, 2 columns tablet, 3 columns desktop.
- [x] Text does not require horizontal page overflow in visual QA.

## Commands

```bash
npm run p4:check
```

API only:

```bash
cd apps/api
python -m pytest
```

Web only:

```bash
npm run lint
npm run test
npm run build
```
