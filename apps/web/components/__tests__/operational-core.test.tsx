import { fireEvent, render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import {
  CaseCreateWizard,
  CaseResourcePage,
  CasesDashboard,
  ClientDetail,
  ClientOnboardingWizard,
  SearchGlobalBar
} from "@/components/operational-core";
import { findCase, findClient } from "@/lib/operational-demo";

describe("Operational core UI", () => {
  it("renders global search with autocomplete, recent searches, favorites and advanced buckets", () => {
    render(<SearchGlobalBar />);

    fireEvent.change(screen.getByPlaceholderText(/Buscar cliente/i), { target: { value: "Nova" } });

    expect(screen.getAllByText("Nova Capital")[0]).toBeTruthy();
    expect(screen.getByText("Resultado avanzado")).toBeTruthy();
    expect(screen.getAllByText("Favorito")[0]).toBeTruthy();
  });

  it("renders client detail with cases, risk, documents, timeline and communications", () => {
    render(<ClientDetail client={findClient("cli-nova")} />);

    expect(screen.getByText("Cliente 360")).toBeTruthy();
    expect(screen.getAllByText("Cobro ejecutivo Nova")[0]).toBeTruthy();
    expect(screen.getByText("Documentos del cliente")).toBeTruthy();
    expect(screen.getByText("Timeline cliente")).toBeTruthy();
    expect(screen.getByText("Comunicaciones")).toBeTruthy();
    expect(screen.getAllByText("Riesgo")[0]).toBeTruthy();
  });

  it("renders client and case creation wizards with all expected steps", () => {
    render(
      <>
        <ClientOnboardingWizard />
        <CaseCreateWizard />
      </>
    );

    expect(screen.getByText("Expedientes iniciales")).toBeTruthy();
    expect(screen.getByText("Configuracion portal")).toBeTruthy();
    expect(screen.getByText("Automation")).toBeTruthy();
    expect(screen.getByText("SINOE")).toBeTruthy();
  });

  it("renders cases dashboard and SINOE resource page without duplicating judicial logic", () => {
    render(
      <>
        <CasesDashboard />
        <CaseResourcePage legalCase={findCase("case-demo")} type="judicial" />
      </>
    );

    expect(screen.getByText("Centro de expedientes")).toBeTruthy();
    expect(screen.getAllByText("Cobro ejecutivo Nova")[0]).toBeTruthy();
    expect(screen.getAllByText("Actualizaciones judiciales SINOE")[0]).toBeTruthy();
    expect(screen.getByText("Hash y evidencia gestionados por SINOE Module")).toBeTruthy();
  });
});
