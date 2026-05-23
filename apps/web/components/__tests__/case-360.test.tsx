import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { CaseHeader, CaseTimeline, DocumentsPanel, JudicialUpdatesPanel, NextActionsPanel } from "@/components/case-360";
import { getDemoCase360 } from "@/lib/case-360-demo";

describe("Expediente 360 UI", () => {
  it("renders the case header with status, risk and next actions", () => {
    const data = getDemoCase360("case-demo");

    render(<CaseHeader data={data} />);

    expect(screen.getByText("Cobro ejecutivo Nova Capital")).toBeTruthy();
    expect(screen.getByText("risk")).toBeTruthy();
    expect(screen.getByText("Riesgo high")).toBeTruthy();
    expect(screen.getByText("Siguiente")).toBeTruthy();
  });

  it("renders timeline, judicial updates and next actions panels", () => {
    const data = getDemoCase360("case-demo");

    render(
      <>
        <CaseTimeline items={data.timeline} />
        <JudicialUpdatesPanel items={data.judicial_updates} />
        <NextActionsPanel items={data.next_actions} />
      </>
    );

    expect(screen.getByText("Timeline")).toBeTruthy();
    expect(screen.getByText("Fuente judicial pausada")).toBeTruthy();
    expect(screen.getByText("Actualizaciones judiciales")).toBeTruthy();
    expect(screen.getByText("CAPTCHA requerido")).toBeTruthy();
    expect(screen.getByText("Proximas acciones")).toBeTruthy();
  });

  it("renders document trust lifecycle metadata", () => {
    const data = getDemoCase360("case-demo");

    render(<DocumentsPanel items={data.documents} />);

    expect(screen.getByText("Documentos")).toBeTruthy();
    expect(screen.getByText("demanda.pdf")).toBeTruthy();
    expect(screen.getByText("verified")).toBeTruthy();
    expect(screen.getByText("clean")).toBeTruthy();
    expect(screen.getByText("sha256 407e3905")).toBeTruthy();
  });
});
