import { aiDisclaimer } from "@/lib/ai-demo";
import { getDemoCase360 } from "@/lib/case-360-demo";
import { commandKpis } from "@/lib/command-center-demo";
import { portalCases, portalDocuments, portalHearings, portalMessages, portalNotifications, portalReports, portalTimeline } from "@/lib/client-portal-demo";

const case360 = getDemoCase360("case-demo");

export const mobileClient = {
  name: "Nova Capital",
  metrics: [
    { label: "Expedientes", value: String(portalReports.cases), trend: "activos" },
    { label: "Documentos", value: String(portalReports.visible_documents), trend: "autorizados" },
    { label: "Audiencias", value: String(portalReports.hearings), trend: "proximas" },
    { label: "Solicitudes", value: String(portalReports.open_requests), trend: "abiertas" }
  ],
  cases: portalCases,
  timeline: portalTimeline,
  documents: portalDocuments,
  hearings: portalHearings,
  messages: portalMessages,
  notifications: portalNotifications,
  nextSteps: ["Revisar audiencia programada", "Responder solicitud documental", "Consultar nuevo mensaje"]
};

export const mobileLawyer = {
  name: "Demo Lawyer",
  metrics: commandKpis,
  cases: [
    { id: "case-demo", title: case360.case.title, status: case360.case.status, next: case360.case.next_action },
    { id: "case-andes", title: "Laboral colectivo Andes", status: "risk", next: "Preparar pruebas" },
    { id: "case-mercurio", title: "Contrato marco Mercurio", status: "active", next: "Enviar informe" }
  ],
  alerts: case360.alerts,
  tasks: case360.tasks,
  hearings: case360.hearings,
  communications: case360.communications,
  documents: case360.documents,
  judicialUpdates: case360.judicial_updates,
  aiSummary: {
    title: "Resumen IA del expediente",
    body: "Estado, documentos, audiencia proxima, comunicaciones y riesgo consolidados para revision profesional.",
    disclaimer: aiDisclaimer
  }
};
