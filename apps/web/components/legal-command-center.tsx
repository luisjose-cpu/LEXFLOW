"use client";

import { Badge, Button, Card, MetricCard } from "@lexflow/ui";
import { AlertTriangle, Bot, BriefcaseBusiness, FileText, Gauge, Link2, MessageCircle, Scale, ShieldCheck, TrendingUp } from "lucide-react";
import React from "react";
import { aiUsage, commandKpis, communications, decisionQueue, judicialMonitoring, legalTrends, productivityData, riskItems } from "@/lib/command-center-demo";

export function LegalCommandCenter({ mode = "overview" }: { mode?: "overview" | "command" }) {
  return (
    <div className="grid gap-5">
      <header className="rounded-lg border border-white/80 bg-white p-5 shadow-soft">
        <div className="flex flex-wrap gap-2">
          <Badge>P10</Badge>
          <Badge>Dashboard ejecutivo</Badge>
          <Badge>Tenant scoped</Badge>
        </div>
        <div className="mt-4 flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <h1 className="text-3xl font-semibold tracking-normal text-ink sm:text-4xl">Legal Command Center</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Operacion, riesgo, clientes, productividad, expedientes, inteligencia, monitoreo judicial, IA y comunicaciones en una sola vista gerencial.
            </p>
          </div>
          <Button>
            <Gauge size={16} />
            Snapshot ejecutivo
          </Button>
        </div>
      </header>

      <KPIGrid />

      <section className="grid gap-5 xl:grid-cols-[1fr_1fr]">
        <RiskPanel />
        <CasesOverviewCard />
      </section>

      <section className={`grid gap-5 ${mode === "command" ? "xl:grid-cols-[1fr_1fr_1fr]" : "xl:grid-cols-[1.15fr_0.85fr]"}`}>
        <ProductivityChart />
        <JudicialMonitoringPanel />
        {mode === "command" ? <DecisionQueuePanel /> : null}
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        <AIUsagePanel />
        <CommunicationPanel />
        <LegalIntelligencePanel />
      </section>
    </div>
  );
}

function KPIGrid() {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
      {commandKpis.map((item) => (
        <MetricCard key={item.label} label={item.label} value={item.value} trend={item.trend} />
      ))}
    </section>
  );
}

function RiskPanel() {
  return (
    <Card>
      <PanelTitle icon={<AlertTriangle size={18} />} title="Riesgo operativo" />
      <div className="mt-4 grid gap-3">
        {riskItems.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.title}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-ink">{item.title}</p>
              <span className={`rounded-md px-2.5 py-1 text-xs font-semibold ${item.status === "risk" ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"}`}>{item.status}</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.reason}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function CasesOverviewCard() {
  return (
    <Card>
      <PanelTitle icon={<BriefcaseBusiness size={18} />} title="Expedientes y carga" />
      <div className="mt-4 grid gap-3">
        {productivityData.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.name}>
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="font-semibold text-ink">{item.name}</span>
              <span className="text-legal-700">carga {item.carga}</span>
            </div>
            <div className="mt-3 h-3 rounded-full bg-white">
              <div className="h-3 rounded-full bg-legal-700" style={{ width: `${Math.max(12, item.carga * 20)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ProductivityChart() {
  return (
    <Card>
      <PanelTitle icon={<ShieldCheck size={18} />} title="Productividad" />
      <div className="mt-4 flex min-h-72 items-end gap-4 rounded-lg border border-slate-200 bg-mist p-4">
        {productivityData.map((item) => (
          <div className="grid flex-1 gap-2 text-center" key={item.name}>
            <div className="flex h-48 items-end rounded-md bg-white px-2">
              <div className="w-full rounded-t-md bg-legal-700" style={{ height: `${Math.max(10, item.tareas * 18)}%` }} />
            </div>
            <p className="truncate text-xs font-semibold text-ink">{item.name}</p>
            <p className="text-xs text-legal-700">{item.tareas} tareas</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function JudicialMonitoringPanel() {
  return (
    <Card>
      <PanelTitle icon={<Scale size={18} />} title="Monitoreo judicial" />
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {judicialMonitoring.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.label}>
            <p className="text-sm text-slate-500">{item.label}</p>
            <p className="mt-2 text-2xl font-semibold text-ink">{item.value}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function AIUsagePanel() {
  return <CompactBars icon={<Bot size={18} />} title="IA" data={aiUsage.map((item) => ({ label: item.type, value: item.count }))} />;
}

function CommunicationPanel() {
  return <CompactBars icon={<MessageCircle size={18} />} title="Comunicaciones" data={communications.map((item) => ({ label: item.channel, value: item.count }))} />;
}

function LegalIntelligencePanel() {
  return <CompactBars icon={<TrendingUp size={18} />} title="Inteligencia juridica" data={legalTrends.map((item) => ({ label: item.tag, value: item.count }))} />;
}

function CompactBars({ icon, title, data }: { icon: React.ReactNode; title: string; data: Array<{ label: string; value: number }> }) {
  return (
    <Card>
      <PanelTitle icon={icon} title={title} />
      <div className="mt-4 grid gap-3">
        {data.map((item) => (
          <div className="grid gap-2" key={item.label}>
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="font-semibold text-ink">{item.label}</span>
              <span className="text-legal-700">{item.value}</span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div className="h-2 rounded-full bg-legal-700" style={{ width: `${Math.max(12, item.value * 20)}%` }} />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function DecisionQueuePanel() {
  return (
    <Card>
      <PanelTitle icon={<FileText size={18} />} title="Decision queue" />
      <div className="mt-4 grid gap-3">
        {decisionQueue.map((item) => (
          <div className="flex items-start gap-3 rounded-lg border border-slate-200 bg-mist p-3" key={item}>
            <Link2 className="mt-0.5 shrink-0 text-legal-700" size={16} />
            <p className="text-sm font-semibold leading-6 text-ink">{item}</p>
          </div>
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
