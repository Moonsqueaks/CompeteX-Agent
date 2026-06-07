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
  tempDir = await mkdtemp(path.join(tmpdir(), "zijieagent-trace-visual-"));
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
      port: 4174,
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

test("trace DAG, revision details, and folded prompts stay readable on desktop", async ({
  page
}, testInfo) => {
  await page.route("**/tasks/task_trace_visual/trace", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        data: traceResponse(),
        error: null,
        trace_id: "trace_playwright_trace"
      },
      status: 200
    });
  });
  await page.route("**/tasks/task_trace_visual", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        data: taskStatusResponse(),
        error: null,
        trace_id: "trace_playwright_task_status"
      },
      status: 200
    });
  });

  await page.goto("http://127.0.0.1:4174/trace?task_id=task_trace_visual");

  const sidebar = page.getByLabel("主导航");
  const main = page.locator(".workspace-main");
  const evidenceChain = page.getByRole("region", { exact: true, name: "证据链" });

  await expect(evidenceChain).toBeVisible();
  await expect(page.getByRole("tab", { name: /证据链/ })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByText("核心直接竞品在当前切片下形成价格与除臭竞争。")).toBeVisible();
  await expect(page.getByText("商品页快照显示竞品价格与除臭卖点。")).toBeVisible();
  await expect(page.locator(".trace-modern-source-url")).toContainText("visual_trace_readability");

  const evidenceCardBox = await page.locator(".trace-modern-evidence-card").first().boundingBox();
  const evidenceTitleBox = await page.locator(".trace-modern-evidence-card h5").first().boundingBox();
  const sourceUrlBox = await page.locator(".trace-modern-source-url").first().boundingBox();
  expect(evidenceCardBox).not.toBeNull();
  expect(evidenceTitleBox).not.toBeNull();
  expect(sourceUrlBox).not.toBeNull();
  if (evidenceCardBox && evidenceTitleBox && sourceUrlBox) {
    expect(evidenceCardBox.width).toBeGreaterThan(440);
    expect(evidenceTitleBox.width).toBeGreaterThan(300);
    expect(evidenceTitleBox.height).toBeLessThan(120);
    expect(sourceUrlBox.width).toBeGreaterThan(220);
  }

  await page.getByRole("tab", { name: /智能体过程/ }).click();

  const graphPanel = page.getByRole("region", { exact: true, name: "流程图状态" });
  const traceSummary = page.getByRole("complementary", { name: "追踪数据摘要" });
  const technicalDetails = page.locator("details.trace-technical-details");

  await expect(graphPanel).toBeVisible();
  await expect(traceSummary).toBeVisible();
  await expect(page.locator(".react-flow__node")).toHaveCount(4);
  await expect(technicalDetails).toBeVisible();
  expect(await technicalDetails.getAttribute("open")).toBeNull();

  await page.getByRole("tab", { name: /质检记录/ }).click();
  await expect(page.getByRole("region", { name: "质检记录" })).toContainText("价格证据完整性");
  await expect(page.getByRole("region", { name: "质检记录" })).toContainText("已解决");
  await expect(page.getByRole("region", { name: "质检记录" })).toContainText("否，当前已闭环");

  await page.getByRole("tab", { name: /差异记录/ }).click();
  await expect(page.getByRole("region", { name: "差异记录" })).toContainText("QA 打回修复");
  await expect(page.getByRole("region", { name: "差异记录" })).toContainText(
    "补齐访问时间后，相关结论可以进入可复核状态。"
  );
  await expect(page.getByRole("region", { name: "差异记录" })).toContainText("查看结构化前后值");

  await page.getByRole("tab", { name: /智能体过程/ }).click();
  await technicalDetails.click();
  const promptCollapseButton = page.getByRole("button", { name: /提示摘要/ });
  await expect(promptCollapseButton).toBeVisible();
  await expect(promptCollapseButton).toHaveAttribute("aria-expanded", "false");
  await expect(page.getByText("sk-trace-visual-secret")).toHaveCount(0);
  await expect(page.getByText("internal-secret-token")).toHaveCount(0);

  await promptCollapseButton.click();
  await expect(page.getByText(/凭据=\[已脱敏\]/)).toBeVisible();

  const sidebarBox = await sidebar.boundingBox();
  const mainBox = await main.boundingBox();
  const graphBox = await graphPanel.boundingBox();
  const summaryBox = await traceSummary.boundingBox();

  expect(sidebarBox).not.toBeNull();
  expect(mainBox).not.toBeNull();
  expect(graphBox).not.toBeNull();
  expect(summaryBox).not.toBeNull();

  if (sidebarBox && mainBox && graphBox && summaryBox) {
    expect(sidebarBox.x + sidebarBox.width).toBeLessThanOrEqual(mainBox.x);
    expect(graphBox.x + graphBox.width).toBeLessThanOrEqual(summaryBox.x);
    expect(summaryBox.y).toBeLessThan(graphBox.y + graphBox.height);
  }

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
  );
  expect(hasHorizontalOverflow).toBe(false);

  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("trace-desktop.png")
  });
});

function taskStatusResponse() {
  return {
    category: "smart_pet_hardware",
    created_at: "2026-05-28T10:00:00+08:00",
    data_source_mode: "demo_snapshot",
    status: "completed",
    subcategory: "automatic_litter_box",
    target_product_name: "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
    target_product_url: "https://v.douyin.com/mv8e4KRLLwc/",
    task_id: "task_trace_visual",
    updated_at: "2026-05-28T10:08:00+08:00"
  };
}

function traceResponse() {
  return {
    agent_runs: [
      {
        agent_name: "collection_agent",
        ended_at: "2026-05-28T10:01:20+08:00",
        input_summary: "读取本地 SKU 快照和用户研究文本。",
        output_summary: "读取 14 个 SKU，并保留一条缺少访问时间的价格证据用于 QA 打回演示。",
        run_id: "run_collection_visual",
        started_at: "2026-05-28T10:01:00+08:00",
        status: "succeeded",
        task_id: "task_trace_visual"
      },
      {
        agent_name: "analysis_agent",
        ended_at: "2026-05-28T10:03:10+08:00",
        input_summary: "消费 Product、Evidence 与 ReviewInsight。",
        output_summary:
          "生成目标画像、核心 Claim、动态切片竞争边，以及一条需要补齐证据的价格优势判断。",
        run_id: "run_analysis_visual",
        started_at: "2026-05-28T10:01:40+08:00",
        status: "succeeded",
        task_id: "task_trace_visual"
      },
      {
        agent_name: "qa_agent",
        ended_at: "2026-05-28T10:04:00+08:00",
        input_summary: "检查 Claim、Evidence 和 CompetitionEdge。",
        output_summary: "发现价格证据缺少访问时间，向 Collection Agent 发起真实打回。",
        run_id: "run_qa_visual",
        started_at: "2026-05-28T10:03:35+08:00",
        status: "requires_revision",
        task_id: "task_trace_visual"
      },
      {
        agent_name: "writer_agent",
        ended_at: "2026-05-28T10:07:30+08:00",
        input_summary: "消费 QA 修复后的结构化产物。",
        output_summary: "生成网页报告与 Word 导出元信息。",
        run_id: "run_writer_visual",
        started_at: "2026-05-28T10:06:50+08:00",
        status: "succeeded",
        task_id: "task_trace_visual"
      }
    ],
    dag_edges: [
      {
        condition: null,
        edge_id: "edge_collection_analysis",
        label: "Collection -> Analysis",
        source: "collection_agent",
        target: "analysis_agent"
      },
      {
        condition: null,
        edge_id: "edge_analysis_qa",
        label: "Analysis -> QA",
        source: "analysis_agent",
        target: "qa_agent"
      },
      {
        condition: "revision_collection",
        edge_id: "edge_qa_collection",
        label: "QA 打回 Collection",
        source: "qa_agent",
        target: "collection_agent"
      },
      {
        condition: "qa_passed",
        edge_id: "edge_qa_writer",
        label: "QA passed",
        source: "qa_agent",
        target: "writer_agent"
      }
    ],
    dag_nodes: [
      {
        agent_name: "collection_agent",
        current: false,
        failed: false,
        label: "Collection Agent",
        node_id: "collection_agent",
        node_type: "agent",
        run_ids: ["run_collection_visual"],
        status: "succeeded",
        visible: true
      },
      {
        agent_name: "analysis_agent",
        current: false,
        failed: false,
        label: "Analysis Agent",
        node_id: "analysis_agent",
        node_type: "agent",
        run_ids: ["run_analysis_visual"],
        status: "succeeded",
        visible: true
      },
      {
        agent_name: "qa_agent",
        current: true,
        failed: false,
        label: "QA Agent",
        node_id: "qa_agent",
        node_type: "agent",
        run_ids: ["run_qa_visual"],
        status: "requires_revision",
        visible: true
      },
      {
        agent_name: "writer_agent",
        current: false,
        failed: false,
        label: "Writer Agent",
        node_id: "writer_agent",
        node_type: "agent",
        run_ids: ["run_writer_visual"],
        status: "succeeded",
        visible: true
      }
    ],
    diffs: [
      {
        after: {
          access_time: "2026-05-23T16:00:59+08:00",
          confidence_level: "medium",
          risk_flags: []
        },
        before: {
          access_time: null,
          confidence_level: "low",
          risk_flags: ["missing_access_time"]
        },
        business_impact: "补齐访问时间后，相关结论可以进入可复核状态。",
        diff_id: "collection_repair_diff_visual",
        metadata: {
          target_evidence_id: "ev_visual_price"
        },
        revision_message_ids: ["msg_visual_revision"],
        source: "collection_agent_repair",
        status: "repaired",
        target_id: "ev_visual_price_repaired",
        target_type: "evidence"
      }
    ],
    evidence_chains: [
      {
        chain_id: "chain_visual_price",
        claim_content:
          "核心直接竞品在当前切片下形成价格与除臭竞争。该判断需要同时保留价格、除臭卖点和多猫家庭场景的证据边界。",
        claim_id: "claim_visual_price",
        claim_status: "accepted",
        confidence: 0.82,
        evidence_items: [
          {
            access_time_status: "available",
            confidence_level: "medium",
            content_summary: "商品页快照显示竞品价格与除臭卖点。",
            evidence_id: "ev_visual_price",
            limitations: "来源为本地脱敏快照，非实时页面。",
            product_id: "prod_competitor",
            risk_flags: [],
            source_type: "douyin_sku_snapshot",
            source_url:
              "https://example.com/competitor/automatic-litter-box-long-source-path?sku=visual_trace_readability&channel=douyin_snapshot"
          }
        ],
        is_inference: true,
        report_section_ids: ["conclusion_summary"],
        risk_flags: [],
        trace_refs: ["analysis_agent:edge_visual_price"]
      }
    ],
    generated_at: "2026-05-28T10:08:00+08:00",
    metadata: {
      counts: {
        agent_runs: 4,
        diffs: 1,
        tool_calls: 2
      }
    },
    prompt_previews: [
      {
        agent_name: "collection_agent",
        content_summary:
          "Prompt 摘要包含 api_key=sk-trace-visual-secret 与 token=internal-secret-token 的测试文本，页面必须只显示脱敏版本。",
        folded: true,
        preview_id: "prompt_collection_visual",
        redacted: true,
        run_id: "run_collection_visual",
        title: "Collection prompt"
      }
    ],
    process_view: {
      agent_run_count: 4,
      dag_node_count: 4,
      default_tab: "evidence_chain",
      prompt_preview_count: 1,
      technical_details_folded: true,
      token_usage_count: 2,
      tool_call_count: 2
    },
    qa_reviews: [
      {
        check_name: "价格证据完整性",
        created_at: "2026-05-28T10:03:45+08:00",
        evidence_ids: ["ev_visual_price"],
        issue_code: "TIMELY_EVIDENCE_MISSING_ACCESS_TIME",
        message: "价格证据缺少访问时间，不能作为强事实结论直接进入报告。",
        related_claim_ids: ["claim_visual_price"],
        required_action: "补齐访问时间；若无法补齐，则改写为暂无可靠数据。",
        resolved_at: "2026-05-28T10:05:20+08:00",
        review_task_id: "review_visual_price",
        severity: "warning",
        status: "resolved",
        target_agent: "collection_agent",
        target_id: "ev_visual_price",
        target_type: "evidence",
        task_id: "task_trace_visual"
      }
    ],
    quality_records: [
      {
        action_result: "访问时间已补齐，结论可进入复核。",
        check_item: "价格证据完整性",
        evidence_ids: ["ev_visual_price"],
        issue_code: "TIMELY_EVIDENCE_MISSING_ACCESS_TIME",
        issue_summary: "价格证据缺少访问时间。",
        needs_attention: false,
        quality_record_id: "quality_visual_price",
        related_claim_ids: ["claim_visual_price"],
        required_action: "补齐访问时间。",
        resolved: true,
        review_task_id: "review_visual_price",
        severity: "warning",
        status: "resolved",
        target_agent: "collection_agent",
        target_id: "ev_visual_price",
        target_type: "evidence"
      }
    ],
    revision_messages: [
      {
        artifact_type: "claim_evidence_check",
        created_at: "2026-05-28T10:03:50+08:00",
        evidence_ids: ["ev_visual_price"],
        from_agent: "qa_agent",
        message_id: "msg_visual_revision",
        message_type: "revision_request",
        payload: {
          reason: "价格属于时效性信息，缺少访问时间会降低证据置信度。",
          required_action: "补齐访问时间。",
          target_ids: ["ev_visual_price"]
        },
        status: "requires_revision",
        task_id: "task_trace_visual",
        to_agent: "collection_agent"
      }
    ],
    task_id: "task_trace_visual",
    task_status: "completed",
    token_usage: [
      {
        agent_name: "collection_agent",
        completion_tokens: 0,
        created_at: "2026-05-28T10:01:20+08:00",
        model_name: "local_rule_flow",
        prompt_tokens: 0,
        run_id: "run_collection_visual",
        task_id: "task_trace_visual",
        total_tokens: 0,
        usage_id: "usage_collection_visual"
      },
      {
        agent_name: "writer_agent",
        completion_tokens: 96,
        created_at: "2026-05-28T10:07:30+08:00",
        model_name: "Doubao-Seed-2.0-lite",
        prompt_tokens: 168,
        run_id: "run_writer_visual",
        task_id: "task_trace_visual",
        total_tokens: 264,
        usage_id: "usage_writer_visual"
      }
    ],
    tool_calls: [
      {
        arguments_summary: {
          sku_count: 14,
          source: "demo_snapshot"
        },
        duration_ms: 420,
        ended_at: "2026-05-28T10:01:05+08:00",
        error_message: null,
        run_id: "run_collection_visual",
        started_at: "2026-05-28T10:01:00+08:00",
        status: "succeeded",
        task_id: "task_trace_visual",
        tool_call_id: "tool_snapshot_loader_visual",
        tool_name: "snapshot_loader"
      },
      {
        arguments_summary: {
          check_scope: "claim_evidence",
          evidence_count: 14
        },
        duration_ms: 180,
        ended_at: "2026-05-28T10:03:48+08:00",
        error_message: null,
        run_id: "run_qa_visual",
        started_at: "2026-05-28T10:03:45+08:00",
        status: "succeeded",
        task_id: "task_trace_visual",
        tool_call_id: "tool_qa_rules_visual",
        tool_name: "qa_rules"
      }
    ],
    trace_view_id: "trace_task_trace_visual",
    workflow_status: "completed"
  };
}
