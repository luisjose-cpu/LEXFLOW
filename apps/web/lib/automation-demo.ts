export const automationTriggers = [
  "CASE_CREATED",
  "CASE_STATUS_CHANGED",
  "HEARING_CREATED",
  "HEARING_UPCOMING",
  "DOCUMENT_REQUESTED",
  "DOCUMENT_UPLOADED",
  "JUDICIAL_UPDATE_APPROVED",
  "CAPTCHA_REQUIRED",
  "CLIENT_MESSAGE_RECEIVED",
  "TASK_OVERDUE",
  "AI_SUMMARY_COMPLETED",
  "LEGAL_NEWS_ALERT_CREATED"
];

export const automationActions = [
  "CREATE_TASK",
  "SEND_PORTAL_NOTIFICATION",
  "SEND_WHATSAPP_MESSAGE_MOCK",
  "SEND_EMAIL_PREPARED",
  "CREATE_CASE_EVENT",
  "REQUEST_DOCUMENT",
  "CHANGE_CASE_STATUS",
  "ASSIGN_USER",
  "CREATE_CLIENT_ALERT",
  "CREATE_INTERNAL_ALERT",
  "RUN_AI_SUMMARY_MOCK",
  "LINK_LEGAL_NEWS_TO_CASE"
];

export const automationWorkflow = {
  name: "Audiencia proxima -> preparacion",
  status: "active",
  trigger: "HEARING_UPCOMING",
  conditions: [
    { type: "CASE_STATUS_EQUALS", label: "Estado del expediente es active" },
    { type: "FEATURE_ENABLED", label: "Automation Studio habilitado por plan" }
  ],
  actions: [
    { type: "CREATE_TASK", label: "Crear tarea para preparar audiencia" },
    { type: "SEND_PORTAL_NOTIFICATION", label: "Notificar al cliente en portal" },
    { type: "RUN_AI_SUMMARY_MOCK", label: "Generar resumen IA mock" }
  ],
  run: {
    id: "run-demo-p13",
    status: "succeeded",
    steps: [
      { type: "condition", key: "CASE_STATUS_EQUALS", status: "succeeded" },
      { type: "condition", key: "FEATURE_ENABLED", status: "succeeded" },
      { type: "action", key: "CREATE_TASK", status: "succeeded" },
      { type: "action", key: "SEND_PORTAL_NOTIFICATION", status: "succeeded" },
      { type: "action", key: "RUN_AI_SUMMARY_MOCK", status: "succeeded" }
    ]
  }
};

export const automationMetrics = [
  { label: "Workflows", value: "4", trend: "2 activos" },
  { label: "Runs", value: "18", trend: "este mes" },
  { label: "Errores", value: "1", trend: "requiere revision" },
  { label: "Audit", value: "100%", trend: "acciones criticas" }
];
