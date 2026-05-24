import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  CaptchaCheckpointModal,
  SettingsSinoeIntegration,
  SinoeCaseSourceForm,
  SinoeUpdateHistory,
  SinoeUpdatePanel
} from "@/components/sinoe-integration";
import { getDemoCase360 } from "@/lib/case-360-demo";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  localStorage.clear();
  localStorage.setItem("lexflow.access_token", "token");
});

describe("SINOE integration UI", () => {
  it("renders settings status, saves credentials and tests connection without exposing password", async () => {
    fetchMock
      .mockResolvedValueOnce(ok({ provider: "SINOE", configured: false, status: "not_configured", last_checked_at: null, username_hint: null }))
      .mockResolvedValueOnce(ok({ provider: "SINOE", configured: true, status: "configured", last_checked_at: null, username_hint: "de***" }))
      .mockResolvedValueOnce(ok({ provider: "SINOE", configured: true, status: "connected", last_checked_at: "2026-05-24T10:00:00Z", username_hint: "de***" }));

    render(<SettingsSinoeIntegration />);

    expect(await screen.findByText("SINOE")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Usuario SINOE"), { target: { value: "demo.sinoe" } });
    fireEvent.change(screen.getByLabelText("Contrasena SINOE"), { target: { value: "SinoeMockPassword123!" } });
    fireEvent.click(screen.getByText("Guardar credenciales"));
    expect(await screen.findByText("Credenciales SINOE guardadas cifradas.")).toBeTruthy();
    expect(screen.queryByText("SinoeMockPassword123!")).toBeNull();

    fireEvent.click(screen.getByText("Probar conexion"));
    expect(await screen.findByText("Conexion mock SINOE validada.")).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/settings/integrations/sinoe/test"), expect.objectContaining({ method: "POST" }));
  });

  it("renders SINOE source, review action, update history and CAPTCHA modal", () => {
    const data = getDemoCase360("case-demo");

    render(
      <>
        <SinoeUpdatePanel sources={data.case_sources} />
        <SinoeUpdateHistory updates={data.judicial_updates} />
        <CaptchaCheckpointModal checkpoint={{ id: "chk-1", status: "pending", reason: "captcha_required" }} />
      </>
    );

    expect(screen.getByText("Fuentes SINOE")).toBeTruthy();
    expect(screen.getAllByText("Revisar ahora")[0]).toBeTruthy();
    expect(screen.getByText("Historial SINOE")).toBeTruthy();
    expect(screen.getByText("SINOE requiere verificacion humana para continuar.")).toBeTruthy();
    expect(screen.getByText(/automatizacion queda pausada/i)).toBeTruthy();
  });

  it("links a SINOE source from Expediente 360 state", async () => {
    fetchMock.mockResolvedValueOnce(ok({ id: "src-1", source_type: "sinoe", status: "active" }));
    render(<SinoeCaseSourceForm caseId="case-demo" />);

    fireEvent.change(screen.getByLabelText("Numero de expediente"), { target: { value: "SINOE-2026-001" } });
    fireEvent.click(screen.getByText("Agregar fuente SINOE"));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/cases/case-demo/sources/sinoe"), expect.objectContaining({ method: "POST" })));
    expect(await screen.findByText("Fuente SINOE vinculada al expediente.")).toBeTruthy();
  });
});

function ok(body: object) {
  return {
    ok: true,
    json: async () => body
  };
}
