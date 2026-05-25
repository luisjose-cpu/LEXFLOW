# LEVEL3_RISK_REPORT

## Security

- Tenant isolation is enforced through request tenant resolution and RBAC dependencies.
- Memory, graph, knowledge and RAG endpoints are scoped by `tenant_id`.
- AI outputs remain review-required and do not make legal decisions.

## Product Risks

- Indexed memory quality depends on OCR/document extraction maturity.
- RAG confidence is deterministic for pilot and not a substitute for external legal review.
- LATAM registry is structural; real court adapters require authorized integrations.

## Mitigations

- Audit logs are created for knowledge creation, memory indexing, RAG, copilot, graph relationships, marketplace installs, LATAM defaults and agent runs.
- Every AI response includes professional review guardrails.
- No CAPTCHA bypass or anti-bot evasion is introduced.
