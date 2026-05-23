import { Badge, Button, Card, EmptyState, Input, Modal } from "@lexflow/ui";
import { AlertTriangle, Clock, Scale, ShieldCheck } from "lucide-react";
import React from "react";

export interface JudicialSourceView {
  id: string;
  source_type: string;
  external_case_number: string;
  court_name: string;
  status: string;
  captcha_required: boolean;
  last_checked_at?: string | null;
}

export interface JudicialUpdateView {
  id: string;
  title: string;
  summary: string;
  status: string;
  captcha_required: boolean;
  requires_human_intervention: boolean;
}

export interface CaptchaCheckpointView {
  id: string;
  status: string;
  reason: string;
}

export function JudicialSourcesPanel({ sources }: { sources: JudicialSourceView[] }) {
  return (
    <Card>
      <PanelTitle title="Fuentes judiciales" />
      {sources.length ? (
        <div className="mt-4 grid gap-3">
          {sources.map((source) => (
            <div className="rounded-lg border border-slate-200 bg-mist p-4" key={source.id}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-ink">{source.court_name}</p>
                  <p className="mt-1 text-sm text-slate-600">{source.source_type} - {source.external_case_number}</p>
                </div>
                <JudicialUpdateStatusCard status={source.status} captchaRequired={source.captcha_required} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-4">
          <EmptyState title="Sin fuentes configuradas" description="Agrega una fuente oficial o autorizada para monitoreo judicial." />
        </div>
      )}
    </Card>
  );
}

export function JudicialUpdateStatusCard({ status, captchaRequired }: { status: string; captchaRequired: boolean }) {
  if (captchaRequired) {
    return <span className="inline-flex items-center gap-1 rounded-md bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-700"><AlertTriangle size={14} /> CAPTCHA</span>;
  }
  return <span className="inline-flex items-center gap-1 rounded-md bg-legal-50 px-2.5 py-1 text-xs font-semibold text-legal-700"><Clock size={14} /> {status}</span>;
}

export function CaptchaCheckpointModal({ checkpoint }: { checkpoint: CaptchaCheckpointView | null }) {
  if (!checkpoint) return null;
  return (
    <Modal title="Intervencion humana requerida">
      <div className="grid gap-3">
        <p>La fuente judicial requiere CAPTCHA. LEXFLOW pauso el monitoreo y no intentara evadir controles anti-bot.</p>
        <Badge>{checkpoint.status}</Badge>
        <Input label="Nota de resolucion" placeholder="Describe la validacion humana realizada" />
        <Button>Registrar resolucion humana</Button>
      </div>
    </Modal>
  );
}

export function JudicialUpdateTimelineItem({ update }: { update: JudicialUpdateView }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-mist p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-ink">{update.title}</p>
          <p className="mt-1 text-sm leading-6 text-slate-600">{update.summary}</p>
        </div>
        <JudicialUpdateStatusCard status={update.status} captchaRequired={update.captcha_required} />
      </div>
    </div>
  );
}

export function SourceConfigurationForm() {
  return (
    <Card>
      <PanelTitle title="Configurar fuente" />
      <div className="mt-4 grid gap-4">
        <Input label="Radicado externo" placeholder="PJ-2026-001" />
        <Input label="Juzgado o entidad" placeholder="Poder Judicial / CEJ / SINOE / MPFN" />
        <div className="flex flex-wrap gap-2">
          <Button>Guardar fuente</Button>
          <Button tone="secondary">Probar adapter mock</Button>
        </div>
      </div>
    </Card>
  );
}

export function JudicialUpdatesList({ updates }: { updates: JudicialUpdateView[] }) {
  return (
    <Card>
      <PanelTitle title="Timeline judicial" />
      <div className="mt-4 grid gap-3">
        {updates.map((update) => <JudicialUpdateTimelineItem key={update.id} update={update} />)}
      </div>
    </Card>
  );
}

function PanelTitle({ title }: { title: string }) {
  return (
    <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
      <Scale size={18} />
      <span>{title}</span>
      <span className="ml-auto inline-flex items-center gap-1 text-xs text-slate-500"><ShieldCheck size={14} /> autorizado</span>
    </div>
  );
}

export const demoJudicialSources: JudicialSourceView[] = [
  { id: "src-1", source_type: "poder_judicial", external_case_number: "PJ-2026-001", court_name: "Poder Judicial Demo", status: "active", captcha_required: false },
  { id: "src-2", source_type: "cej", external_case_number: "CEJ-CAPTCHA", court_name: "CEJ Demo", status: "paused_captcha", captcha_required: true }
];

export const demoJudicialUpdates: JudicialUpdateView[] = [
  { id: "upd-1", title: "Auto registrado", summary: "Adapter mock obtuvo una actualizacion pendiente de aprobacion.", status: "pending_approval", captcha_required: false, requires_human_intervention: false },
  { id: "upd-2", title: "CAPTCHA detectado", summary: "Consulta pausada para flujo human-in-the-loop.", status: "paused", captcha_required: true, requires_human_intervention: true }
];
