"use client";

import { Badge, Card, EmptyState, MetricCard, PageHeader } from "@lexflow/ui";
import {
  Activity,
  AlertTriangle,
  Building2,
  CheckCircle2,
  CreditCard,
  EyeOff,
  Flag,
  Gauge,
  Headphones,
  LifeBuoy,
  LockKeyhole,
  LogOut,
  PackageCheck,
  ShieldCheck,
  Sparkles,
  ToggleRight,
  Users
} from "lucide-react";
import Link from "next/link";
import React, { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  OwnerTenant,
  findOwnerTenant,
  ownerAuditLogs,
  ownerDashboardMetrics,
  ownerDemos,
  ownerFeatureFlags,
  ownerInterventions,
  ownerPlans,
  ownerSystemChecks,
  ownerSystemIncidents,
  ownerTenants,
  ownerTickets
} from "@/lib/owner-demo";
import {
  API_URL,
  changeOwnerTenantPlan,
  closeOwnerIntervention,
  createOwnerPlan,
  createOwnerDemo,
  createOwnerIntervention,
  createOwnerSystemIncident,
  createOwnerTenant,
  createOwnerTicket,
  hasOwnerSession,
  loadOwnerAuditLogs,
  loadOwnerDashboard,
  loadOwnerDemos,
  loadOwnerFeatures,
  loadOwnerInterventions,
  loadOwnerLimits,
  loadOwnerMfaStatus,
  loadOwnerPlans,
  loadOwnerSystemChecks,
  loadOwnerSystemIncidents,
  loadOwnerTenantDetail,
  loadOwnerTenantUsage,
  loadOwnerTenants,
  loadOwnerTickets,
  logoutOwner,
  reactivateOwnerTenant,
  regenerateOwnerMfaRecoveryCodes,
  resolveOwnerSystemIncident,
  resolveOwnerTicket,
  resetOwnerDemo,
  startOwnerMfaEnrollment,
  suspendOwnerTenant,
  verifyOwnerMfaEnrollment,
  updateOwnerLimits,
  updateOwnerPlan,
  updateOwnerFeatures,
  disableOwnerMfa
} from "@/lib/owner-api";

const ownerNav = [
  { href: "/owner", label: "Dashboard" },
  { href: "/owner/tenants", label: "Tenants" },
  { href: "/owner/plans", label: "Planes" },
  { href: "/owner/support", label: "Soporte" },
  { href: "/owner/system", label: "Sistema" },
  { href: "/owner/demos", label: "Demos" },
  { href: "/owner/interventions", label: "Intervenciones" },
  { href: "/owner/audit", label: "Auditoria" }
];

type OwnerDataSource = "demo" | "loading" | "live" | "fallback";
type UsageTuple = readonly [string, number, number];

export function OwnerLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaCode, setMfaCode] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "error" | "success">("idle");
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("loading");
    setMessage("");
    try {
      const response = await fetch(`${API_URL}/api/v1/owner/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, ...(mfaCode.trim() ? { mfa_code: mfaCode.trim() } : {}) })
      });
      if (!response.ok) throw new Error("Credenciales owner invalidas.");
      const payload = await response.json() as { access_token: string; refresh_token: string; owner: { email: string; role: string } };
      localStorage.setItem("lexflow.owner_access_token", payload.access_token);
      localStorage.setItem("lexflow.owner_refresh_token", payload.refresh_token);
      localStorage.setItem("lexflow.owner_user", JSON.stringify(payload.owner));
      setState("success");
      setMessage(`Owner conectado: ${payload.owner.email} (${payload.owner.role})`);
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo iniciar sesion owner.");
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-mist px-4 py-10 text-ink">
      <section className="w-full max-w-xl rounded-lg border border-white/80 bg-white p-6 shadow-soft">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-12 w-12 items-center justify-center rounded-md bg-legal-900 text-white">
            <ShieldCheck size={22} aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold text-legal-700">LEXFLOW Owner Console</p>
            <h1 className="text-2xl font-semibold text-ink">Acceso propietario</h1>
          </div>
        </div>
        <form className="mt-6 grid gap-4" onSubmit={submit}>
          <label className="grid gap-2 text-sm font-semibold text-ink">
            Correo owner
            <input className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" onChange={(event) => setEmail(event.target.value)} placeholder="owner@lexflow.com" type="email" value={email} />
          </label>
          <label className="grid gap-2 text-sm font-semibold text-ink">
            Password
            <input className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" onChange={(event) => setPassword(event.target.value)} placeholder="Password owner" type="password" value={password} />
          </label>
          <label className="grid gap-2 text-sm font-semibold text-ink">
            Codigo MFA
            <input className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" inputMode="numeric" onChange={(event) => setMfaCode(event.target.value)} placeholder="Opcional si MFA esta activo" value={mfaCode} />
          </label>
          <button className="inline-flex h-11 items-center justify-center rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={state === "loading"} type="submit">
            {state === "loading" ? "Validando..." : "Entrar al Owner Console"}
          </button>
        </form>
        {message ? <p className={`mt-4 rounded-md px-3 py-2 text-sm ${state === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{message}</p> : null}
        <p className="mt-5 text-sm leading-6 text-slate-500">Este acceso administra SaaS metadata. Los datos sensibles de tenants requieren intervencion temporal auditada.</p>
      </section>
    </main>
  );
}

export function OwnerConsoleShell({ children }: { children: ReactNode }) {
  const [sessionActive, setSessionActive] = useState(false);
  const [logoutMessage, setLogoutMessage] = useState("");

  useEffect(() => {
    setSessionActive(hasOwnerSession());
  }, []);

  async function logout() {
    setLogoutMessage("");
    try {
      await logoutOwner();
      setLogoutMessage("Sesion owner cerrada.");
    } catch {
      setLogoutMessage("Sesion local owner cerrada. Revisa conectividad para logout remoto.");
    } finally {
      setSessionActive(false);
    }
  }

  return (
    <main className="min-h-screen bg-mist text-ink">
      <div className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
          <Link className="flex items-center gap-3" href="/owner">
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-legal-900 text-white">
              <ShieldCheck size={20} aria-hidden="true" />
            </span>
            <span>
              <span className="block text-sm font-semibold text-legal-700">LEXFLOW Owner Console</span>
              <span className="block text-xs text-slate-500">Separado del tenant operativo</span>
            </span>
          </Link>
          <nav className="flex gap-2 overflow-x-auto pb-1">
            {ownerNav.map((item) => (
              <Link className="whitespace-nowrap rounded-md px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-legal-50 hover:text-legal-800" href={item.href} key={item.href}>
                {item.label}
              </Link>
            ))}
            {sessionActive ? (
              <button className="inline-flex whitespace-nowrap rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-legal-50 hover:text-legal-800" onClick={() => void logout()} type="button">
                <LogOut className="mr-2" size={16} aria-hidden="true" />
                Cerrar sesion
              </button>
            ) : (
              <Link className="whitespace-nowrap rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-legal-50 hover:text-legal-800" href="/owner/login">
                Owner login
              </Link>
            )}
          </nav>
        </div>
        {logoutMessage ? <div className="mx-auto max-w-7xl px-4 pb-4 text-sm font-medium text-legal-900 sm:px-6">{logoutMessage}</div> : null}
      </div>
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:py-8">{children}</div>
    </main>
  );
}

export function OwnerSecurityPanel() {
  const [loaded, setLoaded] = useState(false);
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [mfaPending, setMfaPending] = useState(false);
  const [recoveryCodesRemaining, setRecoveryCodesRemaining] = useState(0);
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [secret, setSecret] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "saving" | "error" | "success">("idle");
  const [message, setMessage] = useState("");

  async function loadStatus() {
    if (!hasOwnerSession()) {
      setState("error");
      setMessage("Inicia sesion owner para gestionar MFA.");
      return;
    }
    setState("loading");
    setMessage("");
    try {
      const status = await loadOwnerMfaStatus();
      setLoaded(true);
      setMfaEnabled(status.mfa_enabled);
      setMfaPending(status.enrollment_pending);
      setRecoveryCodesRemaining(status.recovery_codes_remaining);
      setState("idle");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo cargar MFA owner.");
    }
  }

  async function beginEnrollment() {
    setState("saving");
    setMessage("");
    try {
      const enrollment = await startOwnerMfaEnrollment();
      setSecret(enrollment.secret);
      setMfaPending(true);
      setMfaEnabled(false);
      setLoaded(true);
      setState("success");
      setMessage("Secreto owner generado. Confirmalo con tu autenticador.");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo iniciar MFA owner.");
    }
  }

  async function confirmEnrollment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("saving");
    setMessage("");
    try {
      const session = await verifyOwnerMfaEnrollment({ code: code.trim() });
      storeOwnerSession(session);
      setMfaEnabled(true);
      setMfaPending(false);
      setRecoveryCodes(session.recovery_codes ?? []);
      setRecoveryCodesRemaining(session.recovery_codes?.length ?? 0);
      setCode("");
      setState("success");
      setMessage("MFA owner activado. Las sesiones anteriores quedaron revocadas.");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo verificar MFA owner.");
    }
  }

  async function removeMfa(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState("saving");
    setMessage("");
    try {
      const session = await disableOwnerMfa({ current_password: password, code: code.trim() || undefined });
      storeOwnerSession(session);
      setMfaEnabled(false);
      setMfaPending(false);
      setRecoveryCodes([]);
      setRecoveryCodesRemaining(0);
      setSecret("");
      setPassword("");
      setCode("");
      setState("success");
      setMessage("MFA owner desactivado y sesiones anteriores revocadas.");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudo desactivar MFA owner.");
    }
  }

  async function regenerateCodes() {
    setState("saving");
    setMessage("");
    try {
      const result = await regenerateOwnerMfaRecoveryCodes({ current_password: password, code: code.trim() });
      setRecoveryCodes(result.recovery_codes);
      setRecoveryCodesRemaining(result.recovery_codes.length);
      setPassword("");
      setCode("");
      setState("success");
      setMessage("Codigos de recuperacion regenerados. Guardalos en un gestor seguro.");
    } catch (caught) {
      setState("error");
      setMessage(caught instanceof Error ? caught.message : "No se pudieron regenerar los codigos.");
    }
  }

  return (
    <Card>
      <SectionTitle icon={<LockKeyhole size={18} />} title="Seguridad owner" />
      <p className="mt-3 text-sm leading-6 text-slate-600">
        MFA TOTP protege el panel propietario. Los cambios revocan sesiones y quedan en owner audit logs.
      </p>
      <div className="mt-4 grid gap-3">
        <button className="inline-flex h-10 items-center justify-center rounded-md border border-slate-200 px-4 text-sm font-semibold text-ink disabled:opacity-60" disabled={state === "loading"} onClick={loadStatus} type="button">
          {state === "loading" ? "Consultando..." : "Consultar MFA owner"}
        </button>
        {loaded ? (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-sm font-semibold text-ink">
            Estado: {mfaEnabled ? "Activo" : mfaPending ? "Pendiente de verificacion" : "Inactivo"}
          </p>
        ) : null}
        {mfaEnabled ? (
          <p className="rounded-md bg-slate-50 px-3 py-2 text-sm font-semibold text-ink">
            Codigos de recuperacion disponibles: {recoveryCodesRemaining}
          </p>
        ) : null}
        {recoveryCodes.length ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
            <p className="font-semibold">Codigos de recuperacion owner</p>
            <div className="mt-2 grid gap-1 font-mono text-xs sm:grid-cols-2">
              {recoveryCodes.map((item) => <span key={item}>{item}</span>)}
            </div>
          </div>
        ) : null}
        {!mfaEnabled ? (
          <>
            <button className="inline-flex h-10 items-center justify-center rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={state === "saving"} onClick={beginEnrollment} type="button">
              {mfaPending ? "Regenerar MFA owner" : "Activar MFA owner"}
            </button>
            {secret ? (
              <div className="rounded-md border border-sky-200 bg-sky-50 p-3 text-xs leading-5 text-legal-900">
                <p className="font-semibold">Secreto MFA owner</p>
                <p className="break-all font-mono">{secret}</p>
              </div>
            ) : null}
            {mfaPending ? (
              <form className="grid gap-3" onSubmit={confirmEnrollment}>
                <label className="grid gap-2 text-sm font-semibold text-ink">
                  Codigo MFA
                  <input className="h-10 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" inputMode="numeric" onChange={(event) => setCode(event.target.value)} value={code} />
                </label>
                <button className="inline-flex h-10 items-center justify-center rounded-md border border-slate-200 px-4 text-sm font-semibold text-ink disabled:opacity-60" disabled={state === "saving"} type="submit">
                  Confirmar MFA owner
                </button>
              </form>
            ) : null}
          </>
        ) : (
          <div className="grid gap-3">
            <label className="grid gap-2 text-sm font-semibold text-ink">
              Password owner
              <input className="h-10 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" onChange={(event) => setPassword(event.target.value)} type="password" value={password} />
            </label>
            <label className="grid gap-2 text-sm font-semibold text-ink">
              Codigo MFA o recuperacion
              <input className="h-10 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500" onChange={(event) => setCode(event.target.value)} value={code} />
            </label>
            <div className="grid gap-2 sm:grid-cols-2">
              <button className="inline-flex h-10 items-center justify-center rounded-md border border-slate-200 px-4 text-sm font-semibold text-ink disabled:opacity-60" disabled={state === "saving"} onClick={regenerateCodes} type="button">
                Regenerar codigos
              </button>
              <form onSubmit={removeMfa}>
                <button className="inline-flex h-10 w-full items-center justify-center rounded-md border border-slate-200 px-4 text-sm font-semibold text-ink disabled:opacity-60" disabled={state === "saving"} type="submit">
                  Desactivar MFA owner
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
      {message ? <p className={`mt-4 rounded-md px-3 py-2 text-sm ${state === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{message}</p> : null}
    </Card>
  );
}

export function OwnerDashboard() {
  const [metrics, setMetrics] = useState(ownerDashboardMetrics());
  const [tenants, setTenants] = useState(ownerTenants);
  const [checks, setChecks] = useState(ownerSystemChecks);
  const [source, setSource] = useState<OwnerDataSource>("demo");

  useEffect(() => {
    if (!hasOwnerSession()) {
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    Promise.all([loadOwnerDashboard(), loadOwnerTenants(), loadOwnerSystemChecks()])
      .then(([nextMetrics, nextTenants, nextChecks]) => {
        if (!active) return;
        setMetrics(nextMetrics.length ? nextMetrics : ownerDashboardMetrics());
        setTenants(nextTenants.length ? nextTenants : ownerTenants);
        setChecks(nextChecks.length ? nextChecks : ownerSystemChecks);
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

  return (
    <OwnerConsoleShell>
      <PageHeader
        eyebrow="Modulo propietario"
        title="Command Center SaaS"
        description="Administra tenants, planes, cobranzas, soporte, consumo, feature flags y salud del sistema sin abrir datos sensibles de estudios juridicos."
      />
      <OwnerDataSourceNotice source={source} />
      <SecurityBoundaryNotice />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <SectionTitle icon={<Building2 size={18} />} title="Tenants en observacion" />
          <div className="mt-4 grid gap-3">
            {tenants.map((tenant) => <TenantRow key={tenant.id} tenant={tenant} />)}
          </div>
        </Card>
        <Card>
          <SectionTitle icon={<Activity size={18} />} title="Salud del sistema" />
          <div className="mt-4 grid gap-3">
            {checks.slice(0, 5).map((check) => (
              <StatusLine key={check.service} label={check.service} value={check.detail} status={check.status} />
            ))}
          </div>
        </Card>
      </div>
      <OwnerSecurityPanel />
      <div className="grid gap-5 lg:grid-cols-3">
        <OwnerQuickCard icon={<CreditCard size={18} />} title="Billing" value="$457 MRR" detail="ARR $5484, churn mock 2.4%" href="/owner/plans" />
        <OwnerQuickCard icon={<Headphones size={18} />} title="Soporte" value="3 tickets" detail="1 critico, 2 dentro de SLA" href="/owner/support" />
        <OwnerQuickCard icon={<Sparkles size={18} />} title="Consumo IA" value="900k tokens" detail="Limites y alertas preparados" href="/owner/tenants/tenant-nova/usage" />
      </div>
    </OwnerConsoleShell>
  );
}

export function TenantsList() {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState<OwnerDataSource>("demo");
  const [loadedTenants, setLoadedTenants] = useState(ownerTenants);
  const [tenantForm, setTenantForm] = useState({ name: "", slug: "", plan: "START", adminEmail: "", adminName: "", adminPassword: "", seats: "5", modules: "expediente360,dashboard,mobile_pwa" });
  const [createState, setCreateState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [createMessage, setCreateMessage] = useState("");
  const tenants = useMemo(() => loadedTenants.filter((tenant) => `${tenant.name} ${tenant.slug} ${tenant.plan}`.toLowerCase().includes(query.toLowerCase())), [loadedTenants, query]);

  useEffect(() => {
    if (!hasOwnerSession()) {
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    loadOwnerTenants()
      .then((payload) => {
        if (!active) return;
        setLoadedTenants(payload.length ? payload : ownerTenants);
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

  async function submitTenant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!hasOwnerSession()) {
      setCreateState("error");
      setCreateMessage("Inicia sesion owner para crear tenants auditados.");
      return;
    }
    setCreateState("saving");
    setCreateMessage("");
    try {
      const tenant = await createOwnerTenant({
        name: tenantForm.name,
        slug: tenantForm.slug,
        plan: tenantForm.plan,
        trial: true,
        admin_email: tenantForm.adminEmail || undefined,
        admin_name: tenantForm.adminName || undefined,
        admin_password: tenantForm.adminPassword || undefined,
        seats: Number(tenantForm.seats),
        modules: splitCsv(tenantForm.modules),
        send_access_email: true
      });
      setLoadedTenants((current) => [tenant, ...current.filter((item) => item.id !== tenant.id)]);
      setTenantForm({ name: "", slug: "", plan: "START", adminEmail: "", adminName: "", adminPassword: "", seats: "5", modules: "expediente360,dashboard,mobile_pwa" });
      setSource("live");
      setCreateState("success");
      setCreateMessage(`Tenant creado: ${tenant.name}. Admin: ${tenant.onboarding?.adminEmail ?? "pendiente"}.`);
    } catch (caught) {
      setCreateState("error");
      setCreateMessage(caught instanceof Error ? caught.message : "No se pudo crear el tenant.");
    }
  }

  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Tenants" title="Gestion de estudios" description="Crea, suspende, reactiva, cambia planes y controla limites por tenant desde una consola separada." />
      <OwnerDataSourceNotice source={source} />
      <form className="grid gap-3 rounded-lg border border-white/80 bg-white p-4 shadow-soft lg:grid-cols-4" onSubmit={submitTenant}>
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setTenantForm((current) => ({ ...current, name: event.target.value }))}
          placeholder="Nombre del estudio"
          required
          value={tenantForm.name}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setTenantForm((current) => ({ ...current, slug: event.target.value }))}
          placeholder="slug-del-tenant"
          required
          value={tenantForm.slug}
        />
        <select
          className="h-11 rounded-md border border-slate-200 px-3 text-sm font-semibold outline-none focus:border-legal-500"
          onChange={(event) => setTenantForm((current) => ({ ...current, plan: event.target.value }))}
          value={tenantForm.plan}
        >
          {["START", "PRO", "AI", "ENTERPRISE"].map((plan) => <option key={plan} value={plan}>{plan}</option>)}
        </select>
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setTenantForm((current) => ({ ...current, seats: event.target.value }))}
          placeholder="seats"
          type="number"
          value={tenantForm.seats}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setTenantForm((current) => ({ ...current, adminEmail: event.target.value }))}
          placeholder="admin@estudio.com"
          type="email"
          value={tenantForm.adminEmail}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setTenantForm((current) => ({ ...current, adminName: event.target.value }))}
          placeholder="Nombre admin"
          value={tenantForm.adminName}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setTenantForm((current) => ({ ...current, adminPassword: event.target.value }))}
          placeholder="Password temporal"
          type="password"
          value={tenantForm.adminPassword}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500 lg:col-span-3"
          onChange={(event) => setTenantForm((current) => ({ ...current, modules: event.target.value }))}
          placeholder="modulos separados por coma"
          value={tenantForm.modules}
        />
        <button className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={createState === "saving"} type="submit">
          <Users size={16} aria-hidden="true" />
          {createState === "saving" ? "Creando..." : "Crear tenant"}
        </button>
      </form>
      {createMessage ? <p className={`rounded-md px-3 py-2 text-sm ${createState === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{createMessage}</p> : null}
      <div className="grid gap-3">
        <input
          className="h-11 rounded-md border border-slate-200 bg-white px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar tenant, plan, slug..."
          value={query}
        />
      </div>
      <div className="grid gap-4">
        {tenants.map((tenant) => <TenantRow key={tenant.id} tenant={tenant} expanded />)}
        {!tenants.length ? <EmptyState title="Sin tenants" description="No hay estudios juridicos con ese filtro." /> : null}
      </div>
    </OwnerConsoleShell>
  );
}

export function TenantDetail({ tenantId }: { tenantId: string }) {
  const [tenant, setTenant] = useState(findOwnerTenant(tenantId));
  const [source, setSource] = useState<OwnerDataSource>("demo");
  const [actionState, setActionState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [actionMessage, setActionMessage] = useState("");
  const [limits, setLimits] = useState<Record<string, number>>({ users: tenant.users || 5, cases: tenant.cases || 100, documents: tenant.documents || 500, storage_mb: tenant.storageGb * 1024 || 10240, ai_tokens: tenant.aiTokens || 0, whatsapp_messages: tenant.whatsappMessages || 0, sinoe_syncs: tenant.sinoeSyncs || 0 });
  const [limitState, setLimitState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [limitMessage, setLimitMessage] = useState("");

  useEffect(() => {
    if (!hasOwnerSession()) {
      setTenant(findOwnerTenant(tenantId));
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    Promise.all([loadOwnerTenantDetail(tenantId), loadOwnerLimits(tenantId)])
      .then(([payload, nextLimits]) => {
        if (!active) return;
        setTenant(payload);
        setLimits(Object.fromEntries(nextLimits.map((item) => [item.limit_key, item.limit_value])));
        setSource("live");
      })
      .catch(() => {
        if (!active) return;
        setTenant(findOwnerTenant(tenantId));
        setSource("fallback");
      });
    return () => {
      active = false;
    };
  }, [tenantId]);

  async function runTenantAction(action: "suspend" | "reactivate" | "plan") {
    if (!hasOwnerSession()) {
      setActionState("error");
      setActionMessage("Inicia sesion owner para ejecutar acciones auditadas.");
      return;
    }
    setActionState("saving");
    setActionMessage("");
    try {
      const nextTenant = action === "suspend"
        ? await suspendOwnerTenant(tenant.id)
        : action === "reactivate"
          ? await reactivateOwnerTenant(tenant.id)
          : await changeOwnerTenantPlan(tenant.id, tenant.plan === "AI" ? "PRO" : "AI");
      setTenant(nextTenant);
      setSource("live");
      setActionState("success");
      setActionMessage(action === "plan" ? `Plan actualizado a ${nextTenant.plan}.` : `Tenant ${nextTenant.status}.`);
    } catch (caught) {
      setActionState("error");
      setActionMessage(caught instanceof Error ? caught.message : "No se pudo ejecutar la accion owner.");
    }
  }

  async function saveLimits() {
    if (!hasOwnerSession()) {
      setLimitState("error");
      setLimitMessage("Inicia sesion owner para guardar limites auditados.");
      return;
    }
    setLimitState("saving");
    setLimitMessage("");
    try {
      const saved = await updateOwnerLimits(tenant.id, limits);
      setLimits(Object.fromEntries(saved.map((item) => [item.limit_key, item.limit_value])));
      setSource("live");
      setLimitState("success");
      setLimitMessage("Limites guardados y auditados.");
    } catch (caught) {
      setLimitState("error");
      setLimitMessage(caught instanceof Error ? caught.message : "No se pudieron guardar los limites.");
    }
  }

  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Tenant" title={tenant.name} description="Vista administrativa con metadata operativa, billing, limites, soporte y flags. Los datos sensibles del estudio permanecen ocultos." />
      <OwnerDataSourceNotice source={source} />
      <SecurityBoundaryNotice />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Health score" value={`${tenant.health}`} trend={tenant.health > 80 ? "Adopcion saludable" : "Requiere seguimiento"} />
        <MetricCard label="Usuarios" value={String(tenant.users)} trend={`${tenant.cases} expedientes`} />
        <MetricCard label="Storage" value={`${tenant.storageGb} GB`} trend={`${tenant.documents} documentos`} />
        <MetricCard label="Tickets" value={String(tenant.openTickets)} trend="Soporte activo" />
      </div>
      <div className="grid gap-5 xl:grid-cols-[1fr_0.9fr]">
        <Card>
          <SectionTitle icon={<Gauge size={18} />} title="Estado comercial" />
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <InfoItem label="Plan" value={tenant.plan} />
            <InfoItem label="Estado" value={tenant.status} />
            <InfoItem label="MRR" value={`$${tenant.mrr}`} />
            <InfoItem label="Ultima actividad" value={tenant.lastSeen} />
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <button className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-legal-50 disabled:opacity-60" disabled={actionState === "saving"} onClick={() => void runTenantAction("suspend")} type="button">
              Suspender
            </button>
            <button className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-legal-50 disabled:opacity-60" disabled={actionState === "saving"} onClick={() => void runTenantAction("reactivate")} type="button">
              Reactivar
            </button>
            <button className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-legal-50 disabled:opacity-60" disabled={actionState === "saving"} onClick={() => void runTenantAction("plan")} type="button">
              Cambiar plan
            </button>
          </div>
          {actionMessage ? <p className={`mt-3 rounded-md px-3 py-2 text-sm ${actionState === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{actionMessage}</p> : null}
        </Card>
        <Card>
          <SectionTitle icon={<EyeOff size={18} />} title="Datos sensibles" />
          <p className="mt-4 text-sm leading-6 text-slate-600">
            El owner no accede a documentos, estrategia, mensajes ni contenido de expedientes sin intervencion autorizada, temporal y auditada.
          </p>
          <Link className="mt-4 inline-flex rounded-md bg-legal-900 px-4 py-2 text-sm font-semibold text-white" href="/owner/interventions">
            Solicitar intervencion
          </Link>
        </Card>
      </div>
      <Card>
        <SectionTitle icon={<Gauge size={18} />} title="Limites comerciales" />
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {["users", "cases", "documents", "storage_mb", "ai_tokens", "whatsapp_messages", "sinoe_syncs"].map((key) => (
            <label className="grid gap-2 text-xs font-semibold uppercase tracking-normal text-slate-500" key={key}>
              {key}
              <input
                className="h-11 rounded-md border border-slate-200 px-3 text-sm font-semibold text-ink outline-none focus:border-legal-500"
                min="0"
                onChange={(event) => setLimits((current) => ({ ...current, [key]: Number(event.target.value) }))}
                type="number"
                value={limits[key] ?? 0}
              />
            </label>
          ))}
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button className="inline-flex h-10 items-center justify-center rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={limitState === "saving"} onClick={() => void saveLimits()} type="button">
            {limitState === "saving" ? "Guardando..." : "Guardar limites"}
          </button>
          {limitMessage ? <span className={`rounded-md px-3 py-2 text-sm ${limitState === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{limitMessage}</span> : null}
        </div>
      </Card>
    </OwnerConsoleShell>
  );
}

export function TenantUsage({ tenantId }: { tenantId: string }) {
  const tenant = findOwnerTenant(tenantId);
  const fallbackUsage = [
    ["Usuarios", tenant.users, 40],
    ["Expedientes", tenant.cases, 1500],
    ["Documentos", tenant.documents, 5000],
    ["Storage GB", tenant.storageGb, 100],
    ["IA tokens", Math.round(tenant.aiTokens / 1000), 1000],
    ["WhatsApp", tenant.whatsappMessages, 5000],
    ["SINOE syncs", tenant.sinoeSyncs, 1000]
  ] as const;
  const [usage, setUsage] = useState<readonly UsageTuple[]>(fallbackUsage);
  const [source, setSource] = useState<OwnerDataSource>("demo");

  useEffect(() => {
    if (!hasOwnerSession()) {
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    loadOwnerTenantUsage(tenantId)
      .then((payload) => {
        if (!active) return;
        setUsage(payload);
        setSource("live");
      })
      .catch(() => {
        if (!active) return;
        setSource("fallback");
      });
    return () => {
      active = false;
    };
  }, [tenantId]);

  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Uso" title={`Consumo de ${tenant.name}`} description="Usuarios, expedientes, documentos, IA, OCR, WhatsApp, automatizaciones y SINOE syncs medidos por tenant." />
      <OwnerDataSourceNotice source={source} />
      <Card>
        <div className="grid gap-4">
          {usage.map(([label, value, max]) => <UsageBar key={label} label={label} value={value} max={max} />)}
        </div>
      </Card>
    </OwnerConsoleShell>
  );
}

export function TenantBilling({ tenantId }: { tenantId: string }) {
  const tenant = findOwnerTenant(tenantId);
  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Billing" title={`Billing de ${tenant.name}`} description="Suscripcion, pagos, facturas, trial, upgrades, downgrades y recordatorios de cobranza." />
      <div className="grid gap-5 lg:grid-cols-3">
        <OwnerQuickCard icon={<CreditCard size={18} />} title="Plan actual" value={tenant.plan} detail={`MRR $${tenant.mrr}`} href="/owner/plans" />
        <OwnerQuickCard icon={<AlertTriangle size={18} />} title="Morosidad" value={tenant.status === "suspended" ? "Activa" : "Sin deuda"} detail="Suspension auditada" href="/owner/audit" />
        <OwnerQuickCard icon={<PackageCheck size={18} />} title="Facturacion" value="3 facturas" detail="Webhook mock preparado" href="/owner/plans" />
      </div>
    </OwnerConsoleShell>
  );
}

export function TenantFeatures({ tenantId }: { tenantId: string }) {
  const tenant = findOwnerTenant(tenantId);
  const [enabled, setEnabled] = useState(new Set(tenant.modules));
  const [featureKeys, setFeatureKeys] = useState(ownerFeatureFlags);
  const [source, setSource] = useState<OwnerDataSource>("demo");
  const [saveState, setSaveState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [saveMessage, setSaveMessage] = useState("");

  useEffect(() => {
    if (!hasOwnerSession()) {
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    loadOwnerFeatures(tenantId)
      .then((payload) => {
        if (!active) return;
        setFeatureKeys(payload.map((feature) => feature.feature_key));
        setEnabled(new Set(payload.filter((feature) => feature.enabled).map((feature) => feature.feature_key)));
        setSource("live");
      })
      .catch(() => {
        if (!active) return;
        setSource("fallback");
      });
    return () => {
      active = false;
    };
  }, [tenantId]);

  async function saveFeatures() {
    if (!hasOwnerSession()) {
      setSaveState("error");
      setSaveMessage("Inicia sesion owner para guardar feature flags auditados.");
      return;
    }
    setSaveState("saving");
    setSaveMessage("");
    try {
      const features = Object.fromEntries(featureKeys.map((feature) => [feature, enabled.has(feature)]));
      const saved = await updateOwnerFeatures(tenantId, features);
      setFeatureKeys(saved.map((feature) => feature.feature_key));
      setEnabled(new Set(saved.filter((feature) => feature.enabled).map((feature) => feature.feature_key)));
      setSource("live");
      setSaveState("success");
      setSaveMessage("Feature flags guardados y auditados.");
    } catch (caught) {
      setSaveState("error");
      setSaveMessage(caught instanceof Error ? caught.message : "No se pudieron guardar los feature flags.");
    }
  }

  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Feature flags" title={`Modulos de ${tenant.name}`} description="Activa o desactiva modulos por tenant con auditoria y limites de plan." />
      <OwnerDataSourceNotice source={source} />
      <Card>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {featureKeys.map((feature) => (
            <button
              className={`flex items-center justify-between rounded-lg border p-4 text-left ${enabled.has(feature) ? "border-legal-200 bg-legal-50" : "border-slate-200 bg-white"}`}
              key={feature}
              onClick={() => setEnabled((current) => {
                const next = new Set(current);
                if (next.has(feature)) next.delete(feature);
                else next.add(feature);
                return next;
              })}
              type="button"
            >
              <span className="text-sm font-semibold text-ink">{feature}</span>
              <ToggleRight className={enabled.has(feature) ? "text-legal-700" : "text-slate-300"} size={22} aria-hidden="true" />
            </button>
          ))}
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button className="inline-flex h-10 items-center justify-center rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={saveState === "saving"} onClick={() => void saveFeatures()} type="button">
            {saveState === "saving" ? "Guardando..." : "Guardar flags"}
          </button>
          {saveMessage ? <span className={`rounded-md px-3 py-2 text-sm ${saveState === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{saveMessage}</span> : null}
        </div>
      </Card>
    </OwnerConsoleShell>
  );
}

export function PlansManager() {
  const [plans, setPlans] = useState(ownerPlans);
  const [source, setSource] = useState<OwnerDataSource>("demo");
  const [planForm, setPlanForm] = useState({ code: "", name: "", monthly: "0", features: "expediente360,dashboard" });
  const [planState, setPlanState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [planMessage, setPlanMessage] = useState("");

  useEffect(() => {
    if (!hasOwnerSession()) {
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    loadOwnerPlans()
      .then((payload) => {
        if (!active) return;
        setPlans(payload.length ? payload : ownerPlans);
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

  async function submitPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!hasOwnerSession()) {
      setPlanState("error");
      setPlanMessage("Inicia sesion owner para crear planes auditados.");
      return;
    }
    setPlanState("saving");
    setPlanMessage("");
    try {
      const plan = await createOwnerPlan({
        code: planForm.code,
        name: planForm.name,
        monthly_price_cents: Math.round(Number(planForm.monthly) * 100),
        status: "active",
        trial_days: 14,
        limits: { users: 10, cases: 100 },
        features: splitCsv(planForm.features)
      });
      setPlans((current) => [plan, ...current.filter((item) => item.name !== plan.name)]);
      setPlanForm({ code: "", name: "", monthly: "0", features: "expediente360,dashboard" });
      setSource("live");
      setPlanState("success");
      setPlanMessage(`Plan creado: ${plan.name}.`);
    } catch (caught) {
      setPlanState("error");
      setPlanMessage(caught instanceof Error ? caught.message : "No se pudo crear el plan.");
    }
  }

  async function togglePlan(plan: typeof plans[number]) {
    if (!hasOwnerSession()) {
      setPlanState("error");
      setPlanMessage("Inicia sesion owner para actualizar planes auditados.");
      return;
    }
    setPlanState("saving");
    setPlanMessage("");
    try {
      const next = await updateOwnerPlan(plan.name, {
        status: plan.status === "active" ? "draft" : "active",
        reason: "Cambio de estado desde Owner Console"
      });
      setPlans((current) => current.map((item) => item.name === next.name ? next : item));
      setSource("live");
      setPlanState("success");
      setPlanMessage(`Plan ${next.name} actualizado a ${next.status}.`);
    } catch (caught) {
      setPlanState("error");
      setPlanMessage(caught instanceof Error ? caught.message : "No se pudo actualizar el plan.");
    }
  }

  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Planes" title="Planes y licencias" description="Precios mensual/anual, limites y modulos incluidos para START, PRO, AI y ENTERPRISE." />
      <OwnerDataSourceNotice source={source} />
      <form className="grid gap-3 rounded-lg border border-white/80 bg-white p-4 shadow-soft lg:grid-cols-[140px_1fr_140px_1fr_auto]" onSubmit={submitPlan}>
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm uppercase outline-none focus:border-legal-500"
          onChange={(event) => setPlanForm((current) => ({ ...current, code: event.target.value }))}
          placeholder="PLAN"
          required
          value={planForm.code}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setPlanForm((current) => ({ ...current, name: event.target.value }))}
          placeholder="Nombre comercial"
          required
          value={planForm.name}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          min="0"
          onChange={(event) => setPlanForm((current) => ({ ...current, monthly: event.target.value }))}
          placeholder="USD/mes"
          type="number"
          value={planForm.monthly}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setPlanForm((current) => ({ ...current, features: event.target.value }))}
          placeholder="features separadas por coma"
          value={planForm.features}
        />
        <button className="inline-flex h-11 items-center justify-center rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={planState === "saving"} type="submit">
          {planState === "saving" ? "Guardando..." : "Crear plan"}
        </button>
      </form>
      {planMessage ? <p className={`rounded-md px-3 py-2 text-sm ${planState === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{planMessage}</p> : null}
      <div className="grid gap-4 lg:grid-cols-2">
        {plans.map((plan) => (
          <Card key={plan.name}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <Badge>{plan.status}</Badge>
                <h2 className="mt-3 text-2xl font-semibold text-ink">{plan.name}</h2>
                <p className="mt-1 text-sm text-slate-500">${plan.monthly}/mes - ${plan.yearly}/anio</p>
              </div>
              <Flag className="text-legal-700" size={22} aria-hidden="true" />
            </div>
            <div className="mt-4 grid gap-2 text-sm text-slate-600">
              {[...plan.limits, ...plan.features].map((item) => <p key={item}>- {item}</p>)}
            </div>
            <button className="mt-5 rounded-md border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-legal-50 disabled:opacity-60" disabled={planState === "saving"} onClick={() => void togglePlan(plan)} type="button">
              {plan.status === "active" ? "Pasar a draft" : "Activar plan"}
            </button>
          </Card>
        ))}
      </div>
    </OwnerConsoleShell>
  );
}

export function SupportTickets() {
  const [tickets, setTickets] = useState(ownerTickets);
  const [source, setSource] = useState<OwnerDataSource>("demo");
  const [ticketForm, setTicketForm] = useState({ title: "", tenantId: "", category: "support", priority: "medium" });
  const [createState, setCreateState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [createMessage, setCreateMessage] = useState("");
  const [resolvingTicketId, setResolvingTicketId] = useState("");
  const [resolveMessage, setResolveMessage] = useState("");

  useEffect(() => {
    if (!hasOwnerSession()) {
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    loadOwnerTickets()
      .then((payload) => {
        if (!active) return;
        setTickets(payload.length ? payload : ownerTickets);
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

  async function submitTicket(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!hasOwnerSession()) {
      setCreateState("error");
      setCreateMessage("Inicia sesion owner para crear tickets auditados.");
      return;
    }
    setCreateState("saving");
    setCreateMessage("");
    try {
      const ticket = await createOwnerTicket({
        title: ticketForm.title,
        tenant_id: ticketForm.tenantId || null,
        category: ticketForm.category,
        priority: ticketForm.priority,
        body: "Ticket creado desde Owner Console"
      });
      setTickets((current) => [ticket, ...current.filter((item) => item.id !== ticket.id)]);
      setTicketForm({ title: "", tenantId: "", category: "support", priority: "medium" });
      setSource("live");
      setCreateState("success");
      setCreateMessage(`Ticket creado: ${ticket.title}.`);
    } catch (caught) {
      setCreateState("error");
      setCreateMessage(caught instanceof Error ? caught.message : "No se pudo crear el ticket.");
    }
  }

  async function resolveTicket(ticketId: string) {
    if (!hasOwnerSession()) {
      setResolveMessage("Inicia sesion owner para resolver tickets auditados.");
      return;
    }
    setResolvingTicketId(ticketId);
    setResolveMessage("");
    try {
      const ticket = await resolveOwnerTicket(ticketId);
      setTickets((current) => current.map((item) => item.id === ticket.id ? ticket : item));
      setSource("live");
      setResolveMessage(`Ticket resuelto: ${ticket.title}.`);
    } catch (caught) {
      setResolveMessage(caught instanceof Error ? caught.message : "No se pudo resolver el ticket.");
    } finally {
      setResolvingTicketId("");
    }
  }

  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Soporte" title="Tickets y SLA" description="Mesa de ayuda con prioridades, responsables, categorias, historial y resolucion auditada." />
      <OwnerDataSourceNotice source={source} />
      <form className="grid gap-3 rounded-lg border border-white/80 bg-white p-4 shadow-soft lg:grid-cols-[1fr_220px_180px_auto]" onSubmit={submitTicket}>
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setTicketForm((current) => ({ ...current, title: event.target.value }))}
          placeholder="Titulo del ticket"
          required
          value={ticketForm.title}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setTicketForm((current) => ({ ...current, tenantId: event.target.value }))}
          placeholder="tenant_id opcional"
          value={ticketForm.tenantId}
        />
        <select
          className="h-11 rounded-md border border-slate-200 px-3 text-sm font-semibold outline-none focus:border-legal-500"
          onChange={(event) => setTicketForm((current) => ({ ...current, priority: event.target.value }))}
          value={ticketForm.priority}
        >
          {["low", "medium", "high", "critical"].map((priority) => <option key={priority} value={priority}>{priority}</option>)}
        </select>
        <button className="inline-flex h-11 items-center justify-center rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={createState === "saving"} type="submit">
          {createState === "saving" ? "Creando..." : "Crear ticket"}
        </button>
      </form>
      {createMessage ? <p className={`rounded-md px-3 py-2 text-sm ${createState === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{createMessage}</p> : null}
      {resolveMessage ? <p className={`rounded-md px-3 py-2 text-sm ${resolveMessage.includes("error") || resolveMessage.includes("No se") || resolveMessage.includes("Inicia") ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{resolveMessage}</p> : null}
      <Card>
        <div className="grid gap-3">
          {tickets.map((ticket) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={ticket.id}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-ink">{ticket.title}</p>
                  <p className="mt-1 text-xs text-slate-500">{ticket.tenant} - {ticket.category} - SLA {ticket.sla} - {ticket.status}</p>
                  {ticket.resolution ? <p className="mt-2 rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">{ticket.resolution}</p> : null}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge>{ticket.priority}</Badge>
                  {ticket.status !== "resolved" ? (
                    <button className="rounded-md border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-legal-50 disabled:opacity-60" disabled={resolvingTicketId === ticket.id} onClick={() => void resolveTicket(ticket.id)} type="button">
                      {resolvingTicketId === ticket.id ? "Resolviendo..." : "Resolver"}
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </OwnerConsoleShell>
  );
}

export function SystemHealth() {
  const [checks, setChecks] = useState(ownerSystemChecks);
  const [incidents, setIncidents] = useState(ownerSystemIncidents);
  const [source, setSource] = useState<OwnerDataSource>("demo");
  const [incidentForm, setIncidentForm] = useState({ component: "api", title: "", severity: "medium", summary: "" });
  const [incidentState, setIncidentState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [incidentMessage, setIncidentMessage] = useState("");
  const [resolvingIncidentId, setResolvingIncidentId] = useState("");

  useEffect(() => {
    if (!hasOwnerSession()) {
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    Promise.all([loadOwnerSystemChecks(), loadOwnerSystemIncidents()])
      .then(([payload, nextIncidents]) => {
        if (!active) return;
        setChecks(payload.length ? payload : ownerSystemChecks);
        setIncidents(nextIncidents);
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

  async function submitIncident(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!hasOwnerSession()) {
      setIncidentState("error");
      setIncidentMessage("Inicia sesion owner devops para crear incidentes auditados.");
      return;
    }
    setIncidentState("saving");
    setIncidentMessage("");
    try {
      const incident = await createOwnerSystemIncident(incidentForm);
      setIncidents((current) => [incident, ...current.filter((item) => item.id !== incident.id)]);
      setIncidentForm({ component: "api", title: "", severity: "medium", summary: "" });
      setSource("live");
      setIncidentState("success");
      setIncidentMessage(`Incidente creado: ${incident.title}.`);
    } catch (caught) {
      setIncidentState("error");
      setIncidentMessage(caught instanceof Error ? caught.message : "No se pudo crear el incidente.");
    }
  }

  async function resolveIncident(incidentId: string) {
    if (!hasOwnerSession()) {
      setIncidentState("error");
      setIncidentMessage("Inicia sesion owner devops para resolver incidentes auditados.");
      return;
    }
    setResolvingIncidentId(incidentId);
    setIncidentMessage("");
    try {
      const incident = await resolveOwnerSystemIncident(incidentId);
      setIncidents((current) => current.map((item) => item.id === incident.id ? incident : item));
      setSource("live");
      setIncidentState("success");
      setIncidentMessage(`Incidente resuelto: ${incident.title}.`);
    } catch (caught) {
      setIncidentState("error");
      setIncidentMessage(caught instanceof Error ? caught.message : "No se pudo resolver el incidente.");
    } finally {
      setResolvingIncidentId("");
    }
  }

  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Monitoreo" title="Salud tecnica" description="API, DB, Redis, storage, IA, WhatsApp, SINOE, jobs, logs y backups en un panel operativo." />
      <OwnerDataSourceNotice source={source} />
      <form className="grid gap-3 rounded-lg border border-white/80 bg-white p-4 shadow-soft lg:grid-cols-[160px_1fr_160px_1fr_auto]" onSubmit={submitIncident}>
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setIncidentForm((current) => ({ ...current, component: event.target.value }))}
          placeholder="api"
          required
          value={incidentForm.component}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setIncidentForm((current) => ({ ...current, title: event.target.value }))}
          placeholder="Titulo del incidente"
          required
          value={incidentForm.title}
        />
        <select
          className="h-11 rounded-md border border-slate-200 px-3 text-sm font-semibold outline-none focus:border-legal-500"
          onChange={(event) => setIncidentForm((current) => ({ ...current, severity: event.target.value }))}
          value={incidentForm.severity}
        >
          {["low", "medium", "high", "critical"].map((severity) => <option key={severity} value={severity}>{severity}</option>)}
        </select>
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setIncidentForm((current) => ({ ...current, summary: event.target.value }))}
          placeholder="Resumen operativo"
          value={incidentForm.summary}
        />
        <button className="inline-flex h-11 items-center justify-center rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={incidentState === "saving"} type="submit">
          {incidentState === "saving" ? "Creando..." : "Crear incidente"}
        </button>
      </form>
      {incidentMessage ? <p className={`rounded-md px-3 py-2 text-sm ${incidentState === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{incidentMessage}</p> : null}
      <div className="grid gap-4 lg:grid-cols-2">
        {checks.map((check) => (
          <Card key={check.service}>
            <StatusLine label={check.service} value={`${check.detail} - ${check.latency}`} status={check.status} />
          </Card>
        ))}
      </div>
      <Card>
        <SectionTitle icon={<AlertTriangle size={18} />} title="Incidentes tecnicos" />
        <div className="mt-4 grid gap-3">
          {incidents.map((incident) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={incident.id}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge>{incident.severity}</Badge>
                    <span className="text-xs font-semibold text-slate-500">{incident.component}</span>
                  </div>
                  <p className="mt-2 font-semibold text-ink">{incident.title}</p>
                  <p className="mt-1 text-sm text-slate-600">{incident.summary || "Sin resumen operativo."}</p>
                  <p className="mt-1 text-xs text-slate-500">Creado: {incident.createdAt}{incident.resolvedAt ? ` - resuelto: ${incident.resolvedAt}` : ""}</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge>{incident.status}</Badge>
                  {incident.status !== "resolved" ? (
                    <button className="rounded-md border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-legal-50 disabled:opacity-60" disabled={resolvingIncidentId === incident.id} onClick={() => void resolveIncident(incident.id)} type="button">
                      {resolvingIncidentId === incident.id ? "Resolviendo..." : "Resolver"}
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
          {!incidents.length ? <EmptyState title="Sin incidentes" description="No hay incidentes tecnicos registrados." /> : null}
        </div>
      </Card>
    </OwnerConsoleShell>
  );
}

export function DemoTenants() {
  const [demos, setDemos] = useState(ownerDemos);
  const [source, setSource] = useState<OwnerDataSource>("demo");
  const [demoForm, setDemoForm] = useState({ name: "", slug: "", demoType: "litigation" });
  const [createState, setCreateState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [createMessage, setCreateMessage] = useState("");
  const [resettingDemoId, setResettingDemoId] = useState("");

  useEffect(() => {
    if (!hasOwnerSession()) {
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    loadOwnerDemos()
      .then((payload) => {
        if (!active) return;
        setDemos(payload);
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

  async function submitDemo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!hasOwnerSession()) {
      setCreateState("error");
      setCreateMessage("Inicia sesion owner para crear demos auditadas.");
      return;
    }
    setCreateState("saving");
    setCreateMessage("");
    try {
      const demo = await createOwnerDemo({
        name: demoForm.name || "LEXFLOW Demo Tenant",
        slug: demoForm.slug || undefined,
        plan: "AI",
        demo_type: demoForm.demoType
      });
      setDemos((current) => [demo, ...current.filter((item) => item.tenant !== demo.tenant)]);
      setDemoForm({ name: "", slug: "", demoType: "litigation" });
      setSource("live");
      setCreateState("success");
      setCreateMessage(`Demo creada: ${demo.name}.`);
    } catch (caught) {
      setCreateState("error");
      setCreateMessage(caught instanceof Error ? caught.message : "No se pudo crear la demo.");
    }
  }

  async function resetDemo(demoId: string) {
    if (!hasOwnerSession()) {
      setCreateState("error");
      setCreateMessage("Inicia sesion owner para resetear demos auditadas.");
      return;
    }
    setResettingDemoId(demoId);
    setCreateMessage("");
    try {
      const demo = await resetOwnerDemo(demoId);
      setDemos((current) => current.map((item) => item.id === demo.id ? demo : item));
      setSource("live");
      setCreateState("success");
      setCreateMessage(`Demo reseteada: ${demo.name}.`);
    } catch (caught) {
      setCreateState("error");
      setCreateMessage(caught instanceof Error ? caught.message : "No se pudo resetear la demo.");
    } finally {
      setResettingDemoId("");
    }
  }

  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Demos" title="Demos comerciales" description="Crea, resetea y carga datos demo por tipo de estudio sin contaminar tenants productivos." />
      <OwnerDataSourceNotice source={source} />
      <form className="grid gap-3 rounded-lg border border-white/80 bg-white p-4 shadow-soft lg:grid-cols-[1fr_220px_180px_auto]" onSubmit={submitDemo}>
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setDemoForm((current) => ({ ...current, name: event.target.value }))}
          placeholder="Nombre demo comercial"
          required
          value={demoForm.name}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setDemoForm((current) => ({ ...current, slug: event.target.value }))}
          placeholder="slug-demo opcional"
          value={demoForm.slug}
        />
        <select
          className="h-11 rounded-md border border-slate-200 px-3 text-sm font-semibold outline-none focus:border-legal-500"
          onChange={(event) => setDemoForm((current) => ({ ...current, demoType: event.target.value }))}
          value={demoForm.demoType}
        >
          {["litigation", "corporate", "labor", "tax"].map((demoType) => <option key={demoType} value={demoType}>{demoType}</option>)}
        </select>
        <button className="inline-flex h-11 items-center justify-center rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={createState === "saving"} type="submit">
          {createState === "saving" ? "Creando..." : "Crear demo"}
        </button>
      </form>
      {createMessage ? <p className={`rounded-md px-3 py-2 text-sm ${createState === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{createMessage}</p> : null}
      <div className="grid gap-4 lg:grid-cols-3">
        {demos.map((demo) => (
          <div className="rounded-lg border border-white/80 bg-white p-5 shadow-soft" key={demo.id ?? demo.tenant}>
            <div className="flex items-center gap-2 text-sm font-semibold text-legal-700"><Sparkles size={18} /><span>{demo.name}</span></div>
            <p className="mt-3 text-2xl font-semibold text-ink">{demo.status}</p>
            <p className="mt-1 text-sm text-slate-500">{demo.tenant} - reset {demo.reset}</p>
            <button className="mt-4 rounded-md border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-legal-50 disabled:opacity-60" disabled={resettingDemoId === demo.id} onClick={() => void resetDemo(demo.id)} type="button">
              {resettingDemoId === demo.id ? "Reseteando..." : "Reset demo"}
            </button>
          </div>
        ))}
      </div>
    </OwnerConsoleShell>
  );
}

export function OwnerAuditLogs() {
  const [audits, setAudits] = useState(ownerAuditLogs);
  const [source, setSource] = useState<OwnerDataSource>("demo");

  useEffect(() => {
    if (!hasOwnerSession()) {
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    loadOwnerAuditLogs()
      .then((payload) => {
        if (!active) return;
        setAudits(payload.length ? payload : ownerAuditLogs);
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

  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Auditoria" title="Owner audit logs" description="Registro de acciones criticas: planes, suspensiones, features, soporte e intervenciones." />
      <OwnerDataSourceNotice source={source} />
      <Card>
        <div className="grid gap-3">
          {audits.map((audit) => (
            <StatusLine key={`${audit.action}-${audit.at}`} label={audit.action} value={`${audit.actor} -> ${audit.target} (${audit.at})`} status="audit" />
          ))}
        </div>
      </Card>
    </OwnerConsoleShell>
  );
}

export function InterventionRequests() {
  const [interventions, setInterventions] = useState(ownerInterventions);
  const [source, setSource] = useState<OwnerDataSource>("demo");
  const [interventionForm, setInterventionForm] = useState({ tenantId: "", reason: "", duration: "60", scopes: "metadata:read" });
  const [createState, setCreateState] = useState<"idle" | "saving" | "error" | "success">("idle");
  const [createMessage, setCreateMessage] = useState("");
  const [closingId, setClosingId] = useState("");

  useEffect(() => {
    if (!hasOwnerSession()) {
      setSource("demo");
      return;
    }
    let active = true;
    setSource("loading");
    loadOwnerInterventions()
      .then((payload) => {
        if (!active) return;
        setInterventions(payload.length ? payload : ownerInterventions);
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

  async function submitIntervention(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!hasOwnerSession()) {
      setCreateState("error");
      setCreateMessage("Inicia sesion owner para crear intervenciones auditadas.");
      return;
    }
    setCreateState("saving");
    setCreateMessage("");
    try {
      const intervention = await createOwnerIntervention({
        tenant_id: interventionForm.tenantId,
        reason: interventionForm.reason,
        duration_minutes: Number(interventionForm.duration),
        scopes: interventionForm.scopes.split(",").map((scope) => scope.trim()).filter(Boolean)
      });
      setInterventions((current) => [intervention, ...current.filter((item) => `${item.tenant}-${item.expires}` !== `${intervention.tenant}-${intervention.expires}`)]);
      setInterventionForm({ tenantId: "", reason: "", duration: "60", scopes: "metadata:read" });
      setSource("live");
      setCreateState("success");
      setCreateMessage(`Intervencion creada para ${intervention.tenant}.`);
    } catch (caught) {
      setCreateState("error");
      setCreateMessage(caught instanceof Error ? caught.message : "No se pudo crear la intervencion.");
    }
  }

  async function closeIntervention(interventionId: string) {
    if (!hasOwnerSession()) {
      setCreateState("error");
      setCreateMessage("Inicia sesion owner para cerrar intervenciones auditadas.");
      return;
    }
    setClosingId(interventionId);
    setCreateMessage("");
    try {
      const closed = await closeOwnerIntervention(interventionId);
      setInterventions((current) => current.map((item) => item.id === closed.id ? closed : item));
      setSource("live");
      setCreateState("success");
      setCreateMessage(`Intervencion cerrada para ${closed.tenant}.`);
    } catch (caught) {
      setCreateState("error");
      setCreateMessage(caught instanceof Error ? caught.message : "No se pudo cerrar la intervencion.");
    } finally {
      setClosingId("");
    }
  }

  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Seguridad soporte" title="Intervenciones temporales" description="Acceso excepcional, con motivo, duracion, alcance limitado, expiracion y audit_log." />
      <OwnerDataSourceNotice source={source} />
      <SecurityBoundaryNotice />
      <form className="grid gap-3 rounded-lg border border-white/80 bg-white p-4 shadow-soft lg:grid-cols-[240px_1fr_120px_220px_auto]" onSubmit={submitIntervention}>
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setInterventionForm((current) => ({ ...current, tenantId: event.target.value }))}
          placeholder="tenant_id"
          required
          value={interventionForm.tenantId}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setInterventionForm((current) => ({ ...current, reason: event.target.value }))}
          placeholder="Motivo autorizado"
          required
          value={interventionForm.reason}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          max="480"
          min="5"
          onChange={(event) => setInterventionForm((current) => ({ ...current, duration: event.target.value }))}
          type="number"
          value={interventionForm.duration}
        />
        <input
          className="h-11 rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setInterventionForm((current) => ({ ...current, scopes: event.target.value }))}
          placeholder="metadata:read"
          value={interventionForm.scopes}
        />
        <button className="inline-flex h-11 items-center justify-center rounded-md bg-legal-900 px-4 text-sm font-semibold text-white disabled:opacity-60" disabled={createState === "saving"} type="submit">
          {createState === "saving" ? "Creando..." : "Crear intervencion"}
        </button>
      </form>
      {createMessage ? <p className={`rounded-md px-3 py-2 text-sm ${createState === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{createMessage}</p> : null}
      <Card>
        <div className="grid gap-3">
          {interventions.map((item) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={item.id ?? `${item.tenant}-${item.expires}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-ink">{item.tenant}</p>
                  <p className="mt-1 text-sm text-slate-600">{item.reason}</p>
                  <p className="mt-1 text-xs text-slate-500">Expira: {item.expires} - scopes: {item.scopes.join(", ")}</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge>{item.status}</Badge>
                  {item.status === "active" ? (
                    <button className="rounded-md border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-legal-50 disabled:opacity-60" disabled={closingId === item.id} onClick={() => void closeIntervention(item.id)} type="button">
                      {closingId === item.id ? "Cerrando..." : "Cerrar"}
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </OwnerConsoleShell>
  );
}

function SecurityBoundaryNotice() {
  return (
    <div className="rounded-lg border border-sky-100 bg-sky-50 px-4 py-3 text-sm text-legal-900">
      <div className="flex gap-3">
        <LockKeyhole className="mt-0.5 shrink-0" size={18} aria-hidden="true" />
        <p>
          Boundary owner activo: metadata SaaS permitida; contenido sensible de clientes, expedientes, documentos y comunicaciones requiere autorizacion temporal y auditada.
        </p>
      </div>
    </div>
  );
}

function OwnerDataSourceNotice({ source }: { source: OwnerDataSource }) {
  const label = source === "live" ? "Owner Console conectado al API cloud." : source === "loading" ? "Consultando Owner API..." : source === "fallback" ? "Owner API no disponible, mostrando demo seguro." : "Modo demo owner sin sesion JWT.";
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-600">
      {label}
    </div>
  );
}

function TenantRow({ tenant, expanded = false }: { tenant: OwnerTenant; expanded?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{tenant.plan}</Badge>
            <HealthPill score={tenant.health} />
            <span className="text-xs font-semibold text-slate-500">{tenant.status}</span>
          </div>
          <Link className="mt-3 block text-lg font-semibold text-ink hover:text-legal-700" href={`/owner/tenants/${tenant.id}`}>
            {tenant.name}
          </Link>
          <p className="mt-1 text-sm text-slate-500">{tenant.slug} - {tenant.users} usuarios - {tenant.cases} expedientes - ultimo uso {tenant.lastSeen}</p>
          {tenant.onboarding ? (
            <p className="mt-2 text-xs font-semibold text-legal-700">
              Onboarding {tenant.onboarding.ready ? "listo" : "pendiente"} - admin {tenant.onboarding.adminEmail ?? "sin crear"}
            </p>
          ) : null}
        </div>
        <div className="grid grid-cols-3 gap-2 lg:min-w-[360px]">
          <MiniMetric label="MRR" value={`$${tenant.mrr}`} />
          <MiniMetric label="IA" value={`${Math.round(tenant.aiTokens / 1000)}k`} />
          <MiniMetric label="Tickets" value={String(tenant.openTickets)} />
        </div>
      </div>
      {expanded ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {["Editar", "Suspender", "Reactivar", "Cambiar plan", "Features", "Uso"].map((action) => (
            <button className="rounded-md border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-legal-50" key={action} type="button">
              {action}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function OwnerQuickCard({ icon, title, value, detail, href }: { icon: ReactNode; title: string; value: string; detail: string; href: string }) {
  return (
    <Link className="rounded-lg border border-white/80 bg-white p-5 shadow-soft transition hover:-translate-y-0.5 hover:border-legal-100" href={href}>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">{icon}<span>{title}</span></div>
      <p className="mt-3 text-2xl font-semibold text-ink">{value}</p>
      <p className="mt-1 text-sm text-slate-500">{detail}</p>
    </Link>
  );
}

function SectionTitle({ icon, title }: { icon: ReactNode; title: string }) {
  return <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">{icon}<span>{title}</span></div>;
}

function storeOwnerSession(session: { access_token: string; refresh_token: string; owner: { email: string; role: string; mfa_enabled?: boolean } }) {
  localStorage.setItem("lexflow.owner_access_token", session.access_token);
  localStorage.setItem("lexflow.owner_refresh_token", session.refresh_token);
  localStorage.setItem("lexflow.owner_user", JSON.stringify(session.owner));
}

function HealthPill({ score }: { score: number }) {
  const tone = score > 80 ? "bg-emerald-50 text-emerald-700" : score > 60 ? "bg-amber-50 text-amber-700" : "bg-rose-50 text-rose-700";
  return <span className={`rounded-md px-2.5 py-1 text-xs font-semibold ${tone}`}>Health {score}</span>;
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-mist p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-ink">{value}</p>
    </div>
  );
}

function StatusLine({ label, value, status }: { label: string; value: string; status: string }) {
  const icon = status === "operational" || status === "audit" ? <CheckCircle2 size={16} /> : status === "degraded" ? <AlertTriangle size={16} /> : <LifeBuoy size={16} />;
  return (
    <div className="flex items-start justify-between gap-3 rounded-lg border border-slate-200 bg-white p-3">
      <div className="flex gap-3">
        <span className="mt-0.5 text-legal-700">{icon}</span>
        <div>
          <p className="text-sm font-semibold text-ink">{label}</p>
          <p className="mt-1 text-xs text-slate-500">{value}</p>
        </div>
      </div>
      <span className="rounded-md bg-mist px-2 py-1 text-xs font-semibold text-slate-600">{status}</span>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-mist p-3">
      <p className="text-xs font-semibold uppercase tracking-normal text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-ink">{value}</p>
    </div>
  );
}

function UsageBar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  return (
    <div>
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="font-semibold text-ink">{label}</span>
        <span className="text-slate-500">{value} / {max}</span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-legal-700" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function splitCsv(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}
