"use client";

import { Card } from "@lexflow/ui";
import { KeyRound, ShieldCheck } from "lucide-react";
import React from "react";
import { FormEvent, useState } from "react";
import { changePassword, hasCloudSession } from "@/lib/lexflow-api";

export function AccountSecurity() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [state, setState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [message, setMessage] = useState("");

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
      localStorage.setItem("lexflow.access_token", session.access_token);
      localStorage.setItem("lexflow.refresh_token", session.refresh_token);
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
    </Card>
  );
}
