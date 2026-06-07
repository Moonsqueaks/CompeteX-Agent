import "@testing-library/jest-dom/vitest";

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TermHint } from "./components/TermHint";
import { TERM_DICTIONARY } from "./domain/termExplanations";

const REQUIRED_TERM_LABELS = [
  "需求替代性",
  "场景匹配度",
  "购买路径影响",
  "证据支撑度",
  "市场信号强度",
  "QA 质检打回",
  "证据可信度",
  "动态切片",
  "综合威胁等级",
  "判断强度"
] as const;

describe("TermHint", () => {
  it("defines explanations for every required product-analysis term", () => {
    const labels = Object.values(TERM_DICTIONARY).map((term) => term.name);

    for (const label of REQUIRED_TERM_LABELS) {
      expect(labels).toContain(label);
    }
  });

  it("shows professional and business-scenario explanations on hover", async () => {
    render(<TermHint term="demand_substitutability" />);

    const trigger = screen.getByRole("button", { name: "需求替代性解释" });
    fireEvent.mouseEnter(trigger);

    expect(
      await screen.findByText("衡量两款产品在核心功能与解决用户底层痛点上的重合程度。")
    ).toBeInTheDocument();
    expect(
      screen.getByText("业务思考：如果用户买了这款竞品，是否意味着不再需要你的产品？")
    ).toBeInTheDocument();

    fireEvent.mouseLeave(trigger);
  });

  it("can render only the info icon when surrounding copy already names the term", () => {
    render(
      <p>
        需求替代性
        <TermHint term="demand_substitutability" showLabel={false} />
      </p>
    );

    const trigger = screen.getByRole("button", { name: "需求替代性解释" });

    expect(trigger).toBeInTheDocument();
    expect(trigger).not.toHaveTextContent("需求替代性");
    expect(screen.getAllByText("需求替代性")).toHaveLength(1);
  });

  it("keeps required dictionary entries structured for professional and scenario copy", () => {
    const explanationText = Object.values(TERM_DICTIONARY)
      .map((term) => `${term.professional} ${term.scenario}`)
      .join(" ");

    expect(explanationText).toContain("业务思考");
    expect(Object.values(TERM_DICTIONARY).every((term) => term.professional && term.scenario)).toBe(
      true
    );
  });
});
