import { Badge, Button, Card, Input, MetricCard } from "@lexflow/ui";
import { Bot, CheckCircle2, FileSearch, ListChecks, ScanText, ShieldCheck, Sparkles } from "lucide-react";
import React from "react";
import { aiDisclaimer, aiDocumentJobs, aiExtractions, aiMetrics, aiPrompts, aiSearchResults } from "@/lib/ai-demo";

export function AIPracticalPanel() {
  return (
    <div className="grid gap-5">
      <header className="rounded-lg border border-white/80 bg-white p-5 shadow-soft">
        <div className="flex flex-wrap gap-2">
          <Badge>P8</Badge>
          <Badge>Mock OCR</Badge>
          <Badge>Mock LLM</Badge>
        </div>
        <h1 className="mt-4 text-3xl font-semibold tracking-normal text-ink sm:text-4xl">IA practica legal</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          OCR, resumen documental, clasificacion, extraccion, pendientes, resumen de expediente y busqueda basica con revision humana obligatoria.
        </p>
        <p className="mt-4 inline-flex rounded-md bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700">{aiDisclaimer}</p>
      </header>

      <section className="grid gap-4 md:grid-cols-4">
        {aiMetrics.map((item) => (
          <MetricCard key={item.label} label={item.label} value={item.value} trend={item.trend} />
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <DocumentPipeline />
        <CaseIntelligence />
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <HumanReviewQueue />
        <PromptPanel />
      </section>
    </div>
  );
}

function DocumentPipeline() {
  return (
    <Card>
      <PanelTitle icon={<ScanText size={18} />} title="Pipeline documental" />
      <div className="mt-4 grid gap-3">
        {aiDocumentJobs.map((job) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={job.id}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-ink">{job.document}</p>
              <Badge>{job.type}</Badge>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{job.result}</p>
            <p className="mt-2 text-xs font-semibold text-rose-700">{aiDisclaimer}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function CaseIntelligence() {
  return (
    <Card>
      <PanelTitle icon={<FileSearch size={18} />} title="Expediente y busqueda" />
      <div className="mt-4 grid gap-4">
        <div className="rounded-lg border border-slate-200 bg-mist p-4">
          <p className="text-sm font-semibold text-ink">Resumen de expediente</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Estado, documentos, audiencias, comunicaciones y proximos pasos consolidados para revision profesional.
          </p>
          <p className="mt-2 text-xs font-semibold text-rose-700">{aiDisclaimer}</p>
        </div>
        <Input label="Busqueda basica" placeholder="demanda, audiencia, poder faltante" />
        <div className="grid gap-3">
          {aiSearchResults.map((item) => (
            <div className="rounded-lg border border-slate-200 bg-white p-3" key={`${item.source}-${item.title}`}>
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{item.source}</Badge>
                <p className="text-sm font-semibold text-ink">{item.title}</p>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-600">{item.excerpt}</p>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}

function HumanReviewQueue() {
  return (
    <Card>
      <PanelTitle icon={<ShieldCheck size={18} />} title="Revision profesional" />
      <div className="mt-4 grid gap-3">
        {aiDocumentJobs.map((job) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={`review-${job.id}`}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-ink">{job.id}</p>
              <Badge>{job.status}</Badge>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button>Aprobar</Button>
              <Button tone="secondary">Rechazar</Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function PromptPanel() {
  return (
    <Card>
      <PanelTitle icon={<Bot size={18} />} title="Prompts versionados" />
      <div className="mt-4 grid gap-3">
        {aiPrompts.map((prompt) => (
          <div className="flex min-w-0 items-center justify-between gap-3 rounded-lg border border-slate-200 bg-mist p-3" key={prompt}>
            <span className="break-all text-sm font-semibold text-ink">{prompt}</span>
            <CheckCircle2 className="shrink-0 text-legal-700" size={16} />
          </div>
        ))}
      </div>
      <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4">
        <PanelTitle icon={<ListChecks size={18} />} title="Extraccion estructurada" />
        <div className="mt-3 grid gap-2">
          {aiExtractions.map((item) => (
            <p className="text-sm text-slate-600" key={item.label}>
              <span className="font-semibold text-ink">{item.label}:</span> {item.value}
            </p>
          ))}
        </div>
      </div>
    </Card>
  );
}

function PanelTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
      {icon}
      <span>{title}</span>
      <Sparkles className="ml-auto text-slate-300" size={16} />
    </div>
  );
}
