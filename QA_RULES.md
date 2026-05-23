# QA_RULES.md

## QA Principle

LEXFLOW is not done when it works once. It is done when it is tested, observable, documented, and safe to change.

## Required Checks

- Lint
- Type checks
- Unit tests
- Integration tests
- Build
- Responsive QA
- Visual QA for UI work
- Security review for sensitive changes
- Tenant isolation tests for backend work

## Test Expectations

- New modules include tests.
- Critical workflows include happy path and failure path tests.
- Authorization and tenant boundaries are tested.
- Audit log creation is tested for critical actions.
- AI and automation logic use deterministic fixtures.

## UI QA

Every user-facing screen must include:

- Loading state
- Empty state
- Error state
- Permission state when relevant
- Mobile layout
- Desktop layout
- Accessible labels for controls

## Release Gate

A release candidate requires:

- All checks passing
- No known critical security issue
- No unreviewed data migration
- Updated changelog
- Updated decision and risk records where applicable
