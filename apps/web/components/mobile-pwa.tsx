"use client";

import { Badge, Button, Card, MetricCard } from "@lexflow/ui";
import { Bell, BriefcaseBusiness, CalendarDays, CheckSquare, FileText, Home, MessageSquare, Scale, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";
import React from "react";
import { mobileClient, mobileLawyer } from "@/lib/mobile-demo";

type ClientView = "home" | "cases" | "case-detail" | "documents" | "messages" | "notifications";
type LawyerView = "home" | "cases" | "case-detail" | "tasks" | "hearings" | "notifications";

const clientTabs = [
  { href: "/m/client", label: "Inicio", icon: Home },
  { href: "/m/client/cases", label: "Casos", icon: Scale },
  { href: "/m/client/documents", label: "Docs", icon: FileText },
  { href: "/m/client/messages", label: "Mensajes", icon: MessageSquare },
  { href: "/m/client/notifications", label: "Avisos", icon: Bell }
];

const lawyerTabs = [
  { href: "/m/lawyer", label: "Inicio", icon: Home },
  { href: "/m/lawyer/cases", label: "Casos", icon: BriefcaseBusiness },
  { href: "/m/lawyer/tasks", label: "Tareas", icon: CheckSquare },
  { href: "/m/lawyer/hearings", label: "Agenda", icon: CalendarDays },
  { href: "/m/lawyer/notifications", label: "Avisos", icon: Bell }
];

export function MobileClientExperience({ view = "home" }: { view?: ClientView }) {
  return (
    <MobileShell subtitle={mobileClient.name} tabs={clientTabs} title="Cliente">
      {view === "home" ? <ClientHome /> : null}
      {view === "cases" ? <ClientCases /> : null}
      {view === "case-detail" ? <ClientCaseDetail /> : null}
      {view === "documents" ? <MobileDocuments /> : null}
      {view === "messages" ? <MobileMessages /> : null}
      {view === "notifications" ? <MobileNotifications /> : null}
    </MobileShell>
  );
}

export function MobileLawyerExperience({ view = "home" }: { view?: LawyerView }) {
  return (
    <MobileShell subtitle={mobileLawyer.name} tabs={lawyerTabs} title="Abogado">
      {view === "home" ? <LawyerHome /> : null}
      {view === "cases" ? <LawyerCases /> : null}
      {view === "case-detail" ? <LawyerCaseDetail /> : null}
      {view === "tasks" ? <LawyerTasks /> : null}
      {view === "hearings" ? <LawyerHearings /> : null}
      {view === "notifications" ? <LawyerNotifications /> : null}
    </MobileShell>
  );
}

function MobileShell({ children, subtitle, tabs, title }: { children: React.ReactNode; subtitle: string; tabs: typeof clientTabs; title: string }) {
  return (
    <main className="min-h-screen bg-mist pb-24">
      <header className="sticky top-0 z-20 border-b border-white/80 bg-white/95 backdrop-blur">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between gap-3 px-4 py-3">
          <Link className="flex min-w-0 items-center gap-3" href={tabs[0].href}>
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-legal-900 text-white">
              <Sparkles size={18} />
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-semibold text-legal-900">LEXFLOW {title}</span>
              <span className="block truncate text-xs text-slate-500">{subtitle}</span>
            </span>
          </Link>
          <Badge>PWA</Badge>
        </div>
      </header>

      <section className="mx-auto grid w-full max-w-3xl gap-4 px-4 py-4">{children}</section>

      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-white/80 bg-white/95 px-2 pb-[calc(env(safe-area-inset-bottom)+0.5rem)] pt-2 shadow-soft backdrop-blur">
        <div className="mx-auto grid max-w-3xl grid-cols-5 gap-1">
          {tabs.map((item) => (
            <Link className="grid min-h-14 place-items-center rounded-md px-1 text-center text-[11px] font-semibold text-slate-600 hover:bg-legal-50 hover:text-legal-900" href={item.href} key={item.href}>
              <item.icon size={18} />
              <span className="mt-1 truncate">{item.label}</span>
            </Link>
          ))}
        </div>
      </nav>
    </main>
  );
}

function MobileHeader({ badge, title, body }: { badge: string; title: string; body: string }) {
  return (
    <Card>
      <Badge>{badge}</Badge>
      <h1 className="mt-3 text-2xl font-semibold tracking-normal text-ink">{title}</h1>
      <p className="mt-2 text-sm leading-6 text-slate-600">{body}</p>
    </Card>
  );
}

function ClientHome() {
  return (
    <>
      <MobileHeader badge="Cliente" title="Mis expedientes" body="Estado, timeline, documentos, audiencias, mensajes, notificaciones y proximos pasos." />
      <MetricGrid metrics={mobileClient.metrics} />
      <ClientCases compact />
      <NextSteps items={mobileClient.nextSteps} />
    </>
  );
}

function ClientCases({ compact = false }: { compact?: boolean }) {
  return (
    <Card>
      <PanelTitle icon={<Scale size={18} />} title={compact ? "Expedientes recientes" : "Mis expedientes"} />
      <div className="mt-4 grid gap-3">
        {mobileClient.cases.map((item) => (
          <Link className="rounded-lg border border-slate-200 bg-mist p-4" href={`/m/client/cases/${item.id}`} key={item.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-ink">{item.title}</p>
                <p className="mt-1 text-sm text-slate-600">{item.external_case_number}</p>
              </div>
              <Badge>{item.status}</Badge>
            </div>
            <p className="mt-3 text-xs font-semibold text-legal-700">Proxima audiencia: {item.next_hearing}</p>
          </Link>
        ))}
      </div>
    </Card>
  );
}

function ClientCaseDetail() {
  return (
    <>
      <MobileHeader badge="Expediente" title="Cobro ejecutivo Nova" body="Vista movil cliente con timeline visible, documentos autorizados, audiencias y mensajes." />
      <Timeline />
      <MobileDocuments />
      <MobileMessages />
    </>
  );
}

function MobileDocuments() {
  return (
    <Card>
      <PanelTitle icon={<FileText size={18} />} title="Documentos" />
      <div className="mt-4 grid gap-3">
        {mobileClient.documents.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <p className="text-sm font-semibold text-ink">{item.filename}</p>
            <p className="mt-1 text-sm text-slate-600">{item.classification}</p>
            <Badge>{item.status}</Badge>
          </div>
        ))}
      </div>
    </Card>
  );
}

function MobileMessages() {
  return (
    <Card>
      <PanelTitle icon={<MessageSquare size={18} />} title="Mensajes" />
      <div className="mt-4 grid gap-3">
        {mobileClient.messages.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <p className="text-sm font-semibold text-ink">{item.direction === "inbound" ? "Cliente" : "Equipo legal"}</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.body}</p>
          </div>
        ))}
      </div>
      <Button>Enviar solicitud</Button>
    </Card>
  );
}

function MobileNotifications() {
  return (
    <Card>
      <PanelTitle icon={<Bell size={18} />} title="Notificaciones" />
      <div className="mt-4 grid gap-3">
        {mobileClient.notifications.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <p className="text-sm font-semibold text-ink">{item.title}</p>
            <p className="mt-1 text-sm leading-6 text-slate-600">{item.body}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function LawyerHome() {
  return (
    <>
      <MobileHeader badge="Abogado" title="Dashboard personal" body="Expedientes asignados, alertas, audiencias, tareas, comunicaciones, documentos, IA y actualizaciones judiciales." />
      <MetricGrid metrics={mobileLawyer.metrics.slice(0, 4)} />
      <LawyerTasks />
      <LawyerCases compact />
    </>
  );
}

function LawyerCases({ compact = false }: { compact?: boolean }) {
  return (
    <Card>
      <PanelTitle icon={<BriefcaseBusiness size={18} />} title={compact ? "Asignados" : "Expedientes asignados"} />
      <div className="mt-4 grid gap-3">
        {mobileLawyer.cases.map((item) => (
          <Link className="rounded-lg border border-slate-200 bg-mist p-4" href={`/m/lawyer/cases/${item.id}`} key={item.id}>
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm font-semibold text-ink">{item.title}</p>
              <Badge>{item.status}</Badge>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.next}</p>
          </Link>
        ))}
      </div>
    </Card>
  );
}

function LawyerCaseDetail() {
  return (
    <>
      <MobileHeader badge="Expediente abogado" title="Cobro ejecutivo Nova" body="Resumen movil con riesgo, tareas, documentos, comunicaciones, actualizaciones judiciales e IA." />
      <Card>
        <PanelTitle icon={<Sparkles size={18} />} title={mobileLawyer.aiSummary.title} />
        <p className="mt-3 text-sm leading-6 text-slate-600">{mobileLawyer.aiSummary.body}</p>
        <p className="mt-3 text-xs font-semibold text-rose-700">{mobileLawyer.aiSummary.disclaimer}</p>
      </Card>
      <LawyerTasks />
      <LawyerHearings />
    </>
  );
}

function LawyerTasks() {
  return (
    <Card>
      <PanelTitle icon={<CheckSquare size={18} />} title="Tareas" />
      <div className="mt-4 grid gap-3">
        {mobileLawyer.tasks.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <p className="text-sm font-semibold text-ink">{item.title}</p>
            <p className="mt-1 text-xs font-semibold text-legal-700">{item.status} - {new Date(item.due_at).toLocaleDateString("es")}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function LawyerHearings() {
  return (
    <Card>
      <PanelTitle icon={<CalendarDays size={18} />} title="Audiencias" />
      <div className="mt-4 grid gap-3">
        {mobileLawyer.hearings.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <p className="text-sm font-semibold text-ink">{item.title}</p>
            <p className="mt-1 text-sm text-slate-600">{new Date(item.starts_at).toLocaleString("es")}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function LawyerNotifications() {
  return (
    <Card>
      <PanelTitle icon={<Bell size={18} />} title="Alertas" />
      <div className="mt-4 grid gap-3">
        {mobileLawyer.alerts.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <p className="text-sm font-semibold text-ink">{item.title}</p>
            <p className="mt-1 text-sm leading-6 text-slate-600">{item.body}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function Timeline() {
  return (
    <Card>
      <PanelTitle icon={<CalendarDays size={18} />} title="Timeline" />
      <div className="mt-4 grid gap-3">
        {mobileClient.timeline.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <p className="text-sm font-semibold text-ink">{item.title}</p>
            <p className="mt-1 text-sm leading-6 text-slate-600">{item.summary}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function NextSteps({ items }: { items: string[] }) {
  return (
    <Card>
      <PanelTitle icon={<ShieldCheck size={18} />} title="Proximos pasos" />
      <div className="mt-4 grid gap-3">
        {items.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-3 text-sm font-semibold text-ink" key={item}>{item}</div>
        ))}
      </div>
    </Card>
  );
}

function MetricGrid({ metrics }: { metrics: Array<{ label: string; value: string; trend: string }> }) {
  return (
    <section className="grid gap-3 sm:grid-cols-2">
      {metrics.map((item) => (
        <MetricCard key={item.label} label={item.label} value={item.value} trend={item.trend} />
      ))}
    </section>
  );
}

function PanelTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
      {icon}
      <span>{title}</span>
    </div>
  );
}
