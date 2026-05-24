# Nivel 1 Test Results

Fecha: 2026-05-24

## Backend

Comando:

```powershell
python -m pytest tests/test_case_overview_p4.py tests/test_sinoe_integration.py tests/test_client_portal_p6.py tests/test_communication_p7.py tests/test_command_center_p10.py tests/test_ai_practical_p8.py tests/test_automation_studio_p13.py tests/test_operational_core.py -q
```

Resultado:

- 37 tests passed.

## Frontend

Comando:

```powershell
npm --workspace apps/web run test -- components/__tests__/case-360.test.tsx components/__tests__/case-360-workspace.test.tsx components/__tests__/sinoe-integration.test.tsx components/__tests__/client-portal.test.tsx components/__tests__/communication-center.test.tsx components/__tests__/legal-command-center.test.tsx components/__tests__/ai-practical.test.tsx components/__tests__/automation-studio.test.tsx components/__tests__/operational-core.test.tsx
```

Resultado:

- 9 test files passed.
- 28 tests passed.

## Lint

Comando:

```powershell
npm run lint
```

Resultado:

- Passed.

## Build

Comando:

```powershell
npm run build
```

Resultado:

- Passed.
- Next.js generated 59 static/dynamic routes successfully.

## Diff hygiene

Comando:

```powershell
git diff --check
```

Resultado:

- Passed.
- Warning only: line-ending normalization notice for `CHANGELOG.md`.

## Conclusion

Nivel 1 queda validado como **PILOT_READY_WITH_MOCKS**.

