import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  ALL_DEVELOPMENT_MOCKS,
  mockBattlefieldFixture,
  mockProfileFixture,
  mockReportFixture,
  mockTraceFixture
} from ".";

function FixturePreview() {
  return (
    <section>
      <h1>{mockProfileFixture.target_product.name}</h1>
      <p>{mockBattlefieldFixture.graph.nodes[1]?.label}</p>
      <p>{mockTraceFixture.dag.nodes.map((node) => node.label).join(" / ")}</p>
      <p>{mockReportFixture.sections.map((section) => section.title).join(" / ")}</p>
    </section>
  );
}

describe("development mock fixtures", () => {
  it("are explicitly marked as frontend development data", () => {
    expect(ALL_DEVELOPMENT_MOCKS).toHaveLength(4);

    for (const fixture of ALL_DEVELOPMENT_MOCKS) {
      expect(fixture.mock_meta.data_kind).toBe("development_mock");
      expect(fixture.mock_meta.generated_for).toBe("frontend_f03");
      expect(fixture.mock_meta.final_demo_data).toBe(false);
      expect(fixture.mock_meta.note).toContain("非最终演示数据");
    }
  });

  it("can drive a typed rendering preview for the four page areas", () => {
    render(<FixturePreview />);

    expect(screen.getByRole("heading", { name: "开发样例自动猫砂盆 A" })).toBeInTheDocument();
    expect(screen.getByText("开发样例竞品 B")).toBeInTheDocument();
    expect(screen.getByText(/采集智能体/)).toBeInTheDocument();
    expect(screen.getByText(/证据索引/)).toBeInTheDocument();
  });

  it("keeps page fixtures independent", () => {
    expect(mockProfileFixture.mock_meta.fixture_name).toBe("profile");
    expect(mockBattlefieldFixture.mock_meta.fixture_name).toBe("battlefield");
    expect(mockTraceFixture.mock_meta.fixture_name).toBe("trace");
    expect(mockReportFixture.mock_meta.fixture_name).toBe("report");
  });

  it("does not contain obvious secrets, phone numbers, or account identifiers", () => {
    const serialized = JSON.stringify(ALL_DEVELOPMENT_MOCKS);
    const forbiddenPatterns = [
      /api[_-]?key/i,
      /bearer\s+[a-z0-9._-]+/i,
      /password/i,
      /secret/i,
      /sk-[a-z0-9]{20,}/i,
      /AKIA[0-9A-Z]{16}/,
      /1[3-9]\d{9}/,
      /\b(?:account|open|union)_?id\b/i
    ];

    for (const pattern of forbiddenPatterns) {
      expect(serialized).not.toMatch(pattern);
    }
  });
});
