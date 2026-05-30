import { expect, test } from "@playwright/test";
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

const BACKEND_PORT = 8001;
const FRONTEND_PORT = 4175;
const backendUrl = `http://127.0.0.1:${BACKEND_PORT}`;
const frontendUrl = `http://127.0.0.1:${FRONTEND_PORT}`;

test.setTimeout(180000);

test.beforeAll(async ({ browserName }, testInfo) => {
  void browserName;
  testInfo.setTimeout(120000);
  tempDir = await mkdtemp(path.join(tmpdir(), "zijieagent-task-flow-"));
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

test("creates a task and opens overview, battlefield, profile, report, and trace from real APIs", async ({
  page
}) => {
  await page.goto(frontendUrl);

  await page.getByRole("button", { name: "启动分析任务" }).click();

  await expect(page).toHaveURL(/\/overview\?task_id=task_/, { timeout: 90000 });
  await expect(page.getByRole("heading", { level: 2, name: "竞争态势总览" })).toBeVisible({
    timeout: 90000
  });
  await expect(page.getByLabel("竞争态势总览首屏")).toBeVisible();
  await expect(page.getByLabel("核心判断")).toBeVisible();
  await expect(page.getByLabel("首要行动建议")).toBeVisible();

  const taskId = new URL(page.url()).searchParams.get("task_id");
  expect(taskId).toBeTruthy();

  await clickNav(page, "竞争图谱");
  await expect(page).toHaveURL(new RegExp(`/battlefield\\?task_id=${taskId}`));
  await expect(page.getByRole("region", { exact: true, name: "竞争关系图" })).toBeVisible();
  await expect(page.getByLabel("关键竞争关系")).toContainText("威胁等级");
  await expect(page.locator(".react-flow__edge")).not.toHaveCount(0);

  await clickNav(page, "产品与竞品画像");
  await expect(page).toHaveURL(new RegExp(`/profile\\?task_id=${taskId}`));
  await expect(page.getByLabel("目标产品与核心竞品横向对比")).toBeVisible();
  await expect(page.getByRole("heading", { name: "基础信息" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "价格与证据" })).toBeVisible();
  await expect(page.getByLabel("修正画像")).toBeVisible();

  await clickNav(page, "分析报告");
  await expect(page).toHaveURL(new RegExp(`/report\\?task_id=${taskId}`));
  await expect(page.getByLabel("报告章节")).toBeVisible();
  await expect(page.getByRole("heading", { exact: true, name: "结论摘要" })).toBeVisible();
  await expect(page.getByRole("heading", { exact: true, name: "证据与质检附录" })).toBeVisible();
  await expect(page.getByRole("button", { name: "下载 Word 报告" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Markdown/ })).toHaveCount(0);

  await clickNav(page, "证据与过程追踪");
  await expect(page).toHaveURL(new RegExp(`/trace\\?task_id=${taskId}`));
  await expect(page.getByText("当前状态：已完成")).toBeVisible({ timeout: 90000 });
  await expect(page.getByRole("region", { exact: true, name: "证据链" })).toBeVisible();
  await page.getByRole("tab", { name: /智能体过程/ }).click();
  await expect(page.getByLabel("运行记录列表")).toContainText("报告智能体");
  await expect(page.getByRole("region", { exact: true, name: "流程图状态" })).toBeVisible();
});

async function clickNav(page: import("@playwright/test").Page, name: string) {
  await page.getByLabel("主导航").getByRole("button", { exact: true, name }).click();
}

function startBackend(runDir: string) {
  const repoRoot = resolveRepoRoot();
  const backendDir = path.join(repoRoot, "backend");
  const bundledPython = path.join(backendDir, ".conda312", "python.exe");
  const python = existsSync(bundledPython) ? bundledPython : "python";
  const databaseUrl = `sqlite:///${path.join(runDir, "task-flow.db").replace(/\\/g, "/")}`;
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
