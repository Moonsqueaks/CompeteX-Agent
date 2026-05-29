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

const BACKEND_PORT = 8002;
const FRONTEND_PORT = 4176;
const backendUrl = `http://127.0.0.1:${BACKEND_PORT}`;
const frontendUrl = `http://127.0.0.1:${FRONTEND_PORT}`;

test.setTimeout(180000);

test.beforeAll(async ({ browserName }, testInfo) => {
  void browserName;
  testInfo.setTimeout(120000);
  tempDir = await mkdtemp(path.join(tmpdir(), "zijieagent-qa-revision-"));
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

test("shows the real QA collection revision, diff, recompute, and repaired report", async ({
  page
}) => {
  await page.goto(frontendUrl);

  await page.getByRole("button", { name: "启动分析任务" }).click();

  await expect(page).toHaveURL(/\/trace\?task_id=task_/, { timeout: 90000 });
  await expect(page.getByText("当前状态：已完成")).toBeVisible({ timeout: 90000 });

  const taskId = new URL(page.url()).searchParams.get("task_id");
  expect(taskId).toBeTruthy();

  const traceData = await getApiData(page, `${backendUrl}/tasks/${taskId}/trace`);
  const collectionRuns = traceData.agent_runs.filter(
    (run: Record<string, unknown>) => run.agent_name === "collection_agent"
  );
  const analysisRuns = traceData.agent_runs.filter(
    (run: Record<string, unknown>) => run.agent_name === "analysis_agent"
  );
  const qaRuns = traceData.agent_runs.filter(
    (run: Record<string, unknown>) => run.agent_name === "qa_agent"
  );
  const collectionRevision = traceData.revision_messages.find(
    (message: Record<string, unknown>) =>
      message.message_type === "revision_request" && message.to_agent === "collection_agent"
  );
  const collectionDiff = traceData.diffs.find(
    (diff: Record<string, unknown>) => diff.source === "collection_agent_repair"
  );
  const analysisDiff = traceData.diffs.find(
    (diff: Record<string, unknown>) => diff.source === "analysis_agent_recompute"
  );
  const qaReview = traceData.qa_reviews.find(
    (review: Record<string, unknown>) => review.issue_code === "TIMELY_EVIDENCE_MISSING_ACCESS_TIME"
  );

  expect(collectionRuns).toHaveLength(2);
  expect(analysisRuns).toHaveLength(2);
  expect(qaRuns).toHaveLength(2);
  expect(collectionRevision).toBeTruthy();
  expect(qaReview?.status).toBe("resolved");
  expect(collectionDiff?.before.access_time).toBeNull();
  expect(collectionDiff?.after.access_time).toBeTruthy();
  expect(collectionDiff?.after.evidence_id).toBe("ev_sku_01_repair_001");
  expect(analysisDiff?.before.edge_score).not.toBe(analysisDiff?.after.edge_score);

  await expect(page.getByLabel("QA Review 列表")).toContainText(
    "TIMELY_EVIDENCE_MISSING_ACCESS_TIME"
  );
  await expect(page.getByLabel("QA Review 列表")).toContainText("已解决");
  await expect(page.getByLabel("QA 打回消息")).toContainText("QA Agent");
  await expect(page.getByLabel("QA 打回消息")).toContainText("Collection Agent");
  await expect(page.getByLabel("Diff View")).toContainText("collection_agent_repair");
  await expect(page.getByLabel("Diff View")).toContainText("analysis_agent_recompute");
  await expect(page.getByLabel("Diff View")).toContainText("ev_sku_01_repair_001");

  await page.getByRole("button", { name: "竞争图谱" }).click();
  await expect(page).toHaveURL(new RegExp(`/battlefield\\?task_id=${taskId}`));
  await expect(page.getByLabel("QA 打回记录")).toContainText("已通过");
  await expect(page.getByLabel("QA 打回记录")).toContainText("开放 0 条");
  await expect(page.getByLabel("QA 打回记录")).toContainText("已解决 1 条");

  await page.getByRole("button", { name: "分析报告" }).click();
  await expect(page).toHaveURL(new RegExp(`/report\\?task_id=${taskId}`));
  await expect(page.getByLabel("报告章节")).toContainText("QA 审查摘要");
  await expect(page.getByLabel("报告章节")).toContainText("Collection 修复");
  await expect(page.getByLabel("报告章节")).toContainText("Analysis 重算");

  const reportData = await getApiData(page, `${backendUrl}/tasks/${taskId}/report`);
  const competitorItems = reportData.competitor_findings.items as Array<Record<string, unknown>>;
  const repairedItem = competitorItems.find((item) => item.edge_id === analysisDiff?.target_id);
  const repairedClaims = (repairedItem?.claims ?? []) as Array<Record<string, unknown>>;
  const repairedClaim = repairedClaims.find((claim) =>
    (claim.evidence_ids as string[] | undefined)?.includes("ev_sku_01_repair_001")
  );

  expect(repairedClaim).toBeTruthy();
  expect(repairedClaim?.evidence_ids).toContain("ev_sku_01_repair_001");
  expect(repairedClaim?.evidence_ids).not.toContain("ev_sku_01");
  for (const item of competitorItems) {
    for (const claim of (item.claims ?? []) as Array<Record<string, unknown>>) {
      expect(claim.evidence_ids).toBeTruthy();
      expect(claim.risk_flags ?? []).not.toContain("missing_evidence");
      expect(claim.risk_flags ?? []).not.toContain("missing_access_time");
    }
  }
});

function startBackend(runDir: string) {
  const repoRoot = resolveRepoRoot();
  const backendDir = path.join(repoRoot, "backend");
  const bundledPython = path.join(backendDir, ".conda312", "python.exe");
  const python = existsSync(bundledPython) ? bundledPython : "python";
  const databaseUrl = `sqlite:///${path.join(runDir, "qa-revision.db").replace(/\\/g, "/")}`;
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

async function getApiData(page: Page, url: string) {
  const response = await page.request.get(url);
  expect(response.ok()).toBeTruthy();
  const payload = await response.json();
  expect(payload.error).toBeNull();
  return payload.data;
}
