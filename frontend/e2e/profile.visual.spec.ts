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
  tempDir = await mkdtemp(path.join(tmpdir(), "zijieagent-profile-visual-"));
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

test("profile comparison stacks without severe horizontal overflow on narrow screens", async ({
  page
}, testInfo) => {
  await page.route("**/tasks/task_profile_visual/profile", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        data: profileResponse(),
        error: null,
        trace_id: "trace_playwright_profile"
      },
      status: 200
    });
  });

  await page.setViewportSize({ height: 820, width: 390 });
  await page.goto("/profile?task_id=task_profile_visual");

  await expect(page.getByRole("heading", { name: "目标产品与核心竞品对比" })).toBeVisible();
  await expect(page.getByText("最高威胁直接竞品")).toBeVisible();
  await expect(page.getByText("最高威胁替代竞品")).toBeVisible();
  await expect(page.getByRole("button", { name: "查看依据" }).first()).toBeVisible();

  const documentWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(documentWidth).toBeLessThanOrEqual(430);

  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("profile-narrow.png")
  });
});

test("profile comparison keeps product names readable on desktop workspace widths", async ({
  page
}, testInfo) => {
  await page.route("**/tasks/task_profile_visual/profile", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        data: profileResponse(),
        error: null,
        trace_id: "trace_playwright_profile"
      },
      status: 200
    });
  });

  await page.setViewportSize({ height: 900, width: 1366 });
  await page.goto("/profile?task_id=task_profile_visual");

  await expect(page.getByRole("heading", { name: "目标产品与核心竞品对比" })).toBeVisible();

  const titleBoxes = await page.locator(".profile-comparison-column h5").evaluateAll((nodes) =>
    nodes.map((node) => {
      const box = node.getBoundingClientRect();
      return { height: box.height, width: box.width };
    })
  );
  expect(titleBoxes.length).toBeGreaterThanOrEqual(3);
  for (const box of titleBoxes) {
    expect(box.width).toBeGreaterThan(160);
    expect(box.height).toBeLessThan(96);
  }

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
  );
  expect(hasHorizontalOverflow).toBe(false);

  await page.screenshot({
    fullPage: true,
    path: testInfo.outputPath("profile-desktop-readable.png")
  });
});

function profileResponse() {
  return {
    evidence_summaries: [
      {
        access_time: "2026-05-27T08:00:00Z",
        access_time_status: "available",
        confidence_level: "medium",
        content_summary: "商品页快照记录目标产品价格、核心卖点和套装信息。",
        evidence_id: "ev_profile_price",
        limitations: "来源为本地脱敏快照，非实时页面。",
        product_id: "prod_target",
        risk_flags: [],
        screenshot_path: "data/raw/sku_02/price.png",
        source_type: "douyin_sku_snapshot",
        source_url: "https://v.douyin.com/mv8e4KRLLwc/"
      }
    ],
    feature_tree: {
      cleaning_capability: ["自动铲砂", "可视化清理状态"],
      evidence_ids: ["ev_profile_price"],
      feature_tree_id: "feature_target",
      maintenance_cost: ["耗材需要定期补充"],
      odor_control: ["封闭仓体", "除味模块"],
      product_id: "prod_target",
      risk_flags: [],
      safety_features: ["运行状态检测"],
      smart_features: ["应用提醒"],
      task_id: "task_profile_visual"
    },
    generated_at: "2026-05-27T08:05:00Z",
    horizontal_comparison: {
      compared_products: [
        {
          brand: "小佩",
          primary_image_path: null,
          product_id: "prod_target",
          product_name: "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆 长名称桌面可读性验证款",
          product_url: "https://v.douyin.com/mv8e4KRLLwc/",
          slot: "target"
        },
        {
          brand: "竞品品牌",
          primary_image_path: null,
          product_id: "prod_competitor",
          product_name: "核心直接竞品 全自动除臭大容量多猫家庭智能猫砂盆",
          product_url: "https://example.com/direct",
          slot: "highest_threat_direct_competitor"
        },
        {
          brand: "替代品牌",
          primary_image_path: null,
          product_id: "prod_alternative",
          product_name: "场景替代竞品 低维护封闭式基础自动清理套装",
          product_url: "https://example.com/alternative",
          slot: "highest_threat_alternative"
        }
      ],
      dimensions: [
        comparisonDimension("price_band", "价格带", "优势", "advantage", [
          ["prod_target", "1500-2000"],
          ["prod_competitor", "2000-3000"],
          ["prod_alternative", "1500-2000"]
        ]),
        comparisonDimension("core_selling_points", "核心卖点", "持平", "parity", [
          ["prod_target", "自动铲砂、封闭仓体、应用提醒"],
          ["prod_competitor", "除臭模块、低维护套装"],
          ["prod_alternative", "低价套装、基础自动清理"]
        ]),
        comparisonDimension("persona", "主要人群", "持平", "parity", [
          ["prod_target", "多猫家庭"],
          ["prod_competitor", "多猫家庭、重除臭用户"],
          ["prod_alternative", "预算敏感家庭"]
        ]),
        comparisonDimension("scenario", "使用场景", "优势", "advantage", [
          ["prod_target", "小户型客厅"],
          ["prod_competitor", "重除臭"],
          ["prod_alternative", "低维护"]
        ]),
        comparisonDimension("evidence_credibility", "证据可信状态", "持平", "parity", [
          ["prod_target", "谨慎参考"],
          ["prod_competitor", "可直接采纳"],
          ["prod_alternative", "谨慎参考"]
        ])
      ],
      target_product_id: "prod_target"
    },
    metadata: {
      evidence_count: 1
    },
    pricing_evidence: {
      access_time: "2026-05-27T08:00:00Z",
      access_time_status: "available",
      evidence_ids: ["ev_profile_price"],
      risk_flags: []
    },
    pricing_model: {
      access_time: "2026-05-27T08:00:00Z",
      bundle_description: "主机与基础耗材套装",
      currency: "CNY",
      evidence_ids: ["ev_profile_price"],
      final_price: 1699,
      list_price: 1899,
      price_band: "1500-2000",
      pricing_model_id: "pricing_target",
      product_id: "prod_target",
      promotions: ["直播间优惠"],
      risk_flags: [],
      task_id: "task_profile_visual"
    },
    product: {
      brand: "小佩",
      category: "smart_pet_hardware",
      created_at: "2026-05-27T08:00:00Z",
      evidence_ids: ["ev_profile_price"],
      name: "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
      product_id: "prod_target",
      product_url: "https://v.douyin.com/mv8e4KRLLwc/",
      primary_image_status: "missing",
      role: "target",
      shop_name: "小佩宠物旗舰店",
      sku_id: "sku_02",
      subcategory: "automatic_litter_box",
      task_id: "task_profile_visual",
      tags: ["自动清理", "可视化"]
    },
    profile_id: "profile_task_profile_visual_prod_target",
    task_id: "task_profile_visual",
    user_persona: {
      decision_factors: ["清洁稳定性", "维护成本"],
      evidence_ids: ["ev_profile_price"],
      is_inference: true,
      pain_points: ["清理频率高", "异味扩散"],
      persona_id: "persona_target",
      personas: ["多猫家庭"],
      product_id: "prod_target",
      risk_flags: [],
      scenarios: ["小户型客厅"],
      task_id: "task_profile_visual"
    }
  };
}

function comparisonDimension(
  key: string,
  label: string,
  reasonStatus: string,
  targetStatus: string,
  values: Array<[string, string]>
) {
  return {
    dimension_key: key,
    dimension_label: label,
    evidence_ids: ["ev_profile_price"],
    risk_flags: [],
    status_reason: `${label}判断为${reasonStatus}，依据来自可追溯快照。`,
    target_status: targetStatus,
    trace_refs: [`profile:task_profile_visual:${key}`],
    values: values.map(([productId, value]) => ({
      evidence_ids: ["ev_profile_price"],
      product_id: productId,
      value
    }))
  };
}
