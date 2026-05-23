import { Badge, Button, Card, Input, MetricCard } from "@lexflow/ui";
import { Bell, FileText, Mail, MessageCircle, Send, Smartphone, Workflow } from "lucide-react";
import React from "react";
import { communicationMetrics, communicationThreads, messageTemplates, notificationRules } from "@/lib/communication-demo";

export function CommunicationCenter() {
  return (
    <div className="grid gap-5">
      <header className="rounded-lg border border-white/80 bg-white p-5 shadow-soft">
        <div className="flex flex-wrap items-center gap-2">
          <Badge>P7</Badge>
          <Badge>WhatsApp mock</Badge>
          <Badge>email preparado</Badge>
        </div>
        <h1 className="mt-4 text-3xl font-semibold tracking-normal text-ink sm:text-4xl">Comunicacion multicanal</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Portal, email preparado, WhatsApp Business preparado, recordatorios, solicitudes de documentos, avisos de audiencia e historial auditable.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-4">
        {communicationMetrics.map((item) => (
          <MetricCard key={item.label} label={item.label} value={item.value} trend={item.trend} />
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <ThreadsPanel />
        <ComposerPanel />
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <TemplatesPanel />
        <RulesPanel />
      </section>
    </div>
  );
}

function ThreadsPanel() {
  return (
    <Card>
      <PanelTitle icon={<MessageCircle size={18} />} title="Historial por expediente" />
      <div className="mt-4 grid gap-3">
        {communicationThreads.map((thread) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={thread.id}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-ink">{thread.subject}</p>
              <Badge>{thread.channel}</Badge>
            </div>
            <div className="mt-3 grid gap-2">
              {thread.messages.map((message) => (
                <div className="rounded-md border border-slate-200 bg-white p-3" key={message.id}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-xs font-semibold uppercase text-legal-700">{message.channel} / {message.direction}</p>
                    <span className="text-xs font-semibold text-slate-500">{message.status}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{message.body}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ComposerPanel() {
  return (
    <Card>
      <PanelTitle icon={<Send size={18} />} title="Enviar comunicacion" />
      <div className="mt-4 grid gap-4">
        <Input label="Canal" placeholder="whatsapp / portal / email" />
        <Input label="Plantilla" placeholder="audiencia_proxima" />
        <Input label="Mensaje" placeholder="Recordatorio de audiencia para Nova Capital" />
        <div className="flex flex-wrap gap-2">
          <Button>Enviar WhatsApp mock</Button>
          <Button tone="secondary">Probar plantilla</Button>
        </div>
      </div>
    </Card>
  );
}

function TemplatesPanel() {
  return (
    <Card>
      <PanelTitle icon={<FileText size={18} />} title="Plantillas" />
      <div className="mt-4 grid gap-3">
        {messageTemplates.map((template) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={template.code}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-ink">{template.name}</p>
              <Badge>{template.channel}</Badge>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{template.body}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function RulesPanel() {
  return (
    <Card>
      <PanelTitle icon={<Workflow size={18} />} title="Reglas de notificacion" />
      <div className="mt-4 grid gap-3">
        {notificationRules.map((rule) => (
          <div className="rounded-lg border border-slate-200 bg-mist p-4" key={rule.id}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-ink">{rule.name}</p>
              <Badge>{rule.status}</Badge>
            </div>
            <p className="mt-2 text-sm text-slate-600">{rule.event_type}</p>
            <p className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-legal-700">
              {rule.channel === "whatsapp" ? <Smartphone size={14} /> : rule.channel === "email" ? <Mail size={14} /> : <Bell size={14} />}
              {rule.channel}
            </p>
          </div>
        ))}
      </div>
    </Card>
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
