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
