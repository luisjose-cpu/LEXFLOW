"use client";

import { Button, Card } from "@lexflow/ui";
import { ArrowLeft, KeyRound, MailCheck, ShieldCheck } from "lucide-react";
import Link from "next/link";
import React from "react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { confirmPasswordReset, requestPasswordReset } from "@/lib/lexflow-api";

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

export function PasswordResetRequest() {
  const [tenantSlug, setTenantSlug] = useState("piloto");
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const [devToken, setDevToken] = useState("");
  const canSubmit = useMemo(() => tenantSlug.trim() && email.trim(), [email, tenantSlug]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit || status === "loading") return;

    setStatus("loading");
    setMessage("");
    setDevToken("");

    try {
      const response = await requestPasswordReset({
        email: email.trim(),
        tenant_slug: tenantSlug.trim()
      });
      setStatus("success");
      setMessage("Si la cuenta existe, enviaremos instrucciones de recuperacion.");
      setDevToken(response.reset_token ?? "");
    } catch (caught) {
      setStatus("error");
      setMessage(caught instanceof Error ? caught.message : "No pudimos preparar la recuperacion.");
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-mist px-4 py-8">
      <Card className="w-full max-w-md">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-md bg-legal-900 text-white">
            <MailCheck size={20} aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold text-legal-900">Recuperar acceso</p>
            <p className="text-xs text-slate-500">Token temporal con expiracion y auditoria</p>
          </div>
        </div>
        <form className="mt-8 grid gap-4" onSubmit={submit}>
          <Field autoComplete="organization" label="Estudio" onChange={setTenantSlug} placeholder="piloto" value={tenantSlug} />
          <Field autoComplete="email" label="Correo" onChange={setEmail} placeholder="socia@estudio.com" type="email" value={email} />
          {message ? (
            <div
              className={`rounded-md px-3 py-2 text-sm font-medium ${status === "error" ? "border border-red-200 bg-red-50 text-red-700" : "bg-legal-50 text-legal-900"}`}
              role={status === "error" ? "alert" : "status"}
            >
              {message}
            </div>
          ) : null}
          {devToken ? (
            <div className="rounded-md border border-sky-200 bg-sky-50 p-3 text-xs leading-5 text-legal-900">
              <p className="font-semibold">Token local/test</p>
              <p className="break-all font-mono">{devToken}</p>
            </div>
          ) : null}
          <Button type="submit">{status === "loading" ? "Preparando..." : "Enviar instrucciones"}</Button>
        </form>
        <div className="mt-5 flex items-center justify-between gap-3 text-sm">
          <Link className="inline-flex items-center gap-2 font-semibold text-legal-900" href="/login">
            <ArrowLeft size={16} aria-hidden="true" />
            Volver al login
          </Link>
          <Link className="font-semibold text-legal-900" href="/login/reset/confirm">
            Ya tengo un token
          </Link>
        </div>
      </Card>
    </main>
  );
}

export function PasswordResetConfirm() {
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const canSubmit = useMemo(() => resetToken.trim() && newPassword.length >= 10 && confirmPassword.length >= 10, [confirmPassword, newPassword, resetToken]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const queryToken = params.get("token");
    if (queryToken) setResetToken(queryToken);
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    if (newPassword !== confirmPassword) {
      setStatus("error");
      setMessage("La nueva password y la confirmacion no coinciden.");
      return;
    }
    if (!canSubmit || status === "loading") return;

    setStatus("loading");
    try {
      await confirmPasswordReset({
        reset_token: resetToken.trim(),
        new_password: newPassword
      });
      setResetToken("");
      setNewPassword("");
      setConfirmPassword("");
      setStatus("success");
      setMessage("Password actualizada. Ya puedes iniciar sesion.");
    } catch (caught) {
      setStatus("error");
      setMessage(caught instanceof Error ? caught.message : "El token no pudo validarse.");
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-mist px-4 py-8">
      <Card className="w-full max-w-md">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-md bg-legal-900 text-white">
            <KeyRound size={20} aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold text-legal-900">Definir nueva password</p>
            <p className="text-xs text-slate-500">El token se consume una sola vez</p>
          </div>
        </div>
        <form className="mt-8 grid gap-4" onSubmit={submit}>
          <Field label="Token de recuperacion" onChange={setResetToken} placeholder="Token recibido" value={resetToken} />
          <Field autoComplete="new-password" label="Nueva password" onChange={setNewPassword} placeholder="Minimo 10 caracteres" type="password" value={newPassword} />
          <Field autoComplete="new-password" label="Confirmar nueva password" onChange={setConfirmPassword} placeholder="Repite la password" type="password" value={confirmPassword} />
          {message ? (
            <div
              className={`rounded-md px-3 py-2 text-sm font-medium ${status === "error" ? "border border-red-200 bg-red-50 text-red-700" : "bg-legal-50 text-legal-900"}`}
              role={status === "error" ? "alert" : "status"}
            >
              {message}
            </div>
          ) : null}
          <Button type="submit">{status === "loading" ? "Actualizando..." : "Actualizar password"}</Button>
        </form>
        <div className="mt-6 flex items-start gap-2 rounded-lg border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-600">
          <ShieldCheck size={16} className="mt-0.5 text-legal-700" aria-hidden="true" />
          <p>Por seguridad, los tokens previos quedan revocados despues del cambio.</p>
        </div>
        <Link className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-legal-900" href="/login">
          <ArrowLeft size={16} aria-hidden="true" />
          Volver al login
        </Link>
      </Card>
    </main>
  );
}
