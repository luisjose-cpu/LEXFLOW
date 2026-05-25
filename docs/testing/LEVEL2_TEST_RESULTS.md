# LEVEL2 Test Results

Fecha: 2026-05-24

## Ejecutado

- `python -m pytest tests/test_level2_commercial_modules.py -q`
  - 3 passed.
- `npm --workspace apps/web run test -- components/__tests__/level2-commercial.test.tsx`
  - 1 file passed.
  - 5 tests passed.
- `python -m pytest -q`
  - 158 passed.
- `npm run test`
  - 25 files passed.
  - 87 tests passed.
- `npm run lint`
  - Passed without warnings after cleanup.
- `npm run build`
  - Passed.
  - Next.js generated 63 routes, including `/war-room`, `/crm`, `/financial`, `/risk` and `/demo`.
- Browser visual QA on local Next dev server `http://localhost:3050`
  - `/war-room`: rendered, no horizontal overflow detected.
  - `/crm`: rendered, no horizontal overflow detected.
  - `/financial`: rendered, no horizontal overflow detected.
  - `/risk`: rendered, no horizontal overflow detected.
  - `/demo`: rendered, no horizontal overflow detected.

## Pendiente de validacion global

- E2E browser cloud.
