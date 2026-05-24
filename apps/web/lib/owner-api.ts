import {
  OwnerPlan,
  OwnerTenant,
  ownerAuditLogs,
  ownerDashboardMetrics,
  ownerDemos,
  ownerFeatureFlags,
  ownerInterventions,
  ownerPlans,
  ownerSystemChecks,
  ownerTickets
} from "@/lib/owner-demo";
import { API_URL } from "@/lib/lexflow-api";

export { API_URL };

export function getOwnerAccessToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("lexflow.owner_access_token") ?? "";
}

export function hasOwnerSession() {
  return Boolean(getOwnerAccessToken());
}

export async function ownerApiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getOwnerAccessToken();
  const response = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {})
    }
  });

  if (!response.ok) throw new Error(`LEXFLOW Owner API error ${response.status}`);
  return (await response.json()) as T;
}

type ApiOwnerDashboard = {
  tenants?: { active?: number; trial?: number; suspended?: number; total?: number };
  revenue?: { mrr_cents?: number; arr_cents?: number; churn?: string };
  support?: { open_tickets?: number; sla_risk?: number };
  usage?: { ai_tokens?: number; whatsapp_messages?: number; storage_mb?: number };
};

type ApiOwnerTenant = {
  id: string;
  name: string;
  slug: string;
  status: string;
  plan: string;
  users?: number;
  cases?: number;
  health_score?: number;
  features?: { feature_key: string; enabled: boolean }[];
  usage?: { totals?: { users?: number; cases?: number; documents?: number }; metrics?: { metric_key: string; used: number }[] };
  health?: { score?: number };
};

type ApiOwnerPlan = {
  code?: string;
  name?: string;
  monthly_price_cents?: number;
  status?: string;
  limits?: Record<string, unknown>;
};

export async function loadOwnerDashboard() {
  const body = await ownerApiRequest<ApiOwnerDashboard>("/owner/dashboard");
  const mrr = Math.round((body.revenue?.mrr_cents ?? 0) / 100);
  const arr = Math.round((body.revenue?.arr_cents ?? 0) / 100);
  return [
    { label: "Tenants activos", value: String(body.tenants?.active ?? 0), trend: `${body.tenants?.trial ?? 0} trial, ${body.tenants?.suspended ?? 0} suspendido` },
    { label: "MRR", value: `$${mrr}`, trend: `ARR $${arr}` },
    { label: "Tickets abiertos", value: String(body.support?.open_tickets ?? 0), trend: `${body.support?.sla_risk ?? 0} SLA riesgo` },
    { label: "Uso IA", value: `${Math.round((body.usage?.ai_tokens ?? 0) / 1000)}k`, trend: "tokens este mes" }
  ];
}

export async function loadOwnerTenants(): Promise<OwnerTenant[]> {
  const body = await ownerApiRequest<ApiOwnerTenant[]>("/owner/tenants");
  return body.map(normalizeOwnerTenant);
}

export async function loadOwnerTenantDetail(tenantId: string): Promise<OwnerTenant> {
  const body = await ownerApiRequest<ApiOwnerTenant>(`/owner/tenants/${tenantId}`);
  return normalizeOwnerTenant(body);
}

export async function loadOwnerTenantUsage(tenantId: string) {
  const body = await ownerApiRequest<{ totals?: Record<string, number>; metrics?: { metric_key: string; used: number }[] }>(`/owner/tenants/${tenantId}/usage`);
  const totals = body.totals ?? {};
  const metrics = Object.fromEntries((body.metrics ?? []).map((item) => [item.metric_key, item.used]));
  return [
    ["Usuarios", totals.users ?? 0, 40],
    ["Expedientes", totals.cases ?? 0, 1500],
    ["Documentos", totals.documents ?? 0, 5000],
    ["Storage MB", metrics.storage_mb ?? 0, 102400],
    ["IA tokens", Math.round((metrics.ai_tokens ?? 0) / 1000), 1000],
    ["WhatsApp", metrics.whatsapp_messages ?? 0, 5000],
    ["SINOE syncs", metrics.sinoe_syncs ?? 0, 1000]
  ] as const;
}

export async function loadOwnerFeatures(tenantId: string) {
  const body = await ownerApiRequest<{ feature_key: string; enabled: boolean }[]>(`/owner/tenants/${tenantId}/features`);
  return body;
}

export async function loadOwnerPlans(): Promise<OwnerPlan[]> {
  const body = await ownerApiRequest<ApiOwnerPlan[]>("/owner/plans");
  return body.map((plan) => ({
    name: plan.code ?? plan.name ?? "PLAN",
    monthly: Math.round((plan.monthly_price_cents ?? 0) / 100),
    yearly: Math.round(((plan.monthly_price_cents ?? 0) * 12) / 100),
    status: plan.status === "active" ? "active" : "draft",
    limits: Object.entries(plan.limits ?? {}).map(([key, value]) => `${key}: ${value}`),
    features: ["Feature gates API"]
  }));
}

export async function loadOwnerTickets() {
  const body = await ownerApiRequest<{ id: string; tenant_id?: string | null; priority: string; status: string; category: string; title: string }[]>("/owner/support/tickets");
  return body.map((ticket) => ({ ...ticket, tenant: ticket.tenant_id ?? "Sin tenant", sla: ticket.priority === "high" ? "2h" : "8h" }));
}

export async function loadOwnerSystemChecks() {
  const body = await ownerApiRequest<{ checks?: { component: string; status: string; latency_ms: number }[] }>("/owner/system/health");
  return (body.checks ?? []).map((check) => ({ service: check.component.toUpperCase(), status: check.status, latency: `${check.latency_ms} ms`, detail: "API health" }));
}

export async function loadOwnerDemos() {
  const body = await ownerApiRequest<{ tenant_id: string; demo_type: string; status: string; last_reset_at?: string | null }[]>("/owner/demos");
  return body.map((demo) => ({ name: `Demo ${demo.demo_type}`, status: demo.status, tenant: demo.tenant_id, reset: demo.last_reset_at ?? "pendiente" }));
}

export async function loadOwnerInterventions() {
  const body = await ownerApiRequest<{ tenant_id: string; status: string; reason: string; expires_at: string; scopes: string[] }[]>("/owner/interventions");
  return body.map((item) => ({ tenant: item.tenant_id, status: item.status, reason: item.reason, expires: item.expires_at, scopes: item.scopes }));
}

export async function loadOwnerAuditLogs() {
  const body = await ownerApiRequest<{ owner_email: string; action: string; tenant_id?: string | null; created_at: string }[]>("/owner/audit-logs");
  return body.map((item) => ({ actor: item.owner_email, action: item.action, target: item.tenant_id ?? "system", at: item.created_at }));
}

export const ownerDemoFallback = {
  metrics: ownerDashboardMetrics,
  tenants: () => Promise.resolve([]),
  plans: () => Promise.resolve(ownerPlans),
  tickets: () => Promise.resolve(ownerTickets),
  system: () => Promise.resolve(ownerSystemChecks),
  demos: () => Promise.resolve(ownerDemos),
  interventions: () => Promise.resolve(ownerInterventions),
  audit: () => Promise.resolve(ownerAuditLogs),
  features: () => Promise.resolve(ownerFeatureFlags.map((feature_key) => ({ feature_key, enabled: false })))
};

function normalizeOwnerTenant(tenant: ApiOwnerTenant): OwnerTenant {
  const metrics = Object.fromEntries((tenant.usage?.metrics ?? []).map((item) => [item.metric_key, item.used]));
  const totals = tenant.usage?.totals ?? {};
  return {
    id: tenant.id,
    name: tenant.name,
    slug: tenant.slug,
    plan: normalizePlan(tenant.plan),
    status: normalizeStatus(tenant.status),
    health: tenant.health?.score ?? tenant.health_score ?? 82,
    mrr: normalizePlanPrice(tenant.plan),
    users: totals.users ?? tenant.users ?? 0,
    cases: totals.cases ?? tenant.cases ?? 0,
    documents: totals.documents ?? 0,
    storageGb: Math.round((metrics.storage_mb ?? 0) / 1024),
    aiTokens: metrics.ai_tokens ?? 0,
    whatsappMessages: metrics.whatsapp_messages ?? 0,
    sinoeSyncs: metrics.sinoe_syncs ?? 0,
    openTickets: 0,
    modules: (tenant.features ?? []).filter((feature) => feature.enabled).map((feature) => feature.feature_key),
    lastSeen: "API cloud"
  };
}

function normalizePlan(plan: string): OwnerTenant["plan"] {
  const value = plan.toUpperCase();
  if (value === "PRO" || value === "AI" || value === "ENTERPRISE") return value;
  return "START";
}

function normalizeStatus(status: string): OwnerTenant["status"] {
  if (status === "trial" || status === "suspended" || status === "cancelled") return status;
  return "active";
}

function normalizePlanPrice(plan: string) {
  return { START: 99, PRO: 249, AI: 399, ENTERPRISE: 0 }[normalizePlan(plan)] ?? 0;
}
