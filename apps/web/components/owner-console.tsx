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
  PackageCheck,
  ShieldCheck,
  Sparkles,
  ToggleRight,
  Users
} from "lucide-react";
import Link from "next/link";
import React, { ReactNode, useMemo, useState } from "react";
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
  ownerTenants,
  ownerTickets
} from "@/lib/owner-demo";

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

export function OwnerConsoleShell({ children }: { children: ReactNode }) {
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
          </nav>
        </div>
      </div>
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:py-8">{children}</div>
    </main>
  );
}

export function OwnerDashboard() {
  return (
    <OwnerConsoleShell>
      <PageHeader
        eyebrow="Modulo propietario"
        title="Command Center SaaS"
        description="Administra tenants, planes, cobranzas, soporte, consumo, feature flags y salud del sistema sin abrir datos sensibles de estudios juridicos."
      />
      <SecurityBoundaryNotice />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {ownerDashboardMetrics().map((metric) => <MetricCard key={metric.label} {...metric} />)}
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <SectionTitle icon={<Building2 size={18} />} title="Tenants en observacion" />
          <div className="mt-4 grid gap-3">
            {ownerTenants.map((tenant) => <TenantRow key={tenant.id} tenant={tenant} />)}
          </div>
        </Card>
        <Card>
          <SectionTitle icon={<Activity size={18} />} title="Salud del sistema" />
          <div className="mt-4 grid gap-3">
            {ownerSystemChecks.slice(0, 5).map((check) => (
              <StatusLine key={check.service} label={check.service} value={check.detail} status={check.status} />
            ))}
          </div>
        </Card>
      </div>
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
  const tenants = useMemo(() => ownerTenants.filter((tenant) => `${tenant.name} ${tenant.slug} ${tenant.plan}`.toLowerCase().includes(query.toLowerCase())), [query]);

  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Tenants" title="Gestion de estudios" description="Crea, suspende, reactiva, cambia planes y controla limites por tenant desde una consola separada." />
      <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
        <input
          className="h-11 rounded-md border border-slate-200 bg-white px-3 text-sm outline-none focus:border-legal-500"
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar tenant, plan, slug..."
          value={query}
        />
        <button className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white" type="button">
          <Users size={16} aria-hidden="true" />
          Crear tenant
        </button>
      </div>
      <div className="grid gap-4">
        {tenants.map((tenant) => <TenantRow key={tenant.id} tenant={tenant} expanded />)}
        {!tenants.length ? <EmptyState title="Sin tenants" description="No hay estudios juridicos con ese filtro." /> : null}
      </div>
    </OwnerConsoleShell>
  );
}

export function TenantDetail({ tenantId }: { tenantId: string }) {
  const tenant = findOwnerTenant(tenantId);
  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Tenant" title={tenant.name} description="Vista administrativa con metadata operativa, billing, limites, soporte y flags. Los datos sensibles del estudio permanecen ocultos." />
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
            {["Suspender", "Reactivar", "Cambiar plan", "Configurar limites"].map((action) => (
              <button className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-legal-50" key={action} type="button">
                {action}
              </button>
            ))}
          </div>
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
    </OwnerConsoleShell>
  );
}

export function TenantUsage({ tenantId }: { tenantId: string }) {
  const tenant = findOwnerTenant(tenantId);
  const usage = [
    ["Usuarios", tenant.users, 40],
    ["Expedientes", tenant.cases, 1500],
    ["Documentos", tenant.documents, 5000],
    ["Storage GB", tenant.storageGb, 100],
    ["IA tokens", Math.round(tenant.aiTokens / 1000), 1000],
    ["WhatsApp", tenant.whatsappMessages, 5000],
    ["SINOE syncs", tenant.sinoeSyncs, 1000]
  ] as const;
  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Uso" title={`Consumo de ${tenant.name}`} description="Usuarios, expedientes, documentos, IA, OCR, WhatsApp, automatizaciones y SINOE syncs medidos por tenant." />
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
  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Feature flags" title={`Modulos de ${tenant.name}`} description="Activa o desactiva modulos por tenant con auditoria y limites de plan." />
      <Card>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {ownerFeatureFlags.map((feature) => (
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
      </Card>
    </OwnerConsoleShell>
  );
}

export function PlansManager() {
  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Planes" title="Planes y licencias" description="Precios mensual/anual, limites y modulos incluidos para START, PRO, AI y ENTERPRISE." />
      <div className="grid gap-4 lg:grid-cols-2">
        {ownerPlans.map((plan) => (
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
          </Card>
        ))}
      </div>
    </OwnerConsoleShell>
  );
}

export function SupportTickets() {
  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Soporte" title="Tickets y SLA" description="Mesa de ayuda con prioridades, responsables, categorias, historial y resolucion auditada." />
      <Card>
        <div className="grid gap-3">
          {ownerTickets.map((ticket) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={ticket.id}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-ink">{ticket.title}</p>
                  <p className="mt-1 text-xs text-slate-500">{ticket.tenant} - {ticket.category} - SLA {ticket.sla}</p>
                </div>
                <Badge>{ticket.priority}</Badge>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </OwnerConsoleShell>
  );
}

export function SystemHealth() {
  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Monitoreo" title="Salud tecnica" description="API, DB, Redis, storage, IA, WhatsApp, SINOE, jobs, logs y backups en un panel operativo." />
      <div className="grid gap-4 lg:grid-cols-2">
        {ownerSystemChecks.map((check) => (
          <Card key={check.service}>
            <StatusLine label={check.service} value={`${check.detail} - ${check.latency}`} status={check.status} />
          </Card>
        ))}
      </div>
    </OwnerConsoleShell>
  );
}

export function DemoTenants() {
  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Demos" title="Demos comerciales" description="Crea, resetea y carga datos demo por tipo de estudio sin contaminar tenants productivos." />
      <div className="grid gap-4 lg:grid-cols-3">
        {ownerDemos.map((demo) => (
          <OwnerQuickCard key={demo.tenant} icon={<Sparkles size={18} />} title={demo.name} value={demo.status} detail={`${demo.tenant} - reset ${demo.reset}`} href="/owner/demos" />
        ))}
      </div>
    </OwnerConsoleShell>
  );
}

export function OwnerAuditLogs() {
  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Auditoria" title="Owner audit logs" description="Registro de acciones criticas: planes, suspensiones, features, soporte e intervenciones." />
      <Card>
        <div className="grid gap-3">
          {ownerAuditLogs.map((audit) => (
            <StatusLine key={`${audit.action}-${audit.at}`} label={audit.action} value={`${audit.actor} -> ${audit.target} (${audit.at})`} status="audit" />
          ))}
        </div>
      </Card>
    </OwnerConsoleShell>
  );
}

export function InterventionRequests() {
  return (
    <OwnerConsoleShell>
      <PageHeader eyebrow="Owner -> Seguridad soporte" title="Intervenciones temporales" description="Acceso excepcional, con motivo, duracion, alcance limitado, expiracion y audit_log." />
      <SecurityBoundaryNotice />
      <Card>
        <div className="grid gap-3">
          {ownerInterventions.map((item) => (
            <div className="rounded-lg border border-slate-200 bg-white p-4" key={`${item.tenant}-${item.expires}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-ink">{item.tenant}</p>
                  <p className="mt-1 text-sm text-slate-600">{item.reason}</p>
                  <p className="mt-1 text-xs text-slate-500">Expira: {item.expires} - scopes: {item.scopes.join(", ")}</p>
                </div>
                <Badge>{item.status}</Badge>
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
