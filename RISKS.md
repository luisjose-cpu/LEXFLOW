# RISKS.md

## Risk Register

| ID | Risk | Impact | Probability | Mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| R-001 | Product scope becomes too broad for early phases | High | High | Enforce roadmap and phase gates | Open |
| R-002 | Tenant isolation is missed in early models | Critical | Medium | Require tenant design and tests in P1 | Open |
| R-003 | Audit logging is added inconsistently | High | Medium | Create shared audit service and test policy | Open |
| R-004 | UI becomes a set of isolated screens | High | Medium | Enforce product spine and workflow reviews | Open |
| R-005 | Legal AI produces unreviewed legal conclusions | Critical | Medium | Require source traceability and human review | Open |
| R-006 | WhatsApp or judicial automation causes unauthorized external action | Critical | Medium | Require explicit authorization, idempotency, and audit | Open |
| R-007 | Security is delayed until late hardening | Critical | Medium | Treat security as P1 platform requirement | Open |
| R-008 | Billing and tenant lifecycle are bolted on too late | High | Medium | Include SaaS billing architecture before production | Open |
| R-009 | Cloud costs or complexity grow too early | Medium | Medium | Start cloud-ready, not cloud-overbuilt | Open |
| R-010 | Existing pre-P0 scaffold diverges from governance | Medium | Medium | Review and align scaffold before P1 implementation | Open |

## Immediate Improvements

- Create P1 scope with strict acceptance criteria.
- Define canonical tenant context and audit interfaces before feature work.
- Add security threat model before integrations.
- Decide migration strategy before persistent database work.
- Define UX navigation model around the product spine.
