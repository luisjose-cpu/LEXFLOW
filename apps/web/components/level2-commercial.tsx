"use client";

import { Badge, Button, Card, MetricCard, PageHeader } from "@lexflow/ui";
import { BarChart3, BriefcaseBusiness, CalendarClock, DollarSign, Flame, Gauge, History, LayoutDashboard, RefreshCcw, Search, ShieldAlert, Sparkles, Target, TrendingUp, Users, Workflow } from "lucide-react";
import React from "react";
import { crmLeads, demoDatasets, financialCases, riskCases, warRoomAlerts, warRoomCriticalCases } from "@/lib/level2-demo";

export function WarRoomDashboard() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N2-M1 War Room Legal" title="War Room Legal" description="Centro operativo en tiempo real para gerencia, partners y equipos enterprise: riesgo, SINOE, IA, audiencias, automatizaciones y salud del estudio." />
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Score estudio" value="82" trend="salud operativa alta" />
        <MetricCard label="Casos criticos" value="3" trend="+1 esta semana" />
        <MetricCard label="CAPTCHA" value="1" trend="requiere humano" />
        <MetricCard label="IA pendiente" value="4" trend="revision profesional" />
      </section>
      <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <PanelTitle icon={<Flame size={18} />} title="Casos criticos" />
          <div className="mt-4 grid gap-3">
            {warRoomCriticalCases.map((item) => (
              <div className="grid gap-3 rounded-lg border border-slate-200 bg-mist p-4 md:grid-cols-[1fr_auto]" key={item.title}>
                <div>
                  <p className="font-semibold text-ink">{item.title}</p>
                  <p className="mt-1 text-sm leading-6 text-slate-600">{item.signal}</p>
                </div>
                <RiskPill score={item.score} />
              </div>
            ))}
          </div>
        </Card>
        <Card>
          <PanelTitle icon={<LayoutDashboard size={18} />} title="Mission control" />
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {warRoomAlerts.map((item) => (
              <div className="rounded-lg border border-slate-200 bg-white p-4" key={item.title}>
                <p className="text-xs font-semibold uppercase tracking-normal text-legal-700">{item.type}</p>
                <p className="mt-2 text-2xl font-semibold text-ink">{item.count}</p>
                <p className="mt-1 text-sm text-slate-600">{item.title}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>
      <section className="grid gap-5 lg:grid-cols-3">
        <CompactPanel icon={<CalendarClock size={18} />} title="Audiencias proximas" items={["Audiencia Andes - 4 dias", "Vista Nova - 8 dias", "Conciliacion Mercurio - 13 dias"]} />
        <CompactPanel icon={<Users size={18} />} title="Carga abogados" items={["Demo Lawyer: saturado", "Socia Mariana: disponible", "Asistente: 3 pendientes"]} />
        <CompactPanel icon={<TrendingUp size={18} />} title="Tendencias juridicas" items={["Debido proceso", "Laboral colectivo", "Contratos marco"]} />
      </section>
    </div>
  );
}

export function CRMBoard() {
  const stages = ["lead", "contact", "meeting", "proposal", "negotiation", "won"];
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N2-M2 Legal CRM" title="Pipeline comercial legal" description="De lead a cliente, expediente, portal y workflow. Controla valor esperado, probabilidad, reuniones, propuestas y siguiente accion." />
      <Card>
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <label className="relative flex-1">
            <Search className="absolute left-3 top-3 text-slate-400" size={18} />
            <input className="h-11 w-full rounded-md border border-slate-200 bg-white pl-10 pr-3 text-sm outline-none focus:border-legal-500" placeholder="Buscar lead, RUC, DNI, correo, campana o responsable" />
          </label>
          <Button><Sparkles size={16} /> Importar leads</Button>
        </div>
      </Card>
      <section className="grid gap-4 xl:grid-cols-6">
        {stages.map((stage) => (
          <Card className="p-4" key={stage}>
            <p className="text-sm font-semibold capitalize text-legal-700">{stage}</p>
            <div className="mt-3 grid gap-3">
              {crmLeads.filter((lead) => lead.stage === stage).map((lead) => <LeadCard key={lead.company} lead={lead} />)}
              {!crmLeads.some((lead) => lead.stage === stage) ? <p className="rounded-md border border-dashed border-slate-200 p-3 text-xs text-slate-500">Sin oportunidades</p> : null}
            </div>
          </Card>
        ))}
      </section>
      <section className="grid gap-5 lg:grid-cols-3">
        <MetricCard label="Pipeline ponderado" value="$25.4k" trend="probabilidad comercial" />
        <MetricCard label="Win rate" value="41%" trend="+8% vs mes anterior" />
        <MetricCard label="Siguiente accion" value="7" trend="hoy" />
      </section>
    </div>
  );
}

function LeadCard({ lead }: { lead: (typeof crmLeads)[number] }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-mist p-3">
      <p className="text-sm font-semibold text-ink">{lead.company}</p>
      <p className="mt-1 text-xs text-slate-500">{lead.value} · score {lead.score}</p>
      <p className="mt-2 text-xs leading-5 text-slate-600">{lead.next}</p>
    </article>
  );
}

export function FinancialOverview() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N2-M3 Engine Rentabilidad" title="Rentabilidad por expediente" description="Honorarios, horas, gastos, presupuesto, facturado, pendiente, margen, ROI y alertas de perdida." />
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Honorarios" value="$33.5k" trend="pipeline activo" />
        <MetricCard label="Margen" value="$12.1k" trend="36% promedio" />
        <MetricCard label="ROI" value="74%" trend="por expediente" />
        <MetricCard label="Perdida" value="1" trend="requiere ajuste" />
      </section>
      <Card>
        <PanelTitle icon={<DollarSign size={18} />} title="Mapa financiero" />
        <div className="mt-4 grid gap-3">
          {financialCases.map((item) => (
            <div className="grid gap-3 rounded-lg border border-slate-200 bg-mist p-4 md:grid-cols-[1fr_repeat(3,auto)] md:items-center" key={item.title}>
              <p className="font-semibold text-ink">{item.title}</p>
              <Badge>{item.status}</Badge>
              <span className="text-sm font-semibold text-legal-700">{item.margin}</span>
              <span className="text-sm text-slate-600">{item.roi} ROI · {item.hours}h</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

export function RiskDashboard() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N2-M4 Risk Engine" title="Riesgo juridico operativo" description="Score 0-100 con semaforo, causas explicables y revision profesional. No decide por el abogado." />
      <section className="grid gap-4 sm:grid-cols-3">
        <MetricCard label="Score estudio" value="61" trend="ambar" />
        <MetricCard label="Rojo" value="1" trend="caso critico" />
        <MetricCard label="Amber" value="1" trend="seguimiento" />
      </section>
      <section className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <PanelTitle icon={<ShieldAlert size={18} />} title="Heatmap" />
          <div className="mt-4 grid grid-cols-3 gap-3">
            <Heat label="Verde" value="1" className="bg-emerald-50 text-emerald-700" />
            <Heat label="Ambar" value="1" className="bg-amber-50 text-amber-700" />
            <Heat label="Rojo" value="1" className="bg-rose-50 text-rose-700" />
          </div>
        </Card>
        <Card>
          <PanelTitle icon={<Gauge size={18} />} title="Breakdown" />
          <div className="mt-4 grid gap-3">
            {riskCases.map((item) => (
              <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.title}>
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold text-ink">{item.title}</p>
                  <RiskPill score={item.score} />
                </div>
                <p className="mt-2 text-sm text-slate-600">{item.factors.join(", ")}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}

export function Level2DemoMode() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N2-M5 Demo Mode" title="Demo comercial LEXFLOW" description="Selecciona dataset, restaura demo, crea snapshot y recorre la historia de venta de 10 minutos." />
      <section className="grid gap-4 lg:grid-cols-4">
        {demoDatasets.map((item) => (
          <Card className="p-4" key={item.name}>
            <p className="font-semibold text-ink">{item.name}</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.modules}</p>
          </Card>
        ))}
      </section>
      <Card>
        <PanelTitle icon={<RefreshCcw size={18} />} title="Controles demo" />
        <div className="mt-4 flex flex-wrap gap-3">
          <Button><RefreshCcw size={16} /> Reset Demo</Button>
          <Button tone="secondary"><History size={16} /> Crear snapshot demo</Button>
          <Button tone="secondary"><Target size={16} /> Iniciar tour 10 min</Button>
        </div>
      </Card>
      <section className="grid gap-5 lg:grid-cols-3">
        <CompactPanel icon={<BriefcaseBusiness size={18} />} title="Flujo venta" items={["Dashboard", "War Room", "Expediente360", "SINOE mock", "IA", "Portal", "Automation", "Audit"]} />
        <CompactPanel icon={<BarChart3 size={18} />} title="Metricas demo" items={["3 clientes", "3 expedientes", "2 leads", "1 caso en perdida", "1 CAPTCHA"]} />
        <CompactPanel icon={<Workflow size={18} />} title="Mocks seguros" items={["SINOE mock", "WhatsApp mock", "IA mock", "Automation dry-run"]} />
      </section>
    </div>
  );
}

function RiskPill({ score }: { score: number }) {
  const tone = score >= 71 ? "bg-rose-50 text-rose-700" : score >= 31 ? "bg-amber-50 text-amber-700" : "bg-emerald-50 text-emerald-700";
  return <span className={`rounded-md px-3 py-1 text-sm font-semibold ${tone}`}>{score}</span>;
}

function Heat({ label, value, className }: { label: string; value: string; className: string }) {
  return (
    <div className={`rounded-lg p-4 text-center ${className}`}>
      <p className="text-2xl font-semibold">{value}</p>
      <p className="text-xs font-semibold">{label}</p>
    </div>
  );
}

function CompactPanel({ icon, title, items }: { icon: React.ReactNode; title: string; items: string[] }) {
  return (
    <Card>
      <PanelTitle icon={icon} title={title} />
      <div className="mt-4 grid gap-2">
        {items.map((item) => (
          <div className="rounded-md border border-slate-200 bg-mist p-3 text-sm font-medium text-ink" key={item}>{item}</div>
        ))}
      </div>
    </Card>
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
