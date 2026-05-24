export type SearchResult = {
  id: string;
  type: "cliente" | "expediente" | "documento" | "audiencia" | "sinoe" | "noticia";
  title: string;
  subtitle: string;
  href: string;
  tags: string[];
};

export type ClientOps = {
  id: string;
  name: string;
  businessName: string;
  dni: string;
  ruc: string;
  email: string;
  phone: string;
  address: string;
  contacts: string[];
  representatives: string[];
  company: string;
  position: string;
  sector: string;
  mainMatter: string;
  status: string;
  priority: string;
  risk: string;
  tags: string[];
  notes: string[];
  metrics: { label: string; value: string; trend: string }[];
};

export type CaseOps = {
  id: string;
  clientId: string;
  clientName: string;
  title: string;
  matter: string;
  submatter: string;
  externalNumber: string;
  status: string;
  responsible: string;
  leadLawyer: string;
  team: string[];
  court: string;
  instance: string;
  priority: string;
  risk: string;
  openedAt: string;
  closedAt: string | null;
  nextAction: string;
  criticalDeadline: string;
  tags: string[];
  sinoeStatus: string;
  lastSinoeUpdate: string;
  captchaPending: boolean;
};

export const clientsOps: ClientOps[] = [
  {
    id: "cli-nova",
    name: "Nova Capital",
    businessName: "Nova Capital S.A.C.",
    dni: "",
    ruc: "20609999111",
    email: "legal@novacapital.demo",
    phone: "+51 999 111 222",
    address: "Av. Camino Real 390, Lima",
    contacts: ["Mariana Quiroz - Gerente Legal", "Alonso Prado - Finanzas"],
    representatives: ["Mariana Quiroz"],
    company: "Nova Capital S.A.C.",
    position: "Cliente corporativo",
    sector: "Financiero",
    mainMatter: "Cobro ejecutivo",
    status: "activo",
    priority: "alta",
    risk: "alto",
    tags: ["corporate", "priority", "portal", "SINOE"],
    notes: ["Validar poder vigente antes de presentar memorial.", "Cliente requiere reporte ejecutivo semanal."],
    metrics: [
      { label: "Expedientes", value: "4", trend: "3 activos" },
      { label: "Documentos", value: "32", trend: "6 por revisar" },
      { label: "Riesgo", value: "Alto", trend: "CAPTCHA pendiente" }
    ]
  },
  {
    id: "cli-andes",
    name: "Andes Health",
    businessName: "Andes Health Group",
    dni: "",
    ruc: "20504444123",
    email: "legal@andes.demo",
    phone: "+51 988 222 333",
    address: "Av. La Floresta 120, Lima",
    contacts: ["Renato Salas - Legal"],
    representatives: ["Renato Salas"],
    company: "Andes Health Group",
    position: "Cliente enterprise",
    sector: "Salud",
    mainMatter: "Laboral colectivo",
    status: "activo",
    priority: "media",
    risk: "medio",
    tags: ["health", "laboral", "audiencias"],
    notes: ["Preparar matriz de trabajadores involucrados."],
    metrics: [
      { label: "Expedientes", value: "2", trend: "1 critico" },
      { label: "Documentos", value: "18", trend: "OCR completo" },
      { label: "Riesgo", value: "Medio", trend: "audiencia proxima" }
    ]
  },
  {
    id: "cli-mercurio",
    name: "Mercurio Retail",
    businessName: "Mercurio Retail S.A.",
    dni: "",
    ruc: "20407777333",
    email: "legal@mercurio.demo",
    phone: "+51 977 444 555",
    address: "Av. El Polo 510, Lima",
    contacts: ["Sofia Arana - Operaciones"],
    representatives: ["Sofia Arana"],
    company: "Mercurio Retail S.A.",
    position: "Cliente recurrente",
    sector: "Retail",
    mainMatter: "Contratos",
    status: "activo",
    priority: "normal",
    risk: "bajo",
    tags: ["contracts", "retail", "automation"],
    notes: ["Automatizar recordatorios de renovacion contractual."],
    metrics: [
      { label: "Expedientes", value: "5", trend: "contratos activos" },
      { label: "Documentos", value: "41", trend: "versionado listo" },
      { label: "Riesgo", value: "Bajo", trend: "sin alertas" }
    ]
  }
];

export const casesOps: CaseOps[] = [
  {
    id: "case-demo",
    clientId: "cli-nova",
    clientName: "Nova Capital",
    title: "Cobro ejecutivo Nova",
    matter: "Civil",
    submatter: "Cobro ejecutivo",
    externalNumber: "11001-31-03-001-2026-00001",
    status: "risk",
    responsible: "Dra. Laura Mendoza",
    leadLawyer: "Laura Mendoza",
    team: ["Laura Mendoza", "Mateo Rojas", "Ana Beltran"],
    court: "Juzgado Civil Demo",
    instance: "Primera instancia",
    priority: "alta",
    risk: "alto",
    openedAt: "2026-04-12",
    closedAt: null,
    nextAction: "Preparar memorial y anexos",
    criticalDeadline: "2026-06-02",
    tags: ["SINOE", "cobro", "urgente"],
    sinoeStatus: "paused_captcha",
    lastSinoeUpdate: "SINOE requiere verificacion humana",
    captchaPending: true
  },
  {
    id: "case-andes",
    clientId: "cli-andes",
    clientName: "Andes Health",
    title: "Laboral colectivo Andes",
    matter: "Laboral",
    submatter: "Negociacion colectiva",
    externalNumber: "11001-05-02-002-2026-00002",
    status: "active",
    responsible: "Dr. Mateo Rojas",
    leadLawyer: "Mateo Rojas",
    team: ["Mateo Rojas", "Camila Soto"],
    court: "Juzgado Laboral Demo",
    instance: "Primera instancia",
    priority: "media",
    risk: "medio",
    openedAt: "2026-03-24",
    closedAt: null,
    nextAction: "Clasificar pruebas recibidas",
    criticalDeadline: "2026-06-08",
    tags: ["laboral", "audiencia", "IA"],
    sinoeStatus: "connected",
    lastSinoeUpdate: "Sin nuevas notificaciones",
    captchaPending: false
  },
  {
    id: "case-mercurio",
    clientId: "cli-mercurio",
    clientName: "Mercurio Retail",
    title: "Contrato marco Mercurio",
    matter: "Comercial",
    submatter: "Contratos",
    externalNumber: "11001-40-03-003-2026-00003",
    status: "active",
    responsible: "Dra. Ana Beltran",
    leadLawyer: "Ana Beltran",
    team: ["Ana Beltran"],
    court: "Centro Arbitral Demo",
    instance: "Etapa contractual",
    priority: "normal",
    risk: "bajo",
    openedAt: "2026-05-04",
    closedAt: null,
    nextAction: "Comparar version de clausulas",
    criticalDeadline: "2026-06-20",
    tags: ["contratos", "versionado", "automation"],
    sinoeStatus: "not_applicable",
    lastSinoeUpdate: "No vinculado",
    captchaPending: false
  }
];

export const timelineOps = [
  { id: "tl-1", title: "Cliente creado", description: "Perfil enriquecido y portal preparado.", type: "cliente" },
  { id: "tl-2", title: "Expediente vinculado", description: "Expediente 360 conectado con documentos, SINOE y comunicaciones.", type: "expediente" },
  { id: "tl-3", title: "SINOE pausado", description: "CAPTCHA pendiente con verificacion humana requerida.", type: "sinoe" },
  { id: "tl-4", title: "IA lista", description: "Resumen, plazos, riesgos y busqueda preparados. Requiere revision profesional.", type: "ia" }
];

export const documentsOps = [
  { id: "doc-1", name: "demanda.pdf", type: "PDF", status: "aprobado", visibility: "privado", ai: "resumen listo" },
  { id: "doc-2", name: "contestacion.docx", type: "Word", status: "observado", visibility: "equipo", ai: "clasificacion pendiente" },
  { id: "doc-3", name: "anexos_financieros.xlsx", type: "Excel", status: "aprobado", visibility: "cliente", ai: "OCR no aplica" }
];

export const hearingsOps = [
  { id: "hea-1", title: "Audiencia inicial", date: "2026-06-02", type: "virtual", link: "https://meet.demo/audiencia", responsible: "Laura Mendoza", status: "programada" },
  { id: "hea-2", title: "Vista de causa", date: "2026-06-08", type: "presencial", link: "", responsible: "Mateo Rojas", status: "preparacion" }
];

export const communicationOps = [
  { id: "com-1", channel: "WhatsApp", direction: "outbound", body: "Se envio resumen ejecutivo al cliente.", status: "sent" },
  { id: "com-2", channel: "Portal", direction: "inbound", body: "Cliente cargo poder actualizado.", status: "received" },
  { id: "com-3", channel: "Email preparado", direction: "draft", body: "Solicitud de documentos para audiencia.", status: "draft" }
];

export const searchResultsOps: SearchResult[] = [
  ...clientsOps.map((client) => ({ id: client.id, type: "cliente" as const, title: client.name, subtitle: `${client.ruc} · ${client.email}`, href: `/clients/${client.id}`, tags: client.tags })),
  ...casesOps.map((legalCase) => ({ id: legalCase.id, type: "expediente" as const, title: legalCase.title, subtitle: legalCase.externalNumber, href: `/cases/${legalCase.id}`, tags: legalCase.tags })),
  ...documentsOps.map((document) => ({ id: document.id, type: "documento" as const, title: document.name, subtitle: `${document.type} · ${document.status}`, href: "/cases/case-demo/documents", tags: [document.visibility, document.ai] })),
  ...hearingsOps.map((hearing) => ({ id: hearing.id, type: "audiencia" as const, title: hearing.title, subtitle: `${hearing.date} · ${hearing.responsible}`, href: "/cases/case-demo/hearings", tags: [hearing.type, hearing.status] })),
  { id: "sinoe-1", type: "sinoe", title: "SINOE requiere verificacion humana", subtitle: "CAPTCHA pendiente · Nova Capital", href: "/cases/case-demo/judicial", tags: ["SINOE", "CAPTCHA"] },
  { id: "news-1", type: "noticia", title: "Nuevo criterio sobre notificacion procesal", subtitle: "Inteligencia vinculada", href: "/legal-intelligence", tags: ["jurisprudencia", "debido-proceso"] }
];

export function findClient(id: string) {
  return clientsOps.find((client) => client.id === id) ?? clientsOps[0];
}

export function findCase(id: string) {
  return casesOps.find((legalCase) => legalCase.id === id) ?? casesOps[0];
}

export function casesForClient(clientId: string) {
  return casesOps.filter((legalCase) => legalCase.clientId === clientId);
}
