import { expect, test, type Locator, type Page } from "@playwright/test";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { build, preview } from "vite";

import {
  mockBattlefieldFixture,
  mockOverviewFixture,
  mockProfileFixture,
  mockReportFixture,
  mockTraceFixture
} from "../src/mocks";

let server: Awaited<ReturnType<typeof preview>>;
let tempDir: string;

const FRONTEND_PORT = 4178;
const taskId = "task_responsive_visual";
const baseUrl = `http://127.0.0.1:${FRONTEND_PORT}`;

test.beforeAll(async ({ browserName }, testInfo) => {
  void browserName;
  testInfo.setTimeout(120000);
  tempDir = await mkdtemp(path.join(tmpdir(), "zijieagent-responsive-visual-"));
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
  await server.httpServer.close();
  if (tempDir) {
    await rm(tempDir, { force: true, recursive: true });
  }
});

test.beforeEach(async ({ page }) => {
  await routeResponsiveApis(page);
});

test("overview, graph, profile, report, and trace stay readable on desktop and narrow screens", async ({
  page
}, testInfo) => {
  await page.setViewportSize({ height: 900, width: 1366 });
  await verifyOverview(page, testInfo.outputPath("responsive-overview-desktop.png"), "desktop");
  await verifyBattlefield(
    page,
    testInfo.outputPath("responsive-battlefield-desktop.png"),
    "desktop"
  );
  await verifyProfile(page, testInfo.outputPath("responsive-profile-desktop.png"), "desktop");
  await verifyReport(page, testInfo.outputPath("responsive-report-desktop.png"), "desktop");
  await verifyTrace(page, testInfo.outputPath("responsive-trace-desktop.png"), "desktop");

  await page.setViewportSize({ height: 900, width: 390 });
  await verifyOverview(page, testInfo.outputPath("responsive-overview-narrow.png"), "narrow");
  await verifyBattlefield(page, testInfo.outputPath("responsive-battlefield-narrow.png"), "narrow");
  await verifyProfile(page, testInfo.outputPath("responsive-profile-narrow.png"), "narrow");
  await verifyReport(page, testInfo.outputPath("responsive-report-narrow.png"), "narrow");
  await verifyTrace(page, testInfo.outputPath("responsive-trace-narrow.png"), "narrow");
});

async function verifyOverview(page: Page, screenshotPath: string, mode: "desktop" | "narrow") {
  await page.goto(`${baseUrl}/overview?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "竞争态势总览" })).toBeVisible();
  await expect(page.getByLabel("竞争态势总览首屏")).toBeVisible();
  await expect(page.getByLabel("关键竞品与下钻入口")).toBeVisible();
  await expect(page.getByRole("img", { name: "暂无可靠图片" }).first()).toBeVisible();

  await expectShellLayout(page, mode);
  await expectNoHorizontalOverflow(page);
  await expectNoBoxOverlap(
    page.locator(".overview-thumb").first(),
    page.locator(".overview-competitor-body").first()
  );
  await expectVisibleScreenshot(page, screenshotPath);
}

async function verifyBattlefield(page: Page, screenshotPath: string, mode: "desktop" | "narrow") {
  await page.goto(`${baseUrl}/battlefield?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "竞争关系图谱" })).toBeVisible();
  await expect(page.getByRole("region", { exact: true, name: "竞争关系图" })).toBeVisible();
  await expect(page.getByLabel("关键竞争关系")).toContainText("威胁等级");
  await expect(page.locator(".react-flow__node")).not.toHaveCount(0);
  await expect(page.locator(".react-flow__edge")).not.toHaveCount(0);

  await expectShellLayout(page, mode);
  await expectNoHorizontalOverflow(page);
  await expectStableBox(page.getByRole("region", { exact: true, name: "竞争关系图" }), {
    minHeight: mode === "desktop" ? 440 : 380
  });
  await expectVisibleScreenshot(page, screenshotPath);
}

async function verifyProfile(page: Page, screenshotPath: string, mode: "desktop" | "narrow") {
  await page.goto(`${baseUrl}/profile?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "产品与竞品画像" })).toBeVisible();
  await expect(page.getByLabel("目标产品与核心竞品横向对比")).toBeVisible();
  await expect(page.getByLabel("修正画像")).toBeVisible();
  await expect(page.getByRole("img", { name: "暂无可靠图片" }).first()).toBeVisible();

  await expectShellLayout(page, mode);
  await expectNoHorizontalOverflow(page);
  await expectNoBoxOverlap(
    page.locator(".profile-comparison-image").first(),
    page.locator(".profile-comparison-column").first().locator("h5")
  );
  await expectVisibleScreenshot(page, screenshotPath);
}

async function verifyReport(page: Page, screenshotPath: string, mode: "desktop" | "narrow") {
  await page.goto(`${baseUrl}/report?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "分析报告" })).toBeVisible();
  await expect(page.getByLabel("报告工作台工具栏")).toBeVisible();
  await expect(page.getByRole("button", { name: "下载 Word 报告" })).toBeVisible();
  await expect(page.getByRole("button", { name: "打印或另存 PDF" })).toBeVisible();
  await expect(page.getByLabel("报告章节")).toContainText("结论摘要");
  await expect(page.getByRole("button", { name: /Markdown/ })).toHaveCount(0);

  await expectShellLayout(page, mode);
  await expectNoHorizontalOverflow(page);
  await expectNoBoxOverlap(
    page.getByRole("button", { name: "下载 Word 报告" }),
    page.getByRole("button", { name: "打印或另存 PDF" })
  );
  await expectVisibleScreenshot(page, screenshotPath);
}

async function verifyTrace(page: Page, screenshotPath: string, mode: "desktop" | "narrow") {
  await page.goto(`${baseUrl}/trace?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "证据与过程追踪" })).toBeVisible();
  await expect(page.getByRole("region", { exact: true, name: "证据链" })).toBeVisible();
  await page.getByRole("tab", { name: /智能体过程/ }).click();
  await expect(page.getByRole("region", { exact: true, name: "流程图状态" })).toBeVisible();

  await expectShellLayout(page, mode);
  await expectNoHorizontalOverflow(page);
  await expectStableBox(page.getByRole("region", { exact: true, name: "流程图状态" }), {
    minHeight: 420
  });
  await expectVisibleScreenshot(page, screenshotPath);
}

async function routeResponsiveApis(page: Page) {
  await page.route(`**/tasks/${taskId}`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        data: taskStatusResponse(),
        error: null,
        trace_id: "trace_responsive_task"
      },
      status: 200
    });
  });
  await page.route(`**/tasks/${taskId}/overview**`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: { data: mockOverviewFixture, error: null, trace_id: "trace_responsive_overview" },
      status: 200
    });
  });
  await page.route(`**/tasks/${taskId}/battlefield**`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: { data: mockBattlefieldFixture, error: null, trace_id: "trace_responsive_battlefield" },
      status: 200
    });
  });
  await page.route(`**/tasks/${taskId}/profile**`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: { data: mockProfileFixture, error: null, trace_id: "trace_responsive_profile" },
      status: 200
    });
  });
  await page.route(`**/tasks/${taskId}/report**`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: { data: mockReportFixture, error: null, trace_id: "trace_responsive_report" },
      status: 200
    });
  });
  await page.route(`**/tasks/${taskId}/trace**`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: { data: mockTraceFixture, error: null, trace_id: "trace_responsive_trace" },
      status: 200
    });
  });
}

async function expectShellLayout(page: Page, mode: "desktop" | "narrow") {
  const sidebarBox = await page.getByLabel("主导航").boundingBox();
  const mainBox = await page.locator(".workspace-main").boundingBox();
  expect(sidebarBox).not.toBeNull();
  expect(mainBox).not.toBeNull();
  if (!sidebarBox || !mainBox) {
    return;
  }

  if (mode === "desktop") {
    expect(sidebarBox.x + sidebarBox.width).toBeLessThanOrEqual(mainBox.x + 1);
  } else {
    expect(sidebarBox.y + sidebarBox.height).toBeLessThanOrEqual(mainBox.y + 1);
  }
}

async function expectNoHorizontalOverflow(page: Page) {
  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2
  );
  expect(hasHorizontalOverflow).toBe(false);
}

async function expectNoBoxOverlap(first: Locator, second: Locator) {
  const firstBox = await first.boundingBox();
  const secondBox = await second.boundingBox();
  expect(firstBox).not.toBeNull();
  expect(secondBox).not.toBeNull();
  if (!firstBox || !secondBox) {
    return;
  }

  const overlaps =
    firstBox.x < secondBox.x + secondBox.width &&
    firstBox.x + firstBox.width > secondBox.x &&
    firstBox.y < secondBox.y + secondBox.height &&
    firstBox.y + firstBox.height > secondBox.y;
  expect(overlaps).toBe(false);
}

async function expectStableBox(locator: Locator, { minHeight }: { minHeight: number }) {
  const box = await locator.boundingBox();
  expect(box).not.toBeNull();
  if (!box) {
    return;
  }
  expect(box.height).toBeGreaterThanOrEqual(minHeight);
  expect(box.width).toBeGreaterThan(280);
}

async function expectVisibleScreenshot(page: Page, outputPath: string) {
  const screenshot = await page.screenshot({ fullPage: false, path: outputPath });
  expect(screenshot.length).toBeGreaterThan(10000);
}

function taskStatusResponse() {
  return {
    category: "smart_pet_hardware",
    created_at: "2026-05-30T08:00:00Z",
    data_source_mode: "demo_snapshot",
    status: "completed",
    subcategory: "automatic_litter_box",
    target_product_name: "开发样例自动猫砂盆 A",
    target_product_url: "https://example.invalid/frontend-dev/target",
    task_id: taskId,
    updated_at: "2026-05-30T08:08:00Z"
  };
}
