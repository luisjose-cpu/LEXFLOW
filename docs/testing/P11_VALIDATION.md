# P11 Validation

## Full Check

```bash
npm run p11:check
```

## Backend Coverage

- Client mobile endpoints.
- Lawyer mobile endpoints.
- Role separation.
- Tenant isolation.
- Client scope.
- Lawyer permissions.

## Frontend Coverage

- `/m/client`.
- `/m/client/cases`.
- `/m/client/cases/[id]`.
- `/m/client/documents`.
- `/m/client/messages`.
- `/m/client/notifications`.
- `/m/lawyer`.
- `/m/lawyer/cases`.
- `/m/lawyer/cases/[id]`.
- `/m/lawyer/tasks`.
- `/m/lawyer/hearings`.
- `/m/lawyer/notifications`.
- Manifest metadata.
- Service worker.
- Offline fallback.

## Manual QA

Verify `/m/client` at 375px and `/m/lawyer` at tablet width. The mobile shell must render styled content, fixed bottom tabs, no horizontal overflow, and role-specific information.
