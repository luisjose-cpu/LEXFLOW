# P12 Validation

## Full Check

```bash
npm run p12:check
```

## Backend Coverage

- Plan catalog.
- Feature gates.
- Current trial subscription.
- Subscribe mock.
- Change plan.
- Usage meters.
- Billing audit logs.
- Mock webhook.
- Billing permissions.
- Tenant scope.

## Frontend Coverage

- `/pricing`.
- `/onboarding`.
- `/settings/billing`.
- `/settings/usage`.
- `/settings/features`.
- PricingCards.
- PlanFeatureTable.
- SubscriptionStatusCard.
- UsageMeter.
- UpgradePrompt.
- OnboardingWizard.

## Manual QA

Verify pricing on desktop, billing settings on tablet, and usage/features on mobile widths. The UI must render styled information, avoid horizontal overflow, and clearly distinguish active gates from upgrade-required gates.
