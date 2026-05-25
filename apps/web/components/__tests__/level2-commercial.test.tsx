import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { CRMBoard, FinancialOverview, Level2DemoMode, RiskDashboard, WarRoomDashboard } from "../level2-commercial";

describe("Level 2 commercial modules", () => {
  it("renders War Room dashboard", () => {
    render(<WarRoomDashboard />);
    expect(screen.getByText("War Room Legal")).toBeTruthy();
    expect(screen.getAllByText("Casos criticos").length).toBeGreaterThan(0);
    expect(screen.getByText("Mission control")).toBeTruthy();
  });

  it("renders Legal CRM board and lead cards", () => {
    render(<CRMBoard />);
    expect(screen.getByText("Pipeline comercial legal")).toBeTruthy();
    expect(screen.getByText("Inversiones Pacifico")).toBeTruthy();
    expect(screen.getByPlaceholderText(/Buscar lead/i)).toBeTruthy();
  });

  it("renders financial overview", () => {
    render(<FinancialOverview />);
    expect(screen.getByText("Rentabilidad por expediente")).toBeTruthy();
    expect(screen.getByText("Mapa financiero")).toBeTruthy();
    expect(screen.getByText("Contrato marco Mercurio")).toBeTruthy();
  });

  it("renders risk dashboard", () => {
    render(<RiskDashboard />);
    expect(screen.getByText("Riesgo juridico operativo")).toBeTruthy();
    expect(screen.getByText("Breakdown")).toBeTruthy();
    expect(screen.getByText("Heatmap")).toBeTruthy();
  });

  it("renders demo selector and reset controls", () => {
    render(<Level2DemoMode />);
    expect(screen.getByText("Demo comercial LEXFLOW")).toBeTruthy();
    expect(screen.getByText("Estudio litigios")).toBeTruthy();
    expect(screen.getByText("Reset Demo")).toBeTruthy();
  });
});
