import { Badge, Button, Card, EmptyState, Input, MetricCard } from "@lexflow/ui";
import { Bell, CalendarDays, FileText, LockKeyhole, MessageSquare, Scale, ShieldCheck, Upload, UserRound } from "lucide-react";
import Link from "next/link";
import React from "react";
import {
  portalCases,
  portalClient,
  portalDocuments,
  portalHearings,
  portalMessages,
  portalNotifications,
  portalReports,
  portalTimeline,
  type PortalCase,
  type PortalDocument,
  type PortalMessage,
  type PortalNotification,
  type PortalTimelineItem
} from "@/lib/client-portal-demo";

const portalLinks = [
  { href: "/portal", label: "Inicio", icon: ShieldCheck },
  { href: "/portal/cases", label: "Expedientes", icon: Scale },
  { href: "/portal/documents", label: "Documentos", icon: FileText },
  { href: "/portal/messages", label: "Mensajes", icon: MessageSquare },
  { href: "/portal/notifications", label: "Avisos", icon: Bell },
  { href: "/portal/profile", label: "Perfil", icon: UserRound }
];

export function PortalShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen bg-mist">
      <header className="border-b border-white/80 bg-white/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <Link className="flex items-center gap-3" href="/portal">
              <span className="grid h-10 w-10 place-items-center rounded-md bg-legal-900 text-white">
                <ShieldCheck size={19} aria-hidden="true" />
              </span>
              <span>
                <span className="block text-sm font-semibold text-legal-900">LEXFLOW Portal</span>
                <span className="block text-xs text-slate-500">{portalClient.name}</span>
              </span>
            </Link>
            <Badge>sesion cliente segura</Badge>
          </div>
          <nav className="flex gap-2 overflow-x-auto pb-1">
            {portalLinks.map((item) => (
              <Link
                className="inline-flex h-10 shrink-0 items-center gap-2 rounded-md px-3 text-sm font-semibold text-slate-600 transition hover:bg-legal-50 hover:text-legal-900"
                href={item.href}
                key={item.href}
              >
                <item.icon size={16} aria-hidden="true" />
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <section className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</section>
    </main>
  );
}

export function PortalLoginView() {
  return (
    <main className="grid min-h-screen bg-mist px-4 py-8">
      <section className="mx-auto grid w-full max-w-5xl items-center gap-6 lg:grid-cols-[1fr_420px]">
        <div>
          <Badge>Portal Cliente</Badge>
          <h1 className="mt-4 max-w-2xl text-4xl font-semibold tracking-normal text-ink sm:text-5xl">Nova Capital</h1>
          <p className="mt-4 max-w-xl text-base leading-7 text-slate-600">
            Expedientes, documentos, audiencias, mensajes e informes autorizados en una experiencia segura.
          </p>
          <div className="mt-6 grid max-w-xl gap-3 sm:grid-cols-3">
            <MetricCard label="Expedientes" value="1" trend="activos" />
            <MetricCard label="Documentos" value="2" trend="visibles" />
            <MetricCard label="Avisos" value="2" trend="pendientes" />
          </div>
        </div>
        <Card>
          <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
            <LockKeyhole size={18} />
            Acceso seguro
          </div>
          <div className="mt-5 grid gap-4">
            <Input label="Email" placeholder="client@lexflow.demo" type="email" />
            <Input label="Password" placeholder="************" type="password" />
            <Button>Ingresar</Button>
          </div>
        </Card>
      </section>
    </main>
  );
}

export function PortalHomeView() {
  return (
    <PortalShell>
      <div className="grid gap-5">
        <PortalHeader title="Portal Cliente" subtitle={portalClient.name} />
        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard label="Expedientes" value={String(portalReports.cases)} trend="autorizados" />
          <MetricCard label="Documentos" value={String(portalReports.visible_documents)} trend="visibles" />
          <MetricCard label="Audiencias" value={String(portalReports.hearings)} trend="programadas" />
          <MetricCard label="Solicitudes" value={String(portalReports.open_requests)} trend="abiertas" />
        </div>
        <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <CasesPanel cases={portalCases} />
          <NotificationsPanel notifications={portalNotifications} />
        </div>
        <TimelinePanel items={portalTimeline} />
      </div>
    </PortalShell>
  );
}

export function PortalCasesView() {
  return (
    <PortalShell>
      <div className="grid gap-5">
        <PortalHeader title="Expedientes" subtitle="Cobertura autorizada" />
        <CasesPanel cases={portalCases} />
      </div>
    </PortalShell>
  );
}

export function PortalCaseDetailView() {
  return (
    <PortalShell>
      <div className="grid gap-5">
        <PortalHeader title="Cobro ejecutivo Nova" subtitle="11001-31-03-001-2026-00001" />
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Estado" value="active" trend="visible para cliente" />
          <MetricCard label="Audiencias" value="1" trend="proxima fecha" />
          <MetricCard label="Documentos" value="2" trend="autorizados" />
        </div>
        <div className="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <TimelinePanel items={portalTimeline} />
          <HearingsPanel />
        </div>
        <DocumentsPanel documents={portalDocuments} />
        <MessagesPanel messages={portalMessages} />
      </div>
    </PortalShell>
  );
}

export function PortalDocumentsView() {
  return (
    <PortalShell>
      <div className="grid gap-5">
        <PortalHeader title="Documentos" subtitle="Autorizados y recibidos" />
        <DocumentsPanel documents={portalDocuments} />
        <UploadPanel />
      </div>
    </PortalShell>
  );
}

export function PortalNotificationsView() {
  return (
    <PortalShell>
      <div className="grid gap-5">
        <PortalHeader title="Avisos" subtitle="Estado del expediente" />
        <NotificationsPanel notifications={portalNotifications} />
      </div>
    </PortalShell>
  );
}

export function PortalMessagesView() {
  return (
    <PortalShell>
      <div className="grid gap-5">
        <PortalHeader title="Mensajes" subtitle="Canal auditado" />
        <MessagesPanel messages={portalMessages} />
        <MessageComposer />
      </div>
    </PortalShell>
  );
}

export function PortalProfileView() {
  return (
    <PortalShell>
      <div className="grid gap-5">
        <PortalHeader title="Perfil" subtitle={portalClient.contact_email} />
        <Card>
          <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
            <UserRound size={18} />
            {portalClient.name}
          </div>
          <div className="mt-4 grid gap-3 text-sm text-slate-600">
            <p>Email: {portalClient.contact_email}</p>
            <p>Estado: {portalClient.status}</p>
            <p>Permisos: portal:read, portal:message, portal:upload</p>
          </div>
        </Card>
      </div>
    </PortalShell>
  );
}

function PortalHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <header className="rounded-lg border border-white/80 bg-white p-5 shadow-soft">
      <p className="text-sm font-semibold text-legal-700">{subtitle}</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-normal text-ink sm:text-4xl">{title}</h1>
    </header>
  );
}

function CasesPanel({ cases }: { cases: PortalCase[] }) {
  if (!cases.length) {
    return <EmptyState title="Sin expedientes" description="No hay expedientes autorizados para esta cuenta." />;
  }
  return (
    <Card>
      <PanelTitle icon={<Scale size={18} />} title="Expedientes" />
      <div className="mt-4 grid gap-3">
        {cases.map((item) => (
          <Link className="rounded-lg border border-slate-200 bg-mist p-4 transition hover:border-legal-200 hover:bg-legal-50" href={`/portal/cases/${item.id}`} key={item.id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-ink">{item.title}</p>
                <p className="mt-1 text-sm text-slate-600">{item.external_case_number}</p>
              </div>
              <Badge>{item.status}</Badge>
            </div>
            <p className="mt-3 text-xs font-semibold text-legal-700">Audiencia: {item.next_hearing}</p>
          </Link>
        ))}
      </div>
    </Card>
  );
}

function TimelinePanel({ items }: { items: PortalTimelineItem[] }) {
  return (
    <Card>
      <PanelTitle icon={<CalendarDays size={18} />} title="Timeline visible" />
      <div className="mt-4 grid gap-3">
        {items.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-ink">{item.title}</p>
              <Badge>{item.type === "judicial_update" ? "aprobado" : "publico"}</Badge>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.summary}</p>
            <p className="mt-2 text-xs font-semibold text-legal-700">{item.occurred_at}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function DocumentsPanel({ documents }: { documents: PortalDocument[] }) {
  return (
    <Card>
      <PanelTitle icon={<FileText size={18} />} title="Documentos autorizados" />
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {documents.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <p className="text-sm font-semibold text-ink">{item.filename}</p>
            <p className="mt-1 text-sm text-slate-600">{item.classification}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge>{item.status}</Badge>
              {item.uploaded_by_client ? <Badge>recibido</Badge> : null}
              <Badge>{item.malware_scan_status}</Badge>
            </div>
            <div className="mt-3 grid gap-1 text-xs font-semibold text-slate-600 sm:grid-cols-3">
              <span>{formatBytes(item.file_size_bytes)}</span>
              <span>{item.storage_verified_at ? "storage verificado" : "storage pendiente"}</span>
              <span>{shortHash(item.checksum_sha256)}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function HearingsPanel() {
  return (
    <Card>
      <PanelTitle icon={<CalendarDays size={18} />} title="Audiencias" />
      <div className="mt-4 grid gap-3">
        {portalHearings.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <p className="text-sm font-semibold text-ink">{item.title}</p>
            <p className="mt-1 text-sm text-slate-600">{item.starts_at}</p>
            <p className="mt-1 text-xs font-semibold text-legal-700">{item.location}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function NotificationsPanel({ notifications }: { notifications: PortalNotification[] }) {
  return (
    <Card>
      <PanelTitle icon={<Bell size={18} />} title="Avisos" />
      <div className="mt-4 grid gap-3">
        {notifications.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <p className="text-sm font-semibold text-ink">{item.title}</p>
            <p className="mt-1 text-sm leading-6 text-slate-600">{item.body}</p>
            <p className="mt-2 text-xs font-semibold text-legal-700">{item.status}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function MessagesPanel({ messages }: { messages: PortalMessage[] }) {
  return (
    <Card>
      <PanelTitle icon={<MessageSquare size={18} />} title="Mensajes" />
      <div className="mt-4 grid gap-3">
        {messages.map((item) => (
          <div className={`rounded-lg border border-slate-200 p-4 ${item.direction === "inbound" ? "bg-white" : "bg-mist"}`} key={item.id}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-ink">{item.direction === "inbound" ? "Cliente" : "Equipo legal"}</p>
              <Badge>{item.status}</Badge>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.body}</p>
            <p className="mt-2 text-xs font-semibold text-legal-700">{item.created_at}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function MessageComposer() {
  return (
    <Card>
      <PanelTitle icon={<MessageSquare size={18} />} title="Nueva solicitud" />
      <div className="mt-4 grid gap-4">
        <Input label="Mensaje" placeholder="Escribe tu solicitud" />
        <Button>Enviar mensaje</Button>
      </div>
    </Card>
  );
}

function UploadPanel() {
  return (
    <Card>
      <PanelTitle icon={<Upload size={18} />} title="Subir documento" />
      <div className="mt-4 grid gap-4">
        <Input label="Archivo" placeholder="comprobante.pdf" />
        <Button>Enviar documento</Button>
      </div>
    </Card>
  );
}

function PanelTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
      {icon}
      <span>{title}</span>
      <span className="ml-auto inline-flex items-center gap-1 text-xs text-slate-500">
        <ShieldCheck size={14} />
        autorizado
      </span>
    </div>
  );
}

function formatBytes(value: number) {
  if (!value) return "sin bytes";
  if (value < 1024) return `${value} B`;
  return `${Math.round(value / 1024)} KB`;
}

function shortHash(value: string | null) {
  return value ? `sha256 ${value.slice(0, 8)}` : "sin checksum";
}
