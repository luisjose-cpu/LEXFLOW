"use client";

import { Badge, Button, Card, MetricCard } from "@lexflow/ui";
import { CheckCircle2, ClipboardList, FileSpreadsheet, Rocket, ShieldCheck, Terminal, UploadCloud, XCircle } from "lucide-react";
import React, { useEffect, useState } from "react";
import { csvTemplates, gateCommands, importFlow, pilotChecklist, pilotMetrics, productionGate } from "@/lib/ops-demo";
import { hasCloudSession, loadProductionGate, ProductionGateReport } from "@/lib/lexflow-api";

type OpsView = "import" | "pilot" | "gate";

export function OpsCenter({ view }: { view: OpsView }) {
  return (
    <div className="grid gap-5">
      <OpsHero view={view} />
      {view === "import" ? <ImportCenter /> : null}
      {view === "pilot" ? <PilotOpsCenter /> : null}
      {view === "gate" ? <ProductionGate /> : null}
    </div>
  );
}

function OpsHero({ view }: { view: OpsView }) {
  const title = {
    import: "Importacion CSV",
    pilot: "Pilot Ops Center",
    gate: "Production Gate"
  }[view];
  const description = {
    import: "Carga clientes, expedientes y manifiestos documentales desde CSV con dry-run, auditoria y storage keys.",
    pilot: "Mide si el tenant esta listo para piloto controlado y que falta para ejecutar la demo real.",
    gate: "Agrupa blockers productivos, comandos obligatorios y controles antes de produccion publica."
  }[view];
  return (
    <header className="rounded-lg border border-white/80 bg-white p-5 shadow-soft">
      <div className="flex flex-wrap gap-2">
        <Badge>P21-P23</Badge>
        <Badge>Ops</Badge>
        <Badge>Tenant scoped</Badge>
      </div>
      <div className="mt-4 flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
        <div>
          <h1 className="text-3xl font-semibold tracking-normal text-ink sm:text-4xl">{title}</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">{description}</p>
        </div>
        <Button>
          <Rocket size={16} />
          Ejecutar checklist
        </Button>
      </div>
    </header>
  );
}

function ImportCenter() {
  return (
    <>
      <section className="grid gap-4 lg:grid-cols-3">
        {csvTemplates.map((template) => (
          <Card key={template.kind}>
            <div className="flex items-center justify-between gap-3">
              <PanelTitle icon={<FileSpreadsheet size={18} />} title={template.label} />
              <Badge>{template.kind}</Badge>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-600">Requeridos: {template.required}</p>
            <pre className="mt-4 overflow-x-auto rounded-lg bg-legal-900 p-4 text-xs leading-5 text-white">{template.csv}</pre>
          </Card>
        ))}
      </section>
      <Card>
        <PanelTitle icon={<UploadCloud size={18} />} title="Flujo recomendado" />
        <div className="mt-4 grid gap-3 md:grid-cols-7">
          {importFlow.map((step, index) => (
            <div className="rounded-lg border border-slate-200 bg-mist p-3" key={step}>
              <span className="grid h-8 w-8 place-items-center rounded-md bg-white text-sm font-semibold text-legal-700">{index + 1}</span>
              <p className="mt-3 text-sm font-semibold text-ink">{step}</p>
            </div>
          ))}
        </div>
      </Card>
    </>
  );
}

function PilotOpsCenter() {
  return (
    <>
      <section className="grid gap-4 md:grid-cols-4">
        {pilotMetrics.map((item) => (
          <MetricCard key={item.label} label={item.label} value={item.value} trend={item.trend} />
        ))}
      </section>
      <Card>
        <PanelTitle icon={<ClipboardList size={18} />} title="Readiness piloto" />
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {pilotChecklist.map((item) => (
            <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-mist p-4" key={item.label}>
              {item.ok ? <CheckCircle2 className="text-emerald-600" size={18} /> : <XCircle className="text-amber-600" size={18} />}
              <span className="text-sm font-semibold text-ink">{item.label}</span>
            </div>
          ))}
        </div>
      </Card>
    </>
  );
}

function ProductionGate() {
  const [report, setReport] = useState<ProductionGateReport | null>(null);
  const [source, setSource] = useState<"demo" | "loading" | "live" | "fallback">("demo");

  useEffect(() => {
    if (!hasCloudSession()) {
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    void loadProductionGate()
      .then((payload) => {
        if (!active) return;
        setReport(payload);
        setSource("live");
      })
      .catch(() => {
        if (!active) return;
        setSource("fallback");
      });
    return () => {
      active = false;
    };
  }, []);

  const liveChecks = report?.readiness?.checks?.length
    ? report.readiness.checks.map((item) => ({
        key: item.key,
        status: item.ok ? "pass" : item.severity,
        detail: item.message
      }))
    : productionGate;
  const commands = report?.commands?.length ? report.commands : gateCommands;
  const blockers = report?.summary?.blockers ?? 0;
  const warnings = report?.summary?.warnings ?? 0;

  return (
    <section className="grid gap-5 xl:grid-cols-[1fr_1fr]">
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <PanelTitle icon={<ShieldCheck size={18} />} title="Gate productivo" />
          <Badge>{source}</Badge>
        </div>
        {report ? (
          <div className="mt-4 grid gap-3 rounded-lg border border-slate-200 bg-mist p-4 sm:grid-cols-2 xl:grid-cols-4">
            <Metric label="Estado" value={report.status} />
            <Metric label="Public prod" value={report.readiness?.public_production_ready ? "ready" : "not ready"} />
            <Metric label="Blockers" value={String(blockers)} />
            <Metric label="Warnings" value={String(warnings)} />
          </div>
        ) : null}
        <div className="mt-4 grid gap-3">
          {liveChecks.map((item) => (
            <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.key}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-semibold text-ink">{item.key}</p>
                <Badge>{item.status}</Badge>
              </div>
              <p className="mt-2 text-sm text-slate-600">{item.detail}</p>
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <PanelTitle icon={<Terminal size={18} />} title="Comandos obligatorios" />
        <div className="mt-4 grid gap-3">
          {commands.map((command) => (
            <code className="rounded-lg border border-slate-200 bg-legal-900 p-3 text-sm font-semibold text-white" key={command}>
              {command}
            </code>
          ))}
        </div>
        {report?.required_before_public_production?.length ? (
          <div className="mt-5 rounded-lg border border-slate-200 bg-mist p-4">
            <p className="text-sm font-semibold text-ink">Pendiente para produccion publica</p>
            <div className="mt-3 grid gap-2">
              {report.required_before_public_production.map((item) => (
                <p className="text-sm text-slate-600" key={item}>{item}</p>
              ))}
            </div>
          </div>
        ) : null}
      </Card>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-normal text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-ink">{value}</p>
    </div>
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
