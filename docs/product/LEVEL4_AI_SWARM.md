# LEVEL4_AI_SWARM

Enterprise AI Swarm coordina agentes con permisos, memoria, contexto, handoff, audit y revision humana.

## Agentes preparados

LegalAgent, CaseAgent, HearingAgent, ResearchAgent, DocumentAgent, ClientAgent, ManagementAgent, RiskAgent, AutomationAgent y NewsAgent.

## Reglas

- No autonomia completa.
- Salidas con `review_required`.
- Contexto tenant-scoped.
- Audit log por ejecucion.
- Citas cuando usa RAG/contexto.
