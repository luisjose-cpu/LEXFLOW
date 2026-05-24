import type { Case360Data } from "@/components/case-360";

export function getDemoCase360(caseId: string): Case360Data {
  const now = new Date();
  const inDays = (days: number) => new Date(now.getTime() + days * 24 * 60 * 60 * 1000).toISOString();
  const agoDays = (days: number) => new Date(now.getTime() - days * 24 * 60 * 60 * 1000).toISOString();

  return {
    case: {
      id: caseId,
      title: "Cobro ejecutivo Nova Capital",
      status: "risk",
      priority: "high",
      risk: "high",
      responsible: "Dra. Laura Mendoza",
      next_action: "Preparar memorial y anexos antes de la audiencia",
      external_case_number: "11001-31-03-001-2026-00001"
    },
    client: {
      name: "Nova Capital",
      contact_email: "legal@novacapital.demo",
      risk_profile: "high",
      tags: ["corporate", "priority", "portal"]
    },
    timeline: [
      { id: "evt-1", title: "Demanda admitida", description: "El juzgado admitio la demanda y ordeno notificar.", occurred_at: agoDays(8) },
      { id: "evt-2", title: "Pruebas clasificadas", description: "IA clasifico anexos y detecto faltante de poder.", occurred_at: agoDays(3) },
      { id: "evt-3", title: "Fuente judicial pausada", description: "La fuente requiere CAPTCHA; se solicito intervencion humana.", occurred_at: agoDays(1) }
    ],
    documents: [
      {
        id: "doc-1",
        filename: "demanda.pdf",
        classification: "pleading",
        status: "verified",
        file_size_bytes: 184320,
        checksum_sha256: "407e390574196ccda2e0366cd124a6f1d4c9dcb33b1c8151f2efa9023265b8ab",
        storage_verified_at: agoDays(2),
        malware_scan_status: "clean",
        created_at: agoDays(9)
      },
      {
        id: "doc-2",
        filename: "anexos_financieros.pdf",
        classification: "evidence",
        status: "pending_review",
        file_size_bytes: 0,
        checksum_sha256: null,
        storage_verified_at: null,
        malware_scan_status: "pending",
        created_at: agoDays(3)
      }
    ],
    hearings: [{ id: "hea-1", title: "Audiencia inicial", starts_at: inDays(6), location: "Virtual", status: "scheduled" }],
    tasks: [
      { id: "tsk-1", title: "Preparar memorial", status: "open", due_at: inDays(2) },
      { id: "tsk-2", title: "Validar poder faltante", status: "open", due_at: inDays(1) }
    ],
    case_sources: [
      {
        id: "src-sinoe-1",
        source_type: "sinoe",
        source_name: "SINOE",
        external_case_number: "SINOE-2026-001",
        court_name: "Lima / Sede Central / Casilla autorizada",
        status: "active",
        captcha_required: false,
        last_checked_at: agoDays(2),
        last_result: "updates_found"
      },
      {
        id: "src-sinoe-2",
        source_type: "sinoe",
        source_name: "SINOE",
        external_case_number: "SINOE-CAPTCHA-001",
        court_name: "Lima / Sede Central",
        status: "paused_captcha",
        captcha_required: true,
        last_checked_at: agoDays(1),
        last_result: "captcha_required"
      }
    ],
    judicial_updates: [
      { id: "jud-1", title: "Auto reconoce personeria", summary: "Actualizacion judicial registrada y auditada.", status: "recorded", captcha_required: false, requires_human_intervention: false, checked_at: agoDays(2) },
      { id: "jud-2", title: "CAPTCHA requerido", summary: "LEXFLOW pauso la consulta y solicito intervencion humana.", status: "paused", captcha_required: true, requires_human_intervention: true, checked_at: agoDays(1) }
    ],
    communications: [
      { id: "com-1", direction: "outbound", channel: "whatsapp", body: "Se envio resumen al cliente por WhatsApp Business.", status: "sent", created_at: agoDays(1) },
      { id: "com-2", direction: "inbound", channel: "portal", body: "Cliente confirma recepcion y solicita detalle de audiencia.", status: "received", created_at: agoDays(0) }
    ],
    alerts: [
      { id: "alt-1", title: "Audiencia proxima", body: "Audiencia en 6 dias.", status: "pending", created_at: agoDays(1) },
      { id: "alt-2", title: "Intervencion humana requerida", body: "Resolver CAPTCHA de fuente judicial.", status: "pending", created_at: agoDays(1) }
    ],
    related_intelligence: [
      {
        id: "int-1",
        title: "Nuevo criterio sobre notificacion procesal",
        category: "Jurisprudencia",
        summary: "Puede impactar expedientes con notificaciones pendientes y alertas SINOE.",
        tags: ["procesal", "debido-proceso"],
        published_at: agoDays(1)
      }
    ],
    audit_summary: {
      total: 18,
      latest: [
        { id: "aud-1", action: "captcha_required", entity_type: "case_source", created_at: agoDays(1) },
        { id: "aud-2", action: "create", entity_type: "document", created_at: agoDays(3) },
        { id: "aud-3", action: "change_status", entity_type: "case", created_at: agoDays(4) }
      ]
    },
    next_actions: [
      { id: "nxt-1", title: "Preparar memorial y anexos", status: "open" },
      { id: "nxt-2", title: "Resolver fuente judicial con intervencion humana", status: "open" }
    ]
  };
}
