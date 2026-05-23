import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { PortalCaseDetailView, PortalHomeView, PortalLoginView } from "@/components/client-portal";
import { portalDocuments, portalTimeline } from "@/lib/client-portal-demo";

describe("Client portal UI", () => {
  it("renders secure login and client home", () => {
    render(<PortalLoginView />);
    expect(screen.getByText("Nova Capital")).toBeTruthy();
    expect(screen.getByText("Acceso seguro")).toBeTruthy();

    render(<PortalHomeView />);
    expect(screen.getAllByText("Portal Cliente").length).toBeGreaterThan(0);
    expect(screen.getByText("Timeline visible")).toBeTruthy();
  });

  it("only includes authorized documents and visible timeline demo data", () => {
    expect(portalDocuments.some((item) => item.filename === "estrategia-interna.pdf")).toBe(false);
    expect(portalTimeline.some((item) => item.title === "Actualizacion no aprobada")).toBe(false);

    render(<PortalCaseDetailView />);
    expect(screen.getByText("Documentos autorizados")).toBeTruthy();
    expect(screen.getByText("storage verificado")).toBeTruthy();
    expect(screen.getByText("sha256 407e3905")).toBeTruthy();
    expect(screen.getByText("Auto reconoce personeria")).toBeTruthy();
    expect(screen.queryByText("Estrategia interna")).toBeNull();
    expect(screen.queryByText("Actualizacion no aprobada")).toBeNull();
  });
});
