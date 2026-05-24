"use client";

import { Card } from "@lexflow/ui";
import { AlertTriangle } from "lucide-react";
import React, { useEffect, useState } from "react";
import {
  acknowledgeSecurityAlert,
  hasCloudSession,
  loadSecurityAlertDeliveries,
  loadSecurityAlerts,
  processSecurityAlertDeliveries,
  SecurityAlert,
  SecurityAlertDelivery
} from "@/lib/lexflow-api";

export function SecurityAlerts() {
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);
  const [deliveries, setDeliveries] = useState<SecurityAlertDelivery[]>([]);
  const [state, setState] = useState<"idle" | "loading" | "error" | "success">("idle");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!hasCloudSession()) return;
    setState("loading");
    void Promise.all([loadSecurityAlerts(), loadSecurityAlertDeliveries()])
      .then(([items, deliveryItems]) => {
        setAlerts(items);
        setDeliveries(deliveryItems);
        setState("success");
      })
      .catch(() => {
        setState("error");
        setMessage("No se pudieron cargar alertas de seguridad.");
      });
  }, []);

  async function acknowledge(alertId: string) {
    setMessage("");
    try {
      const updated = await acknowledgeSecurityAlert(alertId);
      setAlerts((current) => current.map((item) => (item.id === alertId ? updated : item)));
      setMessage("Alerta revisada.");
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "No se pudo revisar la alerta.");
    }
  }

  async function processDeliveries() {
    setMessage("");
    try {
      const result = await processSecurityAlertDeliveries();
      const deliveryItems = await loadSecurityAlertDeliveries();
      setDeliveries(deliveryItems);
      setMessage(`Entregas procesadas: ${result.processed}.`);
    } catch (caught) {
      setMessage(caught instanceof Error ? caught.message : "No se pudieron procesar entregas.");
    }
  }

  const visibleAlerts = alerts.length ? alerts : [
    { id: "empty", severity: "info", event_type: "empty", title: "Sin alertas pendientes", body: hasCloudSession() ? "Los eventos criticos apareceran aqui." : "Inicia sesion para ver alertas reales.", status: "empty", created_at: "" }
  ];

  const visibleDeliveries = deliveries.length ? deliveries : [
    { id: "empty-delivery", template: "security_alert", provider: "prepared", status: "empty", recipient_hint: "sin entregas", attempts: 0, max_attempts: 3, created_at: "" }
  ];

  return (
    <Card>
      <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
        <AlertTriangle size={18} aria-hidden="true" />
        <span>Alertas seguridad</span>
      </div>
      <h2 className="mt-4 text-xl font-semibold text-ink">Eventos criticos</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        Cambios de password, MFA, invitaciones y politica de seguridad para revision del tenant.
      </p>
      <div className="mt-4 grid gap-3">
        {visibleAlerts.map((alert) => (
          <div className="rounded-md border border-slate-200 bg-white p-3" key={alert.id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-ink">{alert.title}</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">{alert.body}</p>
              </div>
              <span className="rounded-md bg-mist px-2 py-1 text-xs font-semibold text-slate-600">{alert.severity}</span>
            </div>
            {alert.status === "open" ? (
              <button className="mt-3 inline-flex h-9 items-center justify-center rounded-md border border-slate-200 px-3 text-xs font-semibold text-ink" onClick={() => void acknowledge(alert.id)} type="button">
                Marcar revisada
              </button>
            ) : (
              <p className="mt-3 text-xs font-semibold text-slate-500">Estado: {alert.status}</p>
            )}
          </div>
        ))}
      </div>
      <div className="mt-5 rounded-md border border-slate-200 bg-slate-50 p-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm font-semibold text-ink">Entregas criticas</p>
          {hasCloudSession() ? (
            <button className="inline-flex h-8 items-center justify-center rounded-md border border-slate-200 bg-white px-3 text-xs font-semibold text-ink" onClick={() => void processDeliveries()} type="button">
              Procesar pendientes
            </button>
          ) : null}
        </div>
        <div className="mt-3 grid gap-2">
          {visibleDeliveries.map((delivery) => (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-white px-3 py-2 text-xs text-slate-600" key={delivery.id}>
              <span className="font-semibold text-ink">{delivery.recipient_hint}</span>
              <span>{delivery.template}</span>
              <span>{delivery.status}</span>
              <span>{delivery.attempts}/{delivery.max_attempts}</span>
            </div>
          ))}
        </div>
      </div>
      {state === "loading" ? <p className="mt-3 text-sm text-slate-500">Cargando alertas...</p> : null}
      {message ? <p className={`mt-3 rounded-md px-3 py-2 text-sm ${state === "error" ? "bg-rose-50 text-rose-700" : "bg-sky-50 text-legal-900"}`}>{message}</p> : null}
    </Card>
  );
}
