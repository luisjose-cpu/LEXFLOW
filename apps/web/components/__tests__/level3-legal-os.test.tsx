import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { DigitalTwinDashboard, KnowledgeVault, LegalGraphExplorer, ManagementCopilot, MarketplaceCatalog, MemorySearch, RAGViewer } from "../level3-legal-os";

describe("Level 3 Legal OS modules", () => {
  it("renders Digital Twin dashboard", () => {
    render(<DigitalTwinDashboard />);
    expect(screen.getByText("Gemelo digital del estudio")).toBeTruthy();
    expect(screen.getByText("Carga de abogados")).toBeTruthy();
    expect(screen.getByText("Complejidad de expedientes")).toBeTruthy();
  });

  it("renders Knowledge Vault libraries", () => {
    render(<KnowledgeVault />);
    expect(screen.getByText("Biblioteca viva del estudio")).toBeTruthy();
    expect(screen.getByText("Demanda ejecutiva con anexos")).toBeTruthy();
    expect(screen.getByPlaceholderText(/Buscar casos parecidos/i)).toBeTruthy();
  });

  it("renders Legal Graph explorer", () => {
    render(<LegalGraphExplorer />);
    expect(screen.getByText("Grafo legal operativo")).toBeTruthy();
    expect(screen.getByText("Relationship map")).toBeTruthy();
    expect(screen.getByText("Nova Capital")).toBeTruthy();
  });

  it("renders Management Copilot with cited sources", () => {
    render(<ManagementCopilot />);
    expect(screen.getByText("IA ejecutiva con fuentes")).toBeTruthy();
    expect(screen.getByText("Respuesta explicable")).toBeTruthy();
    expect(screen.getByText("Demanda Nova.pdf")).toBeTruthy();
  });

  it("renders Marketplace catalog", () => {
    render(<MarketplaceCatalog />);
    expect(screen.getByText("Marketplace extensible")).toBeTruthy();
    expect(screen.getByText("SINOE Human Checkpoint Pack")).toBeTruthy();
  });

  it("renders Memory and RAG views", () => {
    render(<MemorySearch />);
    expect(screen.getByText("Memoria legal contextual")).toBeTruthy();
    expect(screen.getByText("Demanda Nova.pdf")).toBeTruthy();

    render(<RAGViewer />);
    expect(screen.getByText("RAG con contexto y citas")).toBeTruthy();
    expect(screen.getByText("AI Agents framework")).toBeTruthy();
  });
});
