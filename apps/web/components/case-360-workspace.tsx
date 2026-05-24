"use client";

import { Badge, Card } from "@lexflow/ui";
import { Brain, CalendarClock, CheckCircle2, FilePlus2, MessageCircle, Plus, RefreshCcw, ShieldCheck } from "lucide-react";
import React, { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertsPanel,
  AuditSummaryPanel,
  CaseHeader,
  CaseTimeline,
  ClientSummaryCard,
  CommunicationsPanel,
  DocumentsPanel,
  HearingsPanel,
  IntelligenceRelatedPanel,
  JudicialUpdatesPanel,
  NextActionsPanel,
  TasksPanel,
  type Case360Data
} from "@/components/case-360";
import { SinoeCaseSourceForm, SinoeUpdateHistory, SinoeUpdatePanel } from "@/components/sinoe-integration";
import {
  checkSinoeSource,
  createCaseCommunication,
  createCaseDocument,
  createCaseEvent,
  createCaseHearing,
  createCaseTask,
  hasCloudSession,
  loadCaseOverview,
  runCaseAiSummary,
  updateCaseDocument,
  updateCaseHearing,
  updateCaseTask
} from "@/lib/lexflow-api";

type LoadState = "demo" | "loading" | "live" | "fallback";
type ActionState = "idle" | "saving" | "error";

export function Case360Workspace({ initialData }: { initialData: Case360Data }) {
  const [data, setData] = useState(initialData);
  const [source, setSource] = useState<LoadState>("demo");
  const [message, setMessage] = useState("");
  const [actionState, setActionState] = useState<ActionState>("idle");
  const sinoeSources = useMemo(() => data.case_sources.filter((source) => source.source_type === "sinoe"), [data.case_sources]);

  const refresh = useCallback(async () => {
    if (!hasCloudSession()) {
      setSource("demo");
      return;
    }
    setSource("loading");
    try {
      setData(await loadCaseOverview(data.case.id));
      setSource("live");
    } catch {
      setSource("fallback");
    }
  }, [data.case.id]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function runAction(label: string, action: () => Promise<unknown>) {
    setActionState("saving");
    setMessage("");
    try {
      await action();
      setMessage(`${label} completado y auditado.`);
      setActionState("idle");
      await refresh();
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : `No se pudo completar ${label}.`);
      setActionState("error");
    }
  }

  async function checkAllSinoe() {
    if (!sinoeSources.length) {
      setMessage("Vincula una fuente SINOE antes de revisar.");
      return;
    }
    await runAction("Revision SINOE", async () => {
      for (const source of sinoeSources) {
        await checkSinoeSource(source.id);
      }
    });
  }

  return (
    <div className="grid gap-5">
      <CaseHeader data={data} />
      <WorkspaceStatus state={source} message={message} actionState={actionState} onRefresh={() => void refresh()} />
      <section className="grid gap-5 xl:grid-cols-[1.4fr_0.8fr]">
        <div className="grid gap-5">
          <CaseTimeline items={data.timeline} />
          <ActionComposer caseId={data.case.id} runAction={runAction} />
          <DocumentsPanel items={data.documents} />
          <HearingsPanel items={data.hearings} />
          <JudicialUpdatesPanel items={data.judicial_updates} />
          <CommunicationsPanel items={data.communications} />
          <IntelligenceRelatedPanel items={data.related_intelligence} />
        </div>
        <aside className="grid content-start gap-5">
          <ClientSummaryCard data={data} />
          <NextActionsPanel items={data.next_actions} />
          <TasksPanel items={data.tasks} />
          <LifecyclePanel data={data} runAction={runAction} />
          <SinoeActions onCheckAll={() => void checkAllSinoe()} sourceCount={sinoeSources.length} />
          <SinoeUpdatePanel sources={data.case_sources} />
          <SinoeUpdateHistory updates={data.judicial_updates} />
          <SinoeCaseSourceForm caseId={data.case.id} />
          <AiCasePanel caseId={data.case.id} runAction={runAction} />
          <AlertsPanel items={data.alerts} />
          <AuditSummaryPanel data={data.audit_summary} />
        </aside>
      </section>
    </div>
  );
}

function LifecyclePanel({ data, runAction }: { data: Case360Data; runAction: (label: string, action: () => Promise<unknown>) => Promise<void> }) {
  const openTask = data.tasks.find((task) => task.status !== "done");
  const pendingHearing = data.hearings.find((hearing) => !["completed", "cancelled"].includes(hearing.status));
  const pendingDocument = data.documents.find((document) => !["approved", "archived"].includes(document.status));
  const hasActions = Boolean(openTask || pendingHearing || pendingDocument);

  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <CheckCircle2 size={18} aria-hidden="true" />
        <span>Cierre operativo</span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">Avanza tareas, audiencias y documentos con registro en timeline y audit_log.</p>
      <div className="mt-4 grid gap-2">
        {openTask ? (
          <LifecycleButton label={`Cerrar tarea: ${openTask.title}`} onClick={() => void runAction("Cierre de tarea", () => updateCaseTask(data.case.id, openTask.id, { status: "done" }))} />
        ) : null}
        {pendingHearing ? (
          <LifecycleButton label={`Completar audiencia: ${pendingHearing.title}`} onClick={() => void runAction("Cierre de audiencia", () => updateCaseHearing(data.case.id, pendingHearing.id, { status: "completed" }))} />
        ) : null}
        {pendingDocument ? (
          <LifecycleButton label={`Aprobar documento: ${pendingDocument.filename}`} onClick={() => void runAction("Aprobacion documental", () => updateCaseDocument(data.case.id, pendingDocument.id, { status: "approved", is_client_visible: true }))} />
        ) : null}
        {!hasActions ? <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">Sin pendientes operativos inmediatos.</p> : null}
      </div>
    </Card>
  );
}

function LifecycleButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-left text-sm font-semibold text-ink hover:bg-legal-50" onClick={onClick} type="button">
      <CheckCircle2 size={16} aria-hidden="true" />
      <span className="min-w-0 break-words">{label}</span>
    </button>
  );
}

function WorkspaceStatus({ state, message, actionState, onRefresh }: { state: LoadState; message: string; actionState: ActionState; onRefresh: () => void }) {
  const label = {
    demo: "Modo demo hasta iniciar sesion",
    loading: "Cargando Expediente 360 desde API",
    live: "Expediente 360 conectado a datos reales",
    fallback: "API no disponible: mantengo demo seguro"
  }[state];
  return (
    <Card className="p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <Badge>{label}</Badge>
          {actionState === "saving" ? <Badge>guardando</Badge> : null}
          {actionState === "error" ? <Badge>requiere revision</Badge> : null}
        </div>
        <button className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-ink hover:bg-legal-50" onClick={onRefresh} type="button">
          <RefreshCcw size={16} aria-hidden="true" />
          Refrescar
        </button>
      </div>
      {message ? <p className={`mt-3 rounded-md px-3 py-2 text-sm font-medium ${actionState === "error" ? "bg-rose-50 text-rose-700" : "bg-legal-50 text-legal-900"}`}>{message}</p> : null}
    </Card>
  );
}

function ActionComposer({ caseId, runAction }: { caseId: string; runAction: (label: string, action: () => Promise<unknown>) => Promise<void> }) {
  const [note, setNote] = useState("Seguimiento del expediente");
  const [task, setTask] = useState("Preparar siguiente actuacion");
  const [dueAt, setDueAt] = useState("");
  const [documentName, setDocumentName] = useState("nuevo-documento.pdf");
  const [hearingTitle, setHearingTitle] = useState("Audiencia");
  const [hearingAt, setHearingAt] = useState("");
  const [communication, setCommunication] = useState("Mensaje al cliente");

  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <Plus size={18} aria-hidden="true" />
        <span>Acciones del expediente</span>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <MiniForm
          button="Agregar nota"
          icon={<Plus size={16} />}
          onSubmit={() => runAction("Nota", () => createCaseEvent(caseId, { title: note, description: "Creado desde Expediente 360", event_type: "note" }))}
        >
          <Field label="Nota timeline" onChange={setNote} value={note} />
        </MiniForm>
        <MiniForm
          button="Crear tarea"
          icon={<ShieldCheck size={16} />}
          onSubmit={() => runAction("Tarea", () => createCaseTask(caseId, { title: task, due_at: dueAt ? new Date(dueAt).toISOString() : undefined }))}
        >
          <Field label="Tarea" onChange={setTask} value={task} />
          <Field label="Vencimiento" onChange={setDueAt} type="datetime-local" value={dueAt} />
        </MiniForm>
        <MiniForm
          button="Registrar documento"
          icon={<FilePlus2 size={16} />}
          onSubmit={() => runAction("Documento", () => createCaseDocument(caseId, { filename: documentName, storage_key: `case/${caseId}/${documentName}`, classification: "evidence", content_type: "application/pdf" }))}
        >
          <Field label="Documento" onChange={setDocumentName} value={documentName} />
        </MiniForm>
        <MiniForm
          button="Crear audiencia"
          icon={<CalendarClock size={16} />}
          onSubmit={() => runAction("Audiencia", () => createCaseHearing(caseId, { title: hearingTitle, starts_at: hearingAt ? new Date(hearingAt).toISOString() : new Date(Date.now() + 86400000).toISOString(), location: "Virtual" }))}
        >
          <Field label="Audiencia" onChange={setHearingTitle} value={hearingTitle} />
          <Field label="Fecha y hora" onChange={setHearingAt} type="datetime-local" value={hearingAt} />
        </MiniForm>
        <MiniForm
          button="Enviar mensaje"
          icon={<MessageCircle size={16} />}
          onSubmit={() => runAction("Comunicacion", () => createCaseCommunication(caseId, { body: communication, channel: "portal", direction: "outbound" }))}
        >
          <Field label="Mensaje portal" onChange={setCommunication} value={communication} />
        </MiniForm>
      </div>
    </Card>
  );
}

function SinoeActions({ sourceCount, onCheckAll }: { sourceCount: number; onCheckAll: () => void }) {
  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <RefreshCcw size={18} aria-hidden="true" />
        <span>Actualizacion judicial</span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">Consume el modulo SINOE existente. Si aparece CAPTCHA, LEXFLOW pausa y exige intervencion humana.</p>
      <button className="mt-4 inline-flex h-10 items-center justify-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white hover:bg-legal-700" onClick={onCheckAll} type="button">
        <RefreshCcw size={16} aria-hidden="true" />
        Revisar SINOE ({sourceCount})
      </button>
    </Card>
  );
}

function AiCasePanel({ caseId, runAction }: { caseId: string; runAction: (label: string, action: () => Promise<unknown>) => Promise<void> }) {
  const [lastSummary, setLastSummary] = useState("");
  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <Brain size={18} aria-hidden="true" />
        <span>IA expediente</span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">Resumen, plazos, pendientes y riesgos. Toda salida requiere revision profesional.</p>
      <button
        className="mt-4 inline-flex h-10 items-center justify-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white hover:bg-legal-700"
        onClick={() =>
          void runAction("Resumen IA", async () => {
            const result = await runCaseAiSummary(caseId);
            setLastSummary(String(result.result?.summary ?? result.disclaimer ?? "Resumen IA generado. Requiere revision profesional."));
          })
        }
        type="button"
      >
        <Brain size={16} aria-hidden="true" />
        Generar resumen IA
      </button>
      {lastSummary ? <p className="mt-3 rounded-md bg-legal-50 px-3 py-2 text-sm leading-6 text-legal-900">{lastSummary}</p> : null}
    </Card>
  );
}

function MiniForm({ children, button, icon, onSubmit }: { children: React.ReactNode; button: string; icon: React.ReactNode; onSubmit: () => void }) {
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }
  return (
    <form className="grid gap-3 rounded-lg border border-slate-200 bg-mist p-4" onSubmit={submit}>
      {children}
      <button className="inline-flex h-10 w-fit items-center justify-center gap-2 rounded-md bg-white px-4 text-sm font-semibold text-ink shadow-sm hover:bg-legal-50" type="submit">
        {icon}
        {button}
      </button>
    </form>
  );
}

function Field({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (value: string) => void; type?: string }) {
  return (
    <label className="grid gap-2 text-sm font-semibold text-ink">
      {label}
      <input className="h-11 rounded-md border border-slate-200 bg-white px-3 text-sm font-normal text-ink outline-none focus:border-legal-500" onChange={(event) => onChange(event.target.value)} type={type} value={value} />
    </label>
  );
}
