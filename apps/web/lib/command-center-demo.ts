export const commandKpis = [
  { label: "Casos activos", value: "3", trend: "1 critico" },
  { label: "Audiencias", value: "3", trend: "14 dias promedio" },
  { label: "CAPTCHA", value: "1", trend: "pendiente humano" },
  { label: "IA", value: "3", trend: "revision en cola" },
  { label: "Mensajes", value: "6", trend: "portal + WhatsApp" },
  { label: "Noticias", value: "1", trend: "vinculada a caso" }
];

export const productivityData = [
  { name: "Admin", tareas: 0, carga: 1 },
  { name: "Lawyer", tareas: 3, carga: 4 },
  { name: "Assistant", tareas: 0, carga: 2 },
  { name: "Client", tareas: 0, carga: 0 }
];

export const riskItems = [
  { title: "Laboral colectivo Andes", status: "risk", reason: "CAPTCHA y audiencia proxima" },
  { title: "Cobro ejecutivo Nova", status: "active", reason: "Memorial y anexos pendientes" },
  { title: "Contrato marco Mercurio", status: "active", reason: "Revision de cumplimiento" }
];

export const judicialMonitoring = [
  { label: "Fuentes activas", value: "3" },
  { label: "Actualizaciones", value: "2" },
  { label: "CAPTCHA pendientes", value: "1" },
  { label: "Ultimo check", value: "hoy" }
];

export const aiUsage = [
  { type: "summary", count: 3 },
  { type: "ocr", count: 1 },
  { type: "extract", count: 1 },
  { type: "classify", count: 1 }
];

export const communications = [
  { channel: "whatsapp", count: 3 },
  { channel: "portal", count: 3 },
  { channel: "email", count: 0 }
];

export const legalTrends = [
  { tag: "jurisprudencia", count: 1 },
  { tag: "debido-proceso", count: 1 },
  { tag: "procesal", count: 2 },
  { tag: "normativa", count: 1 }
];

export const decisionQueue = [
  "Revisar expedientes criticos",
  "Resolver CAPTCHA pendientes",
  "Aprobar salidas IA en revision",
  "Vincular inteligencia juridica a expedientes activos"
];
