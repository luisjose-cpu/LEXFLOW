# P6 Validation

## Full Check

```bash
npm run p6:check
```

## Backend Coverage

- Client user can resolve portal profile.
- Client sees only its own cases.
- Cross-client case access returns 404.
- Private documents remain hidden.
- Other-client documents remain hidden.
- Internal events remain hidden.
- Pending judicial updates remain hidden.
- Messages and uploads are created and audited.
- Notifications and reports are client scoped.
- Non-client roles cannot use portal endpoints.

## Frontend Coverage

- Portal login renders.
- Portal dashboard renders.
- Portal case detail renders timeline, documents, hearings, and messages.
- Demo data excludes internal strategy and unapproved updates.

## Manual Responsive QA

Verify `/portal` and `/portal/cases/portal-case-1` on desktop and mobile widths. There must be no horizontal overflow.
