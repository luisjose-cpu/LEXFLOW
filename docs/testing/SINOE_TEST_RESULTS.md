# SINOE Test Results

## Automated Coverage

Backend:

- encrypted credential persistence
- no password in API responses
- mock connection test
- SINOE case source linking
- successful mock update
- judicial update creation
- case event creation
- notification creation
- audit log creation
- CAPTCHA detection
- CAPTCHA checkpoint creation
- manual checkpoint resolution
- RBAC block for `client_user`
- cross-tenant block

Frontend:

- Settings SINOE render
- credential save flow
- connection status
- SINOE source in Expediente 360
- review action
- CAPTCHA modal
- update history
- loading/error/empty-adjacent states through component rendering

## Commands

```bash
cd apps/api
python -m pytest tests/test_sinoe_integration.py -q
```

```bash
cd apps/web
npm run test -- --run components/__tests__/sinoe-integration.test.tsx components/__tests__/case-360.test.tsx
```

## Latest Local Result

- Backend targeted SINOE suite: passed
- Frontend targeted SINOE suite: passed
- Backend full suite: 91 passed
- Web full suite: 15 files / 37 tests passed
- Web lint: passed
- Web production build: passed
- Alembic upgrade to head with SINOE migration: passed
- Cloud preflight: passed

Refresh this document on each release candidate or cloud deploy.
