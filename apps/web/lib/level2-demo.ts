export const warRoomCriticalCases = [
  { title: "Laboral colectivo Andes", score: 88, signal: "CAPTCHA pendiente, audiencia en 4 dias, IA sin revisar" },
  { title: "Cobro ejecutivo Nova", score: 74, signal: "Documento observado y cliente sin respuesta" },
  { title: "Contrato marco Mercurio", score: 58, signal: "SINOE actualizado, plazo de revision abierto" }
];

export const warRoomAlerts = [
  { type: "SINOE", title: "Nueva actualizacion judicial", count: 3 },
  { type: "CAPTCHA", title: "Verificacion humana requerida", count: 1 },
  { type: "IA", title: "Resultados pendientes de revision profesional", count: 4 },
  { type: "Automation", title: "Workflow con error controlado", count: 1 }
];

export const crmLeads = [
  { company: "Inversiones Pacifico", stage: "proposal", value: "$12,500", score: 82, next: "Enviar propuesta piloto" },
  { company: "Litigios Norte", stage: "meeting", value: "$8,500", score: 68, next: "Demo War Room" },
  { company: "Retail Andino", stage: "negotiation", value: "$18,000", score: 91, next: "Cerrar alcance SaaS" }
];

export const financialCases = [
  { title: "Cobro ejecutivo Nova", status: "profitable", margin: "$9,180", roi: "104%", hours: 6 },
  { title: "Laboral colectivo Andes", status: "neutral", margin: "$3,320", roi: "31%", hours: 12 },
  { title: "Contrato marco Mercurio", status: "loss", margin: "-$420", roi: "-8%", hours: 9 }
];

export const riskCases = [
  { title: "Laboral colectivo Andes", score: 88, level: "rojo", factors: ["CAPTCHA", "plazo", "audiencia"] },
  { title: "Cobro ejecutivo Nova", score: 64, level: "ambar", factors: ["documento", "cliente"] },
  { title: "Contrato marco Mercurio", score: 28, level: "verde", factors: ["controlado"] }
];

export const demoDatasets = [
  { name: "Estudio pequeno", modules: "Expediente360, Portal, Dashboard" },
  { name: "Estudio corporativo", modules: "CRM, Financial, Risk, IA" },
  { name: "Estudio litigios", modules: "War Room, SINOE, Automation" },
  { name: "Enterprise", modules: "Owner, integraciones, health score" }
];

