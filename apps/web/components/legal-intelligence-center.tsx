"use client";

import { Badge, Button, Card, Input, MetricCard } from "@lexflow/ui";
import { Bell, Bookmark, Filter, Link2, Newspaper, Search, Sparkles, Tags, TrendingUp } from "lucide-react";
import React from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { intelligenceAlerts, intelligenceMetrics, intelligenceNews, intelligenceSources, intelligenceTrends } from "@/lib/legal-intelligence-demo";

export function LegalIntelligenceCenter() {
  return (
    <div className="grid gap-5">
      <header className="rounded-lg border border-white/80 bg-white p-5 shadow-soft">
        <div className="flex flex-wrap gap-2">
          <Badge>P9</Badge>
          <Badge>Adapters mock</Badge>
          <Badge>No scraping agresivo</Badge>
        </div>
        <h1 className="mt-4 text-3xl font-semibold tracking-normal text-ink sm:text-4xl">Centro de Inteligencia Juridica</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Noticias legales, normativa, jurisprudencia, alertas, resumenes IA, favoritos, etiquetas y tendencias conectadas al expediente.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-4">
        {intelligenceMetrics.map((item) => (
          <MetricCard key={item.label} label={item.label} value={item.value} trend={item.trend} />
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <NewsDashboard />
        <AlertPanel />
      </section>

      <section className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <SourcesPanel />
        <TrendChart />
      </section>
    </div>
  );
}

function NewsDashboard() {
  return (
    <Card>
      <PanelTitle icon={<Newspaper size={18} />} title="Noticias y jurisprudencia" />
      <div className="mt-4 grid gap-3 md:grid-cols-[1fr_180px]">
        <Input label="Buscador" placeholder="notificacion, norma, laboral" />
        <label className="grid gap-2 text-sm font-semibold text-ink">
          Filtro
          <select className="h-11 rounded-md border border-slate-200 bg-white px-3 text-sm font-normal text-ink outline-none">
            <option>Todas las fuentes</option>
            <option>Normativa</option>
            <option>Jurisprudencia</option>
          </select>
        </label>
      </div>
      <div className="mt-4 grid gap-3">
        {intelligenceNews.map((item) => (
          <article className="rounded-lg border border-slate-200 bg-mist p-4" key={item.id}>
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{item.source}</Badge>
              <Badge>{item.category}</Badge>
              <span className="rounded-md bg-white px-2.5 py-1 text-xs font-semibold text-legal-700">{item.trend}</span>
            </div>
            <h2 className="mt-3 text-lg font-semibold text-ink">{item.title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.summary}</p>
            <AISummaryBox summary={item.aiSummary} />
            <div className="mt-3 flex flex-wrap gap-2">
              {item.tags.map((tag) => (
                <span className="rounded-md bg-white px-2.5 py-1 text-xs font-semibold text-slate-600" key={tag}>
                  #{tag}
                </span>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <FavoriteButton />
              <LinkToCaseButton caseTitle={item.linkedCase} />
            </div>
          </article>
        ))}
      </div>
    </Card>
  );
}

function AISummaryBox({ summary }: { summary: string }) {
  return (
    <div className="mt-3 rounded-lg border border-legal-100 bg-white p-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <Sparkles size={16} />
        <span>AI Summary</span>
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-600">{summary}</p>
    </div>
  );
}

function FavoriteButton() {
  return (
    <Button tone="secondary">
      <Bookmark size={16} />
      Favorito
    </Button>
  );
}

function LinkToCaseButton({ caseTitle }: { caseTitle: string }) {
  return (
    <Button>
      <Link2 size={16} />
      {caseTitle}
    </Button>
  );
}

function AlertPanel() {
  return (
    <Card>
      <PanelTitle icon={<Bell size={18} />} title="Alertas" />
      <div className="mt-4 grid gap-3">
        {intelligenceAlerts.map((item) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={item.title}>
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-ink">{item.title}</p>
              <span className={`rounded-md px-2.5 py-1 text-xs font-semibold ${item.severity === "high" ? "bg-rose-50 text-rose-700" : "bg-amber-50 text-amber-700"}`}>{item.severity}</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{item.body}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function SourcesPanel() {
  return (
    <Card>
      <PanelTitle icon={<Filter size={18} />} title="Fuentes" />
      <div className="mt-4 grid gap-3">
        {intelligenceSources.map((source) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-3" key={source.name}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-ink">{source.name}</p>
              <Badge>{source.status}</Badge>
            </div>
            <p className="mt-1 text-sm text-slate-600">{source.category} - {source.mode}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function TrendChart() {
  return (
    <Card>
      <PanelTitle icon={<TrendingUp size={18} />} title="Tendencias" />
      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer height="100%" width="100%">
          <BarChart data={intelligenceTrends}>
            <XAxis dataKey="tag" fontSize={12} tickLine={false} />
            <YAxis fontSize={12} tickLine={false} width={28} />
            <Tooltip />
            <Bar dataKey="count" fill="#0a4f8f" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 flex items-center gap-2 text-sm font-semibold text-legal-700">
        <Tags size={16} />
        <span>Etiquetas activas por frecuencia</span>
      </div>
    </Card>
  );
}

function PanelTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
      {icon}
      <span>{title}</span>
      <Search className="ml-auto text-slate-300" size={16} />
    </div>
  );
}
