"use client";

import { Badge, Card, MetricCard, PageHeader } from "@lexflow/ui";
import { Activity, BarChart3, Building2, CloudCog, DatabaseZap, GitBranch, Globe2, KeyRound, Layers3, LineChart, LockKeyhole, Network, Radar, ShieldCheck, Sparkles, Workflow } from "lucide-react";
import React from "react";
import { aiSwarmAgents, cloudEnvironments, dataEvents, enterpriseMetrics, governancePolicies, integrationCards, orchestrationRules, organizations, revenueSignals, telemetryRows } from "@/lib/level4-demo";

export function EnterpriseDashboard() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N4 Enterprise Legal Intelligence Platform" title="LEXFLOW Enterprise OS" description="Capa multi-organizacion, data platform, AI orchestration, telemetry, governance, API economy y legal cloud sobre Expediente360, SINOE, IA, portal y automation." />
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {enterpriseMetrics.map((item) => <MetricCard key={item.label} label={item.label} value={item.value} trend={item.trend} />)}
      </section>
      <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <GlobalAnalytics />
        <CrossTenantInsights />
      </section>
      <section className="grid gap-5 lg:grid-cols-3">
        <EnterpriseCompact icon={<DatabaseZap size={18} />} title="Data platform" items={["event ingestion", "unified index", "analytics pipeline", "future ML"]} />
        <EnterpriseCompact icon={<Workflow size={18} />} title="Orchestration" items={["AI", "Automation", "SINOE", "Portal", "Dashboard"]} />
        <EnterpriseCompact icon={<ShieldCheck size={18} />} title="Governance" items={["audit", "retention", "evidence", "approvals"]} />
      </section>
    </div>
  );
}

export function OrganizationDashboard() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N4-M1 Enterprise Multi-Org" title="Organizaciones, tenants y filiales" description="Estructura ORGANIZATION -> TENANT -> DEPARTMENT -> TEAM -> USER con analytics, permisos, facturacion y riesgo cross-tenant controlado." />
      <section className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
        <MultiOrgExplorer />
        <TenantSwitcher />
      </section>
      <GlobalAnalytics />
    </div>
  );
}

export function MultiOrgExplorer() {
  return (
    <Card>
      <PanelTitle icon={<Building2 size={18} />} title="Multi-org explorer" />
      <div className="mt-4 grid gap-3">
        {organizations.map((item) => (
          <article className="rounded-lg border border-slate-200 bg-mist p-4" key={item.name}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-semibold text-ink">{item.name}</p>
                <p className="mt-1 text-sm text-slate-600">{item.country} - {item.tenants} tenants</p>
              </div>
              <Badge>{item.plan}</Badge>
            </div>
            <p className="mt-3 text-sm font-semibold text-legal-800">Riesgo {item.risk}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}

export function TenantSwitcher() {
  return <EnterpriseCompact icon={<Globe2 size={18} />} title="Tenant switcher" items={["Demo Studio PE activo", "Nova Legal Holding CO disponible", "Acceso cross-tenant solo con permisos y auditoria"]} />;
}

export function GlobalAnalytics() {
  return (
    <Card>
      <PanelTitle icon={<BarChart3 size={18} />} title="Global analytics" />
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {["MRR enterprise", "Riesgo cross-tenant", "Uso IA", "SINOE syncs"].map((label, index) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={label}>
            <p className="text-sm text-slate-600">{label}</p>
            <p className="mt-2 text-2xl font-semibold text-ink">{["$18.4k", "31", "12.4k", "98%"][index]}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function CrossTenantInsights() {
  return <EnterpriseCompact icon={<Radar size={18} />} title="Cross-tenant insights" items={["Memoria aislada por tenant", "Agregados sin revelar datos sensibles", "Intervencion soporte temporal y auditada", "White-label preparado"]} />;
}

export function LegalDataPlatform() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N4-M2 Legal Data Platform" title="Plataforma de datos legal" description="Eventos, memoria, graph, SINOE, IA, OCR, documentos, mensajes y automation centralizados para analytics y busqueda futura." />
      <section className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
        <DataPipeline />
        <EventStream />
      </section>
      <section className="grid gap-5 lg:grid-cols-2">
        <UnifiedIndexer />
        <AnalyticsEngine />
      </section>
    </div>
  );
}

export function DataPipeline() {
  return <EnterpriseCompact icon={<Layers3 size={18} />} title="Data pipeline" items={["Data Lake preparado", "Event Bus in-process", "Search Engine future-ready", "Future ML sin mezclar tenants"]} />;
}

export function EventStream() {
  return (
    <Card>
      <PanelTitle icon={<Activity size={18} />} title="Event stream" />
      <div className="mt-4 grid gap-3">
        {dataEvents.map((item) => (
          <div className="grid gap-2 rounded-lg border border-slate-200 bg-mist p-4 md:grid-cols-[1fr_auto]" key={`${item.type}-${item.entity}`}>
            <div>
              <p className="font-semibold text-ink">{item.type}</p>
              <p className="mt-1 text-sm text-slate-600">{item.entity} - {item.source}</p>
            </div>
            <Badge>{item.status}</Badge>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function UnifiedIndexer() {
  return <EnterpriseCompact icon={<DatabaseZap size={18} />} title="Unified indexer" items={["Expedientes", "Documentos", "Timeline", "Comunicaciones", "Noticias", "Automation runs"]} />;
}

export function AnalyticsEngine() {
  return <EnterpriseCompact icon={<LineChart size={18} />} title="Analytics engine" items={["KPIs legales", "Risk score", "Productividad", "Revenue", "Health score"]} />;
}

export function OrchestrationLayer() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N4-M3 Orchestration Layer" title="Coordinador de eventos legales" description="Cada evento coordina IA, automation, comunicaciones, SINOE, alertas, portal, dashboard, copilot y memory con auditoria." />
      <Card>
        <PanelTitle icon={<Workflow size={18} />} title="Rule engine" />
        <div className="mt-4 grid gap-3">
          {orchestrationRules.map((item) => <div className="rounded-lg border border-slate-200 bg-mist p-4 text-sm font-semibold leading-6 text-ink" key={item}>{item}</div>)}
        </div>
      </Card>
    </div>
  );
}

export function AIEnterpriseSwarm() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N4-M4 Enterprise AI Swarm" title="Agentes IA coordinados" description="LegalAgent, CaseAgent, RiskAgent y ManagementAgent trabajan con memoria, permisos, handoff, output trazable y revision humana obligatoria." />
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {aiSwarmAgents.map((agent) => (
          <Card key={agent.name}>
            <PanelTitle icon={<Sparkles size={18} />} title={agent.name} />
            <p className="mt-3 text-sm leading-6 text-slate-600">{agent.signal}</p>
            <div className="mt-4"><Badge>{agent.status}</Badge></div>
          </Card>
        ))}
      </section>
    </div>
  );
}

export function TelemetryCenter() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N4-M5 Observability" title="Telemetry Center" description="Monitoreo de API, frontend, IA, automation, WhatsApp, SINOE, OCR, portal, DB, Redis, storage y workers." />
      <ObservabilityDashboard />
    </div>
  );
}

export function ObservabilityDashboard() {
  return (
    <Card>
      <PanelTitle icon={<Activity size={18} />} title="System metrics" />
      <div className="mt-4 grid gap-3">
        {telemetryRows.map((item) => (
          <div className="grid gap-2 rounded-lg border border-slate-200 bg-mist p-4 md:grid-cols-[1fr_auto]" key={item.component}>
            <div>
              <p className="font-semibold text-ink">{item.component}</p>
              <p className="mt-1 text-sm text-slate-600">{item.metric}: {item.value}</p>
            </div>
            <Badge>{item.status}</Badge>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function RevenueDashboard() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N4-M6 Revenue & Growth" title="Revenue engine SaaS" description="Trial conversion, upsell, customer health, churn prediction y propuesta enterprise conectadas a uso real del tenant." />
      <section className="grid gap-4 md:grid-cols-3">
        {revenueSignals.map((item) => (
          <Card key={item.signal}>
            <PanelTitle icon={<LineChart size={18} />} title={item.signal} />
            <p className="mt-4 text-3xl font-semibold text-ink">{item.score}</p>
            <p className="mt-2 text-sm text-slate-600">{item.action}</p>
          </Card>
        ))}
      </section>
    </div>
  );
}

export function IntegrationCenter() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N4-M7 API & Integration Platform" title="Integration Center" description="Public API, webhooks, OAuth future-ready, API keys, rate limits y portal developer sin exponer secretos." />
      <section className="grid gap-4 md:grid-cols-2">
        {integrationCards.map((item) => (
          <Card key={item.name}>
            <PanelTitle icon={<KeyRound size={18} />} title={item.name} />
            <p className="mt-3 text-sm leading-6 text-slate-600">{item.detail}</p>
            <div className="mt-4"><Badge>{item.status}</Badge></div>
          </Card>
        ))}
      </section>
      <section className="grid gap-5 lg:grid-cols-2">
        <WebhookManager />
        <DeveloperPortal />
      </section>
    </div>
  );
}

export function WebhookManager() {
  return <EnterpriseCompact icon={<GitBranch size={18} />} title="Webhook manager" items={["case.updated", "sinoe.update.approved", "automation.failed", "ai.summary.completed"]} />;
}

export function DeveloperPortal() {
  return <EnterpriseCompact icon={<Network size={18} />} title="Developer portal" items={["API v1 preparada", "SDK future-ready", "OAuth future-ready", "Rate limits tenant scoped"]} />;
}

export function GovernanceCenter() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N4-M8 Compliance & Governance OS" title="Governance Center" description="Compliance, auditoria total, retention policies, approvals, evidence chain y controles enterprise." />
      <section className="grid gap-4 md:grid-cols-3">
        {governancePolicies.map((item) => (
          <Card key={item.name}>
            <PanelTitle icon={<LockKeyhole size={18} />} title={item.name} />
            <p className="mt-3 text-sm text-slate-600">{item.type}</p>
            <div className="mt-4"><Badge>{item.status}</Badge></div>
          </Card>
        ))}
      </section>
    </div>
  );
}

export function CloudControlCenter() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N4-M9 LEXFLOW Cloud" title="Cloud Control Center" description="Multi-env, staging, production, backup, restore, disaster recovery, HA futura y kubernetes future-ready." />
      <section className="grid gap-4 md:grid-cols-3">
        {cloudEnvironments.map((item) => (
          <Card key={item.name}>
            <PanelTitle icon={<CloudCog size={18} />} title={item.name} />
            <p className="mt-3 text-sm leading-6 text-slate-600">{item.region} - backup {item.backup}</p>
            <div className="mt-4"><Badge>{item.status}</Badge></div>
          </Card>
        ))}
      </section>
    </div>
  );
}

function EnterpriseCompact({ icon, title, items }: { icon: React.ReactNode; title: string; items: string[] }) {
  return (
    <Card>
      <PanelTitle icon={icon} title={title} />
      <div className="mt-4 grid gap-2">
        {items.map((item) => <div className="rounded-md border border-slate-200 bg-mist p-3 text-sm font-semibold leading-6 text-ink" key={item}>{item}</div>)}
      </div>
    </Card>
  );
}

function PanelTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="grid h-8 w-8 place-items-center rounded-md bg-legal-50 text-legal-800">{icon}</span>
      <h2 className="text-base font-semibold text-ink">{title}</h2>
    </div>
  );
}
