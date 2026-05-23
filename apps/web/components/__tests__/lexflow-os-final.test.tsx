import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { LexflowOSFinal } from "@/components/lexflow-os-final";
import { demoSteps, osModules, ragPipeline } from "@/lib/lexflow-os-demo";

describe("LEXFLOW OS final UI", () => {
  it("renders final OS modules and release state", () => {
    render(<LexflowOSFinal />);

    expect(screen.getByRole("heading", { name: "LEXFLOW OS Final" })).toBeTruthy();
    expect(osModules.map((item) => item.name)).toContain("Legal Memory");
    expect(osModules.map((item) => item.name)).toContain("RAG Legal");
    expect(screen.getAllByText("Legal Memory").length).toBeGreaterThan(0);
    expect(screen.getAllByText("RAG Legal").length).toBeGreaterThan(0);
    expect(screen.getByText(/RELEASE READY FOR PILOT \/ NOT READY FOR PUBLIC PRODUCTION/)).toBeTruthy();
  });

  it("shows the RAG pipeline and evidence rule", () => {
    render(<LexflowOSFinal />);

    expect(ragPipeline).toContain("Vector store");
    expect(screen.getByText("Respuesta con fuentes")).toBeTruthy();
    expect(screen.getByText("Toda respuesta cita fuente. Si no hay evidencia, responde: No encontre evidencia en las fuentes disponibles.")).toBeTruthy();
  });

  it("shows the demo E2E chain through audit log", () => {
    render(<LexflowOSFinal view="demo" />);

    expect(demoSteps[0]).toBe("Socio ve dashboard");
    expect(screen.getByText("Socio ve dashboard")).toBeTruthy();
    expect(screen.getByText("WhatsApp mock al cliente")).toBeTruthy();
    expect(screen.getByText("Audit log registra")).toBeTruthy();
    expect(screen.getByText("Demo E2E activo para recorrido comercial.")).toBeTruthy();
  });
});
