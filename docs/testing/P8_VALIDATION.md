# P8 Validation

## Full Check

```bash
npm run p8:check
```

## Backend Coverage

- OCR job creation.
- Document summary.
- Document classification.
- Structured extraction.
- Case summary.
- Case search.
- AI job lookup.
- Human approve and reject.
- RBAC blocking for client users.
- Tenant isolation.
- AI usage audit events.

## Frontend Coverage

- Practical AI route `/ai`.
- Mandatory disclaimer.
- Document pipeline.
- Case intelligence.
- Human review queue.
- Prompt inventory.

## Manual QA

Verify `/ai` on desktop and mobile widths. The page must render with CSS, avoid horizontal overflow, show the review disclaimer, and expose prompt-versioned AI capabilities without implying autonomous legal decisions.
