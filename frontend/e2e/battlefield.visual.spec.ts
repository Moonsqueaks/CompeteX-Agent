import { expect, test, type Locator, type Page } from "@playwright/test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { build, preview } from "vite";

let server: Awaited<ReturnType<typeof preview>>;
let tempDir: string;

const FRONTEND_PORT = 4174;
const baseUrl = `http://127.0.0.1:${FRONTEND_PORT}`;

test.setTimeout(150000);

test.beforeAll(async ({ browserName }, testInfo) => {
  void browserName;
  testInfo.setTimeout(240000);
  tempDir = await mkdtemp(path.join(tmpdir(), "zijieagent-battlefield-visual-"));
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
      port: FRONTEND_PORT,
      strictPort: true
    }
  });
});

test.afterAll(async () => {
  await server?.httpServer.close();
  if (tempDir) {
    await rm(tempDir, { force: true, recursive: true });
  }
});

test("battlefield graph and on-demand insight drawer stay readable on desktop and narrow screens", async ({
  page
}, testInfo) => {
  await page.route("**/tasks/task_battlefield_visual/battlefield**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        data: battlefieldResponse(),
        error: null,
        trace_id: "trace_playwright_battlefield"
      },
      status: 200
    });
  });

  await page.goto(`${baseUrl}/battlefield?task_id=task_battlefield_visual`);

  const graphPanel = page.getByRole("region", { exact: true, name: "竞争关系图" });
  const outlinePanel = page.getByLabel("竞争图谱分析大纲");
  const sliceHud = page.getByLabel("切片拨盘");
  const detailPanel = page.getByRole("complementary", { name: "竞争边详情" });

  await expect(graphPanel).toBeVisible();
  await expect(outlinePanel).toBeVisible();
  await expect(sliceHud).toBeVisible();
  await expect(detailPanel).toHaveCount(0);
  await expect(page.locator(".react-flow__node")).toHaveCount(2);
  await expect(page.locator(".react-flow__edge")).toHaveCount(1);
  await expectSliceTitleStaysOnOneLine(page);
  await expectPageHasNoHorizontalOverflow(page);
  await expectElementHasNoHorizontalOverflow(outlinePanel);

  const graphBox = await graphPanel.boundingBox();
  const hudBox = await sliceHud.boundingBox();
  const outlineBox = await outlinePanel.boundingBox();
  expect(graphBox).not.toBeNull();
  expect(hudBox).not.toBeNull();
  expect(outlineBox).not.toBeNull();

  if (!graphBox || !hudBox || !outlineBox) {
    return;
  }

  expect(outlineBox.x + outlineBox.width).toBeLessThanOrEqual(graphBox.x + 1);
  expect(hudBox.y + hudBox.height).toBeLessThanOrEqual(graphBox.y + 1);
  expect(graphBox.height).toBeGreaterThan(440);

  const desktopInsightButton = outlinePanel.getByRole("button", {
    name: /查看深研/
  });
  await expect(desktopInsightButton).toBeVisible();
  await desktopInsightButton.click({ force: true });
  await expect(detailPanel).toBeVisible();
  await expect(detailPanel).toContainText("竞争边解释");
  await expect(page.getByLabel("四段式竞争解释")).toHaveCount(0);
  await detailPanel.getByRole("tab", { name: "四段解释" }).click();
  await expect(page.getByLabel("四段式竞争解释")).toBeVisible();

  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("battlefield-desktop.png")
  });

  await page.setViewportSize({ height: 820, width: 390 });
  await page.reload();

  const narrowGraphPanel = page.getByRole("region", { exact: true, name: "竞争关系图" });
  const narrowOutlinePanel = page.getByLabel("竞争图谱分析大纲");
  const narrowSliceHud = page.getByLabel("切片拨盘");

  await expect(narrowGraphPanel).toBeVisible();
  await expect(narrowOutlinePanel).toBeVisible();
  await expect(narrowSliceHud).toBeVisible();
  await expectSliceTitleStaysOnOneLine(page);
  await expectPageHasNoHorizontalOverflow(page);
  await expectElementHasNoHorizontalOverflow(narrowOutlinePanel);

  const narrowGraphBox = await narrowGraphPanel.boundingBox();
  const narrowHudBox = await narrowSliceHud.boundingBox();
  const narrowOutlineBox = await narrowOutlinePanel.boundingBox();
  expect(narrowGraphBox).not.toBeNull();
  expect(narrowHudBox).not.toBeNull();
  expect(narrowOutlineBox).not.toBeNull();

  if (!narrowGraphBox || !narrowHudBox || !narrowOutlineBox) {
    return;
  }

  expect(narrowOutlineBox.y + narrowOutlineBox.height).toBeLessThanOrEqual(narrowGraphBox.y);
  expect(narrowHudBox.y + narrowHudBox.height).toBeLessThanOrEqual(narrowGraphBox.y + 1);
  const narrowInsightButton = narrowOutlinePanel.getByRole("button", {
    name: /查看深研/
  });
  await expect(narrowInsightButton).toBeVisible();

  await page.goto(`${baseUrl}/battlefield?task_id=task_battlefield_visual&edge_id=edge_direct_001`);
  await expect(page.getByRole("complementary", { name: "竞争边详情" })).toBeVisible();

  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("battlefield-narrow.png")
  });
});

async function expectPageHasNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth
  );
  expect(overflow).toBeLessThanOrEqual(2);
}

async function expectElementHasNoHorizontalOverflow(locator: Locator) {
  const overflow = await locator.evaluate((element) => element.scrollWidth - element.clientWidth);
  expect(overflow).toBeLessThanOrEqual(2);
}

async function expectSliceTitleStaysOnOneLine(page: Page) {
  const titleBox = await page.locator(".battlefield-modern-hud-title-text").boundingBox();
  expect(titleBox).not.toBeNull();
  if (titleBox) {
    expect(titleBox.width).toBeGreaterThan(52);
    expect(titleBox.height).toBeLessThan(28);
  }
}

function battlefieldResponse() {
  const longCompetitorName =
    "核心直接竞品 Pro Max 多猫家庭重除臭自动猫砂盆超长 SKU 名称压力测试版";

  return {
    available_slices: [
      {
        edge_count: 1,
        persona: "多猫家庭与小户型合租养宠人群",
        price_band: "1500-2000 长价格带标签",
        scenario: "重除臭与低维护频次场景",
        top_edge_score: 0.86
      }
    ],
    battlefield_id: "battlefield_task_battlefield_visual_all",
    decision_chain: [
      {
        average_edge_score: 0.86,
        claim_ids: ["claim_edge_direct"],
        edge_ids: ["edge_direct_001"],
        evidence_ids: ["ev_edge_price"],
        stage: "capability_understanding"
      }
    ],
    evidence_cards: [
      {
        access_time: "2026-05-22T09:30:00+08:00",
        access_time_status: "available",
        confidence_level: "medium",
        content_summary: "商品页快照显示竞品在除臭和维护体验上形成直接竞争。",
        evidence_id: "ev_edge_price",
        limitations: "来源为本地快照，非实时页面。",
        product_id: "prod_competitor",
        risk_flags: [],
        screenshot_path: "data/raw/sku_01/price.png",
        source_type: "douyin_sku_snapshot",
        source_url: "https://example.com/competitor"
      }
    ],
    generated_at: "2026-05-28T10:00:00+08:00",
    graph_edges: [
      {
        claim_ids: ["claim_edge_direct"],
        claim_refs: [
          {
            claim_id: "claim_edge_direct",
            confidence: 0.82,
            content: "核心直接竞品在当前切片下与目标产品争夺同一多猫家庭需求。",
            evidence_ids: ["ev_edge_price"],
            is_inference: true,
            risk_flags: [],
            status: "accepted"
          }
        ],
        competition_type: "direct",
        edge_id: "edge_direct_001",
        edge_score: 0.86,
        evidence_ids: ["ev_edge_price"],
        risk_flags: [],
        risk_status: "normal",
        score_breakdown: {
          context_match: 0.84,
          decision_stage_impact: 0.8,
          demand_substitutability: 0.92,
          evidence_confidence: 0.78,
          market_signal_strength: 0.72
        },
        score_explanations: [
          "edge_score=0.8600; competition_type=direct.",
          "demand_substitutability=0.92, context_match=0.84, decision_stage_impact=0.80."
        ],
        slice: {
          persona: "多猫家庭",
          price_band: "1500-2000",
          scenario: "重除臭"
        },
        source: "prod_target",
        target: "prod_competitor"
      }
    ],
    graph_nodes: [
      {
        brand: "目标品牌",
        label: "目标自动猫砂盆",
        node_id: "prod_target",
        role: "target",
        shop_name: "目标旗舰店"
      },
      {
        brand: "竞品品牌",
        label: longCompetitorName,
        node_id: "prod_competitor",
        role: "direct_competitor",
        shop_name: "竞品旗舰店"
      }
    ],
    key_relations: [
      {
        action_suggestion: "优先补强核心竞品对比表达。",
        claim_ids: ["claim_edge_direct"],
        competitor_brand: "竞品品牌",
        competitor_primary_image_path: null,
        competitor_product_id: "prod_competitor",
        competitor_product_name: longCompetitorName,
        edge_id: "edge_direct_001",
        evidence_credibility: {
          evidence_ids: ["ev_edge_price"],
          label: "可直接采纳",
          reason:
            "证据具备来源、访问时间、截图路径和 QA 通过记录，且这段说明故意较长用于覆盖左侧分栏横向自适应。",
          risk_flags: [],
          trace_refs: ["qa_agent:passed"],
          value: "directly_adoptable"
        },
        evidence_ids: ["ev_edge_price"],
        four_part_explanation: {
          decision_stage_impact: {
            claim_ids: ["claim_edge_direct"],
            evidence_ids: ["ev_edge_price"],
            is_analysis_suggestion: false,
            risk_flags: [],
            text: "主要影响能力理解。",
            trace_refs: ["analysis_agent:edge_direct_001"]
          },
          response_suggestion: {
            claim_ids: ["claim_edge_direct"],
            evidence_ids: ["ev_edge_price"],
            is_analysis_suggestion: true,
            risk_flags: [],
            text: "补强除臭和维护成本对比。",
            trace_refs: ["analysis_agent:edge_direct_001"]
          },
          strength: {
            claim_ids: ["claim_edge_direct"],
            evidence_ids: ["ev_edge_price"],
            is_analysis_suggestion: false,
            risk_flags: [],
            text: "证据完整且关系明确。",
            trace_refs: ["analysis_agent:edge_direct_001"]
          },
          why_competitor: {
            claim_ids: ["claim_edge_direct"],
            evidence_ids: ["ev_edge_price"],
            is_analysis_suggestion: false,
            risk_flags: [],
            text: "同一多猫家庭需求下形成正面竞争。",
            trace_refs: ["analysis_agent:edge_direct_001"]
          }
        },
        inclusion_reason:
          "关系分最高，且与目标产品争夺同一多猫家庭、重除臭和低维护频次需求；该说明较长时也必须在卡片内自然换行。",
        is_default_visible: true,
        relationship_label: "head_to_head",
        relationship_label_explanation: "正面争夺同一需求和同一决策场景。",
        risk_flags: [],
        target_product_id: "prod_target",
        threat_level: "high_threat",
        trace_refs: ["analysis_agent:edge_direct_001"]
      }
    ],
    metadata: {
      edge_count: 1,
      node_count: 2
    },
    qa_summary: {
      open_review_task_count: 0,
      qa_status: "passed",
      resolved_review_task_count: 1,
      review_task_count: 1,
      review_task_ids: ["review_price_access_time"],
      revision_message_count: 1,
      risk_claim_ids: [],
      risk_edge_ids: []
    },
    relation_filter: {
      can_expand_all: false,
      default_limit: 5,
      include_all_relations: false,
      total_relation_count: 13,
      visible_relation_count: 5
    },
    score_explanations: [
      {
        edge_id: "edge_direct_001",
        edge_score: 0.86,
        evidence_ids: ["ev_edge_price"],
        explanations: ["五维评分均来自结构化边与证据。"],
        score_breakdown: {
          context_match: 0.84,
          decision_stage_impact: 0.8,
          demand_substitutability: 0.92,
          evidence_confidence: 0.78,
          market_signal_strength: 0.72
        }
      }
    ],
    selected_slice: {
      persona: null,
      price_band: null,
      scenario: null
    },
    task_id: "task_battlefield_visual"
  };
}
