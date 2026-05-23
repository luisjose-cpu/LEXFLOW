# P10 Command Center Architecture

## Services

- DashboardService: composed executive overview.
- KPIService: operational KPI aggregation.
- RiskService: risk score and critical cases.
- ProductivityService: task and workload analytics.
- CommandCenterService: executive snapshot and decision queue.
- LegalTrendAnalyticsService: intelligence trend analytics.
- JudicialMonitoringAnalyticsService: source/update/CAPTCHA analytics.
- AIAnalyticsService: AI job analytics.
- CommunicationAnalyticsService: channel analytics.

## Endpoints

All endpoints are under `/api/v1/dashboard/*` and require `dashboard:read`.

## Data Strategy

P10 uses existing tenant-scoped entities. No separate analytics warehouse is introduced yet.

## Future Production Path

P11 can add caching, materialized snapshots, schedule-based aggregates, and exports once usage volume justifies it.
