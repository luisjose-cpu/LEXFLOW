import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { OpsCenter } from "@/components/ops-center";
import { csvTemplates, gateCommands, pilotChecklist } from "@/lib/ops-demo";

describe("Ops center UI", () => {
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
});
