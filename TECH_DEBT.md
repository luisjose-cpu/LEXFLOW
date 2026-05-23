# TECH_DEBT

- Some early P1/P2 compatibility endpoints remain alongside newer `/api/v1` contracts.
- Demo frontend data should be wired to TanStack Query when auth/session UX is finalized.
- Automation execution is synchronous and should move to Celery for production.
- Dashboard aggregates should be cached or materialized for larger tenants.
- AI providers are mock/prepared; production provider usage needs cost controls and prompt/version tracking.
- Billing mock provider needs real provider abstraction hardening before launch.
- Restore tests should become automated once production infra exists.
