# P9 Validation

## Full Check

```bash
npm run p9:check
```

## Backend Coverage

- Sources list/create/sync.
- Mock adapter sync.
- News list and detail.
- AI summary.
- Favorites.
- Link to case.
- Alerts.
- Trends.
- Audit events.
- Permissions.
- Tenant isolation.
- Expediente 360 related intelligence.

## Frontend Coverage

- `/legal-intelligence` dashboard.
- Source inventory.
- News cards.
- AI summary boxes.
- Favorite and link buttons.
- Alert panel.
- Trend chart.
- Expediente 360 related intelligence panel.

## Manual QA

Verify `/legal-intelligence` and `/cases/{id}` on desktop and mobile widths. Pages must render with CSS, avoid horizontal overflow, show source policy context, and keep the intelligence flow connected to cases.
