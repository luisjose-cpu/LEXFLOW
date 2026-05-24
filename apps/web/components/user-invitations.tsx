"use client";

import { Badge, Button, Card } from "@lexflow/ui";
import { MailPlus, UsersRound } from "lucide-react";
import React from "react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { cancelUserInvitation, createUserInvitation, EmailDelivery, hasCloudSession, loadEmailDeliveries, loadUserInvitations, resendUserInvitation, UserInvitation } from "@/lib/lexflow-api";

const roles = [
  { value: "tenant_admin", label: "Admin tenant" },
  { value: "partner", label: "Socio" },
  { value: "lawyer", label: "Abogado" },
  { value: "assistant", label: "Asistente" },
  { value: "client_user", label: "Cliente portal" }
];

export function UserInvitations() {
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [role, setRole] = useState("lawyer");
  const [items, setItems] = useState<UserInvitation[]>([]);
  const [deliveries, setDeliveries] = useState<EmailDelivery[]>([]);
  const [state, setState] = useState<"idle" | "loading" | "saving" | "error" | "success">("idle");
  const [message, setMessage] = useState("");
  const [devToken, setDevToken] = useState("");
  const canSubmit = useMemo(() => email.trim() && fullName.trim(), [email, fullName]);

  useEffect(() => {
    if (!hasCloudSession()) return;
    setState("loading");
    void Promise.all([loadUserInvitations(), loadEmailDeliveries()])
      .then(([nextInvitations, nextDeliveries]) => {
        setItems(nextInvitations);
        setDeliveries(nextDeliveries);
        setState("idle");
      })
      .catch(() => setState("idle"));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit || state === "saving") return;
    if (!hasCloudSession()) {
      setState("error");
      setMessage("Inicia sesion para invitar usuarios.");
      return;
    }
    setState("saving");
    setMessage("");
    setDevToken("");
    try {
      const created = await createUserInvitation({
        email: email.trim(),
        full_name: fullName.trim(),
        role
      });
      setItems((current) => [created, ...current]);
      setEmail("");
      setFullName("");
      setState("success");
      setMessage("Invitacion preparada. El usuario definira su propia password.");
      setDevToken(created.invitation_token ?? "");
      await refreshDeliveries();
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo crear la invitacion.");
    }
  }

  async function resend(invitationId: string) {
    setState("saving");
    setMessage("");
    setDevToken("");
    try {
      const updated = await resendUserInvitation(invitationId);
      setItems((current) => current.map((item) => (item.id === invitationId ? updated : item)));
      setState("success");
      setMessage("Invitacion reenviada con token rotado.");
      setDevToken(updated.invitation_token ?? "");
      await refreshDeliveries();
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo reenviar la invitacion.");
    }
  }

  async function refreshDeliveries() {
    try {
      setDeliveries(await loadEmailDeliveries());
    } catch {
      // Delivery telemetry is helpful, but invitation actions should not fail because of a read-side refresh.
    }
  }

  async function cancel(invitationId: string) {
    setState("saving");
    setMessage("");
    setDevToken("");
    try {
      const updated = await cancelUserInvitation(invitationId);
      setItems((current) => current.map((item) => (item.id === invitationId ? updated : item)));
      setState("success");
      setMessage("Invitacion cancelada. El token ya no podra usarse.");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo cancelar la invitacion.");
    }
  }

  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <UsersRound size={18} aria-hidden="true" />
        <span>Equipo</span>
      </div>
      <h2 className="mt-4 text-xl font-semibold text-ink">Invitaciones de usuarios</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        Invita abogados, asistentes o usuarios cliente con token temporal. Nadie comparte passwords y todo queda auditado.
      </p>
      <form className="mt-5 grid gap-3" onSubmit={submit}>
        <label className="grid gap-2 text-sm font-semibold text-ink">
          Correo
          <input
            autoComplete="email"
            className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
            onChange={(event) => setEmail(event.target.value)}
            placeholder="abogada@estudio.com"
            type="email"
            value={email}
          />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-ink">
          Nombre
          <input
            autoComplete="name"
            className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
            onChange={(event) => setFullName(event.target.value)}
            placeholder="Nombre completo"
            value={fullName}
          />
        </label>
        <label className="grid gap-2 text-sm font-semibold text-ink">
          Rol
          <select className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" onChange={(event) => setRole(event.target.value)} value={role}>
            {roles.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <Button type="submit">{state === "saving" ? "Invitando..." : "Crear invitacion"}</Button>
      </form>
      {message ? <p className={`mt-4 rounded-md px-3 py-2 text-sm ${state === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{message}</p> : null}
      {devToken ? (
        <div className="mt-4 rounded-md border border-sky-200 bg-sky-50 p-3 text-xs leading-5 text-legal-900">
          <p className="font-semibold">Token local/test</p>
          <p className="break-all font-mono">{devToken}</p>
        </div>
      ) : null}
      <div className="mt-6 grid gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-ink">
          <MailPlus size={16} aria-hidden="true" />
          Invitaciones recientes
        </div>
        {state === "loading" ? <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">Cargando invitaciones...</p> : null}
        {items.length ? (
          <div className="grid gap-2">
            {items.slice(0, 5).map((item) => (
              <div className="rounded-md border border-slate-200 p-3" key={item.id}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-ink">{item.full_name}</p>
                  <Badge>{item.status}</Badge>
                </div>
                <p className="mt-1 text-xs text-slate-500">{item.email}</p>
                <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-legal-700">Rol: {labelForRole(item.role)}</p>
                  {item.status === "pending" ? (
                    <div className="flex flex-wrap gap-2">
                      <button className="h-8 rounded-md border border-slate-200 px-3 text-xs font-semibold text-ink disabled:opacity-60" disabled={state === "saving"} onClick={() => resend(item.id)} type="button">
                        Reenviar
                      </button>
                      <button className="h-8 rounded-md border border-rose-200 px-3 text-xs font-semibold text-rose-700 disabled:opacity-60" disabled={state === "saving"} onClick={() => cancel(item.id)} type="button">
                        Cancelar
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        ) : state !== "loading" ? (
          <p className="rounded-md border border-dashed border-slate-200 px-3 py-4 text-sm text-slate-500">Aun no hay invitaciones registradas.</p>
        ) : null}
      </div>
      <div className="mt-6 grid gap-3 border-t border-slate-200 pt-5">
        <p className="text-sm font-semibold text-ink">Entregas email</p>
        {deliveries.length ? (
          <div className="grid gap-2">
            {deliveries.slice(0, 4).map((item) => (
              <div className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-600" key={item.id}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-semibold text-ink">{labelForTemplate(item.template)}</span>
                  <Badge>{item.status}</Badge>
                </div>
                <p className="mt-1">
                  {item.recipient_hint} · {item.provider}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="rounded-md border border-dashed border-slate-200 px-3 py-3 text-sm text-slate-500">Sin entregas registradas todavia.</p>
        )}
      </div>
    </Card>
  );
}

function labelForRole(value: string) {
  return roles.find((role) => role.value === value)?.label ?? value;
}

function labelForTemplate(value: string) {
  return value === "user_invitation" ? "Invitacion" : value === "password_reset" ? "Recuperacion" : value;
}
