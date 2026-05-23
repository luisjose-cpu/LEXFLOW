import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { LegalCommandCenter } from "@/components/legal-command-center";
import { commandKpis } from "@/lib/command-center-demo";

describe("Legal command center UI", () => {
  it("renders executive dashboard panels", () => {
    render(<LegalCommandCenter />);

    expect(screen.getByText("Legal Command Center")).toBeTruthy();
    expect(screen.getByText("Riesgo operativo")).toBeTruthy();
    expect(screen.getByText("Productividad")).toBeTruthy();
    expect(screen.getByText("Monitoreo judicial")).toBeTruthy();
    expect(screen.getByText("Inteligencia juridica")).toBeTruthy();
  });

  it("renders command mode decision queue and required KPIs", () => {
    render(<LegalCommandCenter mode="command" />);

    expect(screen.getByText("Decision queue")).toBeTruthy();
    expect(commandKpis.map((item) => item.label)).toContain("Casos activos");
    expect(commandKpis.map((item) => item.label)).toContain("CAPTCHA");
    expect(commandKpis.map((item) => item.label)).toContain("Noticias");
  });
});
