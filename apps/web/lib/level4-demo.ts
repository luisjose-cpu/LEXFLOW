export const enterpriseMetrics = [
  { label: "Organizaciones", value: "4", trend: "holding + filiales" },
  { label: "Tenants conectados", value: "18", trend: "multi pais" },
  { label: "Eventos indexados", value: "42k", trend: "data platform" },
  { label: "Health enterprise", value: "91", trend: "operacion estable" },
];

export const organizations = [
  { name: "LEXFLOW Enterprise Group", country: "LATAM", tenants: 8, risk: "medio", plan: "Enterprise" },
  { name: "Nova Legal Holding", country: "PE", tenants: 4, risk: "bajo", plan: "AI" },
  { name: "Andes Legal Ops", country: "CO", tenants: 3, risk: "alto", plan: "Enterprise" },
];

export const dataEvents = [
  { type: "case.updated", entity: "Cobro ejecutivo Nova", status: "indexed", source: "Expediente360" },
  { type: "sinoe.update.approved", entity: "Laboral colectivo Andes", status: "processed", source: "SINOE" },
  { type: "ai.summary.completed", entity: "Contrato marco Mercurio", status: "review", source: "IA" },
  { type: "automation.failed", entity: "Recordatorio audiencia", status: "alert", source: "Automation" },
];

export const orchestrationRules = [
  "SINOE_UPDATE_APPROVED -> timeline + portal + memory + dashboard",
  "CASE_RISK_ESCALATED -> partner alert + copilot context",
  "AI_SUMMARY_COMPLETED -> human review + audit + memory",
  "CLIENT_MESSAGE_RECEIVED -> lawyer alert + workflow evaluation",
];

export const aiSwarmAgents = [
  { name: "LegalAgent", signal: "contexto juridico", status: "ready" },
  { name: "RiskAgent", signal: "priorizacion riesgo", status: "active" },
  { name: "ManagementAgent", signal: "insight ejecutivo", status: "active" },
  { name: "AutomationAgent", signal: "acciones coordinadas", status: "guarded" },
  { name: "NewsAgent", signal: "impacto normativo", status: "ready" },
];

export const telemetryRows = [
  { component: "API", metric: "p95 latency", value: "210 ms", status: "healthy" },
  { component: "SINOE", metric: "sync success", value: "98%", status: "healthy" },
  { component: "AI", metric: "tokens month", value: "12.4k", status: "watch" },
  { component: "Workers", metric: "failed jobs", value: "2", status: "watch" },
  { component: "Storage", metric: "verified docs", value: "94%", status: "healthy" },
];

export const revenueSignals = [
  { signal: "Trial conversion", score: 86, action: "activar propuesta enterprise" },
  { signal: "Upsell IA", score: 78, action: "ampliar limite tokens" },
  { signal: "Churn risk", score: 24, action: "mantener monitoreo" },
];

export const integrationCards = [
  { name: "Public API", status: "prepared", detail: "API keys, scopes y rate limits tenant-scoped." },
  { name: "Webhooks", status: "ready", detail: "Eventos de expediente, SINOE, IA y automation." },
  { name: "OAuth", status: "future-ready", detail: "Google y Microsoft preparados para autorizacion futura." },
  { name: "Firma digital", status: "future", detail: "Registry listo sin proveedor productivo." },
];

export const governancePolicies = [
  { name: "Revision humana IA", type: "ai_review", status: "active" },
  { name: "Retencion documental 10 anos", type: "retention", status: "active" },
  { name: "Intervencion soporte temporal", type: "support_access", status: "active" },
];

export const cloudEnvironments = [
  { name: "Staging", region: "us-east", status: "healthy", backup: "daily" },
  { name: "Production", region: "us-east", status: "prepared", backup: "pending go-live" },
  { name: "DR Future", region: "southamerica", status: "roadmap", backup: "planned" },
];
