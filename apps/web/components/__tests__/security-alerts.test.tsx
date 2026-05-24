import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SecurityAlerts } from "@/components/security-alerts";

describe("SecurityAlerts", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("loads and acknowledges tenant security alerts", async () => {
    localStorage.setItem("lexflow.access_token", "access");
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([{ id: "alert-1", severity: "high", event_type: "auth.mfa_disabled", title: "MFA desactivado", body: "Revisar evento.", status: "open", created_at: "2026-05-24T00:00:00Z" }])
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ([{ id: "delivery-1", template: "security_alert", provider: "email_prepared", status: "prepared", recipient_hint: "ad***@estudio.com", attempts: 1, max_attempts: 3, created_at: "2026-05-24T00:00:00Z" }])
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: "alert-1", severity: "high", event_type: "auth.mfa_disabled", title: "MFA desactivado", body: "Revisar evento.", status: "acknowledged", created_at: "2026-05-24T00:00:00Z" })
      } as Response);

    render(<SecurityAlerts />);

    expect(await screen.findByText("MFA desactivado")).toBeTruthy();
    expect(screen.getByText("ad***@estudio.com")).toBeTruthy();
    fireEvent.click(screen.getByText("Marcar revisada"));

    await waitFor(() => expect(screen.getByText("Alerta revisada.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/settings/security-alerts/alert-1/acknowledge"), expect.objectContaining({ method: "POST" }));
  });
});
