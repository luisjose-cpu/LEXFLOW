import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  CaseCreateWizard,
  CaseList,
  CaseResourcePage,
  CasesDashboard,
  ClientDetail,
  ClientList,
  ClientOnboardingWizard,
  SearchGlobalBar
} from "@/components/operational-core";
import { findCase, findClient } from "@/lib/operational-demo";

describe("Operational core UI", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders global search with autocomplete, recent searches, favorites and advanced buckets", () => {
    render(<SearchGlobalBar />);

    fireEvent.change(screen.getByPlaceholderText(/Buscar cliente/i), { target: { value: "Nova" } });

    expect(screen.getAllByText("Nova Capital")[0]).toBeTruthy();
    expect(screen.getByText("Resultado avanzado")).toBeTruthy();
    expect(screen.getAllByText("Favorito")[0]).toBeTruthy();
  });

  it("uses cloud search when a session token exists", async () => {
    localStorage.setItem("lexflow.access_token", "token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        quick_results: [
          {
            id: "case-live",
            type: "case",
            title: "Expediente live",
            subtitle: "00042-2026",
            href: "/cases/case-live",
            tags: ["risk"]
          }
        ],
        recent_searches: ["Expediente live"],
        favorites: [{ id: "case-live", type: "case", title: "Expediente live", subtitle: "", href: "/cases/case-live", tags: [] }]
      })
    } as Response);

    render(<SearchGlobalBar />);
    fireEvent.change(screen.getByPlaceholderText(/Buscar cliente/i), { target: { value: "live" } });

    await waitFor(() => expect(screen.getAllByText("Expediente live")[0]).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/dashboard/search?q=live"), expect.objectContaining({
      headers: expect.objectContaining({ Authorization: "Bearer token" })
    }));
  });

  it("loads clients and cases from the cloud API when authenticated", async () => {
    localStorage.setItem("lexflow.access_token", "token");
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/clients/search")) {
        return {
          ok: true,
          json: async () => [
            {
              id: "client-cloud",
              name: "Cliente Cloud",
              contact_email: "cloud@cliente.demo",
              status: "active",
              risk_profile: "high",
              tags: ["cloud"],
              case_count: 2,
              active_case_count: 1
            }
          ]
        } as Response;
      }
      if (url.includes("/cases/search")) {
        return {
          ok: true,
          json: async () => [
            {
              id: "case-cloud",
              client_id: "client-cloud",
              client_name: "Cliente Cloud",
              title: "Expediente Cloud",
              matter: "Litigio cloud",
              external_case_number: "0001-2026",
              status: "active",
              priority: "alta",
              risk: "high",
              next_action: "Revisar SINOE",
              critical_deadline: "2026-06-01T10:00:00",
              judicial_updates: 1,
              captcha_pending: 0
            }
          ]
        } as Response;
      }
      return { ok: false, json: async () => ({}) } as Response;
    });

    render(
      <>
        <ClientList />
        <CaseList />
      </>
    );

    await waitFor(() => expect(screen.getByText("Cliente Cloud")).toBeTruthy());
    await waitFor(() => expect(screen.getByText("Expediente Cloud")).toBeTruthy());
    expect(screen.getByText("Clientes conectados al API cloud.")).toBeTruthy();
    expect(screen.getByText("Expedientes conectados al API cloud.")).toBeTruthy();
  });

  it("loads client detail resources from the cloud API when authenticated", async () => {
    localStorage.setItem("lexflow.access_token", "token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        client: {
          id: "cli-nova",
          name: "Nova Capital Live",
          contact_email: "live@nova.demo",
          status: "active",
          risk_profile: "high",
          tags: ["live"],
          case_count: 1,
          active_case_count: 1
        },
        general: { business_name: "Nova Capital Live", sector: "Financiero", main_matter: "Cobro live", status: "active", priority: "alta" },
        metrics: { active_cases: 1, documents: 3, hearings: 1, judicial_updates: 2, captcha_pending: 0 },
        risk: { level: "high", recommendation: "Revisar plazo live" },
        cases: [],
        documents: [{ filename: "Contrato live.pdf", classification: "contrato", status: "approved" }],
        communications: [{ channel: "portal", direction: "inbound", body: "Mensaje live", status: "sent" }],
        judicial_updates: [{ title: "Movimiento SINOE live", summary: "Resolucion", status: "new", checked_at: "2026-05-24" }],
        timeline: [{ title: "Evento live", description: "Timeline cloud", type: "case_event", occurred_at: "2026-05-24" }],
        notes: [{ title: "Nota live", body: "Perfil desde API" }]
      })
    } as Response);

    render(<ClientDetail client={findClient("cli-nova")} />);

    await waitFor(() => expect(screen.getByText("Perfil cliente conectados al API cloud.")).toBeTruthy());
    expect(screen.getByText("Contrato live.pdf - contrato - approved")).toBeTruthy();
    expect(screen.getByText("Movimiento SINOE live - Resolucion - new - 2026-05-24")).toBeTruthy();
    expect(screen.getByText("Nota live: Perfil desde API")).toBeTruthy();
  });

  it("loads case resource items from the cloud API when authenticated", async () => {
    localStorage.setItem("lexflow.access_token", "token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        sources: [{ source_type: "SINOE", external_case_number: "0001-2026", status: "active", last_result: "ok" }],
        updates: [{ title: "Cedula live", summary: "Notificacion electronica", status: "new", hash: "hash-live" }],
        sinoe_module: "consumed"
      })
    } as Response);

    render(<CaseResourcePage legalCase={findCase("case-demo")} type="judicial" />);

    await waitFor(() => expect(screen.getByText("Actualizaciones judiciales sinoe conectados al API cloud.")).toBeTruthy());
    expect(screen.getByText("Fuente SINOE - 0001-2026 - active - ok")).toBeTruthy();
    expect(screen.getByText("Cedula live - Notificacion electronica - new - hash-live")).toBeTruthy();
    expect(screen.getByText("SINOE Module: consumed")).toBeTruthy();
  });

  it("renders client detail with cases, risk, documents, timeline and communications", () => {
    render(<ClientDetail client={findClient("cli-nova")} />);

    expect(screen.getByText("Cliente 360")).toBeTruthy();
    expect(screen.getAllByText("Cobro ejecutivo Nova")[0]).toBeTruthy();
    expect(screen.getByText("Documentos del cliente")).toBeTruthy();
    expect(screen.getByText("Timeline cliente")).toBeTruthy();
    expect(screen.getByText("Comunicaciones")).toBeTruthy();
    expect(screen.getAllByText("Riesgo")[0]).toBeTruthy();
  });

  it("renders client and case creation wizards with all expected steps", () => {
    render(
      <>
        <ClientOnboardingWizard />
        <CaseCreateWizard />
      </>
    );

    expect(screen.getByText("Expedientes iniciales")).toBeTruthy();
    expect(screen.getByText("Configuracion portal")).toBeTruthy();
    expect(screen.getByText("Automation")).toBeTruthy();
    expect(screen.getByText("SINOE")).toBeTruthy();
  });

  it("renders cases dashboard and SINOE resource page without duplicating judicial logic", () => {
    render(
      <>
        <CasesDashboard />
        <CaseResourcePage legalCase={findCase("case-demo")} type="judicial" />
      </>
    );

    expect(screen.getByText("Centro de expedientes")).toBeTruthy();
    expect(screen.getAllByText("Cobro ejecutivo Nova")[0]).toBeTruthy();
    expect(screen.getAllByText("Actualizaciones judiciales SINOE")[0]).toBeTruthy();
    expect(screen.getByText("Hash y evidencia gestionados por SINOE Module")).toBeTruthy();
  });
});
