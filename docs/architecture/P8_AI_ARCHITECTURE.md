# P8 AI Architecture

## Services

- AIService: facade for route-level AI actions.
- OCRService: OCR orchestration.
- DocumentAnalysisService: summary, classification, and extraction.
- CaseSummaryService: case summary and search.
- AIJobService: job persistence, lookup, approval, and rejection.
- AIUsageAuditService: audit trail for AI usage.

## Providers

- MockOCRProvider: active P8 OCR provider.
- FutureCloudOCRProvider: production-ready boundary placeholder.
- MockLLMProvider: active P8 language provider.
- OpenAILLMProvider: prepared production provider boundary without hardcoded credentials.

## Data Model

`ai_jobs` stores tenant, case, document, type, status, provider, result JSON, reviewer, review note, and timestamps.

## Endpoint Boundary

All P8 endpoints live under `/api/v1/ai`. They require internal authenticated users and AI-specific RBAC permissions.

## Audit

P8 writes audit events for AI job creation, approval, and rejection.
