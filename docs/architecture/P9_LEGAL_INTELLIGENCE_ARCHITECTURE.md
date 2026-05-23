# P9 Legal Intelligence Architecture

## Services

- LegalNewsSourceService: source CRUD and sync orchestration.
- LegalNewsService: news list/detail, AI summary, favorites, and case links.
- LegalAlertService: legal alert listing.
- LegalTagService: tenant-scoped tag registry.
- LegalTrendService: tag-frequency trend calculation.
- LegalNewsAIService: mock AI summary boundary.

## Data Model

- `legal_news_sources`
- `legal_news`
- `legal_news_favorites`
- `legal_news_case_links`
- `legal_alerts`
- `legal_tags`

## Adapter Boundary

Adapters are mock in P9. Production sources must use APIs, RSS, official exports, provider contracts, or integrations that explicitly allow access.

## Expediente 360 Integration

News linked to a case appears in `related_intelligence` in the case overview response and in the frontend `Inteligencia relacionada` panel.
