# SECURITY.md

## Security Baseline

LEXFLOW handles confidential legal information. Security is a product requirement, not a later hardening task.

## Core Requirements

- No hardcoded secrets.
- Tenant isolation is mandatory.
- Authorization is server-side and role-aware.
- Critical actions produce audit logs.
- Sensitive data is not written to logs.
- Production credentials must come from managed secrets or environment configuration.
- Backups must be encrypted or protected by equivalent cloud controls.

## Identity And Access

- Authentication must support firm users and client portal users.
- Authorization must support tenant, role, matter, document, and action boundaries.
- Administrative actions require stronger audit and eventual step-up verification.

## Audit

Audit logs are required for:

- Entity create, update, delete
- Document upload, classification, sharing, deletion
- Communication send and receive events
- Automation trigger and approval
- AI extraction, classification, summary, or recommendation
- Billing, role, permission, and tenant configuration changes

## AI Security

- AI inputs must be authorized.
- AI outputs must be traceable to source material.
- Sensitive prompts and responses must follow retention policy.
- Human review is required for legal decisions and external actions.

## Integration Security

- External provider credentials must be tenant-aware where applicable.
- Webhooks require signature verification.
- Retries must avoid duplicate legal or billing actions.

## P0 Security Status

Security controls are defined as requirements. Implementation is deferred to P1+.
