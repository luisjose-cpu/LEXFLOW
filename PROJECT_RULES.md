# PROJECT_RULES.md

## Absolute Rules

- LEXFLOW is a legal operating system, not a screen collection.
- No architecture is improvised.
- No existing code is deleted without explicit authorization.
- No credentials are hardcoded.
- No empty screens are accepted.
- All principal entities are multi-tenant.
- All critical actions write audit logs.
- All modules include tests.
- Nothing is done until lint, tests, build, and QA pass.

## Engineering Rules

- Prefer established local patterns over new abstractions.
- Keep changes small, traceable, and tied to a phase.
- Separate product, architecture, security, UX, cloud, and QA concerns.
- Document every meaningful architectural decision.
- Use structured APIs and parsers where available.
- Avoid broad refactors during feature work.

## Phase Rules

- P0: governance and documentation only.
- P1: foundation implementation only after P0 readiness.
- P2+: product modules, integrations, automation, AI, billing, and hardening by roadmap priority.

## Definition Of Done

A change is done only when:

- Scope is satisfied.
- Tenant and audit requirements are handled.
- Security concerns are reviewed.
- Tests are present and passing.
- Documentation is updated.
- Known risks are listed.
