import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { CommunicationCenter } from "@/components/communication-center";
import { messageTemplates } from "@/lib/communication-demo";

describe("Communication center UI", () => {
  it("renders multichannel threads, templates, and WhatsApp mock state", () => {
    render(<CommunicationCenter />);

    expect(screen.getByText("Comunicacion multicanal")).toBeTruthy();
    expect(screen.getAllByText("WhatsApp mock").length).toBeGreaterThan(0);
    expect(screen.getByText("Historial por expediente")).toBeTruthy();
    expect(screen.getByText("Enviar WhatsApp mock")).toBeTruthy();
  });

  it("contains the required P7 templates", () => {
    const codes = messageTemplates.map((template) => template.code);

    expect(codes).toContain("audiencia_proxima");
    expect(codes).toContain("documento_requerido");
    expect(codes).toContain("informe_disponible");
    expect(codes).toContain("actualizacion_expediente");
    expect(codes).toContain("proximo_paso");
  });
});
