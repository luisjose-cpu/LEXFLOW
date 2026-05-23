# P7 Validation

## Full Check

```bash
npm run p7:check
```

## Backend Coverage

- Template CRUD.
- Template render test.
- WhatsApp mock send.
- Communication audit.
- Notification send/list/mark-read.
- Portal client to lawyer communication bridge.
- Client user blocked from internal communication endpoint.

## Frontend Coverage

- Communication center route.
- Multichannel thread history.
- WhatsApp mock state.
- Required templates.
- Notification rule preview.

## Manual QA

Verify `/communication` on desktop and mobile widths. The page must render with CSS, show WhatsApp mock state, and avoid horizontal overflow.
