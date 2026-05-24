import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AccountSecurity } from "@/components/account-security";

describe("AccountSecurity", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("changes password and stores rotated session tokens", async () => {
    localStorage.setItem("lexflow.access_token", "old-access");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "new-access", refresh_token: "new-refresh", token_type: "bearer" })
    } as Response);

    render(<AccountSecurity />);

    fireEvent.change(screen.getByLabelText("Password actual"), { target: { value: "LexflowPilot2026!" } });
    fireEvent.change(screen.getByLabelText("Nueva password"), { target: { value: "NewPilotPassword123!" } });
    fireEvent.change(screen.getByLabelText("Confirmar nueva password"), { target: { value: "NewPilotPassword123!" } });
    fireEvent.click(screen.getByText("Actualizar password"));

    await waitFor(() => expect(screen.getByText("Password actualizada. Las sesiones anteriores quedaron revocadas.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/auth/change-password"), expect.objectContaining({ method: "POST" }));
    expect(localStorage.getItem("lexflow.access_token")).toBe("new-access");
    expect(localStorage.getItem("lexflow.refresh_token")).toBe("new-refresh");
  });

  it("blocks mismatched password confirmation before calling API", () => {
    localStorage.setItem("lexflow.access_token", "old-access");
    const fetchMock = vi.spyOn(globalThis, "fetch");

    render(<AccountSecurity />);

    fireEvent.change(screen.getByLabelText("Password actual"), { target: { value: "LexflowPilot2026!" } });
    fireEvent.change(screen.getByLabelText("Nueva password"), { target: { value: "NewPilotPassword123!" } });
    fireEvent.change(screen.getByLabelText("Confirmar nueva password"), { target: { value: "DifferentPassword123!" } });
    fireEvent.click(screen.getByText("Actualizar password"));

    expect(screen.getByText("La nueva password y la confirmacion no coinciden.")).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalledWith(expect.stringContaining("/api/v1/auth/change-password"), expect.any(Object));
  });

  it("enrolls MFA and stores rotated tokens after verification", async () => {
    localStorage.setItem("lexflow.access_token", "old-access");
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ mfa_enabled: false, enrollment_pending: false })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: "pending", secret: "ABC123", otpauth_url: "otpauth://totp/LEXFLOW:test" })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access_token: "mfa-access", refresh_token: "mfa-refresh", token_type: "bearer" })
      } as Response);

    render(<AccountSecurity />);

    fireEvent.click(screen.getByText("Activar MFA"));

    expect(await screen.findByText("Secreto MFA")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Codigo MFA"), { target: { value: "123456" } });
    fireEvent.click(screen.getByText("Confirmar MFA"));

    await waitFor(() => expect(screen.getByText("MFA activado. Las sesiones anteriores quedaron revocadas.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/auth/mfa/enroll"), expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/auth/mfa/verify"), expect.objectContaining({ method: "POST" }));
    expect(localStorage.getItem("lexflow.access_token")).toBe("mfa-access");
    expect(localStorage.getItem("lexflow.refresh_token")).toBe("mfa-refresh");
  });
});
