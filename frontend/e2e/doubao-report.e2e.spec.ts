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
  testInfo.setTimeout(210000);
  tempDir = await mkdtemp(path.join(tmpdir(), "zijieagent-doubao-report-"));
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
  await stopBackendProcess();
  if (tempDir) {
    await rm(tempDir, { force: true, recursive: true });
  }
});

test("creates a Doubao builtin-candidate task and opens the AI assistant report", async ({
  page
}) => {
  await page.goto(frontendUrl);

  await expect(page.getByRole("heading", { name: "分析任务输入" })).toBeVisible();
  await chooseSelectOption(page, "品类", "互联网产品");

  await expect(page.getByRole("textbox", { name: "目标产品链接" })).toHaveValue(
    "https://www.doubao.com/chat/"
  );
  await expect(page.getByText("AI 助手").first()).toBeVisible();
  await expect(page.getByText(/Kimi、DeepSeek、千问、腾讯元宝/).first()).toBeVisible();
  await expect(page.getByText("内置候选池").first()).toBeVisible();

  await page.getByRole("button", { name: "启动分析任务" }).click();

  await expect(page).toHaveURL(/\/overview\?task_id=task_/, { timeout: 120000 });
  const taskId = new URL(page.url()).searchParams.get("task_id");
  expect(taskId).toBeTruthy();

  await expect(page.getByRole("heading", { name: "竞争态势总览" })).toBeVisible({
    timeout: 120000
  });
  await expect(page.getByLabel("竞争态势总览首屏")).toContainText("豆包", {
    timeout: 120000
  });

  await page.getByLabel("主导航").getByRole("button", { exact: true, name: "分析报告" }).click();

  await expect(page).toHaveURL(new RegExp(`/report\\?task_id=${taskId}`));
  await expect(page.getByRole("heading", { name: "分析报告" })).toBeVisible({
    timeout: 120000
  });
  await expect(page.getByLabel("报告章节")).toContainText("豆包", { timeout: 120000 });
  await expect(page.getByLabel("报告章节")).toContainText("Kimi");
  await expect(page.getByLabel("报告章节")).toContainText("商业模式/付费层");
  await expect(page.getByLabel("报告章节")).toContainText(/互联网产品\s*\/\s*AI 助手/);
  await expect(page.getByRole("button", { name: "下载 Word 报告" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Markdown/ })).toHaveCount(0);
});

async function chooseSelectOption(page: Page, label: string, option: string) {
  await page.getByRole("combobox", { exact: true, name: label }).click();
  await page
    .locator(".ant-select-item-option")
    .filter({ hasText: new RegExp(`^${escapeRegExp(option)}$`) })
    .last()
    .click();
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function startBackend(runDir: string) {
  const repoRoot = resolveRepoRoot();
  const backendDir = path.join(repoRoot, "backend");
  const bundledPython = path.join(backendDir, ".conda312", "python.exe");
  const python = existsSync(bundledPython) ? bundledPython : "python";
  const databaseUrl = `sqlite:///${path.join(runDir, "doubao-report.db").replace(/\\/g, "/")}`;
  const reportOutputDir = path.join(runDir, "reports");

  const child = spawn(
    python,
    ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", String(backendPort)],
    {
      cwd: backendDir,
      env: {
        ...process.env,
        DATABASE_URL: databaseUrl,
        DOUBAO_API_KEY: "",
        DOUBAO_BASE_URL: "",
        LLM_ENABLED: "false",
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

async function stopBackendProcess() {
  if (
    !backendProcess ||
    backendProcess.exitCode !== null ||
    backendProcess.signalCode !== null ||
    backendProcess.killed
  ) {
    return;
  }

  await new Promise<void>((resolve) => {
    const timeout = setTimeout(resolve, 5000);
    backendProcess.once("close", () => {
      clearTimeout(timeout);
      resolve();
    });
    if (!backendProcess.kill()) {
      clearTimeout(timeout);
      resolve();
    }
  });
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
  const deadline = Date.now() + 90000;
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
