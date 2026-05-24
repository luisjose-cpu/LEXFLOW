"use client";

import { Card } from "@lexflow/ui";
import { KeyRound, QrCode, ShieldCheck } from "lucide-react";
import React from "react";
import { FormEvent, useEffect, useState } from "react";
import { changePassword, disableMfa, hasCloudSession, loadMfaStatus, startMfaEnrollment, verifyMfaEnrollment } from "@/lib/lexflow-api";

export function AccountSecurity() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [state, setState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [message, setMessage] = useState("");
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [mfaPending, setMfaPending] = useState(false);
  const [mfaSecret, setMfaSecret] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [mfaPassword, setMfaPassword] = useState("");
  const [mfaPolicyRequired, setMfaPolicyRequired] = useState(false);
  const [mfaState, setMfaState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [mfaMessage, setMfaMessage] = useState("");

  useEffect(() => {
    if (!hasCloudSession()) return;
    void loadMfaStatus()
      .then((status) => {
        setMfaEnabled(status.mfa_enabled);
        setMfaPending(status.enrollment_pending);
        setMfaPolicyRequired(Boolean(status.policy_required));
      })
      .catch(() => undefined);
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    if (!hasCloudSession()) {
      setState("error");
      setMessage("Inicia sesion para cambiar tu password.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setState("error");
      setMessage("La nueva password y la confirmacion no coinciden.");
      return;
    }
    setState("saving");
    try {
      const session = await changePassword({ current_password: currentPassword, new_password: newPassword });
      storeSession(session);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setState("success");
      setMessage("Password actualizada. Las sesiones anteriores quedaron revocadas.");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo cambiar la password.");
    }
  }

  async function beginMfa() {
    setMfaState("saving");
    setMfaMessage("");
    try {
      const enrollment = await startMfaEnrollment();
      setMfaSecret(enrollment.secret);
      setMfaPending(true);
      setMfaState("success");
      setMfaMessage("Escanea el QR o copia el secreto en tu autenticador y confirma el codigo.");
    } catch (caught) {
      setMfaState("error");
      setMfaMessage(caught instanceof Error ? caught.message : "No se pudo iniciar MFA.");
    }
  }

  async function confirmMfa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMfaState("saving");
    setMfaMessage("");
    try {
      const session = await verifyMfaEnrollment({ code: mfaCode.trim() });
      storeSession(session);
      setMfaEnabled(true);
      setMfaPending(false);
      setMfaCode("");
      setMfaState("success");
      setMfaMessage("MFA activado. Las sesiones anteriores quedaron revocadas.");
    } catch (caught) {
      setMfaState("error");
      setMfaMessage(caught instanceof Error ? caught.message : "No se pudo verificar el codigo MFA.");
    }
  }

  async function removeMfa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMfaState("saving");
    setMfaMessage("");
    try {
      const session = await disableMfa({ current_password: mfaPassword, code: mfaCode.trim() || undefined });
      storeSession(session);
      setMfaEnabled(false);
      setMfaPending(false);
      setMfaSecret("");
      setMfaCode("");
      setMfaPassword("");
      setMfaState("success");
      setMfaMessage("MFA desactivado y sesiones anteriores revocadas.");
    } catch (caught) {
      setMfaState("error");
      setMfaMessage(caught instanceof Error ? caught.message : "No se pudo desactivar MFA.");
    }
  }

  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <ShieldCheck size={18} aria-hidden="true" />
        <span>Seguridad de cuenta</span>
      </div>
      <h2 className="mt-4 text-xl font-semibold text-ink">Cambio de password</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        Actualiza tu password y revoca refresh/access tokens anteriores para reducir riesgo de sesiones expuestas.
      </p>
      <form className="mt-5 grid gap-3" onSubmit={submit}>
        <label className="grid gap-2 text-sm font-semibold text-ink">
          Password actual
          <input
            autoComplete="current-password"
            className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
            onChange={(event) => setCurrentPassword(event.target.value)}
            type="password"
            value={currentPassword}
          />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-ink">
          Nueva password
          <input
            autoComplete="new-password"
            className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
            minLength={10}
            onChange={(event) => setNewPassword(event.target.value)}
            type="password"
            value={newPassword}
          />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-ink">
          Confirmar nueva password
          <input
            autoComplete="new-password"
            className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
            minLength={10}
            onChange={(event) => setConfirmPassword(event.target.value)}
            type="password"
            value={confirmPassword}
          />
        </label>
        <button className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={state === "saving"} type="submit">
          <KeyRound size={16} aria-hidden="true" />
          {state === "saving" ? "Actualizando..." : "Actualizar password"}
        </button>
      </form>
      {message ? <p className={`mt-4 rounded-md px-3 py-2 text-sm ${state === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{message}</p> : null}
      <div className="mt-8 border-t border-slate-200 pt-6">
        <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
          <QrCode size={18} aria-hidden="true" />
          <span>MFA TOTP</span>
        </div>
        <p className="mt-2 text-sm leading-6 text-slate-600">
          Protege la cuenta con un codigo temporal de autenticador. Al activar o desactivar MFA se revocan sesiones previas.
        </p>
        <p className="mt-3 rounded-md bg-slate-50 px-3 py-2 text-sm font-semibold text-ink">
          Estado: {mfaEnabled ? "Activo" : mfaPending ? "Pendiente de verificacion" : "Inactivo"}
        </p>
        {mfaPolicyRequired ? (
          <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-800">
            Politica del tenant: tu rol requiere MFA antes de iniciar sesion nuevamente.
          </p>
        ) : null}
        {!mfaEnabled ? (
          <div className="mt-4 grid gap-3">
            <button className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={mfaState === "saving"} onClick={beginMfa} type="button">
              <QrCode size={16} aria-hidden="true" />
              {mfaPending ? "Regenerar secreto MFA" : "Activar MFA"}
            </button>
            {mfaSecret ? (
              <div className="rounded-md border border-sky-200 bg-sky-50 p-3 text-xs leading-5 text-legal-900">
                <p className="font-semibold">Secreto MFA</p>
                <p className="break-all font-mono">{mfaSecret}</p>
              </div>
            ) : null}
            {mfaPending ? (
              <form className="grid gap-3" onSubmit={confirmMfa}>
                <label className="grid gap-2 text-sm font-semibold text-ink">
                  Codigo MFA
                  <input className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" inputMode="numeric" onChange={(event) => setMfaCode(event.target.value)} value={mfaCode} />
                </label>
                <button className="inline-flex h-11 items-center justify-center rounded-md border border-slate-200 px-4 text-sm font-semibold text-ink disabled:opacity-60" disabled={mfaState === "saving"} type="submit">
                  Confirmar MFA
                </button>
              </form>
            ) : null}
          </div>
        ) : (
          <form className="mt-4 grid gap-3" onSubmit={removeMfa}>
            <label className="grid gap-2 text-sm font-semibold text-ink">
              Password actual
              <input className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" onChange={(event) => setMfaPassword(event.target.value)} type="password" value={mfaPassword} />
            </label>
            <label className="grid gap-2 text-sm font-semibold text-ink">
              Codigo MFA
              <input className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" inputMode="numeric" onChange={(event) => setMfaCode(event.target.value)} value={mfaCode} />
            </label>
            <button className="inline-flex h-11 items-center justify-center rounded-md border border-slate-200 px-4 text-sm font-semibold text-ink disabled:opacity-60" disabled={mfaState === "saving"} type="submit">
              Desactivar MFA
            </button>
          </form>
        )}
        {mfaMessage ? <p className={`mt-4 rounded-md px-3 py-2 text-sm ${mfaState === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{mfaMessage}</p> : null}
      </div>
    </Card>
  );
}

function storeSession(session: { access_token: string; refresh_token: string }) {
  localStorage.setItem("lexflow.access_token", session.access_token);
  localStorage.setItem("lexflow.refresh_token", session.refresh_token);
}
