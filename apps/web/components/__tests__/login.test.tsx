import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import LoginPage from "@/app/login/page";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push })
}));

describe("LoginPage", () => {
  beforeEach(() => {
    push.mockReset();
    localStorage.clear();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          access_token: "access-token",
          refresh_token: "refresh-token",
          token_type: "bearer",
          user: {
            id: "user-1",
            tenant_id: "tenant-1",
            email: "ljiturri@iturri.com.pe",
            full_name: "Luis",
            role: "tenant_admin"
          }
        })
      })
    );
  });

  it("authenticates against the cloud API and stores the session", async () => {
    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Correo"), { target: { value: "ljiturri@iturri.com.pe" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "LexflowPilot2026!" } });
    fireEvent.click(screen.getByText("Entrar al Legal OS"));

    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/v1/auth/login"), expect.any(Object)));

    expect(localStorage.getItem("lexflow.access_token")).toBe("access-token");
    expect(localStorage.getItem("lexflow.tenant_slug")).toBe("piloto");
    expect(push).toHaveBeenCalledWith("/dashboard");
  });

  it("shows invalid credential feedback", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({ ok: false, status: 401 } as Response);

    render(<LoginPage />);

    fireEvent.change(screen.getByLabelText("Correo"), { target: { value: "ljiturri@iturri.com.pe" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "bad-password" } });
    fireEvent.click(screen.getByText("Entrar al Legal OS"));

    expect(await screen.findByText("Credenciales o estudio incorrectos.")).toBeTruthy();
  });
});
