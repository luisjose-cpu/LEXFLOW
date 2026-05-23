import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { LegalIntelligenceCenter } from "@/components/legal-intelligence-center";
import { intelligenceSources } from "@/lib/legal-intelligence-demo";

describe("Legal intelligence center UI", () => {
  it("renders P9 dashboard, sources, alerts and trends", () => {
    render(<LegalIntelligenceCenter />);

    expect(screen.getByText("Centro de Inteligencia Juridica")).toBeTruthy();
    expect(screen.getByText("No scraping agresivo")).toBeTruthy();
    expect(screen.getByText("Noticias y jurisprudencia")).toBeTruthy();
    expect(screen.getAllByText("Alertas").length).toBeGreaterThan(1);
    expect(screen.getAllByText("Tendencias").length).toBeGreaterThan(1);
    expect(screen.getAllByText("AI Summary").length).toBeGreaterThan(0);
  });

  it("contains the required source adapters", () => {
    const sourceNames = intelligenceSources.map((source) => source.name);

    expect(sourceNames).toContain("LP Derecho");
    expect(sourceNames).toContain("Juris.pe");
    expect(sourceNames).toContain("El Peruano");
    expect(sourceNames).toContain("SPIJ");
    expect(sourceNames).toContain("Poder Judicial");
    expect(sourceNames).toContain("MPFN");
    expect(sourceNames).toContain("SINOE");
  });
});
