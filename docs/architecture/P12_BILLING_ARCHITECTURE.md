# P12 Billing Architecture

## Tables

- `billing_plans`
- `plan_features`
- `tenant_subscriptions`
- `tenant_usage`
- `billing_events`
- `invoices`

All billing runtime entities are tenant scoped. The plan catalog is seeded per tenant so limits and commercial terms can vary safely.

## Service

`BillingService` owns:

- Plan catalog creation.
- Current subscription.
- Trial/mock subscription.
- Plan change.
- Usage meters.
- Feature gate response.
- Mock webhook processing.
- Billing audit records.

## Endpoints

All endpoints are under `/api/v1/billing/*`.

Read endpoints require `billing:read`. Write/mock provider endpoints require `billing:write`.

## Provider Boundary

P12 uses a mock billing provider. Real payment integration must be added behind the service boundary without exposing provider secrets to frontend code or logs.

## Future Production Path

P13 can add deeper automation studio or revenue operations. Real billing provider work should keep idempotency keys, enable `REQUIRE_BILLING_WEBHOOK_SIGNATURE=true`, then add tax rules, payment method vaulting, and dunning policies.
