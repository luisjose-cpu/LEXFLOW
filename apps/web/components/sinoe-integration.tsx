"use client";

import { Badge, Card, EmptyState, PageHeader } from "@lexflow/ui";
import { AlertTriangle, CheckCircle2, Clock3, KeyRound, Link2, RefreshCcw, ShieldCheck, Trash2 } from "lucide-react";
import React, { FormEvent, useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://lexflow-api.onrender.com";

type IntegrationStatus = {
  provider: string;
  configured: boolean;
  status: string;
  last_checked_at: string | null;
  username_hint: string | null;
};

type UpdateView = {
  id: string;
  title: string;
  summary: string;
  status: string;
  captcha_required: boolean;
  checked_at?: string | null;
};

type SourceView = {
  id: string;
  source_type: string;
  source_name?: string | null;
  external_case_number: string;
  court_name?: string | null;
  status: string;
  captcha_required: boolean;
  last_checked_at?: string | null;
  last_result?: string | null;
};

function token() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("lexflow.access_token") ?? "";
}

async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token()}`,
      ...(options.headers ?? {})
    }
  });
  if (!response.ok) {
    throw new Error(response.status === 403 ? "No tienes permiso para administrar SINOE." : "No se pudo completar la operacion SINOE.");
  }
  return (await response.json()) as T;
}

export function SettingsSinoeIntegration() {
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [state, setState] = useState<"loading" | "idle" | "saving" | "testing" | "deleting" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    void loadStatus();
  }, []);

  async function loadStatus() {
    setState("loading");
    setMessage("");
    try {
      setStatus(await apiRequest<IntegrationStatus>("/settings/integrations/sinoe"));
      setState("idle");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo cargar SINOE.");
    }
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("saving");
    setMessage("");
    try {
      const next = await apiRequest<IntegrationStatus>("/settings/integrations/sinoe", {
        method: "POST",
        body: JSON.stringify({ username, password })
      });
      setStatus(next);
      setPassword("");
      setMessage("Credenciales SINOE guardadas cifradas.");
      setState("idle");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo guardar SINOE.");
    }
  }

  async function testConnection() {
    setState("testing");
    setMessage("");
    try {
      setStatus(await apiRequest<IntegrationStatus>("/settings/integrations/sinoe/test", { method: "POST" }));
      setMessage("Conexion mock SINOE validada.");
      setState("idle");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo probar SINOE.");
    }
  }

  async function remove() {
    setState("deleting");
    setMessage("");
    try {
      setStatus(await apiRequest<IntegrationStatus>("/settings/integrations/sinoe", { method: "DELETE" }));
      setMessage("Integracion SINOE desactivada.");
      setState("idle");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo desactivar SINOE.");
    }
  }

  const canSave = useMemo(() => username.trim().length > 0 && password.length > 0 && state !== "saving", [password, state, username]);

  return (
    <div className="grid gap-5">
      <PageHeader
        description="Configura credenciales autorizadas del SINOE para monitorear expedientes con pausa human-in-the-loop cuando exista CAPTCHA."
        eyebrow="Settings -> Integraciones"
        title="SINOE"
      />
      <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <SinoeConnectionStatus status={status} loading={state === "loading"} />
        <Card>
          <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
            <KeyRound size={18} aria-hidden="true" />
            <span>Credenciales autorizadas</span>
          </div>
          <SinoeCredentialsForm
            canSave={canSave}
            onPasswordChange={setPassword}
            onSubmit={save}
            onUsernameChange={setUsername}
            password={password}
            saving={state === "saving"}
            username={username}
          />
          <div className="mt-4 flex flex-wrap gap-2">
            <ActionButton icon={<CheckCircle2 size={16} />} label="Probar conexion" loading={state === "testing"} onClick={testConnection} tone="secondary" />
            <ActionButton
              icon={<RefreshCcw size={16} />}
              label="Actualizar expedientes"
              onClick={() => setMessage("Usa Revisar ahora desde cada Expediente 360 vinculado a SINOE.")}
              tone="secondary"
            />
            <ActionButton icon={<Trash2 size={16} />} label="Desactivar integracion" loading={state === "deleting"} onClick={remove} tone="ghost" />
          </div>
          {message ? (
            <div className={`mt-4 rounded-md border px-3 py-2 text-sm font-medium ${state === "error" ? "border-red-200 bg-red-50 text-red-700" : "border-legal-100 bg-legal-50 text-legal-900"}`} role="status">
              {message}
            </div>
          ) : null}
        </Card>
      </div>
      <Card>
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-semibold text-ink">Politica CAPTCHA</p>
            <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600">
              LEXFLOW pausa la automatizacion si SINOE solicita verificacion humana. No evade CAPTCHA, no rompe controles anti-bot y no automatiza su resolucion.
            </p>
          </div>
          <Badge>human-in-the-loop</Badge>
        </div>
      </Card>
    </div>
  );
}

export function SinoeCredentialsForm({
  username,
  password,
  onUsernameChange,
  onPasswordChange,
  onSubmit,
  canSave,
  saving
}: {
  username: string;
  password: string;
  onUsernameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  canSave: boolean;
  saving: boolean;
}) {
  return (
    <form className="mt-5 grid gap-4" onSubmit={onSubmit}>
      <Field autoComplete="username" label="Usuario SINOE" onChange={onUsernameChange} placeholder="usuario autorizado" value={username} />
      <Field autoComplete="new-password" label="Contrasena SINOE" onChange={onPasswordChange} placeholder="se guarda cifrada" type="password" value={password} />
      <div>
        <button
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white transition hover:bg-legal-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={!canSave}
          type="submit"
        >
          <ShieldCheck size={16} aria-hidden="true" />
          {saving ? "Guardando..." : "Guardar credenciales"}
        </button>
      </div>
    </form>
  );
}

export function SinoeConnectionStatus({ status, loading }: { status: IntegrationStatus | null; loading?: boolean }) {
  const configured = Boolean(status?.configured);
  return (
    <Card>
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
          <ShieldCheck size={18} aria-hidden="true" />
          <span>Estado de conexion</span>
        </div>
        <StatusPill status={loading ? "loading" : status?.status ?? "not_configured"} />
      </div>
      {loading ? (
        <div className="mt-5">
          <EmptyState title="Cargando SINOE" description="Consultando el estado de integracion del tenant." />
        </div>
      ) : (
        <div className="mt-5 grid gap-3 text-sm">
          <Row label="Proveedor" value="SINOE" />
          <Row label="Configurado" value={configured ? "Si" : "No"} />
          <Row label="Usuario" value={status?.username_hint ?? "No expuesto"} />
          <Row label="Ultima verificacion" value={status?.last_checked_at ? formatDate(status.last_checked_at) : "Sin verificacion"} />
        </div>
      )}
    </Card>
  );
}

export function SinoeCaseSourceForm({ caseId }: { caseId: string }) {
  const [externalCaseNumber, setExternalCaseNumber] = useState("");
  const [district, setDistrict] = useState("");
  const [site, setSite] = useState("");
  const [reference, setReference] = useState("");
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await apiRequest(`/cases/${caseId}/sources/sinoe`, {
        method: "POST",
        body: JSON.stringify({ external_case_number: externalCaseNumber, district, site, reference })
      });
      setMessage("Fuente SINOE vinculada al expediente.");
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "No se pudo vincular SINOE.");
    }
  }

  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <Link2 size={18} aria-hidden="true" />
        <span>Vincular SINOE</span>
      </div>
      <form className="mt-4 grid gap-4" onSubmit={submit}>
        <Field label="Numero de expediente" onChange={setExternalCaseNumber} placeholder="SINOE-2026-001" value={externalCaseNumber} />
        <div className="grid gap-4 md:grid-cols-3">
          <Field label="Distrito" onChange={setDistrict} placeholder="Lima" value={district} />
          <Field label="Sede" onChange={setSite} placeholder="Sede central" value={site} />
          <Field label="Referencia" onChange={setReference} placeholder="Casilla autorizada" value={reference} />
        </div>
        <button className="inline-flex h-10 w-fit items-center justify-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white transition hover:bg-legal-700" type="submit">
          <Link2 size={16} aria-hidden="true" />
          Agregar fuente SINOE
        </button>
      </form>
      {message ? <p className="mt-3 rounded-md bg-legal-50 px-3 py-2 text-sm font-medium text-legal-900">{message}</p> : null}
    </Card>
  );
}

export function SinoeUpdatePanel({ sources }: { sources: SourceView[] }) {
  const sinoeSources = sources.filter((source) => source.source_type === "sinoe");
  const [message, setMessage] = useState("");

  async function checkSource(sourceId: string) {
    setMessage("");
    try {
      const result = await apiRequest<{ status: string }>(`/case-sources/${sourceId}/sinoe/check`, { method: "POST" });
      setMessage(result.status === "captcha_required" ? "SINOE requiere verificacion humana para continuar." : "Revision SINOE ejecutada.");
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "No se pudo revisar SINOE.");
    }
  }

  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <RefreshCcw size={18} aria-hidden="true" />
        <span>Fuentes SINOE</span>
      </div>
      {sinoeSources.length ? (
        <div className="mt-4 grid gap-3">
          {sinoeSources.map((source) => (
            <div className="rounded-lg border border-slate-200 bg-mist p-4" key={source.id}>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-ink">{source.source_name ?? "SINOE"}</p>
                  <p className="mt-1 text-sm text-slate-600">{source.external_case_number}</p>
                  <p className="mt-2 text-xs font-medium text-slate-500">
                    Ultima revision: {source.last_checked_at ? formatDate(source.last_checked_at) : "pendiente"} · Resultado: {source.last_result ?? "sin resultado"}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <StatusPill status={source.captcha_required ? "captcha_required" : source.status} />
                  <button
                    className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-xs font-semibold text-ink hover:bg-legal-50"
                    onClick={() => void checkSource(source.id)}
                    type="button"
                  >
                    <RefreshCcw size={14} aria-hidden="true" />
                    Revisar ahora
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="mt-4">
          <EmptyState title="Sin fuente SINOE" description="Vincula el expediente para recibir movimientos, notificaciones o cambios relevantes autorizados." />
        </div>
      )}
      {message ? <p className="mt-3 rounded-md bg-legal-50 px-3 py-2 text-sm font-medium text-legal-900">{message}</p> : null}
    </Card>
  );
}

export function CaptchaCheckpointModal({ checkpoint }: { checkpoint: { id: string; status: string; reason: string } | null }) {
  if (!checkpoint) return null;
  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-rose-700">
        <AlertTriangle size={18} aria-hidden="true" />
        <span>SINOE requiere verificacion humana para continuar.</span>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-600">
        La automatizacion queda pausada. Un usuario autorizado debe completar manualmente la verificacion en SINOE; LEXFLOW solo registra la resolucion y auditoria.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <Badge>{checkpoint.status}</Badge>
        <Badge>{checkpoint.reason}</Badge>
      </div>
    </Card>
  );
}

export function SinoeUpdateHistory({ updates }: { updates: UpdateView[] }) {
  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <Clock3 size={18} aria-hidden="true" />
        <span>Historial SINOE</span>
      </div>
      {updates.length ? (
        <div className="mt-4 grid gap-3">
          {updates.map((update) => (
            <article className="rounded-lg border border-slate-200 bg-mist p-4" key={update.id}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-ink">{update.title}</p>
                  <p className="mt-1 text-sm leading-6 text-slate-600">{update.summary}</p>
                </div>
                <StatusPill status={update.captcha_required ? "captcha_required" : update.status} />
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="mt-4">
          <EmptyState title="Sin actualizaciones SINOE" description="El historial se llenara con revisiones mock autorizadas y futuras integraciones permitidas." />
        </div>
      )}
    </Card>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  autoComplete
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  type?: string;
  autoComplete?: string;
}) {
  return (
    <label className="grid gap-2 text-sm font-semibold text-ink">
      {label}
      <input
        autoComplete={autoComplete}
        className="h-11 rounded-md border border-slate-200 bg-white px-3 text-sm font-normal text-ink outline-none transition placeholder:text-slate-400 focus:border-legal-500 focus:shadow-[0_0_0_3px_rgba(36,153,232,0.18)]"
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        type={type}
        value={value}
      />
    </label>
  );
}

function ActionButton({
  label,
  icon,
  onClick,
  loading,
  tone
}: {
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  loading?: boolean;
  tone: "secondary" | "ghost";
}) {
  const classes =
    tone === "secondary"
      ? "border border-slate-200 bg-white text-ink hover:border-legal-100 hover:bg-legal-50"
      : "text-slate-600 hover:bg-slate-100";
  return (
    <button className={`inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-semibold transition ${classes}`} onClick={onClick} type="button">
      {icon}
      {loading ? "Procesando..." : label}
    </button>
  );
}

function StatusPill({ status }: { status: string }) {
  const captcha = status === "captcha_required" || status === "paused_captcha";
  const connected = status === "connected" || status === "active" || status === "configured";
  const classes = captcha ? "bg-rose-50 text-rose-700" : connected ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-700";
  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-semibold ${classes}`}>
      {captcha ? <AlertTriangle size={14} aria-hidden="true" /> : connected ? <CheckCircle2 size={14} aria-hidden="true" /> : <Clock3 size={14} aria-hidden="true" />}
      {status}
    </span>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-mist px-3 py-2">
      <span className="text-slate-500">{label}</span>
      <span className="text-right font-semibold text-ink">{value}</span>
    </div>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}
