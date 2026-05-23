# P8 AI Safety

## Rules

- AI does not make legal decisions.
- Every output includes `Requiere revisión profesional.`
- No provider credentials are hardcoded.
- OpenAILLMProvider is prepared as a boundary, not enabled with secrets.
- AI endpoints are tenant scoped.
- Client users cannot access internal AI endpoints.
- Professional review is required before accepting AI output.

## Data Handling

- Use tenant-scoped document and case lookups.
- Do not expose another tenant's data through AI jobs, search, or summaries.
- Store provider metadata, result JSON, and audit events.
- Avoid storing secrets in prompts, logs, fixtures, or frontend demo data.

## Future Production Requirements

- Add provider rate limits and retry policy.
- Add redaction and retention controls.
- Add model/version tracking.
- Add token and cost accounting.
- Add prompt change review workflow.
