export const aiDisclaimer = "Requiere revisión profesional.";

export const aiMetrics = [
  { label: "OCR", value: "3", trend: "documentos procesados" },
  { label: "Extracciones", value: "12", trend: "fechas, partes y plazos" },
  { label: "Pendientes", value: "4", trend: "revision profesional" },
  { label: "Auditoria", value: "100%", trend: "uso IA trazado" }
];

export const aiDocumentJobs = [
  {
    id: "job-ocr-1",
    type: "ocr",
    document: "demanda.pdf",
    status: "pending_review",
    result: "Texto OCR extraido con fecha 2026-05-28, parte Nova Capital y plazo de 5 dias."
  },
  {
    id: "job-classify-1",
    type: "classify",
    document: "anexos_financieros.pdf",
    status: "pending_review",
    result: "Clasificacion sugerida: evidence, confianza 0.86."
  },
  {
    id: "job-extract-1",
    type: "extract",
    document: "demanda.pdf",
    status: "pending_review",
    result: "Fechas, partes, plazos y obligaciones extraidas para revision."
  }
];

export const aiExtractions = [
  { label: "Fechas", value: "2026-05-28 audiencia" },
  { label: "Partes", value: "Nova Capital, Equipo legal" },
  { label: "Plazos", value: "5 dias para presentar anexos" },
  { label: "Obligaciones", value: "Presentar anexos, revisar poder faltante" }
];

export const aiPrompts = [
  "summarize_document",
  "classify_document",
  "extract_dates",
  "extract_parties",
  "extract_deadlines",
  "extract_obligations",
  "case_summary",
  "smart_search",
  "draft_assistant"
];

export const aiSearchResults = [
  { source: "Documento", title: "demanda.pdf", excerpt: "Contiene admision de demanda y anexos requeridos." },
  { source: "Timeline", title: "Pruebas clasificadas", excerpt: "IA detecto faltante de poder." },
  { source: "Comunicacion", title: "Portal cliente", excerpt: "Cliente confirma recepcion y solicita detalle de audiencia." }
];
