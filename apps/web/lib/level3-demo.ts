export const digitalTwinMetrics = [
  { label: "Salud estudio", value: "84", trend: "operacion estable" },
  { label: "Carga promedio", value: "68%", trend: "2 abogados saturados" },
  { label: "Complejidad alta", value: "3", trend: "requiere partner" },
  { label: "Riesgo propagado", value: "5", trend: "alertas activas" },
];

export const lawyerLoad = [
  { name: "Luis Iturri", load: 82, status: "saturado", signal: "audiencias + SINOE + IA pendiente" },
  { name: "Mariana Rios", load: 61, status: "balanceado", signal: "documentos y portal cliente" },
  { name: "Asistente Legal", load: 44, status: "disponible", signal: "checklists y notificaciones" },
];

export const complexityCases = [
  { title: "Laboral colectivo Andes", score: 88, drivers: ["audiencia", "CAPTCHA", "cliente sin respuesta"] },
  { title: "Cobro ejecutivo Nova", score: 74, drivers: ["plazo", "documentos", "SINOE"] },
  { title: "Contrato marco Mercurio", score: 42, drivers: ["versionado", "noticias vinculadas"] },
];

export const knowledgeItems = [
  { title: "Demanda ejecutiva con anexos", type: "template", tags: "cobro, plazo, Nova", summary: "Base reutilizable para expedientes ejecutivos con checklist y fuentes." },
  { title: "Precedente laboral colectivo", type: "precedent", tags: "laboral, audiencia", summary: "Criterios internos para riesgo y preparacion de audiencia." },
  { title: "Prompt de resumen con citas", type: "prompt", tags: "RAG, fuentes", summary: "Instruccion segura: responder solo con evidencia del expediente." },
];

export const memoryItems = [
  { source: "Documento", title: "Demanda Nova.pdf", citation: "document:chunk-001", status: "indexed" },
  { source: "Timeline", title: "Audiencia Andes creada", citation: "event:timeline-004", status: "indexed" },
  { source: "WhatsApp", title: "Solicitud de documento", citation: "message:wa-018", status: "indexed" },
];

export const graphNodes = [
  { label: "Nova Capital", type: "cliente", x: "18%", y: "42%" },
  { label: "Cobro ejecutivo Nova", type: "expediente", x: "45%", y: "30%" },
  { label: "Demanda.pdf", type: "documento", x: "72%", y: "22%" },
  { label: "Riesgo plazo", type: "riesgo", x: "70%", y: "60%" },
  { label: "Luis Iturri", type: "abogado", x: "42%", y: "70%" },
];

export const marketplaceItems = [
  { name: "SINOE Human Checkpoint Pack", type: "integration", status: "available", detail: "Plantillas, auditoria y flujo humano para CAPTCHA." },
  { name: "Precedent Template Pack", type: "template", status: "installed", detail: "Biblioteca de demandas, contratos y prompts seguros." },
  { name: "Risk War Room Widgets", type: "dashboard", status: "available", detail: "Paneles para propagacion de riesgo y carga de abogados." },
];

export const ragSources = [
  { title: "Demanda Nova.pdf", chunk: "chunk-doc-001", confidence: "0.91" },
  { title: "Timeline Cobro ejecutivo Nova", chunk: "chunk-event-004", confidence: "0.84" },
  { title: "Memoria operativa Nova", chunk: "chunk-memory-002", confidence: "0.79" },
];

export const agentCatalog = [
  "CaseAgent",
  "DocumentAgent",
  "HearingAgent",
  "ClientAgent",
  "NewsAgent",
  "ManagementAgent",
  "AutomationAgent",
];
