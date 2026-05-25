# ARCHITECTURE.md

## Architecture Goal

LEXFLOW must be a modular, multi-tenant, cloud-ready SaaS with a governed legal workflow spine.

## System Boundary

Major layers:

- Web/PWA application
- API application
- Database
- Object storage
- Queue and workers
- AI services
- Communication integrations
- Billing integrations
- Observability and audit

## Core Architectural Principles

- Multi-tenant by default.
- Audit by default for critical actions.
- Authorization enforced server-side.
- Clear separation between product modules and shared platform services.
- Cloud-ready interfaces before cloud-specific lock-in.
- Background jobs for slow or external work.
- Observability designed before production.

## Principal Domains

- Tenant
- User and role
- Client
- Matter
- Document
- Communication
- Automation
- AI Insight
- Billing
- Audit Log
- Intelligence Metric

## Data Rules

- Principal tables require `tenant_id`.
- Cross-tenant access is forbidden unless a future platform-admin boundary exists.
- Soft delete should be preferred for legal records.
- Audit logs are append-only.
- Legal documents require storage metadata, access controls, and retention policy.

## API Rules

- APIs must resolve tenant context before data access.
- APIs must validate authorization before mutation.
- Mutations must be audited.
- External integration calls must be idempotent when possible.
- Error responses must avoid leaking sensitive details.

## Frontend Rules

- Screens compose into workflows.
- Global navigation must reflect the legal operating system.
- Mobile-first layout is mandatory.
- Empty, loading, error, and permission states are required.

## P0 Architecture Status

This document defines direction only. P0 does not create new backend, frontend, database, table, or Docker behavior.
# Nivel 2 Commercial Architecture

Nivel 2 agrega una capa comercial sobre el core existente. No duplica Expediente360, SINOE, IA ni Automation: consume sus senales y las agrega en War Room, CRM, Financial, Risk y Demo Mode.

Nuevas tablas: `crm_leads`, `case_financials`, `case_expenses`, `case_hours`, `demo_snapshots`.

Nuevos servicios: `WarRoomService`, `CrmService`, `FinancialEngineService`, `RiskEngineService`, `Level2DemoService`.

# Nivel 3 Legal OS Architecture

Nivel 3 eleva P15 desde una superficie OS final a una capa inteligente persistente. No duplica Expediente360, SINOE, IA ni Nivel 2: consume sus senales y las convierte en memoria, grafo, contexto y recomendaciones auditadas.

Nuevas tablas: `knowledge_vault_items`, `legal_memory_items`, `legal_graph_nodes`, `legal_graph_edges`, `marketplace_items`, `marketplace_installations`, `country_configs`, `ai_agent_runs`.

Nuevos servicios: `DigitalTwinService`, `KnowledgeVaultService`, `LegalMemoryService`, `LegalGraphService`, `ContextEngine`, `RAGPipelineService`, `ManagementCopilotService`, `MarketplaceService`, `LatamReadyService`, `AiAgentsFramework`.

Regla RAG: citar fuentes o declarar ausencia de evidencia. Toda salida IA requiere revision profesional.

# Nivel 4 Enterprise Architecture

Nivel 4 agrega una capa enterprise sobre N1, N2 y N3. No duplica Expediente360, SINOE, portal, IA, automation, memory, graph, copilot ni dashboard: los coordina para organizaciones, grupos, filiales, partners y white-label.

Nuevas tablas: `organizations`, `organization_tenants`, `departments`, `teams`, `team_members`, `legal_data_events`, `orchestration_events`, `enterprise_ai_swarm_runs`, `telemetry_metrics`, `public_api_keys`, `webhook_subscriptions`, `governance_policies`, `evidence_vault_items`, `retention_policies`, `cloud_environments`, `backup_records`, `revenue_insights`.

Nuevos servicios: `EnterpriseMultiOrgService`, `LegalDataPlatformService`, `OrchestrationLayerService`, `EnterpriseAiSwarmService`, `TelemetryCenterService`, `RevenueGrowthService`, `ApiIntegrationPlatformService`, `GovernanceOSService`, `LexflowCloudService`.

Regla enterprise: analytics cross-tenant debe ser agregado y autorizado; memoria, documentos, embeddings y secretos permanecen aislados por tenant salvo politica explicita y auditada.
