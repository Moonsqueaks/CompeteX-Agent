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
  tempDir = await mkdtemp(path.join(tmpdir(), "zijieagent-report-visual-"));
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

test("report print view hides navigation controls and keeps formal content visible", async ({
  page
}, testInfo) => {
  await page.route("**/tasks/task_report_visual/report", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        data: reportResponse(),
        error: null,
        trace_id: "trace_playwright_report"
      },
      status: 200
    });
  });

  await page.goto("/report?task_id=task_report_visual");

  await expect(page.getByRole("heading", { exact: true, name: "结论摘要" })).toBeVisible();
  await page.getByRole("button", { name: "切换打印视图" }).click();

  await expect(page.locator(".workspace-sidebar")).toBeHidden();
  await expect(page.locator(".workspace-header")).toBeHidden();
  await expect(page.getByLabel("报告工作台工具栏")).toBeHidden();
  await expect(page.getByLabel("静态图谱摘要")).toBeVisible();
  await expect(page.getByLabel("报告章节")).toBeVisible();
  await expect(page.getByRole("button", { name: "查看依据" })).toHaveCount(0);
  await expect(page.getByText("分析判断：目标产品需要优先补强核心竞品对比表达。")).toBeVisible();

  const titleBox = await page.getByRole("heading", { exact: true, name: "结论摘要" }).boundingBox();
  expect(titleBox).not.toBeNull();
  if (titleBox) {
    expect(titleBox.y + titleBox.height).toBeLessThanOrEqual(900);
  }

  await page.screenshot({
    fullPage: false,
    path: testInfo.outputPath("report-print-view.png")
  });
});

function reportResponse() {
  return {
    analysis_process_appendix: reportSection(
      "analysis_process_appendix",
      "分析流程与系统能力附录",
      [
        {
          appendix_type: "workflow",
          qa_revision: "已记录质检打回、证据补齐和分析重算。"
        }
      ]
    ),
    competitive_landscape_judgment: reportSection(
      "competitive_landscape_judgment",
      "竞争格局判断",
      [
        {
          claim_ids: ["claim_report_visual"],
          edge_ids: ["edge_report_visual"],
          evidence_ids: ["ev_report_visual"],
          judgment_strength: "明确判断",
          summary: "核心直接竞品在当前切片下构成高威胁。"
        }
      ]
    ),
    conclusion_summary: reportSection("conclusion_summary", "结论摘要", [
      {
        claim_ids: ["claim_report_visual"],
        evidence_ids: ["ev_report_visual"],
        is_inference: true,
        summary: "分析判断：目标产品需要优先补强核心竞品对比表达。"
      }
    ]),
    core_competitor_analysis: reportSection("core_competitor_analysis", "核心竞品拆解", [
      {
        competitor_product_name: "核心直接竞品",
        evidence_ids: ["ev_report_visual"],
        relationship_label: "正面硬碰",
        threat_level: "高威胁"
      }
    ]),
    evidence_quality_appendix: reportSection("evidence_quality_appendix", "证据与质检附录", [
      {
        evidence_ids: ["ev_report_visual"],
        qa_status: "通过",
        summary: "证据来自本地脱敏 SKU 快照，非实时全网数据。"
      }
    ]),
    generated_at: "2026-05-30T08:00:00Z",
    product_strategy_recommendations: reportSection(
      "product_strategy_recommendations",
      "产品策略建议",
      [
        {
          evidence_ids: ["ev_report_visual"],
          priority: "P1 本轮优化",
          recommendation: "优先解释除臭、维护成本和安全机制的可验证依据。",
          responsibility_type: "商品详情页/内容表达"
        }
      ]
    ),
    report_id: "report_task_report_visual_001",
    section_order: [
      "conclusion_summary",
      "competitive_landscape_judgment",
      "core_competitor_analysis",
      "user_decision_chain_analysis",
      "target_opportunities_and_risks",
      "product_strategy_recommendations",
      "evidence_quality_appendix",
      "analysis_process_appendix"
    ],
    target_opportunities_and_risks: reportSection(
      "target_opportunities_and_risks",
      "目标产品机会与风险",
      [
        {
          evidence_ids: ["ev_report_visual"],
          opportunity: "商品详情页可补强证据呈现。",
          risk: "部分结论仍应标记为分析判断。"
        }
      ]
    ),
    task_id: "task_report_visual",
    title: "竞品分析报告",
    user_decision_chain_analysis: reportSection("user_decision_chain_analysis", "用户决策链分析", [
      {
        decision_stage: "信任建立",
        evidence_ids: ["ev_report_visual"],
        summary: "用户在下单前会比较除臭、安全和维护成本证据。"
      }
    ])
  };
}

function reportSection(sectionId: string, title: string, items: Array<Record<string, unknown>>) {
  return {
    claim_ids: ["claim_report_visual"],
    evidence_ids: ["ev_report_visual"],
    items,
    risk_flags: [],
    section_id: sectionId,
    summary: `${title}用于打印视图验证。`,
    title
  };
}
