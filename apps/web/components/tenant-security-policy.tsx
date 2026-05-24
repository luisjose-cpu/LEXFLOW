"use client";

import { Card } from "@lexflow/ui";
import { LockKeyhole, ShieldCheck } from "lucide-react";
import React from "react";
import { useEffect, useState } from "react";
import { hasCloudSession, loadTenantSecurityPolicy, updateTenantSecurityPolicy } from "@/lib/lexflow-api";

const roleOptions = [
  { value: "tenant_admin", label: "Tenant admin" },
  { value: "partner", label: "Socio" },
  { value: "lawyer", label: "Abogado" },
  { value: "assistant", label: "Asistente" },
  { value: "client_user", label: "Cliente portal" }
];

export function TenantSecurityPolicy() {
  const [enforceMfa, setEnforceMfa] = useState(false);
  const [requiredRoles, setRequiredRoles] = useState<string[]>(["tenant_admin", "partner"]);
  const [gracePeriodHours, setGracePeriodHours] = useState(72);
  const [allowClientBypass, setAllowClientBypass] = useState(true);
  const [state, setState] = useState<"idle" | "loading" | "saving" | "error" | "success">("idle");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!hasCloudSession()) return;
    setState("loading");
    void loadTenantSecurityPolicy()
      .then((policy) => {
        setEnforceMfa(policy.enforce_mfa);
        setRequiredRoles(policy.mfa_required_roles);
        setGracePeriodHours(policy.grace_period_hours);
        setAllowClientBypass(policy.allow_client_user_mfa_bypass);
        setState("idle");
      })
      .catch(() => {
        setState("error");
        setMessage("No se pudo cargar la politica de seguridad.");
      });
  }, []);

  async function savePolicy() {
    if (!hasCloudSession()) {
      setState("error");
      setMessage("Inicia sesion para cambiar la politica del tenant.");
      return;
    }
    setState("saving");
    setMessage("");
    try {
      const policy = await updateTenantSecurityPolicy({
        enforce_mfa: enforceMfa,
        mfa_required_roles: requiredRoles,
        grace_period_hours: gracePeriodHours,
        allow_client_user_mfa_bypass: allowClientBypass
      });
      setEnforceMfa(policy.enforce_mfa);
      setRequiredRoles(policy.mfa_required_roles);
      setGracePeriodHours(policy.grace_period_hours);
      setAllowClientBypass(policy.allow_client_user_mfa_bypass);
      setState("success");
      setMessage("Politica guardada y auditada.");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo guardar la politica.");
    }
  }

  function toggleRole(role: string) {
    setRequiredRoles((current) => (current.includes(role) ? current.filter((item) => item !== role) : [...current, role]));
  }

  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <ShieldCheck size={18} aria-hidden="true" />
        <span>Politica tenant</span>
      </div>
      <h2 className="mt-4 text-xl font-semibold text-ink">MFA obligatorio</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        Define que roles deben tener MFA activo antes de iniciar sesion. Los cambios se registran en audit_log.
      </p>
      <div className="mt-5 grid gap-4">
        <label className="flex items-center justify-between gap-4 rounded-md border border-slate-200 px-3 py-3 text-sm font-semibold text-ink">
          Exigir MFA para roles seleccionados
          <input checked={enforceMfa} className="h-5 w-5 accent-legal-900" onChange={(event) => setEnforceMfa(event.target.checked)} type="checkbox" />
        </label>
        <div className="grid gap-2">
          <p className="text-sm font-semibold text-ink">Roles cubiertos</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {roleOptions.map((role) => (
              <label className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-700" key={role.value}>
                <input checked={requiredRoles.includes(role.value)} className="h-4 w-4 accent-legal-900" onChange={() => toggleRole(role.value)} type="checkbox" />
                {role.label}
              </label>
            ))}
          </div>
        </div>
        <label className="grid gap-2 text-sm font-semibold text-ink">
          Horas de gracia operacional
          <input
            className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
            max={720}
            min={0}
            onChange={(event) => setGracePeriodHours(Number(event.target.value))}
            type="number"
            value={gracePeriodHours}
          />
        </label>
        <label className="flex items-center justify-between gap-4 rounded-md border border-slate-200 px-3 py-3 text-sm font-semibold text-ink">
          Permitir bypass para cliente portal
          <input checked={allowClientBypass} className="h-5 w-5 accent-legal-900" onChange={(event) => setAllowClientBypass(event.target.checked)} type="checkbox" />
        </label>
        <p className="rounded-md bg-amber-50 px-3 py-2 text-sm leading-6 text-amber-800">
          Antes de activar MFA obligatorio para tu propio rol, activa MFA en tu cuenta para evitar bloqueo administrativo.
        </p>
        <button
          className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60"
          disabled={state === "loading" || state === "saving"}
          onClick={savePolicy}
          type="button"
        >
          <LockKeyhole size={16} aria-hidden="true" />
          {state === "saving" ? "Guardando..." : "Guardar politica"}
        </button>
      </div>
      {message ? <p className={`mt-4 rounded-md px-3 py-2 text-sm ${state === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{message}</p> : null}
    </Card>
  );
}
