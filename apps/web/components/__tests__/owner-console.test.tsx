import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import {
  DemoTenants,
  InterventionRequests,
  OwnerAuditLogs,
  OwnerDashboard,
  PlansManager,
  SupportTickets,
  SystemHealth,
  TenantDetail,
  TenantFeatures,
  TenantUsage,
  TenantsList
} from "@/components/owner-console";

describe("Owner Console UI", () => {
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
