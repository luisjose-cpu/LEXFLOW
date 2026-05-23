# P13 Automation Security

## Feature Gate

Automation execution requires the `automation_studio` feature gate. START plan tenants are blocked from creating or running workflows.

## Authorization

- Client users cannot access Automation Studio.
- Assistants can read and run approved automations.
- Lawyers can create, update, activate, and run automations.
- Tenant admins and partners have full automation control.

## Audit

Critical actions write `audit_logs`:

- `automation.create_workflow`
- `automation.update_workflow`
- `automation.activate_workflow`
- `automation.delete_workflow`
- `automation.run_workflow`

## Legal Safeguards

Automation must not bypass CAPTCHA, anti-bot rules, professional review, or client visibility controls. Sensitive actions such as case status changes, assignments, and external communications need explicit permissions and future approval gates before production use.
