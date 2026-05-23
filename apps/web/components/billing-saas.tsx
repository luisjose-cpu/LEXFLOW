"use client";

import { Badge, Button, Card, MetricCard } from "@lexflow/ui";
import { ArrowRight, Check, CreditCard, Gauge, KeyRound, Layers3, Rocket, ShieldCheck, Sparkles, Zap } from "lucide-react";
import React from "react";
import { billingPlans, currentSubscription, featureLabels, onboardingSteps, usageMeters } from "@/lib/billing-demo";

type BillingView = "pricing" | "onboarding" | "billing" | "usage" | "features";

export function BillingSaaS({ view = "pricing" }: { view?: BillingView }) {
  return (
    <div className="grid gap-5">
      <BillingHero view={view} />
      {view === "pricing" ? (
        <>
          <PricingCards />
          <PlanFeatureTable />
        </>
      ) : null}
      {view === "onboarding" ? <OnboardingWizard /> : null}
      {view === "billing" ? <BillingSettings /> : null}
      {view === "usage" ? <UsageDashboard /> : null}
      {view === "features" ? <FeatureGateCenter /> : null}
    </div>
  );
}

function BillingHero({ view }: { view: BillingView }) {
  const labels: Record<BillingView, string> = {
    pricing: "Planes SaaS",
    onboarding: "Onboarding",
    billing: "Facturacion",
    usage: "Uso",
    features: "Feature gates"
  };
  return (
    <header className="rounded-lg border border-white/80 bg-white p-5 shadow-soft">
      <div className="flex flex-wrap gap-2">
        <Badge>P12</Badge>
        <Badge>Billing SaaS</Badge>
        <Badge>Mock provider</Badge>
      </div>
      <div className="mt-4 flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
        <div>
          <h1 className="text-3xl font-semibold tracking-normal text-ink sm:text-4xl">{labels[view]}</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            Planes, limites, licencias, modulos, trial, suscripcion mock, usage e invoices preparados para vender LEXFLOW como SaaS multitenant.
          </p>
        </div>
        <Button>
          <Rocket size={16} />
          Activar trial
        </Button>
      </div>
    </header>
  );
}

export function PricingCards() {
  return (
    <section className="grid gap-4 lg:grid-cols-4">
      {billingPlans.map((plan) => (
        <Card className={plan.code === "AI" ? "ring-2 ring-sky-200" : ""} key={plan.code}>
          <div className="flex items-start justify-between gap-3">
            <div>
              <Badge>{plan.code}</Badge>
              <h2 className="mt-3 text-xl font-semibold text-ink">{plan.name}</h2>
            </div>
            {plan.code === "AI" ? <Sparkles className="text-legal-700" size={20} /> : null}
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">{plan.description}</p>
          <div className="mt-5 flex items-end gap-2">
            <span className="text-3xl font-semibold text-ink">{plan.price}</span>
            <span className="pb-1 text-sm text-slate-500">{plan.cadence}</span>
          </div>
          <div className="mt-5 grid gap-2">
            {plan.limits.map((limit) => (
              <p className="flex items-center gap-2 text-sm font-semibold text-slate-700" key={limit}>
                <Check size={15} className="text-emerald-600" />
                {limit}
              </p>
            ))}
          </div>
          <div className="mt-5">
            <Button tone={plan.code === "AI" ? "primary" : "secondary"}>
              {plan.code === "ENTERPRISE" ? "Contactar ventas" : "Suscribir mock"}
              <ArrowRight size={15} />
            </Button>
          </div>
        </Card>
      ))}
    </section>
  );
}

export function PlanFeatureTable() {
  const features = Object.keys(featureLabels);
  return (
    <Card>
      <PanelTitle icon={<Layers3 size={18} />} title="Tabla de modulos por plan" />
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[760px] border-separate border-spacing-0 text-sm">
          <thead>
            <tr>
              <th className="rounded-l-md bg-mist px-3 py-3 text-left text-slate-500">Feature gate</th>
              {billingPlans.map((plan, index) => (
                <th className={`bg-mist px-3 py-3 text-left text-slate-500 ${index === billingPlans.length - 1 ? "rounded-r-md" : ""}`} key={plan.code}>{plan.code}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {features.map((feature) => (
              <tr key={feature}>
                <td className="border-b border-slate-100 px-3 py-3 font-semibold text-ink">{featureLabels[feature]}</td>
                {billingPlans.map((plan) => (
                  <td className="border-b border-slate-100 px-3 py-3" key={plan.code}>
                    {plan.features.includes(feature) ? <span className="inline-flex rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">Incluido</span> : <span className="inline-flex rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-500">Upgrade</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

export function SubscriptionStatusCard() {
  return (
    <Card>
      <PanelTitle icon={<CreditCard size={18} />} title="Suscripcion actual" />
      <div className="mt-4 grid gap-4 sm:grid-cols-4">
        <MetricCard label="Plan" value={currentSubscription.plan} trend={currentSubscription.status} />
        <MetricCard label="Licencias" value={String(currentSubscription.seats)} trend="usuarios incluidos" />
        <MetricCard label="Trial hasta" value="05 Jun" trend={currentSubscription.trialEndsAt} />
        <MetricCard label="Invoice mock" value={currentSubscription.amount} trend={currentSubscription.invoice} />
      </div>
    </Card>
  );
}

export function UsageMeter({ item }: { item: (typeof usageMeters)[number] }) {
  const percent = Math.min(100, Math.round((item.used / item.limit) * 100));
  return (
    <div className="rounded-lg border border-slate-200 bg-mist p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-ink">{item.label}</p>
        <span className="text-xs font-semibold text-legal-700">{percent}%</span>
      </div>
      <div className="mt-3 h-3 rounded-full bg-white">
        <div className="h-3 rounded-full bg-legal-700" style={{ width: `${Math.max(4, percent)}%` }} />
      </div>
      <p className="mt-2 text-xs text-slate-500">{item.used} de {item.limit}</p>
    </div>
  );
}

export function UpgradePrompt() {
  return (
    <Card className="border-sky-100 bg-sky-50">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <PanelTitle icon={<Zap size={18} />} title="Upgrade recomendado" />
          <p className="mt-2 text-sm leading-6 text-slate-600">API access y dominio propio requieren ENTERPRISE. IA y branding ya estan activos en el plan AI.</p>
        </div>
        <Button>
          Evaluar Enterprise
          <ArrowRight size={15} />
        </Button>
      </div>
    </Card>
  );
}

export function OnboardingWizard() {
  return (
    <section className="grid gap-4 lg:grid-cols-4">
      {onboardingSteps.map((step, index) => (
        <Card key={step.title}>
          <span className="grid h-9 w-9 place-items-center rounded-md bg-legal-900 text-sm font-semibold text-white">{index + 1}</span>
          <h2 className="mt-4 text-lg font-semibold text-ink">{step.title}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">{step.body}</p>
        </Card>
      ))}
    </section>
  );
}

function BillingSettings() {
  return (
    <>
      <SubscriptionStatusCard />
      <section className="grid gap-5 lg:grid-cols-[1fr_0.8fr]">
        <Card>
          <PanelTitle icon={<ShieldCheck size={18} />} title="Mock billing provider" />
          <div className="mt-4 grid gap-3">
            {["subscribe_mock", "change_plan", "invoice.created", "invoice.payment_succeeded"].map((item) => (
              <div className="rounded-lg border border-slate-200 bg-mist p-4 text-sm font-semibold text-ink" key={item}>{item}</div>
            ))}
          </div>
        </Card>
        <UpgradePrompt />
      </section>
    </>
  );
}

function UsageDashboard() {
  return (
    <>
      <SubscriptionStatusCard />
      <Card>
        <PanelTitle icon={<Gauge size={18} />} title="Medicion de uso" />
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {usageMeters.map((item) => (
            <UsageMeter item={item} key={item.feature} />
          ))}
        </div>
      </Card>
    </>
  );
}

function FeatureGateCenter() {
  return (
    <>
      <UpgradePrompt />
      <Card>
        <PanelTitle icon={<KeyRound size={18} />} title="Feature gates activos" />
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {Object.entries(featureLabels).map(([key, label]) => {
            const included = billingPlans.find((item) => item.code === currentSubscription.plan)?.features.includes(key);
            return (
              <div className="rounded-lg border border-slate-200 bg-mist p-4" key={key}>
                <p className="text-sm font-semibold text-ink">{label}</p>
                <p className={`mt-2 text-xs font-semibold ${included ? "text-emerald-700" : "text-rose-700"}`}>{included ? "Activo" : "Upgrade requerido"}</p>
              </div>
            );
          })}
        </div>
      </Card>
    </>
  );
}

function PanelTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
      {icon}
      <span>{title}</span>
    </div>
  );
}
