# Operational Core Test Results

Date: 2026-05-24

## Scope

Validated the client, case and advanced Expediente 360 operational core, including global search, client profile resources, case resource views and SINOE module consumption.

## Backend Results

- `python -m pytest tests/test_operational_core.py -q`: passed, 4 tests.
- `python -m pytest tests/test_sinoe_integration.py tests/test_case_overview_p4.py tests/test_operational_core.py -q`: passed, 14 tests.
- `python -m pytest -q`: passed, 95 tests.

Coverage includes:

- Global search.
- Client search, profile, timeline, documents, metrics and risk.
- Case documents, hearings, judicial/SINOE, automation and intelligence resources.
- Tenant isolation and cross-tenant blocking.

## Frontend Results

- `npm run lint`: passed.
- `npm run test -- --run components/__tests__/operational-core.test.tsx`: passed, 4 tests.
- `npm run test -- --run`: passed, 41 tests across 16 files.
- `npm run build`: passed, Next.js generated 47 app routes.

Coverage includes:

- Global search autocomplete, recent searches, favorites and advanced result buckets.
- Client detail with cases, documents, risk, timeline and communications.
- Client and case creation wizards.
- Cases dashboard and SINOE resource page without duplicated judicial logic.

## Cloud Readiness

- `npm run cloud:preflight`: passed.

## QA Notes

Automated desktop/tablet/mobile visual QA was not executed in this pass because no browser automation session was available in this turn. Responsive behavior is implemented through Tailwind grid breakpoints and verified through build/type checks.
