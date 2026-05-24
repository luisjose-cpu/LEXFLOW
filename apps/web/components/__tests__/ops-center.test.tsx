import { render, screen } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { OpsCenter } from "@/components/ops-center";
import { csvTemplates, gateCommands, pilotChecklist } from "@/lib/ops-demo";

describe("Ops center UI", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("renders import templates and ordered flow", () => {
    render(<OpsCenter view="import" />);

    expect(screen.getByText("Importacion CSV")).toBeTruthy();
    expect(csvTemplates.map((item) => item.kind)).toContain("clients");
    expect(screen.getByText("Clientes")).toBeTruthy();
    expect(screen.getByText("Manifiesto documental")).toBeTruthy();
  });

  it("renders pilot readiness checklist", () => {
    render(<OpsCenter view="pilot" />);

    expect(screen.getByText("Pilot Ops Center")).toBeTruthy();
    expect(pilotChecklist.length).toBeGreaterThan(5);
    expect(screen.getByText("Tenant configurado")).toBeTruthy();
    expect(screen.getByText("Documentos verificados")).toBeTruthy();
  });

  it("renders production gate commands", () => {
    render(<OpsCenter view="gate" />);

    expect(screen.getByText("Production Gate")).toBeTruthy();
    expect(gateCommands).toContain("npm run test:api");
    expect(screen.getByText("npm run build")).toBeTruthy();
    expect(screen.getByText("Pentest")).toBeTruthy();
  });

  it("loads production gate readiness from cloud session", async () => {
    localStorage.setItem("lexflow.access_token", "tenant-token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        status: "blocked",
        public_production_status: "blocked",
        revision: "abc123",
        external_providers: { ai: "mock", whatsapp: "mock", billing: "mock" },
        summary: { blockers: 1, warnings: 2 },
        readiness: {
          public_production_ready: false,
          checks: [
            { key: "database_postgresql", ok: true, severity: "blocker", message: "Production must use PostgreSQL." },
            { key: "cors_no_localhost", ok: false, severity: "blocker", message: "Production origins must not point to localhost." }
          ]
        },
        commands: ["npm run cloud:smoke"],
        required_before_public_production: ["External pentest and monitoring"]
      })
    } as Response);

    render(<OpsCenter view="gate" />);

    expect(await screen.findByText("database_postgresql")).toBeTruthy();
    expect(screen.getByText("cors_no_localhost")).toBeTruthy();
    expect(screen.getAllByText("blocked").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText("abc123")).toBeTruthy();
    expect(screen.getByText(/ai=mock/)).toBeTruthy();
    expect(screen.getByText("npm run cloud:smoke")).toBeTruthy();
    expect(screen.getByText("External pentest and monitoring")).toBeTruthy();
  });
});
