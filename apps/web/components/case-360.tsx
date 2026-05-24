import { Badge, Card, EmptyState, MetricCard } from "@lexflow/ui";
import { AlertTriangle, CheckCircle2, Clock, FileText, MessageCircle, Newspaper, Scale, ShieldCheck } from "lucide-react";
import React from "react";
import type { ReactNode } from "react";

export interface Case360Data {
  case: {
    id: string;
    title: string;
    status: string;
    priority: string;
    risk: string;
    responsible: string;
    next_action: string;
    external_case_number: string;
  };
  client: {
    name: string;
    contact_email: string;
    risk_profile: string;
    tags: string[];
  };
  timeline: Array<{ id: string; title: string; description: string; occurred_at: string }>;
  documents: Array<{
    id: string;
    filename: string;
    classification: string;
    status: string;
    file_size_bytes: number;
    checksum_sha256: string | null;
    storage_verified_at: string | null;
    malware_scan_status: string;
    is_client_visible?: boolean;
    created_at: string;
  }>;
  hearings: Array<{ id: string; title: string; starts_at: string; location: string; status: string }>;
  tasks: Array<{ id: string; title: string; status: string; due_at: string }>;
  case_sources: Array<{
    id: string;
    source_type: string;
    source_name?: string | null;
    external_case_number: string;
    court_name?: string | null;
    status: string;
    captcha_required: boolean;
    last_checked_at?: string | null;
    last_result?: string | null;
  }>;
  judicial_updates: Array<{ id: string; title: string; summary: string; status: string; captcha_required: boolean; requires_human_intervention: boolean; checked_at: string }>;
  communications: Array<{ id: string; direction: string; channel?: string; body: string; status: string; created_at: string }>;
  alerts: Array<{ id: string; title: string; body: string; status: string; created_at: string }>;
  related_intelligence: Array<{ id: string; title: string; category: string; summary: string; tags: string[]; published_at: string }>;
  audit_summary: { total: number; latest: Array<{ id: string; action: string; entity_type: string; created_at: string }> };
  next_actions: Array<{ id: string; title: string; status: string }>;
}

export function StatusBadge({ status }: { status: string }) {
  const tone = status === "risk" ? "bg-rose-50 text-rose-700" : status === "closed" ? "bg-slate-100 text-slate-700" : "bg-emerald-50 text-emerald-700";
  return <span className={`rounded-md px-2.5 py-1 text-xs font-semibold ${tone}`}>{status}</span>;
}

export function RiskBadge({ risk }: { risk: string }) {
  const tone = risk === "high" ? "bg-rose-50 text-rose-700" : risk === "medium" ? "bg-amber-50 text-amber-700" : "bg-legal-50 text-legal-700";
  return <span className={`rounded-md px-2.5 py-1 text-xs font-semibold ${tone}`}>Riesgo {risk}</span>;
}

export function CaseHeader({ data }: { data: Case360Data }) {
  return (
    <Card>
      <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge>Expediente 360</Badge>
            <StatusBadge status={data.case.status} />
            <RiskBadge risk={data.case.risk} />
          </div>
          <h1 className="mt-4 text-3xl font-semibold tracking-normal text-ink sm:text-4xl">{data.case.title}</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            Radicado {data.case.external_case_number}. Responsable: {data.case.responsible}.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-3 lg:min-w-[420px]">
          <MetricCard label="Prioridad" value={data.case.priority} trend="segun riesgo y vencimientos" />
          <MetricCard label="Auditoria" value={String(data.audit_summary.total)} trend="eventos trazados" />
          <MetricCard label="Siguiente" value={data.next_actions.length ? String(data.next_actions.length) : "0"} trend="acciones abiertas" />
        </div>
      </div>
    </Card>
  );
}

export function ClientSummaryCard({ data }: { data: Case360Data }) {
  return (
    <Card>
      <PanelTitle icon={<ShieldCheck size={18} />} title="Cliente" />
      <h2 className="mt-4 text-xl font-semibold text-ink">{data.client.name}</h2>
      <p className="mt-1 text-sm text-slate-500">{data.client.contact_email}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {data.client.tags.map((tag) => (
          <Badge key={tag}>{tag}</Badge>
        ))}
      </div>
    </Card>
  );
}

export function CaseTimeline({ items }: { items: Case360Data["timeline"] }) {
  return (
    <Card className="lg:col-span-2">
      <PanelTitle icon={<Clock size={18} />} title="Timeline" />
      <div className="mt-4 grid gap-3">
        {items.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <p className="text-sm font-semibold text-ink">{item.title}</p>
            <p className="mt-1 text-sm text-slate-600">{item.description}</p>
            <p className="mt-2 text-xs font-medium text-legal-700">{formatDate(item.occurred_at)}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function DocumentsPanel({ items }: { items: Case360Data["documents"] }) {
  return (
    <Card>
      <PanelTitle icon={<FileText size={18} />} title="Documentos" />
      <div className="mt-4 grid gap-3">
        {items.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-ink">{item.filename}</p>
              <StatusBadge status={item.status} />
            </div>
            <p className="mt-2 text-sm text-slate-600">{item.classification}</p>
            <div className="mt-3 grid gap-2 text-xs font-semibold text-slate-600 sm:grid-cols-3">
              <span>{formatBytes(item.file_size_bytes)}</span>
              <span>{item.malware_scan_status}</span>
              <span>{shortHash(item.checksum_sha256)}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function HearingsPanel({ items }: { items: Case360Data["hearings"] }) {
  return <ListPanel icon={<Scale size={18} />} title="Audiencias" items={items.map((item) => `${item.title} - ${formatDate(item.starts_at)}`)} empty="Sin audiencias" />;
}

export function TasksPanel({ items }: { items: Case360Data["tasks"] }) {
  return <ListPanel icon={<CheckCircle2 size={18} />} title="Tareas" items={items.map((item) => `${item.title} - ${item.status}`)} empty="Sin tareas abiertas" />;
}

export function JudicialUpdatesPanel({ items }: { items: Case360Data["judicial_updates"] }) {
  return (
    <Card>
      <PanelTitle icon={<Scale size={18} />} title="Actualizaciones judiciales" />
      <div className="mt-4 grid gap-3">
        {items.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-ink">{item.title}</p>
              {item.captcha_required ? <RiskBadge risk="high" /> : <StatusBadge status={item.status} />}
            </div>
            <p className="mt-2 text-sm text-slate-600">{item.summary}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function CommunicationsPanel({ items }: { items: Case360Data["communications"] }) {
  return <ListPanel icon={<MessageCircle size={18} />} title="Comunicaciones" items={items.map((item) => `${item.channel ?? "portal"} / ${item.direction}: ${item.body}`)} empty="Sin comunicaciones" />;
}

export function AlertsPanel({ items }: { items: Case360Data["alerts"] }) {
  return <ListPanel icon={<AlertTriangle size={18} />} title="Alertas" items={items.map((item) => `${item.title} - ${item.status}`)} empty="Sin alertas" />;
}

export function AuditSummaryPanel({ data }: { data: Case360Data["audit_summary"] }) {
  return <ListPanel icon={<ShieldCheck size={18} />} title="Bitacora" items={data.latest.map((item) => `${item.action} - ${item.entity_type}`)} empty="Sin auditoria" />;
}

export function IntelligenceRelatedPanel({ items }: { items: Case360Data["related_intelligence"] }) {
  return (
    <Card>
      <PanelTitle icon={<Newspaper size={18} />} title="Inteligencia relacionada" />
      {items.length ? (
        <div className="mt-4 grid gap-3">
          {items.map((item) => (
            <div className="rounded-lg border border-slate-200 bg-mist p-3" key={item.id}>
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{item.category}</Badge>
                {item.tags.slice(0, 2).map((tag) => (
                  <span className="rounded-md bg-white px-2.5 py-1 text-xs font-semibold text-slate-600" key={tag}>
                    #{tag}
                  </span>
                ))}
              </div>
              <p className="mt-3 text-sm font-semibold text-ink">{item.title}</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">{item.summary}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-4">
          <EmptyState description="Vincula noticias, normativa o jurisprudencia desde el Centro de Inteligencia." title="Sin inteligencia vinculada" />
        </div>
      )}
    </Card>
  );
}

export function NextActionsPanel({ items }: { items: Case360Data["next_actions"] }) {
  return <ListPanel icon={<CheckCircle2 size={18} />} title="Proximas acciones" items={items.map((item) => `${item.title} - ${item.status}`)} empty="Sin acciones pendientes" />;
}

function ListPanel({ icon, title, items, empty }: { icon: ReactNode; title: string; items: string[]; empty: string }) {
  return (
    <Card>
      <PanelTitle icon={icon} title={title} />
      {items.length ? (
        <ul className="mt-4 grid gap-3">
          {items.map((item) => (
            <li className="rounded-lg border border-slate-200 bg-mist p-3 text-sm font-medium leading-6 text-ink" key={item}>
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-4">
          <EmptyState description="Este panel se actualiza con el flujo real del expediente." title={empty} />
        </div>
      )}
    </Card>
  );
}

function PanelTitle({ icon, title }: { icon: ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
      {icon}
      <span>{title}</span>
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function formatBytes(value: number) {
  if (!value) return "sin bytes";
  if (value < 1024) return `${value} B`;
  return `${Math.round(value / 1024)} KB`;
}

function shortHash(value: string | null) {
  return value ? `sha256 ${value.slice(0, 8)}` : "sin checksum";
}
