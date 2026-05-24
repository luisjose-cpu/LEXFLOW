import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { InvitationAccept } from "@/components/invitation-accept";
import { UserInvitations } from "@/components/user-invitations";

describe("UserInvitations", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("creates a tenant invitation without exposing tokens in the list", async () => {
    localStorage.setItem("lexflow.access_token", "access");
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => []
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => []
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: "invite-1",
          email: "newlawyer@lexflow.com",
          full_name: "New Lawyer",
          role: "lawyer",
          status: "pending",
          expires_at: "2026-05-31T00:00:00Z",
          delivery: "email_prepared",
          invitation_token: "local-token"
        })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ id: "email-1", template: "user_invitation", provider: "email_prepared", status: "prepared", recipient_hint: "ne***@lexflow.com", created_at: "2026-05-24T00:00:00Z" }]
      } as Response);

    render(<UserInvitations />);

    expect(await screen.findByText("Aun no hay invitaciones registradas.")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Correo"), { target: { value: "newlawyer@lexflow.com" } });
    fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: "New Lawyer" } });
    fireEvent.click(screen.getByText("Crear invitacion"));

    await waitFor(() => expect(screen.getByText("Invitacion preparada. El usuario definira su propia password.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/users/invitations"), expect.objectContaining({ method: "POST" }));
    expect(screen.getByText("local-token")).toBeTruthy();
    expect(screen.getByText("New Lawyer")).toBeTruthy();
  });

  it("resends and cancels pending invitations", async () => {
    localStorage.setItem("lexflow.access_token", "access");
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          {
            id: "invite-1",
            email: "pending@lexflow.com",
            full_name: "Pending Lawyer",
            role: "lawyer",
            status: "pending",
            expires_at: "2026-05-31T00:00:00Z"
          }
        ]
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => []
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: "invite-1",
          email: "pending@lexflow.com",
          full_name: "Pending Lawyer",
          role: "lawyer",
          status: "pending",
          expires_at: "2026-05-31T01:00:00Z",
          delivery: "prepared",
          invitation_token: "rotated-token"
        })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ id: "email-1", template: "user_invitation", provider: "email_prepared", status: "prepared", recipient_hint: "pe***@lexflow.com", created_at: "2026-05-24T00:00:00Z" }]
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: "invite-1",
          email: "pending@lexflow.com",
          full_name: "Pending Lawyer",
          role: "lawyer",
          status: "cancelled",
          expires_at: "2026-05-31T01:00:00Z"
        })
      } as Response);

    render(<UserInvitations />);

    expect(await screen.findByText("Pending Lawyer")).toBeTruthy();
    fireEvent.click(screen.getByText("Reenviar"));
    await waitFor(() => expect(screen.getByText("Invitacion reenviada con token rotado.")).toBeTruthy());
    expect(screen.getByText("rotated-token")).toBeTruthy();

    fireEvent.click(screen.getByText("Cancelar"));
    await waitFor(() => expect(screen.getByText("Invitacion cancelada. El token ya no podra usarse.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/users/invitations/invite-1/resend"), expect.objectContaining({ method: "POST" }));
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/users/invitations/invite-1/cancel"), expect.objectContaining({ method: "POST" }));
  });

  it("accepts an invitation and stores session tokens", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ status: "accepted", access_token: "new-access", refresh_token: "new-refresh", token_type: "bearer" })
    } as Response);

    render(<InvitationAccept />);

    fireEvent.change(screen.getByLabelText("Token de invitacion"), { target: { value: "local-token" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "InvitedLawyer123!" } });
    fireEvent.change(screen.getByLabelText("Confirmar password"), { target: { value: "InvitedLawyer123!" } });
    fireEvent.click(screen.getByRole("button", { name: "Aceptar invitacion" }));

    await waitFor(() => expect(screen.getByText("Invitacion aceptada. Ya tienes una sesion activa.")).toBeTruthy());
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/api/v1/auth/invitations/accept"), expect.objectContaining({ method: "POST" }));
    expect(localStorage.getItem("lexflow.access_token")).toBe("new-access");
    expect(localStorage.getItem("lexflow.refresh_token")).toBe("new-refresh");
  });
});
