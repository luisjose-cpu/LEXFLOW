import { CaseOps, ClientOps, SearchResult } from "@/lib/operational-demo";
import type { Case360Data } from "@/components/case-360";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://lexflow-api.onrender.com";

type ApiSearchResult = {
  id: string;
  type: string;
  title: string;
  subtitle: string;
  href: string;
  tags?: string[];
};

type ApiSearchResponse = {
  quick_results?: ApiSearchResult[];
  recent_searches?: string[];
  favorites?: ApiSearchResult[];
};

type ApiClientSummary = {
  id: string;
  name: string;
  contact_email?: string | null;
  status: string;
  risk_profile: string;
  tags?: string[];
  case_count: number;
  active_case_count: number;
};

type ApiCaseSummary = {
  id: string;
  client_id: string;
  client_name?: string | null;
  title: string;
  matter?: string | null;
  external_case_number?: string | null;
  status: string;
  priority: string;
  risk: string;
  next_action: string;
  critical_deadline?: string | null;
  judicial_updates: number;
  captcha_pending: number;
};

type ApiClientProfile = {
  client: ApiClientSummary;
  general?: {
    business_name?: string | null;
    sector?: string | null;
    main_matter?: string | null;
    status?: string | null;
    priority?: string | null;
  };
  metrics?: {
    active_cases?: number;
    documents?: number;
    hearings?: number;
    judicial_updates?: number;
    captcha_pending?: number;
  };
  risk?: {
    level?: string;
    signals?: string[];
    recommendation?: string;
  };
  cases?: ApiCaseSummary[];
  documents?: Record<string, unknown>[];
  communications?: Record<string, unknown>[];
  hearings?: Record<string, unknown>[];
  judicial_updates?: Record<string, unknown>[];
  timeline?: Record<string, unknown>[];
  notes?: { title?: string; body?: string }[];
};

const resultTypeMap: Record<string, SearchResult["type"]> = {
  client: "cliente",
  case: "expediente",
  document: "documento",
  hearing: "audiencia",
  judicial_update: "sinoe",
  legal_news: "noticia"
};

export function getAccessToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("lexflow.access_token") ?? "";
}

export function hasCloudSession() {
  return Boolean(getAccessToken());
}

export async function changePassword(payload: { current_password: string; new_password: string }) {
  return apiRequest<{ access_token: string; refresh_token: string; token_type: string }>("/auth/change-password", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function loadMfaStatus() {
  return apiRequest<{ mfa_enabled: boolean; enrollment_pending: boolean; policy_required?: boolean }>("/auth/mfa/status");
}

export async function startMfaEnrollment() {
  return apiRequest<{ status: string; secret: string; otpauth_url: string }>("/auth/mfa/enroll", {
    method: "POST",
    body: JSON.stringify({})
  });
}

export async function verifyMfaEnrollment(payload: { code: string }) {
  return apiRequest<{ access_token: string; refresh_token: string; token_type: string }>("/auth/mfa/verify", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function disableMfa(payload: { current_password: string; code?: string }) {
  return apiRequest<{ access_token: string; refresh_token: string; token_type: string }>("/auth/mfa/disable", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export type TenantSecurityPolicy = {
  tenant_id: string;
  enforce_mfa: boolean;
  mfa_required_roles: string[];
  grace_period_hours: number;
  allow_client_user_mfa_bypass: boolean;
};

export async function loadTenantSecurityPolicy() {
  return apiRequest<TenantSecurityPolicy>("/settings/security-policy");
}

export async function updateTenantSecurityPolicy(payload: Partial<Omit<TenantSecurityPolicy, "tenant_id">>) {
  return apiRequest<TenantSecurityPolicy>("/settings/security-policy", {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export type SecurityAlert = {
  id: string;
  severity: string;
  event_type: string;
  title: string;
  body: string;
  status: string;
  created_at: string;
};

export type SecurityAlertDelivery = {
  id: string;
  template: string;
  provider?: string | null;
  status: string;
  recipient_hint: string;
  attempts: number;
  max_attempts: number;
  created_at: string;
};

export async function loadSecurityAlerts() {
  return apiRequest<SecurityAlert[]>("/settings/security-alerts?limit=10");
}

export async function acknowledgeSecurityAlert(alertId: string) {
  return apiRequest<SecurityAlert>(`/settings/security-alerts/${alertId}/acknowledge`, {
    method: "POST"
  });
}

export async function loadSecurityAlertDeliveries() {
  return apiRequest<SecurityAlertDelivery[]>("/settings/security-alert-deliveries?limit=10");
}

export async function processSecurityAlertDeliveries() {
  return apiRequest<{ processed: number }>("/settings/security-alert-deliveries/process", {
    method: "POST"
  });
}

export type ProductionGateReport = {
  status: string;
  public_production_status?: string;
  revision?: string;
  external_providers?: Record<string, string>;
  summary?: {
    blockers?: number;
    warnings?: number;
  };
  readiness?: {
    app_env?: string;
    production_ready?: boolean;
    public_production_ready?: boolean;
    status?: string;
    blockers?: { key: string; message: string; severity: string; ok: boolean }[];
    warnings?: { key: string; message: string; severity: string; ok: boolean }[];
    checks?: { key: string; message: string; severity: string; ok: boolean }[];
  };
  commands?: string[];
  required_before_public_production?: string[];
};

export async function loadProductionGate() {
  return apiRequest<ProductionGateReport>("/ops/production-gate");
}

export async function requestPasswordReset(payload: { email: string; tenant_slug: string }) {
  return publicApiRequest<{ status: string; delivery: string; reset_token?: string }>("/auth/password-reset/request", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function confirmPasswordReset(payload: { reset_token: string; new_password: string }) {
  return publicApiRequest<{ status: string }>("/auth/password-reset/confirm", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export type UserInvitation = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  status: string;
  expires_at: string;
  accepted_at?: string | null;
  created_at?: string;
};

export type EmailDelivery = {
  id: string;
  template: string;
  provider: string;
  status: string;
  recipient_hint: string;
  created_at: string;
};

export async function loadUserInvitations() {
  return apiRequest<UserInvitation[]>("/users/invitations");
}

export async function loadEmailDeliveries() {
  return apiRequest<EmailDelivery[]>("/settings/email/deliveries?limit=10");
}

export async function createUserInvitation(payload: { email: string; full_name: string; role: string }) {
  return apiRequest<UserInvitation & { delivery: string; invitation_token?: string }>("/users/invitations", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function resendUserInvitation(invitationId: string) {
  return apiRequest<UserInvitation & { delivery: string; invitation_token?: string }>(`/users/invitations/${invitationId}/resend`, {
    method: "POST"
  });
}

export async function cancelUserInvitation(invitationId: string) {
  return apiRequest<UserInvitation>(`/users/invitations/${invitationId}/cancel`, {
    method: "POST"
  });
}

export async function acceptUserInvitation(payload: { invitation_token: string; password: string }) {
  return publicApiRequest<{ status: string; access_token: string; refresh_token: string; token_type: string }>("/auth/invitations/accept", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

async function publicApiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {})
    }
  });

  if (!response.ok) {
    throw new Error(`LEXFLOW API error ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  const response = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {})
    }
  });

  if (!response.ok) {
    throw new Error(`LEXFLOW API error ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function searchOperational(query: string) {
  const params = new URLSearchParams({ q: query, limit: "12" });
  const body = await apiRequest<ApiSearchResponse>(`/dashboard/search?${params.toString()}`);
  return {
    results: (body.quick_results ?? []).map(normalizeSearchResult),
    recent: body.recent_searches ?? [],
    favorites: (body.favorites ?? []).map((item) => item.title)
  };
}

export async function loadOperationalClients(): Promise<ClientOps[]> {
  const body = await apiRequest<ApiClientSummary[]>("/clients/search?limit=50");
  return body.map(normalizeClient);
}

export async function loadOperationalCases(): Promise<CaseOps[]> {
  const body = await apiRequest<ApiCaseSummary[]>("/cases/search?limit=50");
  return body.map(normalizeCase);
}

export async function loadClientProfile(clientId: string) {
  const body = await apiRequest<ApiClientProfile>(`/clients/${clientId}/profile`);
  const client = normalizeClient(body.client);
  const metrics = body.metrics;
  const risk = body.risk;
  return {
    client: {
      ...client,
      businessName: body.general?.business_name ?? client.businessName,
      sector: body.general?.sector ?? client.sector,
      mainMatter: body.general?.main_matter ?? client.mainMatter,
      status: body.general?.status ?? client.status,
      priority: body.general?.priority ?? client.priority,
      risk: normalizeRisk(risk?.level ?? client.risk),
      notes: body.notes?.map((note) => [note.title, note.body].filter(Boolean).join(": ")) ?? client.notes,
      metrics: metrics
        ? [
            { label: "Expedientes", value: String(metrics.active_cases ?? 0), trend: "activos" },
            { label: "Documentos", value: String(metrics.documents ?? 0), trend: `${metrics.hearings ?? 0} audiencias` },
            { label: "Riesgo", value: capitalize(normalizeRisk(risk?.level ?? client.risk)), trend: risk?.recommendation ?? "revisar expediente" }
          ]
        : client.metrics
    },
    cases: (body.cases ?? []).map(normalizeCase),
    documents: (body.documents ?? []).map((item) => itemLabel(item, ["filename", "classification", "status"])),
    communications: (body.communications ?? []).map((item) => itemLabel(item, ["channel", "direction", "body", "status"])),
    hearings: (body.hearings ?? []).map((item) => itemLabel(item, ["title", "starts_at", "location", "status"])),
    judicialUpdates: (body.judicial_updates ?? []).map((item) => itemLabel(item, ["title", "summary", "status", "checked_at"])),
    timeline: (body.timeline ?? []).map((item) => itemLabel(item, ["title", "description", "type", "occurred_at"]))
  };
}

export async function loadCaseResource(caseId: string, type: "documents" | "hearings" | "communications" | "judicial" | "automation" | "intelligence") {
  const body = await apiRequest<unknown>(`/cases/${caseId}/${type}`);
  if (type === "judicial") return normalizeJudicialResource(body);
  if (type === "automation") return normalizeAutomationResource(body);
  if (type === "intelligence") return normalizeIntelligenceResource(body);
  const items = Array.isArray(body) ? body : [];
  const keys = {
    documents: ["filename", "classification", "status", "malware_scan_status"],
    hearings: ["title", "starts_at", "location", "status"],
    communications: ["channel", "direction", "body", "status"]
  }[type];
  return items.map((item) => itemLabel(item as Record<string, unknown>, keys));
}

export async function loadCaseOverview(caseId: string) {
  return apiRequest<Case360Data>(`/cases/${caseId}/overview`);
}

export async function createCaseEvent(caseId: string, payload: { title: string; description?: string; event_type?: string }) {
  return apiRequest<{ id: string }>(`/cases/${caseId}/events`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function createCaseTask(caseId: string, payload: { title: string; due_at?: string }) {
  return apiRequest<{ id: string }>(`/cases/${caseId}/tasks`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function createCaseDocument(caseId: string, payload: { filename: string; storage_key: string; classification?: string; content_type?: string }) {
  return apiRequest<{ id: string }>(`/cases/${caseId}/documents`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function createCaseHearing(caseId: string, payload: { title: string; starts_at: string; location?: string; status?: string }) {
  return apiRequest<{ id: string }>(`/cases/${caseId}/hearings`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function createCaseCommunication(caseId: string, payload: { body: string; channel?: string; direction?: string }) {
  return apiRequest<{ id: string }>(`/cases/${caseId}/communications`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function runCaseAiSummary(caseId: string) {
  return apiRequest<{ id: string; result: Record<string, unknown>; disclaimer?: string }>(`/ai/cases/${caseId}/summary`, {
    method: "POST"
  });
}

export async function checkSinoeSource(sourceId: string) {
  return apiRequest<{ status: string }>(`/case-sources/${sourceId}/sinoe/check`, {
    method: "POST"
  });
}

function normalizeSearchResult(result: ApiSearchResult): SearchResult {
  return {
    id: result.id,
    type: resultTypeMap[result.type] ?? "expediente",
    title: result.title,
    subtitle: result.subtitle,
    href: result.href,
    tags: result.tags ?? []
  };
}

function normalizeClient(client: ApiClientSummary): ClientOps {
  const risk = normalizeRisk(client.risk_profile);
  const tags = client.tags?.length ? client.tags : ["cliente"];
  return {
    id: client.id,
    name: client.name,
    businessName: client.name,
    dni: "",
    ruc: "",
    email: client.contact_email ?? "sin-correo@lexflow.local",
    phone: "No registrado",
    address: "Direccion pendiente",
    contacts: [client.contact_email ?? "Contacto pendiente"],
    representatives: ["Representante pendiente"],
    company: client.name,
    position: "Cliente operativo",
    sector: tags[0] ?? "Legal",
    mainMatter: client.active_case_count ? "Expedientes activos" : "Sin materia activa",
    status: client.status,
    priority: risk === "alto" ? "alta" : "normal",
    risk,
    tags,
    notes: ["Datos cargados desde API cloud.", "Completar DNI/RUC, telefono, direccion y representantes."],
    metrics: [
      { label: "Expedientes", value: String(client.case_count), trend: `${client.active_case_count} activos` },
      { label: "Documentos", value: "-", trend: "ver expediente" },
      { label: "Riesgo", value: capitalize(risk), trend: client.risk_profile }
    ]
  };
}

function normalizeCase(legalCase: ApiCaseSummary): CaseOps {
  const risk = normalizeRisk(legalCase.risk);
  return {
    id: legalCase.id,
    clientId: legalCase.client_id,
    clientName: legalCase.client_name ?? "Cliente sin nombre",
    title: legalCase.title,
    matter: legalCase.matter ?? "Materia principal",
    submatter: legalCase.matter ?? "Submateria pendiente",
    externalNumber: legalCase.external_case_number ?? "Sin numero externo",
    status: legalCase.status,
    responsible: "Equipo legal",
    leadLawyer: "Abogado principal pendiente",
    team: ["Equipo legal"],
    court: "Juzgado pendiente",
    instance: "Instancia pendiente",
    priority: legalCase.priority,
    risk,
    openedAt: "Fecha apertura pendiente",
    closedAt: null,
    nextAction: legalCase.next_action,
    criticalDeadline: legalCase.critical_deadline ?? "Sin plazo critico",
    tags: [legalCase.status, legalCase.priority].filter(Boolean),
    sinoeStatus: legalCase.judicial_updates ? "con actualizaciones" : "sin novedades",
    lastSinoeUpdate: legalCase.judicial_updates ? `${legalCase.judicial_updates} actualizaciones` : "Sin sincronizacion",
    captchaPending: legalCase.captcha_pending > 0
  };
}

function normalizeRisk(value: string) {
  return value === "high" || value === "alto" || value === "risk" ? "alto" : value === "medium" || value === "medio" ? "medio" : "bajo";
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function itemLabel(item: Record<string, unknown>, keys: string[]) {
  return keys
    .map((key) => item[key])
    .filter((value) => value !== undefined && value !== null && String(value).trim())
    .map(String)
    .join(" · ");
}

function normalizeJudicialResource(body: unknown) {
  if (!body || typeof body !== "object") return [];
  const payload = body as { sources?: Record<string, unknown>[]; updates?: Record<string, unknown>[]; sinoe_module?: string };
  return [
    ...(payload.sources ?? []).map((source) => `Fuente ${itemLabel(source, ["source_type", "external_case_number", "status", "last_result"])}`),
    ...(payload.updates ?? []).map((update) => itemLabel(update, ["title", "summary", "status", "hash"])),
    payload.sinoe_module ? `SINOE Module: ${payload.sinoe_module}` : ""
  ].filter(Boolean);
}

function normalizeAutomationResource(body: unknown) {
  if (!body || typeof body !== "object") return [];
  const payload = body as { workflows?: Record<string, unknown>[]; available_triggers?: string[] };
  return [
    ...(payload.workflows ?? []).map((workflow) => itemLabel(workflow, ["name", "trigger_key", "status"])),
    ...(payload.available_triggers ?? []).map((trigger) => `Trigger disponible: ${trigger}`)
  ];
}

function normalizeIntelligenceResource(body: unknown) {
  if (!body || typeof body !== "object") return [];
  const payload = body as { linked_news?: Record<string, unknown>[]; trend_notes?: string[] };
  return [
    ...(payload.linked_news ?? []).map((news) => itemLabel(news, ["title", "summary"])),
    ...(payload.trend_notes ?? [])
  ];
}
