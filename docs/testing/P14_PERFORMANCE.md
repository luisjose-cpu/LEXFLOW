# P14 Performance

## Targets

| Surface | Target |
| --- | --- |
| Dashboard overview | < 2s |
| Expediente 360 overview | < 1s |
| Timeline | < 1s |
| Search | < 2s |
| Portal | < 2s |

## RC1 State

The current RC1 runs deterministic local/demo data and Next.js static routes for most frontend surfaces. API responses include `X-Response-Time-Ms` to support measurement in QA and pilot environments.

## Local RC1 Smoke Evidence

Measured against `next start` on localhost after production build:

| Surface | Local Load |
| --- | --- |
| `/dashboard` | 889ms |
| `/cases/case-demo` | 879ms |
| `/portal` mobile viewport | 695ms |
| `/automation` mobile viewport | 744ms |

All measured surfaces rendered styled content with no horizontal overflow.

## Required Pilot Measurements

- Capture p50/p95 response times for `/api/v1/dashboard/overview`.
- Capture p50/p95 response times for `/api/v1/cases/{case_id}/overview`.
- Capture p50/p95 response times for portal case detail.
- Capture frontend route load time for `/dashboard`, `/cases/[id]`, `/portal`, `/automation`.

## Optimization Plan

- Cache dashboard aggregates once tenant volume increases.
- Add database indexes during migration review for high-cardinality filters.
- Move automation and AI execution to Celery for long-running jobs.
- Add CDN/static cache policy for web assets.
