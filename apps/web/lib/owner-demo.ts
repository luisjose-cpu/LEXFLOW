export type OwnerTenant = {
  id: string;
  name: string;
  slug: string;
  plan: "START" | "PRO" | "AI" | "ENTERPRISE";
  status: "active" | "trial" | "suspended" | "cancelled";
  health: number;
  mrr: number;
  users: number;
  cases: number;
  documents: number;
  storageGb: number;
  aiTokens: number;
  whatsappMessages: number;
  sinoeSyncs: number;
  openTickets: number;
  modules: string[];
  lastSeen: string;
};

export type OwnerPlan = {
  name: string;
  monthly: number;
  yearly: number;
  status: "active" | "draft";
  limits: string[];
  features: string[];
};

export type OwnerTicket = {
  id: string;
  tenant: string;
  tenant_id?: string | null;
  priority: string;
  status: string;
  category: string;
  title: string;
  sla: string;
  resolution?: string | null;
};

export const ownerTenants: OwnerTenant[] = [
  {
    id: "tenant-nova",
    name: "Nova Legal Studio",
    slug: "nova",
    plan: "AI",
    status: "active",
    health: 91,
    mrr: 249,
    users: 18,
    cases: 126,
    documents: 842,
    storageGb: 41,
    aiTokens: 780000,
    whatsappMessages: 2150,
    sinoeSyncs: 384,
    openTickets: 1,
    modules: ["expediente360", "client_portal", "ai", "sinoe", "automation"],
    lastSeen: "2026-05-24 09:40"
  },
  {
    id: "tenant-andes",
    name: "Andes & Asociados",
    slug: "andes",
    plan: "PRO",
    status: "trial",
    health: 76,
    mrr: 129,
    users: 8,
    cases: 48,
    documents: 230,
    storageGb: 12,
    aiTokens: 120000,
    whatsappMessages: 620,
    sinoeSyncs: 101,
    openTickets: 2,
    modules: ["expediente360", "client_portal", "sinoe"],
    lastSeen: "2026-05-24 08:15"
  },
  {
    id: "tenant-mercurio",
    name: "Mercurio Retail Legal",
    slug: "mercurio",
    plan: "START",
    status: "suspended",
    health: 42,
    mrr: 79,
    users: 5,
    cases: 31,
    documents: 118,
    storageGb: 6,
    aiTokens: 0,
    whatsappMessages: 90,
    sinoeSyncs: 18,
    openTickets: 3,
    modules: ["expediente360"],
    lastSeen: "2026-05-20 16:10"
  }
];

export const ownerPlans: OwnerPlan[] = [
  { name: "START", monthly: 79, yearly: 790, status: "active", limits: ["5 usuarios", "100 expedientes", "5 GB"], features: ["Expediente 360", "PWA", "Dashboard"] },
  { name: "PRO", monthly: 129, yearly: 1290, status: "active", limits: ["15 usuarios", "500 expedientes", "25 GB"], features: ["Portal Cliente", "SINOE", "WhatsApp mock"] },
  { name: "AI", monthly: 249, yearly: 2490, status: "active", limits: ["40 usuarios", "1500 expedientes", "100 GB"], features: ["IA", "OCR", "Automation Studio"] },
  { name: "ENTERPRISE", monthly: 690, yearly: 6900, status: "draft", limits: ["Usuarios ilimitados", "SLA dedicado", "S3 propio"], features: ["Custom domain", "SSO futuro", "Soporte premium"] }
];

export const ownerFeatureFlags = [
  "client_portal",
  "whatsapp",
  "ai",
  "ocr",
  "sinoe",
  "legal_intelligence",
  "automation_studio",
  "dashboard",
  "mobile_pwa"
];

export const ownerTickets: OwnerTicket[] = [
  { id: "ticket-901", tenant: "Nova Legal Studio", priority: "high", status: "open", category: "SINOE", title: "Checkpoint CAPTCHA pendiente", sla: "2h" },
  { id: "ticket-902", tenant: "Andes & Asociados", priority: "medium", status: "open", category: "Billing", title: "Validar cambio de plan PRO", sla: "8h" },
  { id: "ticket-903", tenant: "Mercurio Retail Legal", priority: "critical", status: "open", category: "Cobranza", title: "Tenant suspendido por deuda", sla: "1h" }
];

export const ownerSystemChecks = [
  { service: "API", status: "operational", latency: "210 ms", detail: "Health OK" },
  { service: "DB", status: "operational", latency: "34 ms", detail: "Postgres activo" },
  { service: "Redis", status: "operational", latency: "19 ms", detail: "Queue ready" },
  { service: "Storage", status: "degraded", latency: "620 ms", detail: "S3 mock con latencia" },
  { service: "IA", status: "operational", latency: "880 ms", detail: "Provider mock/OpenAI preparado" },
  { service: "SINOE", status: "human_review", latency: "n/a", detail: "CAPTCHA human-in-the-loop" }
];

export const ownerDemos = [
  { name: "Demo litigios", status: "ready", tenant: "demo-litigios", reset: "2026-05-24 06:00" },
  { name: "Demo corporativo", status: "ready", tenant: "demo-corp", reset: "2026-05-24 06:00" },
  { name: "Demo cobranza", status: "refreshing", tenant: "demo-cobranza", reset: "2026-05-23 23:30" }
];

export const ownerAuditLogs = [
  { actor: "owner@lexflow.test", action: "tenant_created", target: "Andes & Asociados", at: "2026-05-24 08:21" },
  { actor: "finance@lexflow.test", action: "plan_changed", target: "Nova Legal Studio", at: "2026-05-24 07:42" },
  { actor: "support@lexflow.test", action: "intervention_opened", target: "Mercurio Retail Legal", at: "2026-05-23 18:05" }
];

export const ownerInterventions = [
  { tenant: "Nova Legal Studio", status: "active", reason: "Revision de metadata SINOE autorizada", expires: "2026-05-24 11:00", scopes: ["metadata:read", "logs:read"] },
  { tenant: "Mercurio Retail Legal", status: "expired", reason: "Diagnostico de soporte cerrado", expires: "2026-05-23 19:00", scopes: ["billing:read"] }
];

export function findOwnerTenant(id: string) {
  return ownerTenants.find((tenant) => tenant.id === id) ?? ownerTenants[0];
}

export function ownerDashboardMetrics() {
  const active = ownerTenants.filter((tenant) => tenant.status === "active").length;
  const trial = ownerTenants.filter((tenant) => tenant.status === "trial").length;
  const suspended = ownerTenants.filter((tenant) => tenant.status === "suspended").length;
  const mrr = ownerTenants.reduce((sum, tenant) => sum + tenant.mrr, 0);
  const tickets = ownerTickets.filter((ticket) => ticket.status === "open").length;
  const aiTokens = ownerTenants.reduce((sum, tenant) => sum + tenant.aiTokens, 0);
  return [
    { label: "Tenants activos", value: String(active), trend: `${trial} trial, ${suspended} suspendido` },
    { label: "MRR", value: `$${mrr}`, trend: `ARR $${mrr * 12}` },
    { label: "Tickets abiertos", value: String(tickets), trend: "SLA monitoreado" },
    { label: "Uso IA", value: `${Math.round(aiTokens / 1000)}k`, trend: "tokens este mes" }
  ];
}
