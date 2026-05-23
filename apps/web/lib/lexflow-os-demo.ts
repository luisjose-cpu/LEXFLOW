export const osModules = [
  { name: "Legal Memory", status: "pilot-ready", detail: "Linea viva de cliente, expediente, documento, comunicacion, IA y decision." },
  { name: "RAG Legal", status: "pilot-ready", detail: "Documento -> OCR -> chunks -> embeddings -> vector store -> respuesta con fuentes." },
  { name: "Busqueda global", status: "pilot-ready", detail: "Busca clientes, expedientes, documentos, comunicaciones e inteligencia." },
  { name: "Copiloto Juridico", status: "pilot-ready", detail: "Asistente operativo con fuentes, acciones sugeridas y revision profesional." },
  { name: "Agentes IA especializados", status: "pilot-ready", detail: "Riesgo, plazos, documentos, cliente, monitoreo judicial e inteligencia." },
  { name: "Legal Graph", status: "pilot-ready", detail: "Grafo que conecta entidades y sostiene decisiones auditables." },
  { name: "Marketplace futuro", status: "planned", detail: "Adapters, plantillas, SSO, analytics y extensiones enterprise." },
  { name: "Demo Mode", status: "pilot-ready", detail: "Recorrido E2E vendible para pilotos y demos comerciales." }
];

export const ragPipeline = [
  "Documento",
  "OCR",
  "Chunks",
  "Embeddings",
  "Vector store",
  "Consulta contextual",
  "Respuesta con fuentes"
];

export const legalMemory = [
  { type: "Cliente", title: "Nova Capital", signal: "cliente prioritario con expediente activo" },
  { type: "Expediente", title: "Cobro ejecutivo Nova", signal: "riesgo controlado y proxima accion definida" },
  { type: "Documento", title: "Demanda y anexos.pdf", signal: "visible para IA y portal segun permisos" },
  { type: "Comunicacion", title: "WhatsApp mock enviado", signal: "historial multicanal auditado" },
  { type: "Decision", title: "Crear tarea posterior a respuesta cliente", signal: "automatizacion con trazabilidad" }
];

export const copilotCards = [
  { title: "Pregunta con contexto", text: "Resume el estado de Nova y cita fuentes." },
  { title: "Respuesta controlada", text: "Incluye evidencia encontrada o declara que no hay evidencia." },
  { title: "Accion sugerida", text: "Crear tarea, notificar cliente o pedir revision humana." }
];

export const aiAgents = [
  "Agente de riesgo",
  "Agente de plazos",
  "Agente documental",
  "Agente cliente",
  "Agente judicial autorizado",
  "Agente de inteligencia"
];

export const graphNodes = [
  { label: "Cliente", x: "8%", y: "48%" },
  { label: "Expediente", x: "22%", y: "24%" },
  { label: "Documento", x: "38%", y: "48%" },
  { label: "Comunicacion", x: "54%", y: "24%" },
  { label: "Automatizacion", x: "68%", y: "48%" },
  { label: "IA", x: "80%", y: "24%" },
  { label: "Decision", x: "90%", y: "48%" }
];

export const marketplaceItems = [
  "Adapters judiciales oficiales",
  "Plantillas legales verificadas",
  "SSO enterprise",
  "Analytics predictivo"
];

export const demoSteps = [
  "Socio ve dashboard",
  "Abre Expediente 360",
  "Actualizacion judicial mock",
  "IA genera resumen",
  "WhatsApp mock al cliente",
  "Cliente entra al portal",
  "Descarga documento",
  "Cliente responde",
  "Abogado ve comunicacion",
  "Automation Studio crea tarea",
  "Audit log registra"
];

export const releaseReadiness = [
  { label: "Piloto", value: "READY", tone: "good" },
  { label: "Venta SaaS", value: "DEMO READY", tone: "good" },
  { label: "Produccion publica", value: "NOT READY", tone: "risk" },
  { label: "Enterprise", value: "ROADMAP", tone: "watch" }
];

export const productionPending = [
  "Proveedor WhatsApp Business real y plantillas aprobadas.",
  "Credenciales e integraciones oficiales por fuente judicial autorizada.",
  "Vector store productivo con cifrado, backups y politicas de retencion.",
  "Pasarela de pago real, facturacion fiscal y conciliacion.",
  "Pentest externo, monitoreo 24/7 y runbooks operativos firmados."
];
