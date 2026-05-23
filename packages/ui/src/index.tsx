import type { ReactNode } from "react";
import React from "react";

type Tone = "primary" | "secondary" | "ghost";

function toneClass(tone: Tone) {
  if (tone === "primary") return "bg-legal-900 text-white hover:bg-legal-700";
  if (tone === "secondary") return "border border-slate-200 bg-white text-ink hover:border-legal-100 hover:bg-legal-50";
  return "text-slate-600 hover:bg-slate-100";
}

export function Button({
  children,
  tone = "primary",
  type = "button"
}: {
  children: ReactNode;
  tone?: Tone;
  type?: "button" | "submit";
}) {
  return (
    <button
      className={`inline-flex h-10 items-center justify-center gap-2 rounded-md px-4 text-sm font-semibold transition ${toneClass(tone)}`}
      type={type}
    >
      {children}
    </button>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`min-w-0 rounded-lg border border-white/80 bg-white p-5 shadow-soft ${className}`}>{children}</section>;
}

export function Badge({ children }: { children: ReactNode }) {
  return <span className="inline-flex rounded-md bg-legal-50 px-2.5 py-1 text-xs font-semibold text-legal-700">{children}</span>;
}

export function Input({ label, placeholder, type = "text" }: { label: string; placeholder?: string; type?: string }) {
  return (
    <label className="grid gap-2 text-sm font-semibold text-ink">
      {label}
      <input
        className="h-11 rounded-md border border-slate-200 bg-white px-3 text-sm font-normal text-ink outline-none transition placeholder:text-slate-400 focus:border-legal-500 focus:shadow-[0_0_0_3px_rgba(36,153,232,0.18)]"
        placeholder={placeholder}
        type={type}
      />
    </label>
  );
}

export function Modal({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-soft">
      <h2 className="text-lg font-semibold text-ink">{title}</h2>
      <div className="mt-3 text-sm text-slate-600">{children}</div>
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-mist p-6 text-center">
      <h3 className="text-base font-semibold text-ink">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-600">{description}</p>
    </div>
  );
}

export function PageHeader({ eyebrow, title, description }: { eyebrow: string; title: string; description: string }) {
  return (
    <header className="flex flex-col gap-2">
      <p className="text-sm font-semibold text-legal-700">{eyebrow}</p>
      <h1 className="text-3xl font-semibold tracking-normal text-ink sm:text-4xl">{title}</h1>
      <p className="max-w-3xl text-base leading-7 text-slate-600">{description}</p>
    </header>
  );
}

export function MetricCard({ label, value, trend }: { label: string; value: string; trend: string }) {
  return (
    <article className="rounded-lg border border-slate-200 bg-mist p-4">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-ink">{value}</p>
      <p className="mt-1 text-xs font-medium text-legal-700">{trend}</p>
    </article>
  );
}
