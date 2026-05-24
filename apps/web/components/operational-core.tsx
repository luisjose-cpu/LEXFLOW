"use client";

import { Badge, Card, EmptyState, MetricCard, PageHeader } from "@lexflow/ui";
import {
  AlertTriangle,
  Brain,
  BriefcaseBusiness,
  CalendarClock,
  FileText,
  History,
  MessageCircle,
  Search,
  ShieldCheck,
  Sparkles,
  Tag,
  Workflow
} from "lucide-react";
import Link from "next/link";
import React, { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import { hasCloudSession, searchOperational } from "@/lib/lexflow-api";
import {
  CaseOps,
  ClientOps,
  SearchResult,
  casesForClient,
  casesOps,
  clientsOps,
  communicationOps,
  documentsOps,
  hearingsOps,
  searchResultsOps,
  timelineOps
} from "@/lib/operational-demo";

export function SearchGlobalBar({ compact = false }: { compact?: boolean }) {
  const [query, setQuery] = useState("");
  const [recent, setRecent] = useState(["Nova Capital", "SINOE", "audiencia"]);
  const [favorites, setFavorites] = useState(["Cobro ejecutivo Nova"]);
  const [liveResults, setLiveResults] = useState<SearchResult[] | null>(null);
  const [searchState, setSearchState] = useState<"demo" | "loading" | "live" | "fallback">("demo");
  const demoResults = useMemo(() => filterResults(query), [query]);
  const results = liveResults ?? demoResults;

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedRecent = localStorage.getItem("lexflow.search.recent");
    const storedFavorites = localStorage.getItem("lexflow.search.favorites");
    if (storedRecent) setRecent(JSON.parse(storedRecent) as string[]);
    if (storedFavorites) setFavorites(JSON.parse(storedFavorites) as string[]);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem("lexflow.search.recent", JSON.stringify(recent.slice(0, 5)));
  }, [recent]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem("lexflow.search.favorites", JSON.stringify(favorites.slice(0, 5)));
  }, [favorites]);

  useEffect(() => {
    const clean = query.trim();
    if (clean.length < 2 || !hasCloudSession()) {
      setLiveResults(null);
      setSearchState("demo");
      return;
    }

    let active = true;
    const timeout = window.setTimeout(async () => {
      setSearchState("loading");
      try {
        const payload = await searchOperational(clean);
        if (!active) return;
        setLiveResults(payload.results);
        setSearchState("live");
        if (payload.recent.length) setRecent((current) => mergeUnique([...payload.recent, ...current], 5));
        if (payload.favorites.length) setFavorites((current) => mergeUnique([...payload.favorites, ...current], 5));
      } catch {
        if (!active) return;
        setLiveResults(null);
        setSearchState("fallback");
      }
    }, 260);

    return () => {
      active = false;
      window.clearTimeout(timeout);
    };
  }, [query]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const clean = query.trim();
    if (clean && !recent.includes(clean)) setRecent([clean, ...recent].slice(0, 5));
  }

  return (
    <Card className={compact ? "p-4" : ""}>
      <form className="flex flex-col gap-3 lg:flex-row lg:items-center" onSubmit={submit}>
        <label className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-3 text-slate-400" size={18} aria-hidden="true" />
          <input
            className="h-11 w-full rounded-md border border-slate-200 bg-white pl-10 pr-3 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-legal-500 focus:shadow-[0_0_0_3px_rgba(36,153,232,0.18)]"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Buscar cliente, expediente, DNI, RUC, correo, responsable, documento, audiencia, SINOE..."
            value={query}
          />
        </label>
        <button className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white hover:bg-legal-700" type="submit">
          <Sparkles size={16} aria-hidden="true" />
          Buscar
        </button>
      </form>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs font-medium text-slate-500">
        <span>{searchState === "live" ? "Conectado a API cloud" : searchState === "loading" ? "Consultando Legal OS..." : "Modo demo con fallback seguro"}</span>
        {searchState === "fallback" ? <span className="text-amber-700">API no disponible, mostrando datos demo.</span> : null}
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {mergeUnique([...recent, ...favorites], 8).map((item) => (
          <button className="rounded-md border border-slate-200 bg-mist px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-legal-50" key={item} onClick={() => setQuery(item)} type="button">
            {item}
          </button>
        ))}
      </div>
      {query ? (
        <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_0.8fr]">
          <div className="grid gap-2">
            <p className="text-xs font-semibold uppercase tracking-normal text-slate-500">Resultado rapido</p>
            {results.slice(0, 4).map((result) => (
              <SearchResultRow key={`${result.type}-${result.id}`} result={result} onFavorite={() => setFavorites([result.title, ...favorites.filter((item) => item !== result.title)].slice(0, 5))} />
            ))}
            {!results.length ? <EmptyState title="Sin resultados" description="Prueba con cliente, expediente, documento, audiencia o SINOE." /> : null}
          </div>
          <div className="rounded-lg border border-slate-200 bg-mist p-4">
            <p className="text-xs font-semibold uppercase tracking-normal text-slate-500">Resultado avanzado</p>
            <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
              {["cliente", "expediente", "documento", "audiencia", "sinoe", "noticia"].map((type) => (
                <div className="rounded-md bg-white px-3 py-2" key={type}>
                  <span className="font-semibold text-ink">{results.filter((result) => result.type === type).length}</span>
                  <span className="ml-2 text-slate-500">{type}</span>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-500">Preparado para busqueda IA futura con fuentes y permisos por tenant.</p>
          </div>
        </div>
      ) : null}
    </Card>
  );
}

function mergeUnique(items: string[], limit: number) {
  return Array.from(new Set(items.filter(Boolean))).slice(0, limit);
}

export function ClientList({ clients = clientsOps }: { clients?: ClientOps[] }) {
  return (
    <div className="grid gap-4">
      {clients.map((client) => (
        <ClientCard key={client.id} client={client} />
      ))}
    </div>
  );
}

export function ClientSearch() {
  return <SearchGlobalBar compact />;
}

export function ClientCard({ client }: { client: ClientOps }) {
  return (
    <Card>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{client.sector}</Badge>
            <RiskPill risk={client.risk} />
          </div>
          <Link className="mt-3 block text-xl font-semibold text-ink hover:text-legal-700" href={`/clients/${client.id}`}>
            {client.name}
          </Link>
          <p className="mt-1 text-sm text-slate-600">{client.businessName} · RUC {client.ruc}</p>
          <p className="mt-2 text-sm text-slate-500">{client.email} · {client.phone}</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-3 lg:min-w-[390px]">
          {client.metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}
        </div>
      </div>
    </Card>
  );
}

export function ClientDetail({ client }: { client: ClientOps }) {
  const relatedCases = casesForClient(client.id);
  return (
    <div className="grid gap-5">
      <PageHeader description={`${client.businessName} · ${client.mainMatter} · ${client.email}`} eyebrow="Cliente 360" title={client.name} />
      <SearchGlobalBar compact />
      <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="grid gap-5">
          <ClientMetrics client={client} />
          <ClientCasesGrid cases={relatedCases} />
          <ClientTimeline />
          <ClientDocuments />
          <ClientCommunications />
        </div>
        <div className="grid gap-5">
          <ClientRiskPanel client={client} />
          <ClientTags tags={client.tags} />
          <ClientNotes notes={client.notes} />
          <ClientInfo client={client} />
        </div>
      </section>
    </div>
  );
}

export function ClientEditForm({ client }: { client?: ClientOps }) {
  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <ShieldCheck size={18} aria-hidden="true" />
        <span>{client ? "Editar cliente" : "Registro cliente"}</span>
      </div>
      <form className="mt-5 grid gap-4">
        <Field label="Nombre / razon social" value={client?.businessName ?? ""} placeholder="Nova Capital S.A.C." />
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="DNI" value={client?.dni ?? ""} placeholder="Documento identidad" />
          <Field label="RUC" value={client?.ruc ?? ""} placeholder="RUC" />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Correo" value={client?.email ?? ""} placeholder="legal@cliente.com" />
          <Field label="Telefono" value={client?.phone ?? ""} placeholder="+51..." />
        </div>
        <Field label="Direccion" value={client?.address ?? ""} placeholder="Direccion principal" />
        <button className="h-10 w-fit rounded-md bg-legal-900 px-4 text-sm font-semibold text-white" type="button">Guardar cliente</button>
      </form>
    </Card>
  );
}

export function ClientOnboardingWizard() {
  const steps = ["Datos basicos", "Contactos", "Empresa", "Documentos", "Expedientes iniciales", "Configuracion portal", "Alertas", "Automatizacion"];
  return (
    <div className="grid gap-5">
      <PageHeader description="Wizard mobile-first para registrar cliente, expediente inicial, portal, alertas y automatizacion opcional." eyebrow="Clientes" title="Nuevo cliente" />
      <Card>
        <div className="grid gap-3 md:grid-cols-4">
          {steps.map((step, index) => (
            <div className="rounded-lg border border-slate-200 bg-mist p-4" key={step}>
              <span className="grid h-8 w-8 place-items-center rounded-md bg-white text-sm font-semibold text-legal-900">{index + 1}</span>
              <p className="mt-3 text-sm font-semibold text-ink">{step}</p>
            </div>
          ))}
        </div>
      </Card>
      <ClientEditForm />
    </div>
  );
}

export function ClientDocuments() {
  return <ResourcePanel icon={<FileText size={18} />} title="Documentos del cliente" items={documentsOps.map((doc) => `${doc.name} · ${doc.status} · ${doc.ai}`)} />;
}

export function ClientCasesGrid({ cases }: { cases: CaseOps[] }) {
  return (
    <Card>
      <PanelTitle icon={<BriefcaseBusiness size={18} />} title="Expedientes" />
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {cases.map((legalCase) => <CaseCard key={legalCase.id} legalCase={legalCase} />)}
      </div>
    </Card>
  );
}

export function ClientTimeline() {
  return <ResourcePanel icon={<History size={18} />} title="Timeline cliente" items={timelineOps.map((item) => `${item.title} · ${item.description}`)} />;
}

export function ClientTags({ tags }: { tags: string[] }) {
  return (
    <Card>
      <PanelTitle icon={<Tag size={18} />} title="Etiquetas" />
      <div className="mt-4 flex flex-wrap gap-2">{tags.map((tag) => <Badge key={tag}>{tag}</Badge>)}</div>
    </Card>
  );
}

export function ClientRiskPanel({ client }: { client: ClientOps }) {
  return (
    <Card>
      <PanelTitle icon={<AlertTriangle size={18} />} title="Riesgo" />
      <p className="mt-4 text-3xl font-semibold text-ink">{client.risk}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">Prioridad {client.priority}. Recomendacion: revisar plazos, SINOE y pendientes criticos.</p>
    </Card>
  );
}

export function ClientNotes({ notes }: { notes: string[] }) {
  return <ResourcePanel icon={<History size={18} />} title="Notas" items={notes} />;
}

export function ClientCommunications() {
  return <ResourcePanel icon={<MessageCircle size={18} />} title="Comunicaciones" items={communicationOps.map((item) => `${item.channel} · ${item.direction}: ${item.body}`)} />;
}

export function ClientMetrics({ client }: { client: ClientOps }) {
  return <div className="grid gap-3 md:grid-cols-3">{client.metrics.map((metric) => <MetricCard key={metric.label} {...metric} />)}</div>;
}

export function ClientInfo({ client }: { client: ClientOps }) {
  return (
    <Card>
      <PanelTitle icon={<ShieldCheck size={18} />} title="Informacion general" />
      <div className="mt-4 grid gap-2 text-sm">
        <InfoRow label="RUC" value={client.ruc} />
        <InfoRow label="Direccion" value={client.address} />
        <InfoRow label="Representantes" value={client.representatives.join(", ")} />
        <InfoRow label="Contactos" value={client.contacts.join(", ")} />
      </div>
    </Card>
  );
}

export function CaseList({ cases = casesOps }: { cases?: CaseOps[] }) {
  return <div className="grid gap-4">{cases.map((legalCase) => <CaseCard key={legalCase.id} legalCase={legalCase} />)}</div>;
}

export function CaseCard({ legalCase }: { legalCase: CaseOps }) {
  return (
    <Card>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge>{legalCase.matter}</Badge>
            <RiskPill risk={legalCase.risk} />
            {legalCase.captchaPending ? <span className="rounded-md bg-rose-50 px-2.5 py-1 text-xs font-semibold text-rose-700">CAPTCHA</span> : null}
          </div>
          <Link className="mt-3 block text-lg font-semibold text-ink hover:text-legal-700" href={`/cases/${legalCase.id}`}>
            {legalCase.title}
          </Link>
          <p className="mt-1 text-sm text-slate-600">{legalCase.clientName} · {legalCase.externalNumber}</p>
          <p className="mt-2 text-sm text-slate-500">{legalCase.court} · {legalCase.responsible}</p>
        </div>
        <div className="min-w-[220px] rounded-lg border border-slate-200 bg-mist p-3">
          <p className="text-xs font-semibold text-slate-500">Proxima accion</p>
          <p className="mt-2 text-sm font-semibold leading-5 text-ink">{legalCase.nextAction}</p>
          <p className="mt-2 text-xs text-legal-700">Plazo: {legalCase.criticalDeadline}</p>
        </div>
      </div>
    </Card>
  );
}

export function CasesDashboard() {
  return (
    <div className="grid gap-5">
      <PageHeader description="Expedientes con materia, responsable, juzgado, SINOE, documentos, audiencias, IA y automatizaciones." eyebrow="Expedientes" title="Centro de expedientes" />
      <SearchGlobalBar compact />
      <div className="grid gap-3 md:grid-cols-4">
        <MetricCard label="Activos" value="12" trend="+3 esta semana" />
        <MetricCard label="Criticos" value="4" trend="incluye CAPTCHA" />
        <MetricCard label="Audiencias" value="7" trend="30 dias" />
        <MetricCard label="SINOE" value="91%" trend="fuentes conectadas" />
      </div>
      <CaseList />
    </div>
  );
}

export function CaseCreateWizard() {
  const steps = ["Cliente", "Materia", "Equipo", "SINOE", "Documentos", "Audiencias", "Portal", "Automation"];
  return (
    <div className="grid gap-5">
      <PageHeader description="Alta guiada de expediente conectado a cliente, documentos, audiencias, SINOE, IA, portal y automatizaciones." eyebrow="Expedientes" title="Nuevo expediente" />
      <Card>
        <div className="grid gap-3 md:grid-cols-4">
          {steps.map((step, index) => (
            <div className="rounded-lg border border-slate-200 bg-mist p-4" key={step}>
              <span className="grid h-8 w-8 place-items-center rounded-md bg-white text-sm font-semibold text-legal-900">{index + 1}</span>
              <p className="mt-3 text-sm font-semibold text-ink">{step}</p>
            </div>
          ))}
        </div>
      </Card>
      <CaseEditForm />
    </div>
  );
}

export function CaseEditForm({ legalCase }: { legalCase?: CaseOps }) {
  return (
    <Card>
      <PanelTitle icon={<BriefcaseBusiness size={18} />} title={legalCase ? "Editar expediente" : "Datos del expediente"} />
      <form className="mt-5 grid gap-4">
        <Field label="Titulo" value={legalCase?.title ?? ""} placeholder="Nombre operativo del expediente" />
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Materia" value={legalCase?.matter ?? ""} placeholder="Civil, laboral, comercial..." />
          <Field label="Submateria" value={legalCase?.submatter ?? ""} placeholder="Cobro ejecutivo..." />
        </div>
        <Field label="Numero expediente" value={legalCase?.externalNumber ?? ""} placeholder="Numero externo" />
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Responsable" value={legalCase?.responsible ?? ""} placeholder="Abogado responsable" />
          <Field label="Juzgado" value={legalCase?.court ?? ""} placeholder="Juzgado / sede" />
        </div>
        <button className="h-10 w-fit rounded-md bg-legal-900 px-4 text-sm font-semibold text-white" type="button">Guardar expediente</button>
      </form>
    </Card>
  );
}

export function CaseResourcePage({ legalCase, type }: { legalCase: CaseOps; type: "documents" | "hearings" | "communications" | "judicial" | "automation" | "intelligence" }) {
  const map = {
    documents: { title: "Documentos", icon: <FileText size={18} />, items: documentsOps.map((item) => `${item.name} · ${item.type} · ${item.status} · ${item.ai}`) },
    hearings: { title: "Audiencias", icon: <CalendarClock size={18} />, items: hearingsOps.map((item) => `${item.title} · ${item.date} · ${item.type} · ${item.responsible}`) },
    communications: { title: "Comunicaciones", icon: <MessageCircle size={18} />, items: communicationOps.map((item) => `${item.channel} · ${item.direction}: ${item.body}`) },
    judicial: { title: "Actualizaciones judiciales SINOE", icon: <ShieldCheck size={18} />, items: [`Estado SINOE: ${legalCase.sinoeStatus}`, `Ultima sincronizacion: ${legalCase.lastSinoeUpdate}`, `CAPTCHA pendiente: ${legalCase.captchaPending ? "si" : "no"}`, "Hash y evidencia gestionados por SINOE Module"] },
    automation: { title: "Automatizaciones", icon: <Workflow size={18} />, items: ["HEARING_UPCOMING -> recordatorio", "DOCUMENT_UPLOADED -> IA resumen mock", "CAPTCHA_REQUIRED -> alerta interna"] },
    intelligence: { title: "Inteligencia juridica", icon: <Brain size={18} />, items: ["Noticias vinculadas", "Tendencias procesales", "Graph legal futuro", "Decision snapshot"] }
  }[type];
  return (
    <div className="grid gap-5">
      <PageHeader description={`${legalCase.title} · ${legalCase.clientName}`} eyebrow="Expediente 360" title={map.title} />
      <SearchGlobalBar compact />
      <ResourcePanel icon={map.icon} title={map.title} items={map.items} />
    </div>
  );
}

function SearchResultRow({ result, onFavorite }: { result: SearchResult; onFavorite: () => void }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-lg border border-slate-200 bg-mist p-3">
      <Link className="min-w-0" href={result.href}>
        <p className="text-sm font-semibold text-ink">{result.title}</p>
        <p className="mt-1 text-xs text-slate-500">{result.type} · {result.subtitle}</p>
      </Link>
      <button className="rounded-md bg-white px-2 py-1 text-xs font-semibold text-legal-700" onClick={onFavorite} type="button">Favorito</button>
    </div>
  );
}

function ResourcePanel({ icon, title, items }: { icon: ReactNode; title: string; items: string[] }) {
  return (
    <Card>
      <PanelTitle icon={icon} title={title} />
      <div className="mt-4 grid gap-3">
        {items.map((item) => <div className="rounded-lg border border-slate-200 bg-mist p-3 text-sm font-medium leading-6 text-ink" key={item}>{item}</div>)}
      </div>
    </Card>
  );
}

function PanelTitle({ icon, title }: { icon: ReactNode; title: string }) {
  return <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">{icon}<span>{title}</span></div>;
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-3 rounded-md bg-mist px-3 py-2"><span className="text-slate-500">{label}</span><span className="text-right font-semibold text-ink">{value}</span></div>;
}

function RiskPill({ risk }: { risk: string }) {
  const tone = risk === "alto" ? "bg-rose-50 text-rose-700" : risk === "medio" ? "bg-amber-50 text-amber-700" : "bg-legal-50 text-legal-700";
  return <span className={`rounded-md px-2.5 py-1 text-xs font-semibold ${tone}`}>Riesgo {risk}</span>;
}

function Field({ label, value, placeholder }: { label: string; value: string; placeholder: string }) {
  const [current, setCurrent] = useState(value);
  return (
    <label className="grid gap-2 text-sm font-semibold text-ink">
      {label}
      <input className="h-11 rounded-md border border-slate-200 bg-white px-3 text-sm font-normal text-ink outline-none transition placeholder:text-slate-400 focus:border-legal-500 focus:shadow-[0_0_0_3px_rgba(36,153,232,0.18)]" onChange={(event) => setCurrent(event.target.value)} placeholder={placeholder} value={current} />
    </label>
  );
}

function filterResults(query: string) {
  const needle = query.trim().toLowerCase();
  if (!needle) return [];
  return searchResultsOps.filter((result) => [result.title, result.subtitle, ...result.tags].some((value) => value.toLowerCase().includes(needle)));
}
