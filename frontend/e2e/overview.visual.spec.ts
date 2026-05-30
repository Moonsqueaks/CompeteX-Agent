import { expect, test } from "@playwright/test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { build, preview } from "vite";

let server: Awaited<ReturnType<typeof preview>>;
let tempDir: string;

test.beforeAll(async ({ browserName }, testInfo) => {
  void browserName;
  testInfo.setTimeout(120000);
  tempDir = await mkdtemp(path.join(tmpdir(), "zijieagent-overview-visual-"));
  const outDir = path.join(tempDir, "frontend-dist");

  await build({
    build: {
      emptyOutDir: true,
      outDir
    },
    configLoader: "runner"
  });
  server = await preview({
    build: {
      outDir
    },
    configLoader: "runner",
    preview: {
      host: "127.0.0.1",
      port: 4173,
      strictPort: true
    }
  });
});

test.afterAll(async () => {
  await server.httpServer.close();
  if (tempDir) {
    await rm(tempDir, { force: true, recursive: true });
  }
});

test("overview core judgment remains visible in the desktop first viewport", async ({
  page
}, testInfo) => {
  await page.route("**/tasks/task_overview_visual/overview**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        data: overviewResponse(),
        error: null,
        trace_id: "trace_playwright_overview"
      },
      status: 200
    });
  });
  await page.route("**/tasks/task_overview_visual/battlefield**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        data: battlefieldSliceOptionsResponse(),
        error: null,
        trace_id: "trace_playwright_overview_slices"
      },
      status: 200
    });
  });

  await page.goto("/overview?task_id=task_overview_visual");

  const judgment = page.getByRole("heading", {
    exact: true,
    name: "核心直接竞品正在争夺同一多猫家庭需求。"
  });
  const scopeNotice = page.getByText("本报告基于用户提供的脱敏 SKU 快照，不代表实时全网数据。");

  await expect(judgment).toBeVisible();
  await expect(scopeNotice).toBeVisible();
  await expect(page.getByText("优先补强关键竞品对比表达")).toBeVisible();
  await expect(page.getByText("暂无可靠图片")).toBeVisible();

  const judgmentBox = await judgment.boundingBox();
  expect(judgmentBox).not.toBeNull();
  if (judgmentBox) {
    expect(judgmentBox.y + judgmentBox.height).toBeLessThanOrEqual(900);
  }

  await page.screenshot({
    fullPage: false,
    path: testInfo.outputPath("overview-first-viewport.png")
  });
});

function battlefieldSliceOptionsResponse() {
  return {
    available_slices: [
      {
        edge_count: 1,
        persona: "多猫家庭",
        price_band: "1500-2000",
        scenario: "重除臭",
        top_edge_score: 0.86
      }
    ],
    battlefield_id: "battlefield_task_overview_visual_all",
    decision_chain: [],
    evidence_cards: [],
    generated_at: "2026-05-27T08:05:00Z",
    graph_edges: [],
    graph_nodes: [],
    metadata: {},
    qa_summary: {
      open_review_task_count: 0,
      qa_status: "passed",
      resolved_review_task_count: 0,
      review_task_count: 0,
      review_task_ids: [],
      revision_message_count: 0,
      risk_claim_ids: [],
      risk_edge_ids: []
    },
    score_explanations: [],
    selected_slice: {
      persona: null,
      price_band: null,
      scenario: null
    },
    task_id: "task_overview_visual"
  };
}

function overviewResponse() {
  return {
    action_recommendations: [
      {
        action_id: "action_competitor_expression",
        description: "把核心竞品的除臭与维护成本证据放到首屏对比，减少用户跳出。",
        drilldown_refs: [],
        evidence_ids: ["ev_overview_competitor"],
        expected_impact: "提升用户对差异点的理解效率",
        missing_reference_reason: null,
        priority: "p1_current_iteration",
        responsibility_type: "content_expression",
        risk_flags: [],
        title: "优先补强关键竞品对比表达",
        trace_refs: ["analysis_agent:edge_direct_001"]
      }
    ],
    analysis_scope: {
      access_time_range: "2026-05-23 至 2026-05-27",
      category: "smart_pet_hardware",
      data_source_label: "本地快照",
      data_source_mode: "demo_snapshot",
      evidence_count: 6,
      evidence_ids: ["ev_overview_competitor", "ev_overview_risk"],
      missing_fields: [],
      platform_label: "抖音",
      platforms: ["douyin"],
      product_count: 3,
      scope_notice: "本报告基于用户提供的脱敏 SKU 快照，不代表实时全网数据。",
      sku_count: 3,
      snapshot_date: "2026-05-27",
      snapshot_version: "demo_v2",
      source_description: "用户提供的脱敏 SKU 快照",
      subcategory: "automatic_litter_box",
      task_id: "task_overview_visual"
    },
    current_slice: {
      persona: null,
      price_band: null,
      scenario: null
    },
    decision_usability: {
      evidence_ids: ["ev_overview_competitor"],
      label: "可用于初步决策",
      reason: "核心判断已有可追溯证据支撑",
      risk_flags: [],
      trace_refs: ["qa_agent:passed"],
      value: "ready_for_initial_decision"
    },
    drilldown_refs: [],
    generated_at: "2026-05-27T08:05:00Z",
    judgment_strength: {
      evidence_ids: ["ev_overview_competitor"],
      label: "明确判断",
      reason: "最高分关系与行动建议方向一致",
      risk_flags: [],
      trace_refs: ["analysis_agent:edge_direct_001"],
      value: "clear_judgment"
    },
    key_competitors: [
      {
        brand: "竞品品牌",
        competitor_type: "highest_threat_direct_competitor",
        drilldown_refs: [
          {
            label: "查看竞争关系",
            reference_type: "battlefield",
            route: "/tasks/task_overview_visual/battlefield?edge_id=edge_direct_001",
            target_id: "edge_direct_001"
          }
        ],
        evidence_credibility: {
          evidence_ids: ["ev_overview_competitor"],
          label: "可直接采纳",
          reason: "证据来自本地脱敏 SKU 快照并有访问时间",
          risk_flags: [],
          trace_refs: ["qa_agent:passed"],
          value: "directly_adoptable"
        },
        evidence_ids: ["ev_overview_competitor"],
        inclusion_reason: "关系分最高，且与目标产品争夺同一多猫家庭需求。",
        missing_reference_reason: null,
        primary_image_path: null,
        product_id: "prod_competitor",
        product_name: "核心直接竞品",
        relationship_label: "head_to_head",
        risk_flags: [],
        sku_id: "sku_01",
        threat_level: "high_threat",
        trace_refs: ["analysis_agent:edge_direct_001"]
      }
    ],
    metadata: {
      evidence_count: 6
    },
    one_sentence_judgment: {
      content: "核心直接竞品正在争夺同一多猫家庭需求。",
      drilldown_refs: [],
      evidence_ids: ["ev_overview_competitor"],
      missing_reference_reason: null,
      risk_flags: [],
      trace_refs: ["analysis_agent:edge_direct_001"]
    },
    opportunities: [],
    overview_id: "overview_task_overview_visual",
    risk_points: [
      {
        description: "部分截图仍需关注访问时间，使用时应保留证据链说明。",
        drilldown_refs: [],
        evidence_ids: ["ev_overview_risk"],
        finding_id: "risk_overview_access_time",
        finding_type: "evidence_risk",
        missing_reference_reason: null,
        risk_flags: ["missing_access_time"],
        title: "证据风险提示",
        trace_refs: ["qa_agent:review"]
      }
    ],
    status_reasons: ["证据链已覆盖首要竞品关系"],
    task_id: "task_overview_visual"
  };
}
