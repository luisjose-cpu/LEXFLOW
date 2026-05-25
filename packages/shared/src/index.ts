import type { LegalMetric, NavigationItem } from "@lexflow/types";

export const productSpine = [
  "Cliente",
  "Expediente",
  "Documento",
  "Comunicacion",
  "Automatizacion",
  "IA",
  "Inteligencia",
  "Decision"
] as const;

export const webNavigation: NavigationItem[] = [
  { label: "LEXFLOW OS", href: "/lexflow-os", module: "analytics" },
  { label: "Digital Twin", href: "/digital-twin", module: "analytics" },
  { label: "Knowledge", href: "/knowledge", module: "intelligence" },
  { label: "Graph", href: "/graph", module: "intelligence" },
  { label: "Copilot", href: "/copilot", module: "ai" },
  { label: "Marketplace", href: "/marketplace", module: "automation" },
  { label: "Dashboard", href: "/dashboard", module: "analytics" },
  { label: "Clientes", href: "/clients", module: "legal-core" },
  { label: "Expedientes", href: "/cases", module: "expediente360" },
  { label: "Documentos", href: "/documents", module: "legal-core" },
  { label: "Audiencias", href: "/hearings", module: "legal-core" },
  { label: "Comunicacion", href: "/communication", module: "communication" },
  { label: "Automation", href: "/automation", module: "automation" },
  { label: "Portal", href: "/portal", module: "portal" },
  { label: "IA Legal", href: "/ai", module: "ai" },
  { label: "Inteligencia", href: "/legal-intelligence", module: "intelligence" },
  { label: "Memory", href: "/intelligence/memory", module: "intelligence" },
  { label: "RAG", href: "/intelligence/rag", module: "ai" },
  { label: "Demo", href: "/demo", module: "analytics" },
  { label: "Import", href: "/settings/import", module: "legal-core" },
  { label: "Pilot Ops", href: "/settings/pilot", module: "analytics" },
  { label: "Settings", href: "/settings", module: "legal-core" }
];

export const p1Metrics: LegalMetric[] = [
  { label: "Tenants preparados", value: "Multi", trend: "aislamiento obligatorio" },
  { label: "Acciones auditables", value: "100%", trend: "para eventos criticos" },
  { label: "Superficies P1", value: "11", trend: "web + mobile-ready" }
];
