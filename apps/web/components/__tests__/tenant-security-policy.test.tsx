import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TenantSecurityPolicy } from "@/components/tenant-security-policy";

describe("TenantSecurityPolicy", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("loads and saves MFA policy for selected roles", async () => {
    localStorage.setItem("lexflow.access_token", "access");
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          tenant_id: "tenant-1",
          enforce_mfa: false,
          mfa_required_roles: ["tenant_admin", "partner"],
          grace_period_hours: 72,
          allow_client_user_mfa_bypass: true
        })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          tenant_id: "tenant-1",
          enforce_mfa: true,
          mfa_required_roles: ["tenant_admin", "partner", "lawyer"],
          grace_period_hours: 48,
          allow_client_user_mfa_bypass: true
        })
      } as Response);

    render(<TenantSecurityPolicy />);

    expect(await screen.findByText("MFA obligatorio")).toBeTruthy();
    fireEvent.click(screen.getByLabelText("Exigir MFA para roles seleccionados"));
    fireEvent.click(screen.getByLabelText("Abogado"));
    fireEvent.change(screen.getByLabelText("Horas de gracia operacional"), { target: { value: "48" } });
    fireEvent.click(screen.getByText("Guardar politica"));

    await waitFor(() => expect(screen.getByText("Politica guardada y auditada.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/settings/security-policy"), expect.objectContaining({ method: "PATCH" }));
  });

  it("requires an active session before saving policy", () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");

    render(<TenantSecurityPolicy />);

    fireEvent.click(screen.getByText("Guardar politica"));

    expect(screen.getByText("Inicia sesion para cambiar la politica del tenant.")).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
