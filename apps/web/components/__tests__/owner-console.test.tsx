import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  DemoTenants,
  InterventionRequests,
  OwnerAuditLogs,
  OwnerDashboard,
  OwnerLogin,
  OwnerSecurityAlertsPanel,
  OwnerSecurityPanel,
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

  it("sends owner MFA code during login when provided", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        access_token: "owner-access",
        refresh_token: "owner-refresh",
        owner: { email: "owner@lexflow.test", role: "owner_admin", mfa_enabled: true }
      })
    } as Response);

    render(<OwnerLogin />);
    fireEvent.change(screen.getByPlaceholderText("owner@lexflow.com"), { target: { value: "owner@lexflow.test" } });
    fireEvent.change(screen.getByPlaceholderText("Password owner"), { target: { value: "OwnerPassword123!" } });
    fireEvent.change(screen.getByPlaceholderText("Opcional si MFA esta activo"), { target: { value: "123456" } });
    fireEvent.click(screen.getByText("Entrar al Owner Console"));

    await waitFor(() => expect(screen.getByText(/Owner conectado/i)).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/owner/auth/login"),
      expect.objectContaining({ body: expect.stringContaining('"mfa_code":"123456"') })
    );
  });

  it("logs out owner sessions and clears stored owner tokens", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    localStorage.setItem("lexflow.owner_refresh_token", "owner-refresh");
    localStorage.setItem("lexflow.owner_user", JSON.stringify({ email: "owner@lexflow.test", role: "owner_admin" }));
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes("/owner/auth/logout")) return { ok: true } as Response;
      if (url.includes("/owner/dashboard")) return { ok: true, json: async () => ({}) } as Response;
      if (url.includes("/owner/tenants")) return { ok: true, json: async () => [] } as Response;
      if (url.includes("/owner/system/health")) return { ok: true, json: async () => ({ checks: [] }) } as Response;
      return { ok: false, json: async () => ({}) } as Response;
    });

    render(<OwnerDashboard />);
    fireEvent.click(await screen.findByText("Cerrar sesion"));

    await waitFor(() => expect(localStorage.getItem("lexflow.owner_access_token")).toBeNull());
    expect(localStorage.getItem("lexflow.owner_refresh_token")).toBeNull();
    expect(localStorage.getItem("lexflow.owner_user")).toBeNull();
    expect(screen.getByText("Sesion owner cerrada.")).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/owner/auth/logout"), expect.objectContaining({ method: "POST" }));
  });

  it("renders owner dashboard with SaaS metrics and security boundary", () => {
    render(<OwnerDashboard />);

    expect(screen.getByText("Command Center SaaS")).toBeTruthy();
    expect(screen.getByText("Tenants activos")).toBeTruthy();
    expect(screen.getByText(/Boundary owner activo/i)).toBeTruthy();
    expect(screen.getByText("Tenants en observacion")).toBeTruthy();
  });

  it("enrolls owner MFA from the security panel", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ mfa_enabled: false, enrollment_pending: false, recovery_codes_remaining: 0 })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: "pending", secret: "OWNERSECRET", otpauth_url: "otpauth://totp/LEXFLOWOwner:test" })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: "new-owner-access",
          refresh_token: "new-owner-refresh",
          token_type: "bearer",
          owner: { email: "owner@lexflow.test", role: "owner_admin", mfa_enabled: true },
          recovery_codes: ["LF-1111-2222-3333"]
        })
      } as Response);

    render(<OwnerSecurityPanel />);
    fireEvent.click(screen.getByText("Consultar MFA owner"));
    await waitFor(() => expect(screen.getByText("Estado: Inactivo")).toBeTruthy());
    fireEvent.click(screen.getByText("Activar MFA owner"));
    expect(await screen.findByText("Secreto MFA owner")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Codigo MFA"), { target: { value: "123456" } });
    fireEvent.click(screen.getByText("Confirmar MFA owner"));

    await waitFor(() => expect(screen.getByText("MFA owner activado. Las sesiones anteriores quedaron revocadas.")).toBeTruthy());
    expect(screen.getByText("LF-1111-2222-3333")).toBeTruthy();
    expect(localStorage.getItem("lexflow.owner_access_token")).toBe("new-owner-access");
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/owner/auth/mfa/verify"), expect.objectContaining({ method: "POST" }));
  });

  it("shows owner security alert deliveries and processes retries", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([{ id: "alert-owner-1", severity: "critical", event_type: "owner.owner_mfa_disabled", title: "MFA owner desactivado", body: "Revisar evento.", status: "open", created_at: "2026-05-24T00:00:00Z" }])
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([{ id: "delivery-owner-1", template: "security_alert", provider: "email_prepared", status: "prepared", recipient_hint: "ow***@lexflow.com", attempts: 1, max_attempts: 3, created_at: "2026-05-24T00:00:00Z" }])
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ processed: 1 })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([{ id: "delivery-owner-1", template: "security_alert", provider: "email_prepared", status: "prepared", recipient_hint: "ow***@lexflow.com", attempts: 1, max_attempts: 3, created_at: "2026-05-24T00:00:00Z" }])
      } as Response);

    render(<OwnerSecurityAlertsPanel />);

    expect(await screen.findByText("MFA owner desactivado")).toBeTruthy();
    expect(screen.getByText("ow***@lexflow.com")).toBeTruthy();
    fireEvent.click(screen.getByText("Procesar pendientes"));

    await waitFor(() => expect(screen.getByText("Entregas owner procesadas: 1.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/owner/security-alert-deliveries/process"), expect.objectContaining({ method: "POST" }));
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
          json: async () => ({ checks: [{ component: "readiness", status: "ready", latency_ms: 0, detail: "blockers=0 warnings=0" }] })
        } as Response;
      }
      return { ok: false, json: async () => ({}) } as Response;
    });

    render(<OwnerDashboard />);

    await waitFor(() => expect(screen.getByText("Owner Console conectado al API cloud.")).toBeTruthy());
    expect(screen.getByText("Tenant Live")).toBeTruthy();
    expect(screen.getByText("$990")).toBeTruthy();
    expect(screen.getByText("blockers=0 warnings=0")).toBeTruthy();
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
    fireEvent.change(screen.getByPlaceholderText("admin@estudio.com"), { target: { value: "admin@delta.lexflow.com" } });
    fireEvent.change(screen.getByPlaceholderText("Nombre admin"), { target: { value: "Admin Delta" } });
    fireEvent.change(screen.getByPlaceholderText("Password temporal"), { target: { value: "DeltaPassword123!" } });
    fireEvent.click(screen.getByText("Crear tenant"));

    await waitFor(() => expect(screen.getByText("Tenant creado: Estudio Delta. Admin: pendiente.")).toBeTruthy());
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
      if (url.includes("/owner/tenants/tenant-nova/limits")) {
        return {
          ok: true,
          json: async () => [
            { limit_key: "users", limit_value: 20, hard_limit: true },
            { limit_key: "cases", limit_value: 500, hard_limit: true }
          ]
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

  it("saves tenant commercial limits through the owner API", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/owner/tenants/tenant-nova/limits") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => [
            { limit_key: "users", limit_value: 33, hard_limit: true },
            { limit_key: "cases", limit_value: 500, hard_limit: true }
          ]
        } as Response;
      }
      if (url.includes("/owner/tenants/tenant-nova/limits")) {
        return {
          ok: true,
          json: async () => [
            { limit_key: "users", limit_value: 20, hard_limit: true },
            { limit_key: "cases", limit_value: 500, hard_limit: true }
          ]
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
    fireEvent.change(screen.getByDisplayValue("20"), { target: { value: "33" } });
    fireEvent.click(screen.getByText("Guardar limites"));

    await waitFor(() => expect(screen.getByText("Limites guardados y auditados.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/tenants/tenant-nova/limits"), expect.objectContaining({ method: "POST" }));
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

  it("creates and updates owner plans through the owner API", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/owner/plans/PILOT")) {
        return {
          ok: true,
          json: async () => ({ code: "PILOT", name: "Pilot", monthly_price_cents: 19900, status: "draft", limits: { users: 10 }, features: ["expediente360"] })
        } as Response;
      }
      if (url.includes("/owner/plans") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ code: "PILOT", name: "Pilot", monthly_price_cents: 19900, status: "active", limits: { users: 10 }, features: ["expediente360", "dashboard"] })
        } as Response;
      }
      if (url.includes("/owner/plans")) return { ok: true, json: async () => [] } as Response;
      return { ok: false, json: async () => ({}) } as Response;
    });

    render(<PlansManager />);
    await waitFor(() => expect(screen.getByText("Owner Console conectado al API cloud.")).toBeTruthy());
    fireEvent.change(screen.getByPlaceholderText("PLAN"), { target: { value: "PILOT" } });
    fireEvent.change(screen.getByPlaceholderText("Nombre comercial"), { target: { value: "Pilot" } });
    fireEvent.change(screen.getByPlaceholderText("USD/mes"), { target: { value: "199" } });
    fireEvent.click(screen.getByText("Crear plan"));

    await waitFor(() => expect(screen.getByText("Plan creado: PILOT.")).toBeTruthy());
    fireEvent.click(screen.getAllByText("Pasar a draft")[0]);
    await waitFor(() => expect(screen.getByText("Plan PILOT actualizado a draft.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/plans"), expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/plans/PILOT"), expect.objectContaining({ method: "PATCH" }));
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

  it("creates and resolves system incidents through owner API", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/owner/system/health")) {
        return {
          ok: true,
          json: async () => ({ checks: [{ component: "storage_backend", status: "warning", latency_ms: 0, detail: "backend=local bucket=local" }] })
        } as Response;
      }
      if (url.includes("/owner/system/incidents/incident-new/resolve")) {
        return {
          ok: true,
          json: async () => ({ id: "incident-new", component: "api", title: "API error rate", severity: "high", status: "resolved", summary: "5xx elevados", created_at: "2026-05-24T21:00:00Z", resolved_at: "2026-05-24T21:05:00Z" })
        } as Response;
      }
      if (url.includes("/owner/system/incidents") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ id: "incident-new", component: "api", title: "API error rate", severity: "high", status: "open", summary: "5xx elevados", created_at: "2026-05-24T21:00:00Z", resolved_at: null })
        } as Response;
      }
      if (url.includes("/owner/system/incidents")) return { ok: true, json: async () => [] } as Response;
      return { ok: false, json: async () => ({}) } as Response;
    });

    render(<SystemHealth />);
    await waitFor(() => expect(screen.getByText("Owner Console conectado al API cloud.")).toBeTruthy());
    expect(screen.getByText("backend=local bucket=local - 0 ms")).toBeTruthy();
    fireEvent.change(screen.getByPlaceholderText("Titulo del incidente"), { target: { value: "API error rate" } });
    fireEvent.change(screen.getByDisplayValue("medium"), { target: { value: "high" } });
    fireEvent.change(screen.getByPlaceholderText("Resumen operativo"), { target: { value: "5xx elevados" } });
    fireEvent.click(screen.getByText("Crear incidente"));

    await waitFor(() => expect(screen.getByText("Incidente creado: API error rate.")).toBeTruthy());
    fireEvent.click(screen.getByText("Resolver"));
    await waitFor(() => expect(screen.getByText("Incidente resuelto: API error rate.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/system/incidents"), expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/system/incidents/incident-new/resolve"), expect.objectContaining({ method: "POST" }));
  });

  it("creates support tickets, demo tenants and interventions through owner API", async () => {
    localStorage.setItem("lexflow.owner_access_token", "owner-token");
    const tenantId = "11111111-1111-1111-1111-111111111111";
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.includes("/owner/support/tickets/ticket-new/resolve")) {
        return {
          ok: true,
          json: async () => ({ id: "ticket-new", tenant_id: tenantId, priority: "high", status: "resolved", category: "support", title: "Cliente necesita ayuda", resolution: "Resuelto desde Owner Console" })
        } as Response;
      }
      if (url.includes("/owner/support/tickets") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ id: "ticket-new", tenant_id: tenantId, priority: "high", status: "open", category: "support", title: "Cliente necesita ayuda" })
        } as Response;
      }
      if (url.includes("/owner/support/tickets")) return { ok: true, json: async () => [] } as Response;
      if (url.includes(`/owner/demos/${tenantId}/reset`)) {
        return {
          ok: true,
          json: async () => ({ id: tenantId, tenant_id: tenantId, demo_type: "labor", status: "ready", last_reset_at: "2026-05-24T21:10:00Z" })
        } as Response;
      }
      if (url.includes("/owner/demos") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ demo: { id: tenantId, tenant_id: tenantId, demo_type: "labor", status: "ready", last_reset_at: null } })
        } as Response;
      }
      if (url.includes("/owner/demos")) return { ok: true, json: async () => [] } as Response;
      if (url.includes("/owner/interventions/intervention-new/close")) {
        return {
          ok: true,
          json: async () => ({ id: "intervention-new", tenant_id: tenantId, status: "closed", reason: "Soporte autorizado por admin", expires_at: "2026-05-24T23:59:00Z", scopes: ["metadata:read"], closed_at: "2026-05-24T21:00:00Z" })
        } as Response;
      }
      if (url.includes("/owner/interventions") && init?.method === "POST") {
        return {
          ok: true,
          json: async () => ({ id: "intervention-new", tenant_id: tenantId, status: "active", reason: "Soporte autorizado por admin", expires_at: "2026-05-24T23:59:00Z", scopes: ["metadata:read"] })
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
    fireEvent.click(screen.getAllByText("Resolver")[0]);
    await waitFor(() => expect(screen.getByText("Ticket resuelto: Cliente necesita ayuda.")).toBeTruthy());

    fireEvent.change(screen.getByPlaceholderText("Nombre demo comercial"), { target: { value: "Demo Laboral" } });
    fireEvent.change(screen.getByDisplayValue("litigation"), { target: { value: "labor" } });
    fireEvent.click(screen.getByText("Crear demo"));
    await waitFor(() => expect(screen.getByText("Demo creada: Demo labor.")).toBeTruthy());
    fireEvent.click(screen.getByText("Reset demo"));
    await waitFor(() => expect(screen.getByText("Demo reseteada: Demo labor.")).toBeTruthy());

    fireEvent.change(screen.getByPlaceholderText("tenant_id"), { target: { value: tenantId } });
    fireEvent.change(screen.getByPlaceholderText("Motivo autorizado"), { target: { value: "Soporte autorizado por admin" } });
    fireEvent.click(screen.getByText("Crear intervencion"));
    await waitFor(() => expect(screen.getByText(`Intervencion creada para ${tenantId}.`)).toBeTruthy());
    fireEvent.click(screen.getAllByText("Cerrar")[0]);
    await waitFor(() => expect(screen.getByText(`Intervencion cerrada para ${tenantId}.`)).toBeTruthy());

    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/support/tickets"), expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/support/tickets/ticket-new/resolve"), expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/demos"), expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining(`/owner/demos/${tenantId}/reset`), expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/interventions"), expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/owner/interventions/intervention-new/close"), expect.objectContaining({ method: "POST" }));
  });
});
