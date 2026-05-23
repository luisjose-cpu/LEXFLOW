import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { AutomationStudio } from "@/components/automation-studio";

describe("P13 Automation Studio UI", () => {
  it("renders the no-code builder and workflow chain", () => {
    render(<AutomationStudio />);

    expect(screen.getByRole("heading", { name: "Automation Studio" })).toBeTruthy();
    expect(screen.getByText("Builder por pasos")).toBeTruthy();
    expect(screen.getByText("Workflow activo")).toBeTruthy();
    expect(screen.getByText("TRIGGER")).toBeTruthy();
    expect(screen.getByText("AUDIT")).toBeTruthy();
    expect(screen.getByText("RESULT")).toBeTruthy();
  });

  it("renders triggers, actions and run result states", () => {
    render(<AutomationStudio />);

    expect(screen.getByText("CASE_CREATED")).toBeTruthy();
    expect(screen.getByText("CAPTCHA_REQUIRED")).toBeTruthy();
    expect(screen.getAllByText("CREATE_TASK").length).toBeGreaterThan(0);
    expect(screen.getAllByText("SEND_PORTAL_NOTIFICATION").length).toBeGreaterThan(0);
    expect(screen.getByText("Resultado de prueba")).toBeTruthy();
    expect(screen.getAllByText("succeeded").length).toBeGreaterThan(0);
  });
});
