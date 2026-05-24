import { SearchResult } from "@/lib/operational-demo";

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
