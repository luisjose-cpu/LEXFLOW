"use client";

import { Badge, Card, MetricCard } from "@lexflow/ui";
import {
  BrainCircuit,
  CheckCircle2,
  CircleDot,
  FileSearch,
  GitBranch,
  LayoutDashboard,
  MessageSquareText,
  Rocket,
  Scale,
  Search,
  ShieldCheck,
  Store,
  Workflow
} from "lucide-react";
import Link from "next/link";
import React from "react";
import {
  aiAgents,
  copilotCards,
  demoSteps,
  graphNodes,
  legalMemory,
  marketplaceItems,
  osModules,
  productionPending,
  ragPipeline,
  releaseReadiness
} from "@/lib/lexflow-os-demo";

type OSView = "final" | "demo";

export function LexflowOSFinal({ view = "final" }: { view?: OSView }) {
  return (
    <div className="grid gap-5">
      <Hero view={view} />
      <ModuleGrid />
      <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <LegalMemoryPanel />
        <RAGPanel />
      </section>
      <section className="grid gap-5 lg:grid-cols-3">
        <GlobalSearchPanel />
        <CopilotPanel />
        <AgentsPanel />
      </section>
      <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <LegalGraphPanel />
        <MarketplacePanel />
      </section>
      <section className="grid gap-5 xl:grid-cols-[1fr_1fr]">
        <DemoModePanel />
        <ReleasePanel />
      </section>
    </div>
  );
}

function Hero({ view }: { view: OSView }) {
  return (
    <header className="overflow-hidden rounded-lg border border-white/80 bg-white shadow-soft">
      <div className="grid gap-6 p-5 lg:grid-cols-[1.15fr_0.85fr] lg:p-7">
        <div>
          <div className="flex flex-wrap gap-2">
            <Badge>P15</Badge>
            <Badge>LEXFLOW OS Final</Badge>
            <Badge>Pilot ready</Badge>
            <Badge>Enterprise evolution</Badge>
          </div>
          <h1 className="mt-5 text-3xl font-semibold tracking-normal text-ink sm:text-4xl lg:text-5xl">LEXFLOW OS Final</h1>
          <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base sm:leading-7">
            Cierre del sistema operativo legal: memoria, RAG, busqueda global, copiloto, agentes, grafo, marketplace futuro, demo comercial y release final para pilotos.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link className="inline-flex h-10 items-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white transition hover:bg-legal-700" href="/demo">
              <Rocket size={16} />
              Demo Mode
            </Link>
            <Link className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-ink transition hover:border-legal-100 hover:bg-legal-50" href="/dashboard">
              <LayoutDashboard size={16} />
              Command Center
            </Link>
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-mist p-4">
          <div className="grid gap-3 sm:grid-cols-2">
            {releaseReadiness.map((item) => (
              <div className="rounded-md border border-white bg-white p-4" key={item.label}>
                <p className="text-xs font-semibold uppercase text-slate-500">{item.label}</p>
                <p className={`mt-2 text-lg font-semibold ${item.tone === "risk" ? "text-rose-700" : item.tone === "watch" ? "text-amber-700" : "text-emerald-700"}`}>{item.value}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            Estado: RELEASE READY FOR PILOT / NOT READY FOR PUBLIC PRODUCTION.
          </p>
          {view === "demo" ? <p className="mt-2 text-sm font-semibold text-legal-700">Demo E2E activo para recorrido comercial.</p> : null}
        </div>
      </div>
    </header>
  );
}

function ModuleGrid() {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {osModules.map((item) => (
        <article className="rounded-lg border border-white/80 bg-white p-4 shadow-soft" key={item.name}>
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-ink">{item.name}</p>
            <span className={`rounded-md px-2 py-1 text-xs font-semibold ${item.status === "planned" ? "bg-amber-50 text-amber-700" : "bg-emerald-50 text-emerald-700"}`}>
              {item.status}
            </span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">{item.detail}</p>
        </article>
      ))}
    </section>
  );
}

function LegalMemoryPanel() {
  return (
    <Card>
      <PanelTitle icon={<BrainCircuit size={18} />} title="Legal Memory" />
      <p className="mt-3 text-sm leading-6 text-slate-600">
        Memoria operacional por tenant: conserva eventos, documentos, comunicaciones, IA y decisiones conectadas al expediente.
      </p>
      <div className="mt-4 grid gap-3">
        {legalMemory.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.title}>
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{item.type}</Badge>
              <p className="text-sm font-semibold text-ink">{item.title}</p>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.signal}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function RAGPanel() {
  return (
    <Card>
      <PanelTitle icon={<FileSearch size={18} />} title="RAG Legal" />
      <div className="mt-4 grid gap-2">
        {ragPipeline.map((step, index) => (
          <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-mist p-3" key={step}>
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-legal-900 text-sm font-semibold text-white">{index + 1}</span>
            <span className="text-sm font-semibold text-ink">{step}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 rounded-lg border border-legal-100 bg-legal-50 p-4">
        <p className="text-sm font-semibold text-legal-900">Regla de evidencia</p>
        <p className="mt-2 text-sm leading-6 text-legal-700">Toda respuesta cita fuente. Si no hay evidencia, responde: No encontre evidencia en las fuentes disponibles.</p>
      </div>
    </Card>
  );
}

function GlobalSearchPanel() {
  return (
    <Card>
      <PanelTitle icon={<Search size={18} />} title="Busqueda global" />
      <div className="mt-4 rounded-lg border border-slate-200 bg-mist p-4">
        <p className="text-sm font-semibold text-ink">Nova</p>
        <div className="mt-3 grid gap-2">
          {["Cliente: Nova Capital", "Expediente: Cobro ejecutivo Nova", "Documento: Demanda y anexos.pdf", "Inteligencia: debido proceso"].map((item) => (
            <div className="flex items-center gap-2 text-sm text-slate-600" key={item}>
              <CircleDot size={14} className="text-legal-700" />
              {item}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

function CopilotPanel() {
  return (
    <Card>
      <PanelTitle icon={<MessageSquareText size={18} />} title="Copiloto Juridico" />
      <div className="mt-4 grid gap-3">
        {copilotCards.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.title}>
            <p className="text-sm font-semibold text-ink">{item.title}</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.text}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 rounded-md bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700">Requiere revision profesional.</p>
    </Card>
  );
}

function AgentsPanel() {
  return (
    <Card>
      <PanelTitle icon={<Scale size={18} />} title="Agentes IA" />
      <div className="mt-4 grid gap-2">
        {aiAgents.map((item) => (
          <div className="flex items-center gap-2 rounded-md bg-mist px-3 py-2 text-sm font-semibold text-ink" key={item}>
            <CheckCircle2 size={16} className="text-emerald-600" />
            {item}
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-600">Guardrails: no decide estrategia legal, no evade CAPTCHA y audita uso critico.</p>
    </Card>
  );
}

function LegalGraphPanel() {
  return (
    <Card>
      <PanelTitle icon={<GitBranch size={18} />} title="Legal Graph" />
      <div className="relative mt-4 min-h-80 overflow-hidden rounded-lg border border-slate-200 bg-mist">
        <div className="absolute left-[10%] right-[10%] top-1/2 h-px bg-legal-200" />
        <div className="absolute left-[24%] right-[14%] top-[30%] h-px rotate-6 bg-legal-100" />
        {graphNodes.map((node) => (
          <div
            className="absolute min-w-24 -translate-x-1/2 -translate-y-1/2 rounded-md border border-white bg-white px-3 py-2 text-center text-xs font-semibold text-ink shadow-soft"
            key={node.label}
            style={{ left: node.x, top: node.y }}
          >
            {node.label}
          </div>
        ))}
      </div>
    </Card>
  );
}

function MarketplacePanel() {
  return (
    <Card>
      <PanelTitle icon={<Store size={18} />} title="Marketplace futuro" />
      <p className="mt-3 text-sm leading-6 text-slate-600">No instalado en produccion. Preparado como extension enterprise con controles de seguridad y billing.</p>
      <div className="mt-4 grid gap-3">
        {marketplaceItems.map((item) => (
          <div className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-mist p-4" key={item}>
            <span className="text-sm font-semibold text-ink">{item}</span>
            <Badge>planned</Badge>
          </div>
        ))}
      </div>
    </Card>
  );
}

function DemoModePanel() {
  return (
    <Card>
      <PanelTitle icon={<Workflow size={18} />} title="Demo Mode E2E" />
      <div className="mt-4 grid gap-2">
        {demoSteps.map((step, index) => (
          <div className="flex gap-3 rounded-lg border border-slate-200 bg-mist p-3" key={step}>
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-white text-sm font-semibold text-legal-700">{index + 1}</span>
            <p className="self-center text-sm font-semibold text-ink">{step}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ReleasePanel() {
  return (
    <Card>
      <PanelTitle icon={<ShieldCheck size={18} />} title="Release final" />
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <MetricCard label="Piloto" value="Ready" trend="demo + QA final" />
        <MetricCard label="Produccion" value="Not ready" trend="pendientes externos" />
      </div>
      <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
        <p className="text-sm font-semibold text-amber-800">Produccion pendiente</p>
        <div className="mt-3 grid gap-2">
          {productionPending.map((item) => (
            <p className="text-sm leading-6 text-amber-800" key={item}>
              {item}
            </p>
          ))}
        </div>
      </div>
    </Card>
  );
}

function PanelTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2 text-legal-900">
      {icon}
      <h2 className="text-lg font-semibold text-ink">{title}</h2>
    </div>
  );
}
