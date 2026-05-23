import { render, screen } from "@testing-library/react";
import Home from "@/app/page";
import React from "react";
import { describe, expect, it } from "vitest";

describe("LEXFLOW home", () => {
  it("renders the legal operating system spine", () => {
    render(<Home />);

    expect(screen.getByText("LEXFLOW")).toBeTruthy();
    expect(screen.getByText("Del cliente a la decision")).toBeTruthy();
    expect(screen.getByText("Expediente 360")).toBeTruthy();
  });
});
