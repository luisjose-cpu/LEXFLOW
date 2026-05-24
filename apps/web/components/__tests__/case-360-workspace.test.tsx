import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Case360Workspace } from "@/components/case-360-workspace";
import { getDemoCase360 } from "@/lib/case-360-demo";

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  localStorage.clear();
});

describe("Case360Workspace", () => {
  it("renders the operational case workspace with real action panels", () => {
    render(<Case360Workspace initialData={getDemoCase360("case-demo")} />);

    expect(screen.getByText("Acciones del expediente")).toBeTruthy();
    expect(screen.getByText("Agregar nota")).toBeTruthy();
    expect(screen.getByText("Crear tarea")).toBeTruthy();
    expect(screen.getByText("Crear audiencia")).toBeTruthy();
    expect(screen.getByText("Cierre operativo")).toBeTruthy();
    expect(screen.getByText("Actualizacion judicial")).toBeTruthy();
    expect(screen.getByText("IA expediente")).toBeTruthy();
  });

  it("loads live overview and creates audited case actions", async () => {
    localStorage.setItem("lexflow.access_token", "token");
    const overview = getDemoCase360("case-demo");
    fetchMock
      .mockResolvedValueOnce(ok(overview))
      .mockResolvedValueOnce(ok({ id: "evt-live" }))
      .mockResolvedValueOnce(ok(overview));

    render(<Case360Workspace initialData={overview} />);

    await waitFor(() => expect(screen.getByText("Expediente 360 conectado a datos reales")).toBeTruthy());
    fireEvent.change(screen.getByLabelText("Nota timeline"), { target: { value: "Nota live" } });
    fireEvent.click(screen.getByText("Agregar nota"));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/cases/case-demo/events"), expect.objectContaining({ method: "POST" })));
    expect(fetchMock).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer token" }) }));
  });

  it("runs SINOE checks and AI summaries from Expediente 360", async () => {
    localStorage.setItem("lexflow.access_token", "token");
    const overview = getDemoCase360("case-demo");
    fetchMock
      .mockResolvedValueOnce(ok(overview))
      .mockResolvedValueOnce(ok({ status: "checked" }))
      .mockResolvedValueOnce(ok({ status: "captcha_required" }))
      .mockResolvedValueOnce(ok(overview))
      .mockResolvedValueOnce(ok({ id: "ai-1", result: { summary: "Resumen del expediente" } }))
      .mockResolvedValueOnce(ok(overview));

    render(<Case360Workspace initialData={overview} />);
    await screen.findByText("Expediente 360 conectado a datos reales");

    fireEvent.click(screen.getByText(/Revisar SINOE/));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/case-sources/src-sinoe-1/sinoe/check"), expect.objectContaining({ method: "POST" })));

    fireEvent.click(screen.getByText("Generar resumen IA"));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/ai/cases/case-demo/summary"), expect.objectContaining({ method: "POST" })));
  });

  it("updates expediente lifecycle resources from the workspace", async () => {
    localStorage.setItem("lexflow.access_token", "token");
    const overview = getDemoCase360("case-demo");
    fetchMock
      .mockResolvedValueOnce(ok(overview))
      .mockResolvedValueOnce(ok({ id: "tsk-1", status: "done" }))
      .mockResolvedValueOnce(ok(overview))
      .mockResolvedValueOnce(ok({ id: "hea-1", status: "completed" }))
      .mockResolvedValueOnce(ok(overview))
      .mockResolvedValueOnce(ok({ id: "doc-1", status: "approved", is_client_visible: true }))
      .mockResolvedValueOnce(ok(overview));

    render(<Case360Workspace initialData={overview} />);
    await screen.findByText("Expediente 360 conectado a datos reales");

    fireEvent.click(screen.getByText(/Cerrar tarea:/));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/cases/case-demo/tasks/tsk-1"), expect.objectContaining({ method: "PATCH" })));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));

    fireEvent.click(screen.getByText(/Completar audiencia:/));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/cases/case-demo/hearings/hea-1"), expect.objectContaining({ method: "PATCH" })));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(5));

    fireEvent.click(screen.getByText(/Aprobar documento:/));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/cases/case-demo/documents/doc-1"), expect.objectContaining({ method: "PATCH" })));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(7));
  });
});

function ok(body: object) {
  return {
    ok: true,
    json: async () => body
  };
}
