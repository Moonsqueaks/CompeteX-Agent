import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TermHint } from "./TermHint";
import { TERM_EXPLANATIONS } from "./termExplanations";

const REQUIRED_TERM_LABELS = [
  "需求替代性",
  "上下文匹配度",
  "决策阶段影响力",
  "证据置信度",
  "市场信号强度",
  "质检",
  "证据可信状态",
  "动态切片",
  "威胁等级",
  "判断强度"
] as const;

describe("TermHint", () => {
  it("defines explanations for every required product-analysis term", () => {
    const labels = Object.values(TERM_EXPLANATIONS).map((term) => term.label);

    for (const label of REQUIRED_TERM_LABELS) {
      expect(labels).toContain(label);
    }
  });

  it("shows explanations on hover and keyboard focus", () => {
    render(<TermHint term="demand_substitutability" />);

    const trigger = screen.getByRole("button", { name: "需求替代性解释" });
    fireEvent.mouseEnter(trigger);

    expect(screen.getByRole("tooltip")).toHaveTextContent("两件产品能满足同一需求的程度。");

    fireEvent.mouseLeave(trigger);
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();

    fireEvent.focus(trigger);
    expect(screen.getByRole("tooltip")).toHaveTextContent("两件产品能满足同一需求的程度。");
  });

  it("keeps explanation copy free of bare English technical words", () => {
    const explanationText = Object.values(TERM_EXPLANATIONS)
      .map((term) => term.description)
      .join(" ");

    expect(explanationText).not.toMatch(/[A-Za-z]{2,}/);
  });
});
