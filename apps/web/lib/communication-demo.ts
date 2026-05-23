export const communicationThreads = [
  {
    id: "thread-1",
    subject: "Comunicacion Cobro ejecutivo Nova",
    channel: "whatsapp",
    status: "open",
    messages: [
      { id: "msg-1", direction: "outbound", channel: "whatsapp", body: "Recordatorio de audiencia enviado por WhatsApp mock.", status: "sent" },
      { id: "msg-2", direction: "inbound", channel: "portal", body: "Cliente confirma recepcion y adjunta comprobante.", status: "received" }
    ]
  },
  {
    id: "thread-2",
    subject: "Solicitud de documento",
    channel: "portal",
    status: "open",
    messages: [
      { id: "msg-3", direction: "outbound", channel: "portal", body: "Necesitamos el poder actualizado para continuar.", status: "sent" }
    ]
  }
];

export const messageTemplates = [
  { code: "audiencia_proxima", name: "Audiencia proxima", channel: "whatsapp", body: "Recordatorio de audiencia: {{case_title}} tiene audiencia el {{hearing_date}}." },
  { code: "documento_requerido", name: "Documento requerido", channel: "whatsapp", body: "Necesitamos el documento {{document_name}} para continuar con {{case_title}}." },
  { code: "informe_disponible", name: "Informe disponible", channel: "portal", body: "Ya esta disponible el informe de {{case_title}} en tu portal." },
  { code: "actualizacion_expediente", name: "Actualizacion expediente", channel: "whatsapp", body: "Hay una actualizacion aprobada en {{case_title}}: {{update_summary}}." },
  { code: "proximo_paso", name: "Proximo paso", channel: "portal", body: "El proximo paso de {{case_title}} es {{next_action}}." }
];

export const notificationRules = [
  { id: "rule-1", name: "Audiencia proxima", event_type: "hearing.upcoming", channel: "whatsapp", status: "active" },
  { id: "rule-2", name: "Documento requerido", event_type: "document.required", channel: "whatsapp", status: "active" },
  { id: "rule-3", name: "Informe disponible", event_type: "report.available", channel: "portal", status: "active" }
];

export const communicationMetrics = [
  { label: "Threads", value: "2", trend: "expediente actual" },
  { label: "WhatsApp mock", value: "100%", trend: "entrega simulada" },
  { label: "Plantillas", value: "5", trend: "base P7" },
  { label: "Auditoria", value: "100%", trend: "mensajes trazados" }
];
