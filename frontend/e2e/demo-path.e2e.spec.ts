import { expect, test, type Page } from "@playwright/test";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { build, preview } from "vite";

let backendProcess: ChildProcessWithoutNullStreams;
let backendLog = "";
let frontendOutDir: string;
let frontendServer: Awaited<ReturnType<typeof preview>>;
let tempDir: string;

const BACKEND_PORT = 8003;
const FRONTEND_PORT = 4177;
const backendUrl = `http://127.0.0.1:${BACKEND_PORT}`;
const frontendUrl = `http://127.0.0.1:${FRONTEND_PORT}`;

test.setTimeout(240000);

test.beforeAll(async ({ browserName }, testInfo) => {
  void browserName;
  testInfo.setTimeout(120000);
  tempDir = await mkdtemp(path.join(tmpdir(), "zijieagent-demo-path-"));
  frontendOutDir = path.join(tempDir, "frontend-dist");
  backendProcess = startBackend(tempDir);
  await waitForBackend();

  const previousApiBaseUrl = process.env.VITE_API_BASE_URL;
  process.env.VITE_API_BASE_URL = backendUrl;
  try {
    await build({
      build: {
        emptyOutDir: true,
        outDir: frontendOutDir
      },
      configLoader: "runner"
    });
  } finally {
    if (previousApiBaseUrl === undefined) {
      delete process.env.VITE_API_BASE_URL;
    } else {
      process.env.VITE_API_BASE_URL = previousApiBaseUrl;
    }
  }

  frontendServer = await preview({
    build: {
      outDir: frontendOutDir
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
  await frontendServer?.httpServer.close();
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill();
    await new Promise((resolve) => backendProcess.once("close", resolve));
  }
  if (tempDir) {
    await rm(tempDir, { force: true, recursive: true });
  }
});

test("walks the full demo path with screenshots, QA revision, graph, markdown export, and narrow layout checks", async ({
  page
}, testInfo) => {
  await page.goto(frontendUrl);

  await expect(page.getByRole("heading", { level: 2, name: "分析任务输入" })).toBeVisible();
  await expect(page.getByRole("button", { name: "启动分析任务" })).toBeVisible();
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-01-input-desktop.png"));

  await page.getByRole("button", { name: "启动分析任务" }).click();

  await expect(page).toHaveURL(/\/trace\?task_id=task_/, { timeout: 90000 });
  await expect(page.getByText("当前状态：已完成")).toBeVisible({ timeout: 90000 });

  const taskId = new URL(page.url()).searchParams.get("task_id");
  expect(taskId).toBeTruthy();

  await expect(page.getByRole("heading", { level: 2, name: "智能体过程追踪" })).toBeVisible();
  await expect(page.getByRole("region", { exact: true, name: "LangGraph DAG 状态" })).toBeVisible();
  await expect(page.getByLabel("Agent Run 列表")).toContainText("Writer Agent");
  await expect(page.getByLabel("QA Review 列表")).toContainText(
    "TIMELY_EVIDENCE_MISSING_ACCESS_TIME"
  );
  await expect(page.getByLabel("QA Review 列表")).toContainText("已解决");
  await expect(page.getByLabel("Diff View")).toContainText("collection_agent_repair");
  await expect(page.getByLabel("Diff View")).toContainText("analysis_agent_recompute");
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-02-trace-desktop.png"));

  await page.getByRole("button", { name: "查看画像" }).click();
  await expect(page).toHaveURL(new RegExp(`/profile\\?task_id=${taskId}`));
  await expect(page.getByRole("heading", { level: 2, name: "产品画像" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "基础信息" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "PricingModel" })).toBeVisible();
  await expect(page.getByLabel("有限人工修正")).toBeVisible();
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-03-profile-desktop.png"));

  await page.getByRole("button", { name: "竞争图谱" }).click();
  await expect(page).toHaveURL(new RegExp(`/battlefield\\?task_id=${taskId}`));
  await expect(page.getByRole("heading", { level: 2, name: "竞争关系图谱" })).toBeVisible();
  await expect(page.getByRole("region", { exact: true, name: "竞争关系图" })).toBeVisible();
  await expect(page.locator(".react-flow__node")).not.toHaveCount(0);
  await expect(page.locator(".react-flow__edge")).not.toHaveCount(0);
  await expect(page.getByLabel("QA 打回记录")).toContainText("已通过");
  await expect(page.getByLabel("QA 打回记录")).toContainText("已解决 1 条");
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-04-battlefield-desktop.png"));

  await page.getByRole("button", { name: "分析报告" }).click();
  await expect(page).toHaveURL(new RegExp(`/report\\?task_id=${taskId}`));
  await expect(page.getByRole("heading", { level: 2, name: "分析报告" })).toBeVisible();
  await expect(page.getByLabel("报告章节")).toContainText("执行摘要");
  await expect(page.getByLabel("报告章节")).toContainText("QA 审查摘要");

  const markdownResponsePromise = page.waitForResponse((response) =>
    response.url().includes(`/tasks/${taskId}/report/markdown`)
  );
  await page.getByRole("button", { name: "导出 Markdown" }).click();
  const markdownResponse = await markdownResponsePromise;
  const markdownPayload = await markdownResponse.json();
  expect(
    markdownResponse.ok(),
    `Markdown export failed with status ${markdownResponse.status()}: ${JSON.stringify(
      markdownPayload
    )}`
  ).toBeTruthy();
  expect(markdownPayload.error).toBeNull();
  expect(markdownPayload.data.markdown).toContain("# 竞品分析报告");
  await expect(page.getByText(/Markdown 已导出/)).toBeVisible();
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-05-report-desktop.png"));

  await page.setViewportSize({ height: 900, width: 390 });

  await page.goto(`${frontendUrl}/trace?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "智能体过程追踪" })).toBeVisible();
  await expectNarrowLayout(page);
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-06-trace-narrow.png"));

  await page.goto(`${frontendUrl}/battlefield?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "竞争关系图谱" })).toBeVisible();
  await expect(page.locator(".react-flow__node")).not.toHaveCount(0);
  await expectNarrowLayout(page);
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-07-battlefield-narrow.png"));

  await page.goto(`${frontendUrl}/report?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "分析报告" })).toBeVisible();
  await expect(page.getByLabel("报告章节")).toContainText("执行摘要");
  await expectNarrowLayout(page);
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-08-report-narrow.png"));
});

async function expectNonEmptyScreenshot(page: Page, outputPath: string) {
  const screenshot = await page.screenshot({ fullPage: false, path: outputPath });
  expect(screenshot.length).toBeGreaterThan(10000);
}

async function expectNarrowLayout(page: Page) {
  const sidebar = page.getByLabel("主导航");
  const main = page.locator(".workspace-main");
  const sidebarBox = await sidebar.boundingBox();
  const mainBox = await main.boundingBox();
  expect(sidebarBox).not.toBeNull();
  expect(mainBox).not.toBeNull();

  if (sidebarBox && mainBox) {
    expect(sidebarBox.y + sidebarBox.height).toBeLessThanOrEqual(mainBox.y + 1);
  }

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2
  );
  expect(hasHorizontalOverflow).toBe(false);
}

function startBackend(runDir: string) {
  const repoRoot = resolveRepoRoot();
  const backendDir = path.join(repoRoot, "backend");
  const bundledPython = path.join(backendDir, ".conda312", "python.exe");
  const python = existsSync(bundledPython) ? bundledPython : "python";
  const databaseUrl = `sqlite:///${path.join(runDir, "demo-path.db").replace(/\\/g, "/")}`;
  const reportOutputDir = path.join(runDir, "reports");

  const child = spawn(
    python,
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)],
    {
      cwd: backendDir,
      env: {
        ...process.env,
        DATABASE_URL: databaseUrl,
        PYTHONUNBUFFERED: "1",
        REPORT_OUTPUT_DIR: reportOutputDir,
        RUN_TASK_EXECUTION_INLINE: "1"
      }
    }
  );
  child.stdout.on("data", (chunk) => {
    backendLog += chunk.toString();
  });
  child.stderr.on("data", (chunk) => {
    backendLog += chunk.toString();
  });
  child.on("error", (error) => {
    backendLog += `\nSPAWN_ERROR: ${error.message}`;
  });
  return child;
}

function resolveRepoRoot() {
  const cwd = process.cwd();
  for (const candidate of [cwd, path.resolve(cwd, "..")]) {
    if (
      existsSync(path.join(candidate, "backend")) &&
      existsSync(path.join(candidate, "frontend"))
    ) {
      return candidate;
    }
  }
  return path.resolve(cwd, "..");
}

async function waitForBackend() {
  const deadline = Date.now() + 45000;
  while (Date.now() < deadline) {
    if (backendProcess.exitCode !== null) {
      throw new Error(`Backend exited early.\n${backendLog}`);
    }
    try {
      const response = await fetch(`${backendUrl}/health`);
      if (response.ok) {
        return;
      }
    } catch {
      // Keep polling until the backend opens its health endpoint.
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error(`Backend did not become ready.\n${backendLog}`);
}
