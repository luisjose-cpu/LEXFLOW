export interface PortalCase {
  id: string;
  title: string;
  status: string;
  external_case_number: string;
  updated_at: string;
  next_hearing: string;
}

export interface PortalDocument {
  id: string;
  case_id: string;
  filename: string;
  status: string;
  classification: string;
  uploaded_by_client: boolean;
  file_size_bytes: number;
  checksum_sha256: string | null;
  storage_verified_at: string | null;
  malware_scan_status: "pending" | "clean" | "infected";
}

export interface PortalTimelineItem {
  id: string;
  type: "case_event" | "judicial_update";
  title: string;
  summary: string;
  occurred_at: string;
}

export interface PortalNotification {
  id: string;
  title: string;
  body: string;
  status: string;
}

export interface PortalMessage {
  id: string;
  direction: "inbound" | "outbound";
  body: string;
  status: string;
  created_at: string;
}

export const portalClient = {
  name: "Nova Capital",
  contact_email: "client@lexflow.demo",
  status: "active"
};

export const portalCases: PortalCase[] = [
  {
    id: "portal-case-1",
    title: "Cobro ejecutivo Nova",
    status: "active",
    external_case_number: "11001-31-03-001-2026-00001",
    updated_at: "22 may 2026",
    next_hearing: "28 may 2026, 7:51"
  }
];

export const portalTimeline: PortalTimelineItem[] = [
  {
    id: "tl-1",
    type: "case_event",
    title: "Expediente creado",
    summary: "El expediente fue registrado y habilitado para consulta del cliente.",
    occurred_at: "14 may 2026"
  },
  {
    id: "tl-2",
    type: "judicial_update",
    title: "Auto reconoce personeria",
    summary: "Actualizacion judicial aprobada por el equipo legal.",
    occurred_at: "21 may 2026"
  }
];

export const portalDocuments: PortalDocument[] = [
  {
    id: "doc-1",
    case_id: "portal-case-1",
    filename: "demanda.pdf",
    status: "verified",
    classification: "pleading",
    uploaded_by_client: false,
    file_size_bytes: 184320,
    checksum_sha256: "407e390574196ccda2e0366cd124a6f1d4c9dcb33b1c8151f2efa9023265b8ab",
    storage_verified_at: "22 may 2026, 10:20",
    malware_scan_status: "clean"
  },
  {
    id: "doc-2",
    case_id: "portal-case-1",
    filename: "comprobante.pdf",
    status: "pending_review",
    classification: "client_upload",
    uploaded_by_client: true,
    file_size_bytes: 0,
    checksum_sha256: null,
    storage_verified_at: null,
    malware_scan_status: "pending"
  }
];

export const portalHearings = [
  { id: "hr-1", title: "Audiencia inicial", starts_at: "28 may 2026, 7:51", location: "Virtual", status: "scheduled" }
];

export const portalNotifications: PortalNotification[] = [
  { id: "nt-1", title: "Resumen disponible", body: "Tu expediente tiene una actualizacion visible en el portal.", status: "sent" },
  { id: "nt-2", title: "Audiencia proxima", body: "Audiencia inicial programada en sala virtual.", status: "pending" }
];

export const portalMessages: PortalMessage[] = [
  { id: "msg-1", direction: "outbound", body: "Se compartio el resumen aprobado del expediente.", status: "sent", created_at: "21 may 2026" },
  { id: "msg-2", direction: "inbound", body: "Recibido. Enviaremos el comprobante.", status: "received", created_at: "22 may 2026" }
];

export const portalReports = {
  cases: 1,
  visible_documents: 2,
  hearings: 1,
  open_requests: 0
};
