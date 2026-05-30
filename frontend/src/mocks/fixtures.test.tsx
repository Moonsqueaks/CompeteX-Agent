import "@testing-library/jest-dom/vitest";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  ALL_DEVELOPMENT_MOCKS,
  mockBattlefieldFixture,
  mockOverviewFixture,
  mockProfileFixture,
  mockReportFixture,
  mockTraceFixture
} from ".";

const V2_REPORT_SECTION_KEYS = [
  "conclusion_summary",
  "competitive_landscape_judgment",
  "core_competitor_analysis",
  "user_decision_chain_analysis",
  "target_opportunities_and_risks",
  "product_strategy_recommendations",
  "evidence_quality_appendix",
  "analysis_process_appendix"
] as const;

function FixturePreview() {
  const reportTitles = mockReportFixture.section_order
    .map(
      (sectionKey) =>
        mockReportFixture[sectionKey as (typeof V2_REPORT_SECTION_KEYS)[number]]?.title
    )
    .filter(Boolean)
    .join(" / ");

  return (
    <section>
      <h1>{mockOverviewFixture.one_sentence_judgment.content}</h1>
      <p>{mockProfileFixture.product.name}</p>
      <p>{mockBattlefieldFixture.graph_nodes?.[1]?.label}</p>
      <p>{mockTraceFixture.dag_nodes?.map((node) => node.label).join(" / ")}</p>
      <p>{reportTitles}</p>
    </section>
  );
}

describe("development mock fixtures", () => {
  it("are explicitly marked as frontend development data", () => {
    expect(ALL_DEVELOPMENT_MOCKS).toHaveLength(5);

    for (const fixture of ALL_DEVELOPMENT_MOCKS) {
      expect(fixture.mock_meta.data_kind).toBe("development_mock");
      expect(fixture.mock_meta.generated_for).toBe("frontend_f03");
      expect(fixture.mock_meta.final_demo_data).toBe(false);
      expect(fixture.mock_meta.note).toContain("非最终演示数据");
    }
  });

  it("can drive a typed rendering preview for the five page areas", () => {
    render(<FixturePreview />);

    expect(screen.getByRole("heading", { name: /目标产品当前主要压力/ })).toBeInTheDocument();
    expect(screen.getByText("开发样例自动猫砂盆 A")).toBeInTheDocument();
    expect(screen.getByText("开发样例竞品 B")).toBeInTheDocument();
    expect(screen.getByText(/采集智能体/)).toBeInTheDocument();
    expect(screen.getByText(/结论摘要/)).toBeInTheDocument();
  });

  it("keeps page fixtures independent and aligned to the 2.0 page contract", () => {
    expect(mockOverviewFixture.mock_meta.fixture_name).toBe("overview");
    expect(mockProfileFixture.mock_meta.fixture_name).toBe("profile");
    expect(mockBattlefieldFixture.mock_meta.fixture_name).toBe("battlefield");
    expect(mockTraceFixture.mock_meta.fixture_name).toBe("trace");
    expect(mockReportFixture.mock_meta.fixture_name).toBe("report");

    expect(mockOverviewFixture.analysis_scope.data_source_mode).toBe("demo_snapshot");
    expect(mockBattlefieldFixture.graph_nodes).toHaveLength(3);
    expect(
      mockBattlefieldFixture.key_relations?.[0]?.four_part_explanation.response_suggestion.text
    ).toContain("详情页");
    expect(mockTraceFixture.evidence_chains?.[0]?.evidence_items?.[0]?.evidence_id).toBe(
      "ev_trace_direct"
    );
  });

  it("uses the 2.0 eight-section report fixture instead of the 1.0 report shape", () => {
    expect(mockReportFixture.section_order).toEqual([...V2_REPORT_SECTION_KEYS]);

    const reportText = JSON.stringify(mockReportFixture);
    expect(reportText).toContain("结论摘要");
    expect(reportText).toContain("竞争格局判断");
    expect(reportText).not.toContain("执行摘要");
    expect(reportText).not.toContain("目标产品画像");
    expect(reportText).not.toContain("证据索引");
  });

  it("keeps frontend fixtures visibly separate from final demo data", () => {
    const serialized = JSON.stringify(ALL_DEVELOPMENT_MOCKS);

    expect(serialized).toContain("development_mock");
    expect(serialized).toContain("仅用于前端组件开发");
    expect(serialized).not.toContain('final_demo_data":true');
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
