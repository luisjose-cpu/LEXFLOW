"use client";

import { Button, Card } from "@lexflow/ui";
import { ArrowLeft, UserCheck } from "lucide-react";
import Link from "next/link";
import React from "react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { acceptUserInvitation } from "@/lib/lexflow-api";

export function InvitationAccept() {
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const canSubmit = useMemo(() => token.trim() && password.length >= 10 && confirmPassword.length >= 10, [confirmPassword, password, token]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const queryToken = params.get("token");
    if (queryToken) setToken(queryToken);
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    if (password !== confirmPassword) {
      setState("error");
      setMessage("La password y la confirmacion no coinciden.");
      return;
    }
    if (!canSubmit || state === "loading") return;
    setState("loading");
    try {
      const session = await acceptUserInvitation({ invitation_token: token.trim(), password });
      localStorage.setItem("lexflow.access_token", session.access_token);
      localStorage.setItem("lexflow.refresh_token", session.refresh_token);
      setToken("");
      setPassword("");
      setConfirmPassword("");
      setState("success");
      setMessage("Invitacion aceptada. Ya tienes una sesion activa.");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo aceptar la invitacion.");
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-mist px-4 py-8">
      <Card className="w-full max-w-md">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-md bg-legal-900 text-white">
            <UserCheck size={20} aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold text-legal-900">Aceptar invitacion</p>
            <p className="text-xs text-slate-500">Define tu password y activa tu cuenta</p>
          </div>
        </div>
        <form className="mt-8 grid gap-4" onSubmit={submit}>
          <label className="grid gap-2 text-sm font-semibold text-ink">
            Token de invitacion
            <input className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" onChange={(event) => setToken(event.target.value)} placeholder="Token recibido" value={token} />
          </label>
          <label className="grid gap-2 text-sm font-semibold text-ink">
            Password
            <input autoComplete="new-password" className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" minLength={10} onChange={(event) => setPassword(event.target.value)} type="password" value={password} />
          </label>
          <label className="grid gap-2 text-sm font-semibold text-ink">
            Confirmar password
            <input autoComplete="new-password" className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" minLength={10} onChange={(event) => setConfirmPassword(event.target.value)} type="password" value={confirmPassword} />
          </label>
          {message ? <p className={`rounded-md px-3 py-2 text-sm ${state === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{message}</p> : null}
          <Button type="submit">{state === "loading" ? "Activando..." : "Aceptar invitacion"}</Button>
        </form>
        <Link className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-legal-900" href="/login">
          <ArrowLeft size={16} aria-hidden="true" />
          Volver al login
        </Link>
      </Card>
    </main>
  );
}
