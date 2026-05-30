import { expect, test, type Page } from "@playwright/test";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdtemp, rm } from "node:fs/promises";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import path from "node:path";
import { build, preview } from "vite";

let backendProcess: ChildProcessWithoutNullStreams;
let backendLog = "";
let frontendOutDir: string;
let frontendServer: Awaited<ReturnType<typeof preview>>;
let tempDir: string;

let backendPort = 0;
let frontendPort = 0;
let backendUrl = "";
let frontendUrl = "";

test.setTimeout(240000);

test.beforeAll(async ({ browserName }, testInfo) => {
  void browserName;
  testInfo.setTimeout(120000);
  tempDir = await mkdtemp(path.join(tmpdir(), "zijieagent-demo-path-"));
  frontendOutDir = path.join(tempDir, "frontend-dist");
  backendPort = await getFreePort();
  frontendPort = await getFreePortInRange(4100, 4199);
  backendUrl = `http://127.0.0.1:${backendPort}`;
  frontendUrl = `http://127.0.0.1:${frontendPort}`;
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
      port: frontendPort,
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

test("walks the full demo path with screenshots, QA revision, graph, word export, and narrow layout checks", async ({
  page
}, testInfo) => {
  await page.goto(frontendUrl);

  await expect(page.getByRole("heading", { level: 2, name: "分析任务输入" })).toBeVisible();
  await expect(page.getByRole("button", { name: "启动分析任务" })).toBeVisible();
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-01-input-desktop.png"));

  await page.getByRole("button", { name: "启动分析任务" }).click();

  await expect(page).toHaveURL(/\/overview\?task_id=task_/, { timeout: 90000 });
  await expect(page.getByRole("heading", { level: 2, name: "竞争态势总览" })).toBeVisible({
    timeout: 90000
  });
  const taskId = new URL(page.url()).searchParams.get("task_id");
  expect(taskId).toBeTruthy();

  await expect(page.getByLabel("竞争态势总览首屏")).toBeVisible();
  await expect(page.getByLabel("核心判断")).toBeVisible();
  await expect(page.getByLabel("决策可用状态")).toContainText("决策可用性");
  await expect(page.getByLabel("首要行动建议")).toBeVisible();
  await expect(page.getByLabel("关键竞品与下钻入口")).toBeVisible();
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-02-overview-desktop.png"));

  await clickNav(page, "竞争图谱");
  await expect(page).toHaveURL(new RegExp(`/battlefield\\?task_id=${taskId}`));
  await expect(page.getByRole("heading", { level: 2, name: "竞争关系图谱" })).toBeVisible();
  await expect(page.getByRole("region", { exact: true, name: "竞争关系图" })).toBeVisible();
  await expect(page.locator(".react-flow__node")).not.toHaveCount(0);
  await expect(page.locator(".react-flow__edge")).not.toHaveCount(0);
  await expect(page.getByLabel("关键竞争关系")).toContainText("威胁等级");
  await expect(page.getByLabel("质检打回记录")).toContainText("已通过");
  await expect(page.getByLabel("质检打回记录")).toContainText("已解决 1 条");
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-03-battlefield-desktop.png"));

  await clickNav(page, "产品与竞品画像");
  await expect(page).toHaveURL(new RegExp(`/profile\\?task_id=${taskId}`));
  await expect(page.getByRole("heading", { level: 2, name: "产品与竞品画像" })).toBeVisible();
  await expect(page.getByLabel("目标产品与核心竞品横向对比")).toBeVisible();
  await expect(page.getByRole("heading", { name: "基础信息" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "价格与证据" })).toBeVisible();
  await expect(page.getByLabel("修正画像")).toBeVisible();
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-04-profile-desktop.png"));

  await clickNav(page, "分析报告");
  await expect(page).toHaveURL(new RegExp(`/report\\?task_id=${taskId}`));
  await expect(page.getByRole("heading", { level: 2, name: "分析报告" })).toBeVisible();
  await expect(page.getByLabel("报告章节")).toContainText("结论摘要");
  await expect(page.getByLabel("报告章节")).toContainText("竞争格局判断");
  await expect(page.getByLabel("报告章节")).toContainText("核心竞品拆解");
  await expect(page.getByLabel("报告章节")).toContainText("证据与质检附录");
  await expect(page.getByRole("button", { name: /Markdown/ })).toHaveCount(0);

  const docxResponsePromise = page.waitForResponse((response) =>
    response.url().includes(`/tasks/${taskId}/report/docx`)
  );
  await page.getByRole("button", { name: "下载 Word 报告" }).click();
  const docxResponse = await docxResponsePromise;
  const docxBytes = await docxResponse.body();
  expect(docxResponse.ok(), `Word export failed with status ${docxResponse.status()}`).toBeTruthy();
  expect(docxBytes.subarray(0, 2).toString()).toBe("PK");
  await expect(page.getByText(/Word 报告已下载/)).toBeVisible();
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-05-report-desktop.png"));

  await clickNav(page, "证据与过程追踪");
  await expect(page).toHaveURL(new RegExp(`/trace\\?task_id=${taskId}`));
  await expect(page.getByText("当前状态：已完成")).toBeVisible({ timeout: 90000 });
  await expect(page.getByRole("heading", { level: 2, name: "证据与过程追踪" })).toBeVisible();
  await expect(page.getByRole("region", { exact: true, name: "证据链" })).toBeVisible();
  await page.getByRole("tab", { name: /智能体过程/ }).click();
  await expect(page.getByLabel("运行记录列表")).toContainText("报告智能体");
  await page.getByRole("tab", { name: /质检记录/ }).click();
  await expect(page.getByLabel("质检记录")).toContainText("TIMELY_EVIDENCE_MISSING_ACCESS_TIME");
  await expect(page.getByLabel("质检记录")).toContainText("已解决");
  await page.getByRole("tab", { name: /差异记录/ }).click();
  await expect(page.getByLabel("差异记录")).toContainText("QA 打回修复");
  await expect(page.getByLabel("差异记录")).toContainText("QA 打回后的分析重算");
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-06-trace-desktop.png"));

  await page.setViewportSize({ height: 900, width: 390 });

  await page.goto(`${frontendUrl}/overview?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "竞争态势总览" })).toBeVisible();
  await expectNarrowLayout(page);
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-07-overview-narrow.png"));

  await page.goto(`${frontendUrl}/trace?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "证据与过程追踪" })).toBeVisible();
  await expectNarrowLayout(page);
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-08-trace-narrow.png"));

  await page.goto(`${frontendUrl}/battlefield?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "竞争关系图谱" })).toBeVisible();
  await expect(page.locator(".react-flow__node")).not.toHaveCount(0);
  await expectNarrowLayout(page);
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-09-battlefield-narrow.png"));

  await page.goto(`${frontendUrl}/report?task_id=${taskId}`);
  await expect(page.getByRole("heading", { level: 2, name: "分析报告" })).toBeVisible();
  await expect(page.getByLabel("报告章节")).toContainText("结论摘要");
  await expectNarrowLayout(page);
  await expectNonEmptyScreenshot(page, testInfo.outputPath("demo-10-report-narrow.png"));
});

async function expectNonEmptyScreenshot(page: Page, outputPath: string) {
  const screenshot = await page.screenshot({ fullPage: false, path: outputPath });
  expect(screenshot.length).toBeGreaterThan(10000);
}

async function clickNav(page: Page, name: string) {
  await page.getByLabel("主导航").getByRole("button", { exact: true, name }).click();
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
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(backendPort)],
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

async function getFreePort() {
  return new Promise<number>((resolve, reject) => {
    const server = createServer();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      if (address && typeof address === "object") {
        const { port } = address;
        server.close(() => resolve(port));
        return;
      }
      server.close(() => reject(new Error("Could not allocate a free port.")));
    });
  });
}

async function getFreePortInRange(start: number, end: number) {
  for (let port = start; port <= end; port += 1) {
    if (await isPortAvailable(port)) {
      return port;
    }
  }
  throw new Error(`Could not allocate a free port in ${start}-${end}.`);
}

async function isPortAvailable(port: number) {
  return new Promise<boolean>((resolve) => {
    const server = createServer();
    server.once("error", () => resolve(false));
    server.listen(port, "127.0.0.1", () => {
      server.close(() => resolve(true));
    });
  });
}
