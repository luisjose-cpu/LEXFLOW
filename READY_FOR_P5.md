# READY_FOR_P5.md

## Status

LEXFLOW P4 is ready for P5 after validation passes.

## P5 Recommended Scope

P5 should connect authenticated frontend data flows and start Portal Cliente / communication workflows:

- Frontend auth session
- API client with bearer token
- Expediente 360 live data from `/overview`
- Mutation forms for events, tasks, documents, and status
- Portal Cliente read-only case view
- WhatsApp message timeline
- Notification center
- Error/loading/permission UI states backed by API responses

## P5 Entry Criteria

- P4 backend endpoints pass tests.
- P4 frontend components pass tests.
- Expediente 360 route builds.
- Tenant and permission tests pass.
- Audit mutation tests pass.

## P5 Exit Criteria

- A user can log in from web.
- Expediente 360 renders live backend data.
- User can create event/task/document/status update from UI.
- Portal Cliente uses restricted client permissions.
- Communication panel reads real message data.
- QA covers loading, error, empty, permission, desktop, tablet, and mobile states.
