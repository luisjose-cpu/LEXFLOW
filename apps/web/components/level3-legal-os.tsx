"use client";

import { Badge, Button, Card, MetricCard, PageHeader } from "@lexflow/ui";
import { BrainCircuit, Boxes, DatabaseZap, FileSearch, GitBranch, Globe2, Layers3, Network, Search, ShieldCheck, Sparkles, Waypoints } from "lucide-react";
import React from "react";
import { agentCatalog, complexityCases, digitalTwinMetrics, graphNodes, knowledgeItems, lawyerLoad, marketplaceItems, memoryItems, ragSources } from "@/lib/level3-demo";

export function DigitalTwinDashboard() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N3-M1 Legal Digital Twin" title="Gemelo digital del estudio" description="Modelo operativo del estudio: clientes, abogados, expedientes, audiencias, documentos, comunicaciones, IA, automatizaciones, riesgo y KPIs en una sola memoria estructural." />
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {digitalTwinMetrics.map((item) => <MetricCard key={item.label} label={item.label} value={item.value} trend={item.trend} />)}
      </section>
      <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <LawyerLoadGraph />
        <CaseComplexityEngine />
      </section>
      <section className="grid gap-5 lg:grid-cols-3">
        <OperationalMap />
        <StudySimulationPanel />
        <RiskPropagationMap />
      </section>
    </div>
  );
}

export function LawyerLoadGraph() {
  return (
    <Card>
      <PanelTitle icon={<Network size={18} />} title="Carga de abogados" />
      <div className="mt-4 grid gap-4">
        {lawyerLoad.map((item) => (
          <div className="grid gap-2" key={item.name}>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="font-semibold text-ink">{item.name}</p>
                <p className="text-sm text-slate-600">{item.signal}</p>
              </div>
              <Badge>{item.status}</Badge>
            </div>
            <div className="h-3 overflow-hidden rounded-md bg-slate-100">
              <div className="h-full rounded-md bg-legal-700" style={{ width: `${item.load}%` }} />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function CaseComplexityEngine() {
  return (
    <Card>
      <PanelTitle icon={<BrainCircuit size={18} />} title="Complejidad de expedientes" />
      <div className="mt-4 grid gap-3">
        {complexityCases.map((item) => (
          <article className="rounded-lg border border-slate-200 bg-mist p-4" key={item.title}>
            <div className="flex items-center justify-between gap-3">
              <p className="font-semibold text-ink">{item.title}</p>
              <span className="rounded-md bg-legal-50 px-3 py-1 text-sm font-semibold text-legal-800">{item.score}</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.drivers.join(", ")}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}

export function OperationalMap() {
  return <CompactPanel icon={<Waypoints size={18} />} title="Mapa operacional" items={["Cliente -> Expediente -> Documento", "Comunicacion -> Automatizacion -> IA", "Inteligencia -> Decision auditada"]} />;
}

export function StudySimulationPanel() {
  return <CompactPanel icon={<Sparkles size={18} />} title="Simulacion" items={["Si no se resuelve CAPTCHA sube riesgo", "Si abogado supera carga, reasignar tareas", "Si no hay fuente, RAG declara ausencia"]} />;
}

export function RiskPropagationMap() {
  return <CompactPanel icon={<ShieldCheck size={18} />} title="Propagacion de riesgo" items={["Plazo critico afecta cliente y audiencia", "Documento observado bloquea proximo paso", "Automatizacion fallida crea alerta"]} />;
}

export function KnowledgeVault() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N3-M2 Knowledge Vault" title="Biblioteca viva del estudio" description="Demandas, contestaciones, contratos, jurisprudencia, estrategias, informes, prompts y checklists reutilizables con busqueda contextual." />
      <KnowledgeSearch />
      <section className="grid gap-5 lg:grid-cols-3">
        <TemplateLibrary />
        <LegalPrecedentLibrary />
        <PromptLibrary />
      </section>
    </div>
  );
}

export function KnowledgeSearch() {
  return (
    <Card>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <label className="relative flex-1">
          <Search className="absolute left-3 top-3 text-slate-400" size={18} />
          <input className="h-11 w-full rounded-md border border-slate-200 bg-white pl-10 pr-3 text-sm outline-none focus:border-legal-500" placeholder="Buscar casos parecidos, demandas similares, contratos o prompts" />
        </label>
        <Button><FileSearch size={16} /> Buscar similares</Button>
      </div>
    </Card>
  );
}

export function TemplateLibrary() {
  return <KnowledgeColumn title="Plantillas" type="template" icon={<Layers3 size={18} />} />;
}

export function LegalPrecedentLibrary() {
  return <KnowledgeColumn title="Precedentes" type="precedent" icon={<DatabaseZap size={18} />} />;
}

export function PromptLibrary() {
  return <KnowledgeColumn title="Prompts" type="prompt" icon={<BrainCircuit size={18} />} />;
}

function KnowledgeColumn({ title, type, icon }: { title: string; type: string; icon: React.ReactNode }) {
  return (
    <Card>
      <PanelTitle icon={icon} title={title} />
      <div className="mt-4 grid gap-3">
        {knowledgeItems.filter((item) => item.type === type).map((item) => (
          <article className="rounded-lg border border-slate-200 bg-mist p-4" key={item.title}>
            <p className="font-semibold text-ink">{item.title}</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.summary}</p>
            <p className="mt-3 text-xs font-semibold text-legal-700">{item.tags}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}

export function LegalGraphExplorer() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N3-M4 Legal Graph" title="Grafo legal operativo" description="Relaciones entre cliente, expediente, documento, audiencia, noticia, riesgo, abogado, automatizacion y alerta." />
      <GraphSearch />
      <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <RelationshipMap />
        <EntityInspector />
      </section>
    </div>
  );
}

export function GraphSearch() {
  return (
    <Card>
      <label className="relative block">
        <Search className="absolute left-3 top-3 text-slate-400" size={18} />
        <input className="h-11 w-full rounded-md border border-slate-200 bg-white pl-10 pr-3 text-sm outline-none focus:border-legal-500" placeholder="Buscar nodo, relacion, expediente, riesgo o abogado" />
      </label>
    </Card>
  );
}

export function RelationshipMap() {
  return (
    <Card className="min-h-[430px]">
      <PanelTitle icon={<GitBranch size={18} />} title="Relationship map" />
      <div className="relative mt-4 h-[350px] rounded-lg border border-slate-200 bg-[linear-gradient(90deg,#eef6ff_1px,transparent_1px),linear-gradient(#eef6ff_1px,transparent_1px)] bg-[size:36px_36px]">
        {graphNodes.map((node) => (
          <div className="absolute w-32 rounded-lg border border-legal-100 bg-white p-3 text-center shadow-soft" key={node.label} style={{ left: node.x, top: node.y }}>
            <p className="text-sm font-semibold text-ink">{node.label}</p>
            <p className="mt-1 text-xs text-legal-700">{node.type}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function EntityInspector() {
  return <CompactPanel icon={<Boxes size={18} />} title="Inspector" items={["Nodo seleccionado: Cobro ejecutivo Nova", "Relaciones: cliente, documento, riesgo, abogado", "Acciones: abrir expediente, ver fuentes, auditar"]} />;
}

export function ManagementCopilot() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N3-M5 Copiloto Gerencial" title="IA ejecutiva con fuentes" description="El socio pregunta que esta mal, que cliente peligra, que abogado esta saturado y que automatizacion fallo. Responde con contexto y revision profesional." />
      <section className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <PanelTitle icon={<BrainCircuit size={18} />} title="Pregunta gerencial" />
          <textarea className="mt-4 min-h-32 w-full resize-none rounded-md border border-slate-200 p-3 text-sm outline-none focus:border-legal-500" defaultValue="Que expediente es riesgoso y que fuente lo soporta?" />
          <div className="mt-3">
            <Button><Sparkles size={16} /> Preguntar</Button>
          </div>
        </Card>
        <Card>
          <PanelTitle icon={<ShieldCheck size={18} />} title="Respuesta explicable" />
          <p className="mt-4 text-sm leading-6 text-slate-600">Hay riesgo operativo visible en Laboral colectivo Andes y Cobro ejecutivo Nova. Priorizar CAPTCHA pendiente, plazos criticos y carga del abogado responsable.</p>
          <div className="mt-4 grid gap-2">
            {ragSources.map((source) => <SourceRow key={source.chunk} source={source} />)}
          </div>
        </Card>
      </section>
    </div>
  );
}

export function MarketplaceCatalog() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N3-M6 Marketplace Legal" title="Marketplace extensible" description="Catalogo futuro de plantillas, prompts, automatizaciones, dashboards, integraciones, bots, checklists, modulos y workflows. Sin pagos reales todavia." />
      <section className="grid gap-4 lg:grid-cols-3">
        {marketplaceItems.map((item) => (
          <Card className="p-5" key={item.name}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold text-ink">{item.name}</p>
                <p className="mt-1 text-xs font-semibold uppercase tracking-normal text-legal-700">{item.type}</p>
              </div>
              <Badge>{item.status}</Badge>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-600">{item.detail}</p>
          </Card>
        ))}
      </section>
    </div>
  );
}

export function MemorySearch() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N3-M3 Legal Memory Engine" title="Memoria legal contextual" description="Correos, WhatsApp, PDF, resoluciones, audiencias, eventos, OCR, IA outputs, timeline, noticias y automation runs indexados por tenant." />
      <Card>
        <PanelTitle icon={<DatabaseZap size={18} />} title="Indice de memoria" />
        <div className="mt-4 grid gap-3">
          {memoryItems.map((item) => (
            <div className="grid gap-3 rounded-lg border border-slate-200 bg-mist p-4 md:grid-cols-[1fr_auto]" key={item.citation}>
              <div>
                <p className="font-semibold text-ink">{item.title}</p>
                <p className="mt-1 text-sm text-slate-600">{item.source} - {item.citation}</p>
              </div>
              <Badge>{item.status}</Badge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

export function RAGViewer() {
  return (
    <div className="grid gap-5">
      <PageHeader eyebrow="N3-M8 RAG + Context Engine" title="RAG con contexto y citas" description="Tenant, cliente, expediente, documentos, timeline, noticias, riesgos, comunicaciones, automation y memoria en una ventana de contexto controlada." />
      <section className="grid gap-5 lg:grid-cols-[1fr_1fr]">
        <Card>
          <PanelTitle icon={<Globe2 size={18} />} title="Context window" />
          <ol className="mt-4 grid gap-2 text-sm text-slate-600">
            {["MEMORY", "INDEX", "EMBEDDINGS", "RAG", "CONTEXT", "AI RESPONSE"].map((item, index) => (
              <li className="rounded-md border border-slate-200 bg-mist p-3" key={item}>{index + 1}. {item}</li>
            ))}
          </ol>
        </Card>
        <Card>
          <PanelTitle icon={<FileSearch size={18} />} title="Fuentes citadas" />
          <div className="mt-4 grid gap-2">
            {ragSources.map((source) => <SourceRow key={source.chunk} source={source} />)}
          </div>
        </Card>
      </section>
      <Card>
        <PanelTitle icon={<BrainCircuit size={18} />} title="AI Agents framework" />
        <div className="mt-4 flex flex-wrap gap-2">
          {agentCatalog.map((agent) => <span className="rounded-md bg-legal-50 px-3 py-2 text-sm font-semibold text-legal-800" key={agent}>{agent}</span>)}
        </div>
      </Card>
    </div>
  );
}

function SourceRow({ source }: { source: { title: string; chunk: string; confidence: string } }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-mist p-3">
      <p className="text-sm font-semibold text-ink">{source.title}</p>
      <p className="mt-1 text-xs text-slate-600">{source.chunk} - confianza {source.confidence}</p>
    </div>
  );
}

function CompactPanel({ icon, title, items }: { icon: React.ReactNode; title: string; items: string[] }) {
  return (
    <Card>
      <PanelTitle icon={icon} title={title} />
      <div className="mt-4 grid gap-2">
        {items.map((item) => <div className="rounded-md border border-slate-200 bg-mist p-3 text-sm font-medium leading-6 text-ink" key={item}>{item}</div>)}
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
