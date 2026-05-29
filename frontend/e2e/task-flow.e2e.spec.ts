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

test("creates a task and opens trace, profile, battlefield, and report from real APIs", async ({
  page
}) => {
  await page.goto(frontendUrl);

  await page.getByRole("button", { name: "启动分析任务" }).click();

  await expect(page).toHaveURL(/\/trace\?task_id=task_/, { timeout: 90000 });
  await expect(page.getByText("当前状态：已完成")).toBeVisible({ timeout: 90000 });
  await expect(page.getByLabel("Agent Run 列表")).toContainText("Writer Agent");
  await expect(page.getByRole("region", { exact: true, name: "LangGraph DAG 状态" })).toBeVisible();

  const taskId = new URL(page.url()).searchParams.get("task_id");
  expect(taskId).toBeTruthy();

  await page.getByRole("button", { name: "查看画像" }).click();
  await expect(page).toHaveURL(new RegExp(`/profile\\?task_id=${taskId}`));
  await expect(page.getByRole("heading", { name: "基础信息" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "PricingModel" })).toBeVisible();

  await page.getByRole("button", { name: "竞争图谱" }).click();
  await expect(page).toHaveURL(new RegExp(`/battlefield\\?task_id=${taskId}`));
  await expect(page.getByRole("region", { exact: true, name: "竞争关系图" })).toBeVisible();
  await expect(page.locator(".react-flow__edge")).not.toHaveCount(0);

  await page.getByRole("button", { name: "分析报告" }).click();
  await expect(page).toHaveURL(new RegExp(`/report\\?task_id=${taskId}`));
  await expect(page.getByLabel("报告章节")).toBeVisible();
  await expect(page.getByRole("heading", { exact: true, name: "执行摘要" })).toBeVisible();
});

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
