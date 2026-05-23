import { readFileSync } from "node:fs";
import { join } from "node:path";
import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import manifest from "@/app/manifest";
import { MobileClientExperience, MobileLawyerExperience } from "@/components/mobile-pwa";

describe("P11 mobile PWA experience", () => {
  it("renders the client mobile surface with bottom navigation and useful states", () => {
    render(<MobileClientExperience />);

    expect(screen.getByText("LEXFLOW Cliente")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Mis expedientes" })).toBeTruthy();
    expect(screen.getAllByText("Documentos").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Avisos").length).toBeGreaterThan(0);
  });

  it("renders the lawyer mobile surface with assigned work and AI review disclaimer", () => {
    render(<MobileLawyerExperience view="case-detail" />);

    expect(screen.getByText("LEXFLOW Abogado")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Cobro ejecutivo Nova" })).toBeTruthy();
    expect(screen.getByText("Resumen IA del expediente")).toBeTruthy();
    expect(screen.getByText(/Requiere.*profesional/i)).toBeTruthy();
    expect(screen.getAllByText("Tareas").length).toBeGreaterThan(0);
  });

  it("declares installable PWA metadata and mobile shortcuts", () => {
    const pwaManifest = manifest();

    expect(pwaManifest.start_url).toBe("/m/client");
    expect(pwaManifest.display).toBe("standalone");
    expect(pwaManifest.orientation).toBe("portrait");
    expect(JSON.stringify(pwaManifest.shortcuts)).toContain("/m/lawyer");
  });

  it("ships service worker and offline fallback assets", () => {
    const serviceWorker = readFileSync(join(process.cwd(), "public", "sw.js"), "utf8");
    const offlineFallback = readFileSync(join(process.cwd(), "public", "offline.html"), "utf8");

    expect(serviceWorker).toContain("lexflow-pwa-v11");
    expect(serviceWorker).toContain("/m/client");
    expect(serviceWorker).toContain("/m/lawyer");
    expect(offlineFallback).toContain("LEXFLOW");
  });
});
