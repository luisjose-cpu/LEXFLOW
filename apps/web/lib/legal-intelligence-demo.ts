export const intelligenceSources = [
  { name: "LP Derecho", category: "Noticias", status: "active", mode: "RSS/API mock" },
  { name: "Juris.pe", category: "Jurisprudencia", status: "active", mode: "Adapter mock" },
  { name: "El Peruano", category: "Normativa", status: "active", mode: "Fuente oficial" },
  { name: "SPIJ", category: "Normativa", status: "active", mode: "Integracion preparada" },
  { name: "Poder Judicial", category: "Jurisprudencia", status: "active", mode: "Adapter mock" },
  { name: "MPFN", category: "Institucional", status: "active", mode: "Adapter mock" },
  { name: "SINOE", category: "Judicial", status: "watch", mode: "Avisos autorizados" }
];

export const intelligenceNews = [
  {
    id: "news-1",
    title: "Nuevo criterio sobre notificacion procesal",
    source: "LP Derecho",
    category: "Procesal",
    summary: "Analisis especializado sobre notificacion y debido proceso con impacto en expedientes activos.",
    aiSummary: "Resumen IA: revisar expedientes con notificaciones pendientes y alertas SINOE vinculadas. Requiere revision profesional.",
    tags: ["procesal", "notificacion", "debido-proceso"],
    trend: "rising",
    linkedCase: "Cobro ejecutivo Nova"
  },
  {
    id: "news-2",
    title: "Norma publicada para cumplimiento corporativo",
    source: "El Peruano",
    category: "Normativa",
    summary: "Disposicion oficial que requiere seguimiento por clientes corporativos.",
    aiSummary: "Resumen IA: evaluar obligaciones operativas y actualizar matriz de cumplimiento. Requiere revision profesional.",
    tags: ["normativa", "cumplimiento"],
    trend: "watch",
    linkedCase: "Contrato marco Mercurio"
  },
  {
    id: "news-3",
    title: "Jurisprudencia destacada en materia laboral",
    source: "Juris.pe",
    category: "Jurisprudencia",
    summary: "Criterio reciente para revisar estrategia documental en litigios laborales.",
    aiSummary: "Resumen IA: identificar casos laborales con pruebas pendientes de clasificacion. Requiere revision profesional.",
    tags: ["laboral", "jurisprudencia"],
    trend: "rising",
    linkedCase: "Laboral colectivo Andes"
  }
];

export const intelligenceAlerts = [
  { title: "Tendencia procesal", body: "2 fuentes mencionan notificacion y debido proceso.", severity: "medium" },
  { title: "Normativa nueva", body: "El Peruano requiere revision de cumplimiento corporativo.", severity: "high" },
  { title: "Jurisprudencia laboral", body: "Nueva linea detectada para expedientes laborales.", severity: "medium" }
];

export const intelligenceTrends = [
  { tag: "procesal", count: 8 },
  { tag: "normativa", count: 6 },
  { tag: "jurisprudencia", count: 5 },
  { tag: "laboral", count: 3 },
  { tag: "cumplimiento", count: 4 }
];

export const intelligenceMetrics = [
  { label: "Fuentes", value: "7", trend: "oficiales y especializadas" },
  { label: "Noticias", value: "24", trend: "sincronizadas por mock" },
  { label: "Alertas", value: "6", trend: "riesgo operativo" },
  { label: "Tendencias", value: "5", trend: "etiquetas activas" }
];
