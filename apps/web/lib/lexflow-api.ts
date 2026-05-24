import { CaseOps, ClientOps, SearchResult } from "@/lib/operational-demo";

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
