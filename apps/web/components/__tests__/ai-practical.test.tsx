import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it } from "vitest";
import { AIPracticalPanel } from "@/components/ai-practical";
import { aiDisclaimer, aiPrompts } from "@/lib/ai-demo";

describe("AI practical UI", () => {
  it("renders practical AI panels and mandatory review warning", () => {
    render(<AIPracticalPanel />);

    expect(screen.getByText("IA practica legal")).toBeTruthy();
    expect(screen.getAllByText(aiDisclaimer).length).toBeGreaterThan(1);
    expect(screen.getByText("Pipeline documental")).toBeTruthy();
    expect(screen.getByText("Revision profesional")).toBeTruthy();
  });

  it("contains the required P8 prompt contracts", () => {
    expect(aiPrompts).toContain("summarize_document");
    expect(aiPrompts).toContain("classify_document");
    expect(aiPrompts).toContain("extract_dates");
    expect(aiPrompts).toContain("extract_parties");
    expect(aiPrompts).toContain("extract_deadlines");
    expect(aiPrompts).toContain("extract_obligations");
    expect(aiPrompts).toContain("case_summary");
    expect(aiPrompts).toContain("smart_search");
    expect(aiPrompts).toContain("draft_assistant");
  });
});
