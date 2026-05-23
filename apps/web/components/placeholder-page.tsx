"use client";

import { Badge, Card, EmptyState, MetricCard, PageHeader } from "@lexflow/ui";
import { p1Metrics, productSpine } from "@lexflow/shared";
import { motion } from "framer-motion";
import { ArrowRight, ShieldCheck } from "lucide-react";

export interface PlaceholderPageProps {
  eyebrow: string;
  title: string;
  description: string;
  module: string;
  emptyTitle: string;
  emptyDescription: string;
}

export function PlaceholderPage({
  eyebrow,
  title,
  description,
  module,
  emptyTitle,
  emptyDescription
}: PlaceholderPageProps) {
  return (
    <motion.div
      animate={{ opacity: 1, y: 0 }}
      className="grid gap-5"
      initial={{ opacity: 0, y: 10 }}
      transition={{ duration: 0.28, ease: "easeOut" }}
    >
      <Card>
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
          <PageHeader description={description} eyebrow={eyebrow} title={title} />
          <Badge>{module}</Badge>
        </div>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {p1Metrics.map((metric) => (
            <MetricCard key={metric.label} label={metric.label} trend={metric.trend} value={metric.value} />
          ))}
        </div>
      </Card>

      <Card>
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-legal-700">Flujo LEXFLOW OS</p>
            <h2 className="mt-1 text-xl font-semibold text-ink">Cadena operacional conectada</h2>
          </div>
          <ShieldCheck className="text-legal-500" aria-hidden="true" />
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {productSpine.map((step, index) => (
            <div className="flex min-h-24 flex-col justify-between rounded-lg border border-slate-200 bg-mist p-3" key={step}>
              <div className="flex items-center justify-between">
                <span className="grid h-7 w-7 place-items-center rounded-md bg-white text-xs font-semibold text-legal-900">
                  {index + 1}
                </span>
                {index < productSpine.length - 1 ? <ArrowRight size={15} className="text-slate-400" aria-hidden="true" /> : null}
              </div>
              <p className="text-sm font-semibold leading-5 text-ink">{step}</p>
            </div>
          ))}
        </div>
      </Card>

      <EmptyState description={emptyDescription} title={emptyTitle} />
    </motion.div>
  );
}
