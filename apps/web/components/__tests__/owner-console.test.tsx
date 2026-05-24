import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  DemoTenants,
  InterventionRequests,
  OwnerAuditLogs,
  OwnerDashboard,
  OwnerLogin,
  PlansManager,
  SupportTickets,
  SystemHealth,
  TenantDetail,
  TenantFeatures,
  TenantUsage,
  TenantsList
} from "@/components/owner-console";

describe("Owner Console UI", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders owner login and stores owner JWT session", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        access_token: "owner-access",
        refresh_token: "owner-refresh",
        owner: { email: "owner@lexflow.test", role: "owner_admin" }
      })
    } as Response);

    render(<OwnerLogin />);
    fireEvent.change(screen.getByPlaceholderText("owner@lexflow.com"), { target: { value: "owner@lexflow.test" } });
    fireEvent.change(screen.getByPlaceholderText("Password owner"), { target: { value: "OwnerPassword123!" } });
    fireEvent.click(screen.getByText("Entrar al Owner Console"));

    expect(await screen.findByText(/Owner conectado/i)).toBeTruthy();
    expect(localStorage.getItem("lexflow.owner_access_token")).toBe("owner-access");
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/owner/auth/login"), expect.objectContaining({ method: "POST" }));
  });

  it("renders owner dashboard with SaaS metrics and security boundary", () => {
    render(<OwnerDashboard />);

    expect(screen.getByText("Command Center SaaS")).toBeTruthy();
    expect(screen.getByText("Tenants activos")).toBeTruthy();
    expect(screen.getByText(/Boundary owner activo/i)).toBeTruthy();
    expect(screen.getByText("Tenants en observacion")).toBeTruthy();
  });

  it("loads owner dashboard from cloud API when owner token exists", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/owner/dashboard")) {
        return {
          ok: true,
          json: async () => ({
            tenants: { active: 7, trial: 2, suspended: 1 },
            revenue: { mrr_cents: 99000, arr_cents: 1188000 },
            support: { open_tickets: 4, sla_risk: 1 },
            usage: { ai_tokens: 123000 }
          })
        } as Response;
      }
      if (url.includes("/owner/tenants")) {
        return {
          ok: true,
          json: async () => [{ id: "tenant-live", name: "Tenant Live", slug: "live", status: "active", plan: "AI", users: 3, cases: 9, health_score: 88 }]
        } as Response;
      }
      if (url.includes("/owner/system/health")) {
        return {
          ok: true,
          json: async () => ({ checks: [{ component: "api", status: "ok", latency_ms: 10 }] })
        } as Response;
      }
      return { ok: false, json: async () => ({}) } as Response;
    });

    render(<OwnerDashboard />);

    await waitFor(() => expect(screen.getByText("Owner Console conectado al API cloud.")).toBeTruthy());
    expect(screen.getByText("Tenant Live")).toBeTruthy();
    expect(screen.getByText("$990")).toBeTruthy();
  });

  it("renders tenants list with search and lifecycle actions", () => {
    render(<TenantsList />);

    fireEvent.change(screen.getByPlaceholderText(/Buscar tenant/i), { target: { value: "Nova" } });

    expect(screen.getByText("Nova Legal Studio")).toBeTruthy();
    expect(screen.getByText("Crear tenant")).toBeTruthy();
    expect(screen.getByText("Cambiar plan")).toBeTruthy();
  });

  it("creates a tenant through the owner API", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/owner/tenants") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ id: "tenant-created", name: "Estudio Delta", slug: "estudio-delta", status: "trial", plan: "PRO", users: 0, cases: 0, health_score: 82 })
        } as Response;
      }
      if (url.includes("/owner/tenants")) return { ok: true, json: async () => [] } as Response;
      return { ok: false, json: async () => ({}) } as Response;
    });

    render(<TenantsList />);
    await waitFor(() => expect(screen.getByText("Owner Console conectado al API cloud.")).toBeTruthy());
    fireEvent.change(screen.getByPlaceholderText("Nombre del estudio"), { target: { value: "Estudio Delta" } });
    fireEvent.change(screen.getByPlaceholderText("slug-del-tenant"), { target: { value: "estudio-delta" } });
    fireEvent.change(screen.getByDisplayValue("START"), { target: { value: "PRO" } });
    fireEvent.click(screen.getByText("Crear tenant"));

    await waitFor(() => expect(screen.getByText("Tenant creado: Estudio Delta.")).toBeTruthy());
    expect(screen.getByText("Estudio Delta")).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/tenants"), expect.objectContaining({ method: "POST" }));
  });

  it("renders tenant detail without sensitive tenant data", () => {
    render(<TenantDetail tenantId="tenant-nova" />);

    expect(screen.getByText("Nova Legal Studio")).toBeTruthy();
    expect(screen.getByText("Datos sensibles")).toBeTruthy();
    expect(screen.getByText(/no accede a documentos/i)).toBeTruthy();
  });

  it("runs audited tenant lifecycle actions through the owner API", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/owner/tenants/tenant-nova/change-plan")) {
        return {
          ok: true,
          json: async () => ({ id: "tenant-nova", name: "Nova Legal Studio", slug: "nova", status: "active", plan: "PRO", users: 1, cases: 2, health_score: 89 })
        } as Response;
      }
      if (url.includes("/owner/tenants/tenant-nova")) {
        return {
          ok: true,
          json: async () => ({ id: "tenant-nova", name: "Nova Legal Studio", slug: "nova", status: "active", plan: "AI", users: 1, cases: 2, health_score: 89 })
        } as Response;
      }
      return { ok: false, json: async () => ({}) } as Response;
    });

    render(<TenantDetail tenantId="tenant-nova" />);
    await waitFor(() => expect(screen.getByText("Owner Console conectado al API cloud.")).toBeTruthy());
    fireEvent.click(screen.getByText("Cambiar plan"));

    await waitFor(() => expect(screen.getByText("Plan actualizado a PRO.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/tenants/tenant-nova/change-plan"), expect.objectContaining({ method: "POST" }));
  });

  it("renders usage and interactive feature flags", () => {
    render(
      <>
        <TenantUsage tenantId="tenant-nova" />
        <TenantFeatures tenantId="tenant-nova" />
      </>
    );

    expect(screen.getByText("Consumo de Nova Legal Studio")).toBeTruthy();
    expect(screen.getByText("IA tokens")).toBeTruthy();
    expect(screen.getByText("client_portal")).toBeTruthy();
    fireEvent.click(screen.getByText("ocr"));
    expect(screen.getByText("ocr")).toBeTruthy();
  });

  it("saves feature flags through the owner API", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/owner/tenants/tenant-nova/features") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => [
            { feature_key: "ai", enabled: true },
            { feature_key: "ocr", enabled: true }
          ]
        } as Response;
      }
      if (url.includes("/owner/tenants/tenant-nova/features")) {
        return {
          ok: true,
          json: async () => [
            { feature_key: "ai", enabled: true },
            { feature_key: "ocr", enabled: false }
          ]
        } as Response;
      }
      return { ok: false, json: async () => ({}) } as Response;
    });

    render(<TenantFeatures tenantId="tenant-nova" />);
    await waitFor(() => expect(screen.getByText("Owner Console conectado al API cloud.")).toBeTruthy());
    fireEvent.click(screen.getByText("ocr"));
    fireEvent.click(screen.getByText("Guardar flags"));

    await waitFor(() => expect(screen.getByText("Feature flags guardados y auditados.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/tenants/tenant-nova/features"), expect.objectContaining({ method: "POST" }));
  });

  it("renders plans, support, system, demos, interventions and audit", () => {
    render(
      <>
        <PlansManager />
        <SupportTickets />
        <SystemHealth />
        <DemoTenants />
        <InterventionRequests />
        <OwnerAuditLogs />
      </>
    );

    expect(screen.getByText("Planes y licencias")).toBeTruthy();
    expect(screen.getByText("Tickets y SLA")).toBeTruthy();
    expect(screen.getByText("Salud tecnica")).toBeTruthy();
    expect(screen.getByText("Demos comerciales")).toBeTruthy();
    expect(screen.getByText("Intervenciones temporales")).toBeTruthy();
    expect(screen.getByText("Owner audit logs")).toBeTruthy();
  });

  it("creates support tickets, demo tenants and interventions through owner API", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    const tenantId = "11111111-1111-1111-1111-111111111111";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/owner/support/tickets") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ id: "ticket-new", tenant_id: tenantId, priority: "high", status: "open", category: "support", title: "Cliente necesita ayuda" })
        } as Response;
      }
      if (url.includes("/owner/support/tickets")) return { ok: true, json: async () => [] } as Response;
      if (url.includes("/owner/demos") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ demo: { tenant_id: tenantId, demo_type: "labor", status: "ready", last_reset_at: null } })
        } as Response;
      }
      if (url.includes("/owner/demos")) return { ok: true, json: async () => [] } as Response;
      if (url.includes("/owner/interventions") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ tenant_id: tenantId, status: "active", reason: "Soporte autorizado por admin", expires_at: "2026-05-24T23:59:00Z", scopes: ["metadata:read"] })
        } as Response;
      }
      if (url.includes("/owner/interventions")) return { ok: true, json: async () => [] } as Response;
      return { ok: false, json: async () => ({}) } as Response;
    });

    render(
      <>
        <SupportTickets />
        <DemoTenants />
        <InterventionRequests />
      </>
    );
    await waitFor(() => expect(screen.getAllByText("Owner Console conectado al API cloud.").length).toBeGreaterThanOrEqual(3));

    fireEvent.change(screen.getByPlaceholderText("Titulo del ticket"), { target: { value: "Cliente necesita ayuda" } });
    fireEvent.change(screen.getByPlaceholderText("tenant_id opcional"), { target: { value: tenantId } });
    fireEvent.change(screen.getByDisplayValue("medium"), { target: { value: "high" } });
    fireEvent.click(screen.getByText("Crear ticket"));
    await waitFor(() => expect(screen.getByText("Ticket creado: Cliente necesita ayuda.")).toBeTruthy());

    fireEvent.change(screen.getByPlaceholderText("Nombre demo comercial"), { target: { value: "Demo Laboral" } });
    fireEvent.change(screen.getByDisplayValue("litigation"), { target: { value: "labor" } });
    fireEvent.click(screen.getByText("Crear demo"));
    await waitFor(() => expect(screen.getByText("Demo creada: Demo labor.")).toBeTruthy());

    fireEvent.change(screen.getByPlaceholderText("tenant_id"), { target: { value: tenantId } });
    fireEvent.change(screen.getByPlaceholderText("Motivo autorizado"), { target: { value: "Soporte autorizado por admin" } });
    fireEvent.click(screen.getByText("Crear intervencion"));
    await waitFor(() => expect(screen.getByText(`Intervencion creada para ${tenantId}.`)).toBeTruthy());

    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/support/tickets"), expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/demos"), expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/interventions"), expect.objectContaining({ method: "POST" }));
  });
});
