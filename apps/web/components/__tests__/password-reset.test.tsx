import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { PasswordResetConfirm, PasswordResetRequest } from "@/components/password-reset";

describe("Password reset", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("requests a password reset without exposing whether the account exists", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ status: "reset_requested", delivery: "email_prepared" })
    } as Response);

    render(<PasswordResetRequest />);

    fireEvent.change(screen.getByLabelText("Correo"), { target: { value: "ljiturri@iturri.com.pe" } });
    fireEvent.click(screen.getByText("Enviar instrucciones"));

    await waitFor(() => expect(screen.getByText("Si la cuenta existe, enviaremos instrucciones de recuperacion.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/password-reset/request"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "ljiturri@iturri.com.pe", tenant_slug: "piloto" })
      })
    );
  });

  it("shows local/test reset token only when the API returns one", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ status: "reset_requested", delivery: "email_prepared", reset_token: "dev-token-123" })
    } as Response);

    render(<PasswordResetRequest />);

    fireEvent.change(screen.getByLabelText("Correo"), { target: { value: "ljiturri@iturri.com.pe" } });
    fireEvent.click(screen.getByText("Enviar instrucciones"));

    expect(await screen.findByText("Token local/test")).toBeTruthy();
    expect(screen.getByText("dev-token-123")).toBeTruthy();
  });

  it("confirms a reset token and updates the password", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ status: "password_reset_complete" })
    } as Response);

    render(<PasswordResetConfirm />);

    fireEvent.change(screen.getByLabelText("Token de recuperacion"), { target: { value: "reset-token" } });
    fireEvent.change(screen.getByLabelText("Nueva password"), { target: { value: "NewPilotPassword123!" } });
    fireEvent.change(screen.getByLabelText("Confirmar nueva password"), { target: { value: "NewPilotPassword123!" } });
    fireEvent.click(screen.getByText("Actualizar password"));

    await waitFor(() => expect(screen.getByText("Password actualizada. Ya puedes iniciar sesion.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/password-reset/confirm"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ reset_token: "reset-token", new_password: "NewPilotPassword123!" })
      })
    );
  });

  it("blocks mismatched confirmation before confirming token", () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");

    render(<PasswordResetConfirm />);

    fireEvent.change(screen.getByLabelText("Token de recuperacion"), { target: { value: "reset-token" } });
    fireEvent.change(screen.getByLabelText("Nueva password"), { target: { value: "NewPilotPassword123!" } });
    fireEvent.change(screen.getByLabelText("Confirmar nueva password"), { target: { value: "DifferentPassword123!" } });
    fireEvent.click(screen.getByText("Actualizar password"));

    expect(screen.getByText("La nueva password y la confirmacion no coinciden.")).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
