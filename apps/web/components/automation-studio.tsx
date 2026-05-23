"use client";

import { Badge, Button, Card, MetricCard } from "@lexflow/ui";
import { AlertTriangle, ArrowRight, Bolt, CheckCircle2, ClipboardCheck, GitBranch, ListChecks, PlayCircle, ShieldCheck, SlidersHorizontal } from "lucide-react";
import React from "react";
import { automationActions, automationMetrics, automationTriggers, automationWorkflow } from "@/lib/automation-demo";

export function AutomationStudio() {
  return (
    <div className="grid gap-5">
      <header className="rounded-lg border border-white/80 bg-white p-5 shadow-soft">
        <div className="flex flex-wrap gap-2">
          <Badge>P13</Badge>
          <Badge>Automation Studio</Badge>
          <Badge>Trigger - Condition - Action - Audit - Result</Badge>
        </div>
        <div className="mt-4 flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <h1 className="text-3xl font-semibold tracking-normal text-ink sm:text-4xl">Automation Studio</h1>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
              Motor no-code legal para automatizar tareas, comunicaciones, eventos, IA mock e inteligencia sin romper permisos, feature gates ni auditoria.
            </p>
          </div>
          <Button>
            <PlayCircle size={16} />
            Probar workflow
          </Button>
        </div>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {automationMetrics.map((item) => (
          <MetricCard key={item.label} label={item.label} value={item.value} trend={item.trend} />
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <BuilderSteps />
        <WorkflowPreview />
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <CatalogPanel />
        <RunResultPanel />
      </section>
    </div>
  );
}

function BuilderSteps() {
  const steps = [
    { icon: <GitBranch size={18} />, title: "1. Trigger", body: automationWorkflow.trigger },
    { icon: <SlidersHorizontal size={18} />, title: "2. Condiciones", body: automationWorkflow.conditions.map((item) => item.label).join(" + ") },
    { icon: <Bolt size={18} />, title: "3. Acciones", body: automationWorkflow.actions.map((item) => item.type).join(", ") },
    { icon: <PlayCircle size={18} />, title: "4. Probar", body: "Dry run con payload del expediente antes de activar." },
    { icon: <ShieldCheck size={18} />, title: "5. Activar", body: "Audit log obligatorio y ejecucion tenant-scoped." }
  ];
  return (
    <Card>
      <PanelTitle icon={<ClipboardCheck size={18} />} title="Builder por pasos" />
      <div className="mt-4 grid gap-3">
        {steps.map((step) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={step.title}>
            <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
              {step.icon}
              <span>{step.title}</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{step.body}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function WorkflowPreview() {
  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PanelTitle icon={<ListChecks size={18} />} title="Workflow activo" />
        <Badge>{automationWorkflow.status}</Badge>
      </div>
      <h2 className="mt-4 text-xl font-semibold text-ink">{automationWorkflow.name}</h2>
      <div className="mt-5 grid gap-3">
        <FlowRow label="TRIGGER" value={automationWorkflow.trigger} />
        {automationWorkflow.conditions.map((item) => (
          <FlowRow key={item.label} label="CONDITION" value={item.label} />
        ))}
        {automationWorkflow.actions.map((item) => (
          <FlowRow key={item.label} label="ACTION" value={item.label} />
        ))}
        <FlowRow label="AUDIT" value="automation.run_workflow + run_steps" />
        <FlowRow label="RESULT" value="succeeded / skipped / failed" />
      </div>
    </Card>
  );
}

function CatalogPanel() {
  return (
    <Card>
      <PanelTitle icon={<Bolt size={18} />} title="Catalogo no-code" />
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <p className="text-sm font-semibold text-ink">Triggers</p>
          <div className="mt-3 grid gap-2">
            {automationTriggers.slice(0, 8).map((item) => (
              <CatalogChip key={item} text={item} />
            ))}
          </div>
        </div>
        <div>
          <p className="text-sm font-semibold text-ink">Actions</p>
          <div className="mt-3 grid gap-2">
            {automationActions.slice(0, 6).map((item) => (
              <CatalogChip key={item} text={item} />
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
}

function RunResultPanel() {
  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PanelTitle icon={<CheckCircle2 size={18} />} title="Resultado de prueba" />
        <Badge>{automationWorkflow.run.status}</Badge>
      </div>
      <div className="mt-4 grid gap-3">
        {automationWorkflow.run.steps.map((step, index) => (
          <div className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-mist p-3" key={`${step.key}-${index}`}>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-ink">{step.key}</p>
              <p className="text-xs text-slate-500">{step.type}</p>
            </div>
            <span className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">{step.status}</span>
          </div>
        ))}
      </div>
      <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3">
        <div className="flex items-start gap-2">
          <AlertTriangle className="mt-0.5 shrink-0 text-amber-700" size={16} />
          <p className="text-sm leading-6 text-amber-800">Acciones sensibles como cambio de estado o asignacion deben mantenerse auditadas y revisables.</p>
        </div>
      </div>
    </Card>
  );
}

function FlowRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-slate-200 bg-mist p-3">
      <span className="w-24 shrink-0 rounded-md bg-white px-2 py-1 text-xs font-semibold text-legal-700">{label}</span>
      <ArrowRight size={15} className="shrink-0 text-slate-400" />
      <p className="min-w-0 text-sm font-semibold leading-6 text-ink">{value}</p>
    </div>
  );
}

function CatalogChip({ text }: { text: string }) {
  return <span className="rounded-md border border-slate-200 bg-mist px-2.5 py-2 text-xs font-semibold text-slate-700">{text}</span>;
}

function PanelTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
      {icon}
      <span>{title}</span>
    </div>
  );
}
