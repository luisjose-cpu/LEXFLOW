import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { BillingSaaS, PricingCards, SubscriptionStatusCard, UpgradePrompt, UsageMeter } from "@/components/billing-saas";
import { usageMeters } from "@/lib/billing-demo";

describe("P12 Billing SaaS UI", () => {
  it("renders pricing cards and feature table for all plans", () => {
    render(<BillingSaaS view="pricing" />);

    expect(screen.getByRole("heading", { name: "Planes SaaS" })).toBeTruthy();
    expect(screen.getAllByText("START").length).toBeGreaterThan(0);
    expect(screen.getAllByText("PRO").length).toBeGreaterThan(0);
    expect(screen.getAllByText("AI").length).toBeGreaterThan(0);
    expect(screen.getAllByText("ENTERPRISE").length).toBeGreaterThan(0);
    expect(screen.getByText("Tabla de modulos por plan")).toBeTruthy();
  });

  it("renders onboarding and current subscription surfaces", () => {
    render(
      <>
        <BillingSaaS view="onboarding" />
        <SubscriptionStatusCard />
      </>
    );

    expect(screen.getByText("Crear tenant")).toBeTruthy();
    expect(screen.getByText("Activar modulos")).toBeTruthy();
    expect(screen.getByText("Suscripcion actual")).toBeTruthy();
    expect(screen.getByText("MOCK-20260522-AI")).toBeTruthy();
  });

  it("renders usage meters and upgrade prompts", () => {
    render(
      <>
        <UsageMeter item={usageMeters[1]} />
        <UpgradePrompt />
        <PricingCards />
      </>
    );

    expect(screen.getByText("Trabajos IA")).toBeTruthy();
    expect(screen.getByText("Upgrade recomendado")).toBeTruthy();
    expect(screen.getByText("Contactar ventas")).toBeTruthy();
  });

  it("renders feature gate center with active and upgrade states", () => {
    render(<BillingSaaS view="features" />);

    expect(screen.getByText("Feature gates activos")).toBeTruthy();
    expect(screen.getAllByText("Activo").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Upgrade requerido").length).toBeGreaterThan(0);
  });
});
