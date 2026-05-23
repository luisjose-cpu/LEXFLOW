"use client";

import React from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  Bot,
  BriefcaseBusiness,
  CheckCircle2,
  FileText,
  Gauge,
  MessageCircle,
  ShieldCheck,
  Sparkles,
  WalletCards,
  Workflow
} from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const pipeline = [
  "Cliente",
  "Expediente",
  "Documento",
  "Comunicacion",
  "Automatizacion",
  "IA",
  "Inteligencia",
  "Decision"
];

const modules = [
  { name: "Expediente 360", icon: BriefcaseBusiness, value: "482", detail: "asuntos activos" },
  { name: "Portal Cliente", icon: ShieldCheck, value: "91%", detail: "clientes con acceso" },
  { name: "WhatsApp Business", icon: MessageCircle, value: "1.248", detail: "mensajes auditados" },
  { name: "IA practica legal", icon: Bot, value: "318", detail: "insights generados" },
  { name: "Automation Studio", icon: Workflow, value: "42", detail: "flujos autorizados" },
  { name: "Billing SaaS", icon: WalletCards, value: "98%", detail: "cobranza al dia" }
];

const intelligence = [
  { day: "Lun", matters: 22, risk: 6 },
  { day: "Mar", matters: 28, risk: 8 },
  { day: "Mie", matters: 31, risk: 7 },
  { day: "Jue", matters: 37, risk: 11 },
  { day: "Vie", matters: 44, risk: 9 },
  { day: "Sab", matters: 34, risk: 5 },
  { day: "Dom", matters: 38, risk: 4 }
];

const matters = [
  {
    client: "Nova Capital",
    matter: "Cobro ejecutivo",
    status: "Audiencia en 6 dias",
    risk: "Medio",
    next: "Preparar memorial y anexos"
  },
  {
    client: "Andes Health",
    matter: "Laboral colectivo",
    status: "Documento pendiente",
    risk: "Alto",
    next: "Clasificar pruebas recibidas"
  },
  {
    client: "Mercurio Retail",
    matter: "Contrato marco",
    status: "Revision IA lista",
    risk: "Bajo",
    next: "Enviar resumen al cliente"
  }
];

const commandCenter = [
  { label: "Vencimientos criticos", value: "12", trend: "+3 esta semana" },
  { label: "Documentos por clasificar", value: "86", trend: "OCR en cola" },
  { label: "Automatizaciones exitosas", value: "97.4%", trend: "ultimos 30 dias" }
];

export default function Home() {
  return (
    <main className="min-h-screen">
      <section className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between rounded-lg border border-white/80 bg-white/84 px-4 py-3 shadow-soft backdrop-blur sm:px-5">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-md bg-legal-900 text-white">
              <Sparkles size={20} aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold text-legal-900">LEXFLOW</p>
              <p className="text-xs text-slate-500">The Legal Operating System</p>
            </div>
          </div>
          <Link className="inline-flex h-10 items-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-legal-700" href="/dashboard/command-center">
            <Gauge size={16} aria-hidden="true" />
            Command Center
          </Link>
        </header>

        <section className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="flex min-h-[460px] flex-col justify-between rounded-lg border border-white/80 bg-white p-5 shadow-soft sm:p-7">
            <div className="max-w-2xl">
              <p className="mb-4 inline-flex rounded-md bg-legal-50 px-3 py-2 text-sm font-semibold text-legal-700">
                Multiestudio, multitenant, cloud-ready
              </p>
              <h1 className="text-4xl font-semibold tracking-normal text-ink sm:text-5xl">
                El sistema operativo legal para estudios que ya no pueden vivir en Excel.
              </h1>
              <p className="mt-5 max-w-xl text-base leading-7 text-slate-600 sm:text-lg">
                LEXFLOW conecta expediente, documentos, comunicaciones, automatizacion autorizada,
                IA practica e inteligencia gerencial en una sola cadena operativa.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link className="inline-flex h-10 items-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white transition hover:bg-legal-700" href="/lexflow-os">
                  <Sparkles size={16} aria-hidden="true" />
                  Ver LEXFLOW OS
                </Link>
                <Link className="inline-flex h-10 items-center gap-2 rounded-md border border-slate-200 bg-white px-4 text-sm font-semibold text-ink transition hover:border-legal-100 hover:bg-legal-50" href="/demo">
                  <Workflow size={16} aria-hidden="true" />
                  Demo Mode
                </Link>
              </div>
            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              {commandCenter.map((item) => (
                <div key={item.label} className="rounded-lg border border-slate-200 bg-mist p-4">
                  <p className="text-sm text-slate-500">{item.label}</p>
                  <p className="mt-2 text-3xl font-semibold text-ink">{item.value}</p>
                  <p className="mt-1 text-xs font-medium text-legal-700">{item.trend}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-white/80 bg-white p-5 shadow-soft sm:p-6">
            <div className="mb-5 flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-legal-700">Centro de Inteligencia Juridica</p>
                <h2 className="mt-1 text-2xl font-semibold text-ink">Carga y riesgo operativo</h2>
              </div>
              <Activity className="text-legal-500" aria-hidden="true" />
            </div>
            <div className="h-64 min-h-64 w-full min-w-0">
              <ResponsiveContainer width="100%" height="100%" minWidth={280} minHeight={240}>
                <AreaChart data={intelligence}>
                  <defs>
                    <linearGradient id="matters" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="5%" stopColor="#2499e8" stopOpacity={0.32} />
                      <stop offset="95%" stopColor="#2499e8" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: "#64748b", fontSize: 12 }} />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{ borderRadius: 8, border: "1px solid #d9e5ef", boxShadow: "0 12px 36px rgba(16,32,51,.08)" }}
                  />
                  <Area type="monotone" dataKey="matters" stroke="#1264a3" strokeWidth={3} fill="url(#matters)" />
                  <Area type="monotone" dataKey="risk" stroke="#38bdf8" strokeWidth={2} fill="transparent" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-5 space-y-3">
              {matters.map((matter) => (
                <div key={`${matter.client}-${matter.matter}`} className="rounded-lg border border-slate-200 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-ink">{matter.client}</p>
                      <p className="text-sm text-slate-500">{matter.matter}</p>
                    </div>
                    <span className="rounded-md bg-legal-50 px-2.5 py-1 text-xs font-semibold text-legal-700">
                      {matter.risk}
                    </span>
                  </div>
                  <div className="mt-3 flex flex-col gap-2 text-sm text-slate-600 sm:flex-row sm:items-center sm:justify-between">
                    <span>{matter.status}</span>
                    <span className="font-medium text-ink">{matter.next}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-lg border border-white/80 bg-white p-5 shadow-soft sm:p-6">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <p className="text-sm font-semibold text-legal-700">Flujo operacional</p>
              <h2 className="mt-1 text-2xl font-semibold text-ink">Del cliente a la decision</h2>
            </div>
            <div className="inline-flex items-center gap-2 text-sm font-semibold text-legal-700">
              Auditoria activa
              <CheckCircle2 size={16} aria-hidden="true" />
            </div>
          </div>
          <div className="mt-6 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            {pipeline.map((step, index) => (
              <div key={step} className="flex min-h-28 flex-col justify-between rounded-lg border border-slate-200 bg-mist p-3">
                <div className="flex items-center justify-between">
                  <span className="grid h-8 w-8 place-items-center rounded-md bg-white text-sm font-semibold text-legal-900">
                    {index + 1}
                  </span>
                  {index < pipeline.length - 1 ? <ArrowRight size={16} className="text-slate-400" aria-hidden="true" /> : null}
                </div>
                <p className="text-sm font-semibold text-ink">{step}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {modules.map((module) => {
            const Icon = module.icon;
            return (
              <article key={module.name} className="rounded-lg border border-white/80 bg-white p-5 shadow-soft">
                <div className="flex items-center justify-between">
                  <div className="grid h-11 w-11 place-items-center rounded-md bg-legal-50 text-legal-700">
                    <Icon size={20} aria-hidden="true" />
                  </div>
                  <FileText size={18} className="text-slate-300" aria-hidden="true" />
                </div>
                <h3 className="mt-5 text-lg font-semibold text-ink">{module.name}</h3>
                <p className="mt-3 text-3xl font-semibold text-legal-900">{module.value}</p>
                <p className="mt-1 text-sm text-slate-500">{module.detail}</p>
              </article>
            );
          })}
        </section>
      </section>
    </main>
  );
}
