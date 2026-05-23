import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import {
  CaptchaCheckpointModal,
  JudicialSourcesPanel,
  JudicialUpdatesList,
  SourceConfigurationForm,
  demoJudicialSources,
  demoJudicialUpdates
} from "@/components/judicial-sources";

describe("Judicial source UI", () => {
  it("renders sources and CAPTCHA state without suggesting evasion", () => {
    render(<JudicialSourcesPanel sources={demoJudicialSources} />);

    expect(screen.getByText("Fuentes judiciales")).toBeTruthy();
    expect(screen.getByText("Poder Judicial Demo")).toBeTruthy();
    expect(screen.getByText("CAPTCHA")).toBeTruthy();
  });

  it("renders checkpoint modal and source configuration form", () => {
    render(
      <>
        <CaptchaCheckpointModal checkpoint={{ id: "chk-1", status: "pending", reason: "captcha_required" }} />
        <SourceConfigurationForm />
        <JudicialUpdatesList updates={demoJudicialUpdates} />
      </>
    );

    expect(screen.getByText("Intervencion humana requerida")).toBeTruthy();
    expect(screen.getByText(/no intentara evadir controles anti-bot/i)).toBeTruthy();
    expect(screen.getByText("Configurar fuente")).toBeTruthy();
    expect(screen.getByText("Timeline judicial")).toBeTruthy();
  });
});
