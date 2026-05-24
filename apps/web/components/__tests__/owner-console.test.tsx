import { fireEvent, render, screen } from "@testing-library/react";
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

  it("renders tenants list with search and lifecycle actions", () => {
    render(<TenantsList />);

    fireEvent.change(screen.getByPlaceholderText(/Buscar tenant/i), { target: { value: "Nova" } });

    expect(screen.getByText("Nova Legal Studio")).toBeTruthy();
    expect(screen.getByText("Crear tenant")).toBeTruthy();
    expect(screen.getByText("Cambiar plan")).toBeTruthy();
  });

  it("renders tenant detail without sensitive tenant data", () => {
    render(<TenantDetail tenantId="tenant-nova" />);

    expect(screen.getByText("Nova Legal Studio")).toBeTruthy();
    expect(screen.getByText("Datos sensibles")).toBeTruthy();
    expect(screen.getByText(/no accede a documentos/i)).toBeTruthy();
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
});
