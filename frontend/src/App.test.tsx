import "@testing-library/jest-dom/vitest";

import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { ApiClientError } from "./api";
import type { ApiClient, components } from "./api";

type TaskCreateResponse = components["schemas"]["TaskCreateResponse"];
type ProductProfileData = components["schemas"]["ProductProfileData"];
type BattlefieldData = components["schemas"]["BattlefieldData"];
type HumanFeedbackCreateResponse = components["schemas"]["HumanFeedbackCreateResponse"];
type MarkdownReport = components["schemas"]["MarkdownReport"];
type ReportData = components["schemas"]["ReportData"];
type TaskStatus = components["schemas"]["TaskStatus"];
type TaskStatusResponse = components["schemas"]["TaskStatusResponse"];
type TraceData = components["schemas"]["TraceData"];
type MockApiClient = Pick<ApiClient, "get" | "post"> & {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

const ROUTE_TITLES = [
  ["任务输入", "/", "分析任务输入"],
  ["产品画像", "/profile", "产品画像"],
  ["竞争图谱", "/battlefield", "竞争关系图谱"],
  ["分析报告", "/report", "分析报告"],
  ["过程追踪", "/trace", "智能体过程追踪"]
] as const;

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

function createMockApiClient(resolveGet: (path: string) => unknown): MockApiClient {
  return {
    get: vi.fn(<TData,>(path: string) => Promise.resolve(resolveGet(path) as TData)),
    post: vi.fn()
  } as MockApiClient;
}

beforeEach(() => {
  vi.stubGlobal("ResizeObserver", ResizeObserverMock);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
  window.history.pushState({}, "", "/");
});

describe("App workspace routing", () => {
  it.each(ROUTE_TITLES)("renders the %s page route", (_, path, title) => {
    window.history.pushState({}, "", path);

    render(<App />);

    expect(screen.getByRole("heading", { level: 2, name: title })).toBeTruthy();
  });

  it("navigates between all workspace pages", () => {
    render(<App />);

    for (const [label, , title] of ROUTE_TITLES) {
      fireEvent.click(screen.getByRole("button", { name: label }));

      expect(screen.getByRole("heading", { level: 2, name: title })).toBeTruthy();
      expect(screen.getByRole("button", { name: label })).toHaveAttribute("aria-current", "page");
    }
  });

  it("renders the primary navigation landmark", () => {
    render(<App />);

    expect(screen.getByLabelText("主导航")).toBeTruthy();
  });

  it("prevents submitting when required task fields are missing", () => {
    const apiClient = { get: vi.fn(), post: vi.fn() };
    render(<App apiClient={apiClient} />);

    fireEvent.change(screen.getByLabelText("目标产品名称"), { target: { value: "   " } });
    fireEvent.click(screen.getByRole("button", { name: "启动分析任务" }));

    expect(screen.getByText("请输入目标产品名称。")).toBeInTheDocument();
    expect(apiClient.post).not.toHaveBeenCalled();
  });

  it("defaults the task data source mode to the local snapshot", () => {
    render(<App />);

    expect(screen.getByLabelText("本地快照使用脱敏 SKU 快照运行稳定 Demo。")).toBeChecked();
  });

  it("creates a task from a valid form and navigates to the trace page", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(taskStatusResponse("task_frontend_001", "created")),
      post: vi.fn().mockResolvedValue(taskCreateResponse("task_frontend_001"))
    };
    render(<App apiClient={apiClient} />);

    fireEvent.change(screen.getByLabelText("用户研究文本"), {
      target: { value: "多猫家庭关注除臭和维护成本。" }
    });
    fireEvent.click(screen.getByRole("button", { name: "启动分析任务" }));

    expect(await screen.findByRole("heading", { level: 2, name: "智能体过程追踪" })).toBeTruthy();
    expect(window.location.pathname).toBe("/trace");
    expect(window.location.search).toBe("?task_id=task_frontend_001");
    expect(apiClient.post).toHaveBeenCalledWith(
      "/tasks",
      expect.objectContaining({
        category: "smart_pet_hardware",
        data_source_mode: "demo_snapshot",
        research_text: "多猫家庭关注除臭和维护成本。",
        subcategory: "automatic_litter_box",
        target_product_name: "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
        target_product_url: "https://v.douyin.com/mv8e4KRLLwc/"
      })
    );
  });

  it("shows the stability notice for the snapshot plus live mode", () => {
    render(<App />);

    fireEvent.click(
      screen.getByLabelText("快照 + 公开页增强MVP 中记录该模式，并继续以本地快照兜底。")
    );

    expect(
      screen.getByText("公开页增强可能受页面可访问性影响；本次 MVP 会自动降级使用本地快照。")
    ).toBeInTheDocument();
  });

  it("shows API errors from task creation", async () => {
    const apiClient = {
      get: vi.fn(),
      post: vi.fn().mockRejectedValue(
        new ApiClientError({
          code: "TASK_CREATE_FAILED",
          message: "任务创建失败",
          traceId: "trace_create_failed"
        })
      )
    };
    render(<App apiClient={apiClient} />);

    fireEvent.click(screen.getByRole("button", { name: "启动分析任务" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("任务创建失败");
    expect(screen.getByText("错误码：TASK_CREATE_FAILED")).toBeInTheDocument();
    expect(screen.getByText("追踪编号：trace_create_failed")).toBeInTheDocument();
    expect(window.location.pathname).toBe("/");
  });

  it("keeps polling while the task is running", async () => {
    const taskStatuses = [
      taskStatusResponse("task_running_001", "created"),
      taskStatusResponse("task_running_001", "analyzing")
    ];
    const apiClient = createMockApiClient((path: string) => {
      if (path.endsWith("/trace")) {
        return traceResponse();
      }

      return taskStatuses.shift() ?? taskStatusResponse("task_running_001", "analyzing");
    });
    window.history.pushState({}, "", "/trace?task_id=task_running_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("当前状态：已创建")).toBeInTheDocument();

    await waitFor(
      () =>
        expect(
          apiClient.get.mock.calls.filter(([path]) => path === "/tasks/task_running_001").length
        ).toBeGreaterThanOrEqual(2),
      { timeout: 2500 }
    );
    expect(await screen.findByText("当前状态：分析中")).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_running_001");
  }, 4000);

  it("stops polling after the task is completed", async () => {
    const apiClient = createMockApiClient((path: string) =>
      path.endsWith("/trace")
        ? traceResponse({ taskId: "task_completed_001" })
        : taskStatusResponse("task_completed_001", "completed")
    );
    window.history.pushState({}, "", "/trace?task_id=task_completed_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("当前状态：已完成")).toBeInTheDocument();

    await new Promise((resolve) => setTimeout(resolve, 1200));

    expect(
      apiClient.get.mock.calls.filter(([path]) => path === "/tasks/task_completed_001")
    ).toHaveLength(1);
    expect(screen.getByText("已停止轮询")).toBeInTheDocument();
  }, 4000);

  it("keeps the task id when opening completed task result pages", async () => {
    const apiClient = createMockApiClient((path: string) => {
      if (path.endsWith("/trace")) {
        return traceResponse({ taskId: "task_flow_001" });
      }
      if (path.endsWith("/profile")) {
        return productProfileResponse();
      }
      if (path.endsWith("/battlefield")) {
        return battlefieldResponse();
      }
      if (path.endsWith("/report")) {
        return reportResponse();
      }
      return taskStatusResponse("task_flow_001", "completed");
    });
    window.history.pushState({}, "", "/trace?task_id=task_flow_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("当前状态：已完成")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "查看画像" }));
    expect(window.location.pathname).toBe("/profile");
    expect(window.location.search).toBe("?task_id=task_flow_001");
    expect(await screen.findByRole("heading", { level: 4, name: "基础信息" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "PricingModel" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "竞争图谱" }));
    expect(window.location.pathname).toBe("/battlefield");
    expect(window.location.search).toBe("?task_id=task_flow_001");
    expect(await screen.findByText("edge_direct_001")).toBeInTheDocument();
    expect(screen.getByText("核心直接竞品")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "分析报告" }));
    expect(window.location.pathname).toBe("/report");
    expect(window.location.search).toBe("?task_id=task_flow_001");
    expect(await screen.findByText("report_task_report_001_001")).toBeInTheDocument();
  });

  it("shows a failure message for failed tasks", async () => {
    const apiClient = createMockApiClient((path: string) =>
      path.endsWith("/trace")
        ? traceResponse({
            taskId: "task_failed_001",
            taskStatus: "failed",
            workflowStatus: "failed"
          })
        : taskStatusResponse("task_failed_001", "failed")
    );
    window.history.pushState({}, "", "/trace?task_id=task_failed_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("当前状态：失败")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("任务执行失败");
  });

  it("restores task status from the URL after a page refresh", async () => {
    const apiClient = createMockApiClient((path: string) =>
      path.endsWith("/trace")
        ? traceResponse({ taskId: "task_restore_001", taskStatus: "reviewing" })
        : taskStatusResponse("task_restore_001", "reviewing")
    );
    window.history.pushState({}, "", "/trace?task_id=task_restore_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("当前状态：质检中")).toBeInTheDocument();
    expect(screen.getByText("task_restore_001")).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_restore_001");
  });

  it("renders the real trace DAG and agent run details from the Trace API", async () => {
    const apiClient = createMockApiClient((path: string) =>
      path.endsWith("/trace") ? traceResponse() : taskStatusResponse("task_trace_001", "completed")
    );
    window.history.pushState({}, "", "/trace?task_id=task_trace_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("trace_task_trace_001")).toBeInTheDocument();
    const dag = screen.getByLabelText("LangGraph DAG 状态");
    expect(dag).toBeInTheDocument();
    const agentRuns = screen.getByLabelText("Agent Run 列表");
    expect(within(agentRuns).getByText("Collection Agent")).toBeInTheDocument();
    expect(within(agentRuns).getByText("Analysis Agent")).toBeInTheDocument();
    expect(within(agentRuns).getByText("QA Agent")).toBeInTheDocument();
    expect(within(agentRuns).getByText("Writer Agent")).toBeInTheDocument();
    expect(within(agentRuns).getByText("读取本地 SKU 快照并生成结构化证据。")).toBeInTheDocument();
    expect(
      within(screen.getByLabelText("Tool Call 列表")).getByText("snapshot_loader")
    ).toBeInTheDocument();
    expect(
      within(screen.getByLabelText("Token Usage 列表")).getByText("总计 42 tokens")
    ).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_trace_001/trace");
  });

  it("renders QA revision records and diff view from the Trace API", async () => {
    const apiClient = createMockApiClient((path: string) =>
      path.endsWith("/trace") ? traceResponse() : taskStatusResponse("task_trace_001", "completed")
    );
    window.history.pushState({}, "", "/trace?task_id=task_trace_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("价格证据完整性")).toBeInTheDocument();
    expect(screen.getByText("TIMELY_EVIDENCE_MISSING_ACCESS_TIME")).toBeInTheDocument();
    expect(screen.getByText("msg_trace_revision")).toBeInTheDocument();
    expect(screen.getByText("collection_agent_repair")).toBeInTheDocument();
    expect(screen.getByText("Before")).toBeInTheDocument();
    expect(screen.getByText("After")).toBeInTheDocument();
    expect(screen.getByText("2026-05-23 16:00:59+08:00")).toBeInTheDocument();
  });

  it("keeps prompt previews folded and redacts sensitive trace text", async () => {
    const apiClient = createMockApiClient((path: string) =>
      path.endsWith("/trace")
        ? traceResponse({
            promptSummary:
              "调用模型时携带 api_key=sk-test-secret-token、token=internal-secret、" +
              "手机 13800138000、account_id=acct-private-001、地址: 北京市朝阳区幸福路88号3单元501室。"
          })
        : taskStatusResponse("task_trace_001", "completed")
    );
    window.history.pushState({}, "", "/trace?task_id=task_trace_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("Collection prompt")).toBeInTheDocument();
    const promptDetails = screen.getByText("Collection prompt").closest("details");
    expect(promptDetails).not.toHaveAttribute("open");
    expect(
      within((promptDetails as HTMLElement).querySelector("summary") as HTMLElement).getByText(
        /已脱敏/
      )
    ).toBeInTheDocument();
    expect(screen.queryByText("sk-test-secret-token")).not.toBeInTheDocument();
    expect(screen.queryByText("internal-secret")).not.toBeInTheDocument();
    expect(screen.queryByText("13800138000")).not.toBeInTheDocument();
    expect(screen.queryByText("acct-private-001")).not.toBeInTheDocument();
    expect(screen.queryByText("北京市朝阳区幸福路88号3单元501室")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Collection prompt"));

    expect(screen.getByText(/凭据=\[已脱敏\]/)).toBeInTheDocument();
    expect(screen.getByText(/账号=\[已脱敏\]/)).toBeInTheDocument();
    expect(screen.getByText(/地址=\[已脱敏\]/)).toBeInTheDocument();
    expect(screen.queryByText(/api[_-]?key/i)).not.toBeInTheDocument();
  });

  it("renders all product profile modules from the profile API", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(productProfileResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/profile?task_id=task_profile_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByRole("heading", { level: 4, name: "基础信息" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "FeatureTree" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "PricingModel" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "UserPersona" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "Evidence 摘要" })).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_profile_001/profile");
  });

  it("shows a risk state when pricing evidence misses access time", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(
        productProfileResponse({
          pricingAccessTime: null,
          pricingRiskFlags: ["missing_access_time"]
        })
      ),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/profile?task_id=task_profile_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("价格证据：暂无可靠数据")).toBeInTheDocument();
    expect(screen.getAllByText("缺少访问时间").length).toBeGreaterThan(0);
  });

  it("limits the human review form to allowed profile fields", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(productProfileResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/profile?task_id=task_profile_001");

    render(<App apiClient={apiClient} />);

    const reviewPanel = await screen.findByLabelText("有限人工修正");
    const fieldSelect = within(reviewPanel).getByLabelText("修正字段");

    expect(within(fieldSelect).getByRole("option", { name: "品牌" })).toBeInTheDocument();
    expect(within(fieldSelect).getByRole("option", { name: "店铺" })).toBeInTheDocument();
    expect(within(fieldSelect).queryByRole("option", { name: "整份报告" })).not.toBeInTheDocument();
    expect(
      within(fieldSelect).queryByRole("option", { name: "Claim 正文" })
    ).not.toBeInTheDocument();
  });

  it("submits human review feedback and updates the page state", async () => {
    const apiClient = {
      get: vi
        .fn()
        .mockResolvedValueOnce(productProfileResponse())
        .mockResolvedValueOnce(productProfileResponse({ brand: "人工确认品牌" })),
      post: vi.fn().mockResolvedValue(humanFeedbackResponse())
    };
    window.history.pushState({}, "", "/profile?task_id=task_profile_001");

    render(<App apiClient={apiClient} />);

    const reviewPanel = await screen.findByLabelText("有限人工修正");
    fireEvent.change(within(reviewPanel).getByLabelText("修正值"), {
      target: { value: "人工确认品牌" }
    });
    fireEvent.change(within(reviewPanel).getByLabelText("修正理由"), {
      target: { value: "人工复核品牌字段后修正。" }
    });
    fireEvent.click(within(reviewPanel).getByRole("button", { name: "提交人工修正" }));

    expect(
      await within(reviewPanel).findByText("人工修正已提交，相关结果已刷新。")
    ).toBeInTheDocument();
    await waitFor(() => expect(apiClient.get).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("人工确认品牌")).toBeInTheDocument();
    expect(apiClient.post).toHaveBeenCalledWith(
      "/tasks/task_profile_001/feedback",
      expect.objectContaining({
        action: "update_field",
        after_value: {
          field: "brand",
          value: "人工确认品牌"
        },
        reason: "人工复核品牌字段后修正。",
        target_id: "prod_target",
        target_type: "product"
      })
    );
  });

  it("renders competition graph nodes and edges from the battlefield API", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(battlefieldResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/battlefield?task_id=task_battlefield_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("目标自动猫砂盆")).toBeInTheDocument();
    expect(screen.getByText("核心直接竞品")).toBeInTheDocument();
    expect(screen.getByTestId("competition-flow")).toBeInTheDocument();
    expect(screen.getByLabelText("竞争边详情")).toHaveTextContent("edge_direct_001");
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_battlefield_001/battlefield", {
      query: {}
    });
  });

  it("updates selected slice and refetches battlefield data", async () => {
    const apiClient = {
      get: vi
        .fn()
        .mockResolvedValueOnce(battlefieldResponse())
        .mockResolvedValueOnce(
          battlefieldResponse({
            selectedSlice: {
              persona: null,
              price_band: "2000-3000",
              scenario: null
            }
          })
        ),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/battlefield?task_id=task_battlefield_001");

    render(<App apiClient={apiClient} />);

    const sliceDial = await screen.findByLabelText("切片拨盘");
    fireEvent.change(within(sliceDial).getByLabelText("价格带"), {
      target: { value: "2000-3000" }
    });

    await waitFor(() =>
      expect(apiClient.get).toHaveBeenLastCalledWith("/tasks/task_battlefield_001/battlefield", {
        query: {
          price_band: "2000-3000"
        }
      })
    );
    expect(
      await within(sliceDial).findByText("当前切片：价格带 2000-3000 / 全部人群 / 全部场景")
    ).toBeInTheDocument();
  });

  it("shows score explanation, evidence cards, and QA revision records for each edge", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(battlefieldResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/battlefield?task_id=task_battlefield_001");

    render(<App apiClient={apiClient} />);

    const detailPanel = await screen.findByLabelText("竞争边详情");

    expect(within(detailPanel).getByText("评分解释")).toBeInTheDocument();
    expect(within(detailPanel).getByText("需求替代性")).toBeInTheDocument();
    expect(within(detailPanel).getByText("Claim 与 Evidence")).toBeInTheDocument();
    expect(within(detailPanel).getByText("ev_edge_price")).toBeInTheDocument();
    expect(within(detailPanel).getByText("QA 打回记录")).toBeInTheDocument();
    expect(within(detailPanel).getByText("1 条")).toBeInTheDocument();
  });

  it("renders all nine report sections from the report API", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(reportResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    const reportSections = await screen.findByLabelText("报告章节");

    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "执行摘要" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "目标产品画像" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "竞品发现" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "动态竞争切片" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "决策链竞争分析" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "用户研究洞察" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "可执行建议" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "QA 审查摘要" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "Evidence 索引" })
    ).toBeInTheDocument();
    expect(screen.getByText("report_task_report_001_001")).toBeInTheDocument();
    expect(screen.getAllByText("ev_report_price").length).toBeGreaterThan(0);
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_report_001/report");
  });

  it("shows a waiting state instead of final report content when report is not ready", async () => {
    const apiClient = {
      get: vi.fn().mockRejectedValue(
        new ApiClientError({
          code: "REPORT_NOT_READY",
          details: { status: "writing", task_id: "task_report_waiting" },
          message: "Report is only available after the task is completed.",
          status: 409,
          traceId: "trace_report_waiting"
        })
      ),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_waiting");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("报告尚未生成")).toBeInTheDocument();
    expect(screen.getByText(/当前状态：报告生成中/)).toBeInTheDocument();
    expect(screen.queryByLabelText("报告章节")).not.toBeInTheDocument();
  });

  it("exports markdown from the report page", async () => {
    const apiClient = {
      get: vi
        .fn()
        .mockResolvedValueOnce(reportResponse())
        .mockResolvedValueOnce(markdownReportResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("report_task_report_001_001")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "导出 Markdown" }));

    expect(await screen.findByText(/Markdown 已导出/)).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenLastCalledWith("/tasks/task_report_001/report/markdown");
  });

  it("shows markdown export errors without hiding the web report", async () => {
    const apiClient = {
      get: vi
        .fn()
        .mockResolvedValueOnce(reportResponse())
        .mockRejectedValueOnce(
          new ApiClientError({
            code: "MARKDOWN_EXPORT_FAILED",
            message: "Markdown export failed",
            status: 500,
            traceId: "trace_markdown_failed"
          })
        ),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("report_task_report_001_001")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "导出 Markdown" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Markdown export failed");
    expect(screen.getByLabelText("报告章节")).toBeInTheDocument();
    expect(screen.getByText("错误码：MARKDOWN_EXPORT_FAILED")).toBeInTheDocument();
  });
});

function taskCreateResponse(taskId: string): TaskCreateResponse {
  return {
    status: "created",
    task: {
      category: "smart_pet_hardware",
      created_at: "2026-05-27T08:00:00Z",
      data_source_mode: "demo_snapshot",
      metadata: {},
      research_text: "多猫家庭关注除臭和维护成本。",
      status: "created",
      subcategory: "automatic_litter_box",
      target_product_name: "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
      target_product_url: "https://v.douyin.com/mv8e4KRLLwc/",
      task_id: taskId,
      updated_at: "2026-05-27T08:00:00Z"
    },
    task_id: taskId
  };
}

function taskStatusResponse(taskId: string, status: TaskStatus): TaskStatusResponse {
  return {
    category: "smart_pet_hardware",
    created_at: "2026-05-27T08:00:00Z",
    data_source_mode: "demo_snapshot",
    status,
    subcategory: "automatic_litter_box",
    target_product_name: "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
    target_product_url: "https://v.douyin.com/mv8e4KRLLwc/",
    task_id: taskId,
    updated_at: "2026-05-27T08:01:00Z"
  };
}

function traceResponse(
  overrides: {
    promptSummary?: string;
    taskId?: string;
    taskStatus?: string;
    workflowStatus?: string;
  } = {}
): TraceData {
  const taskId = overrides.taskId ?? "task_trace_001";

  return {
    agent_runs: [
      {
        agent_name: "collection_agent",
        ended_at: "2026-05-27T08:01:20Z",
        input_summary: "读取本地 SKU 快照。",
        output_summary: "读取本地 SKU 快照并生成结构化证据。",
        run_id: "run_collection",
        started_at: "2026-05-27T08:01:00Z",
        status: "succeeded",
        task_id: taskId
      },
      {
        agent_name: "analysis_agent",
        ended_at: "2026-05-27T08:02:10Z",
        input_summary: "消费 Product 与 Evidence。",
        output_summary: "生成画像、Claim 和竞争边。",
        run_id: "run_analysis",
        started_at: "2026-05-27T08:01:30Z",
        status: "succeeded",
        task_id: taskId
      },
      {
        agent_name: "qa_agent",
        ended_at: "2026-05-27T08:02:40Z",
        input_summary: "检查 Claim 与 Evidence。",
        output_summary: "发现价格证据缺少访问时间并打回 Collection。",
        run_id: "run_qa",
        started_at: "2026-05-27T08:02:20Z",
        status: "requires_revision",
        task_id: taskId
      },
      {
        agent_name: "writer_agent",
        ended_at: "2026-05-27T08:03:20Z",
        input_summary: "消费 QA 通过后的结构化产物。",
        output_summary: "生成网页报告与 Markdown 元信息。",
        run_id: "run_writer",
        started_at: "2026-05-27T08:03:00Z",
        status: "succeeded",
        task_id: taskId
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
        run_ids: ["run_collection"],
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
        run_ids: ["run_analysis"],
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
        run_ids: ["run_qa"],
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
        run_ids: ["run_writer"],
        status: "succeeded",
        visible: true
      }
    ],
    diffs: [
      {
        after: {
          access_time: "2026-05-23T16:00:59+08:00",
          risk_flags: []
        },
        before: {
          access_time: null,
          risk_flags: ["missing_access_time"]
        },
        diff_id: "collection_repair_diff_001",
        metadata: {
          target_evidence_id: "ev_trace_price"
        },
        revision_message_ids: ["msg_trace_revision"],
        source: "collection_agent_repair",
        status: "repaired",
        target_id: "ev_trace_price_repaired",
        target_type: "evidence"
      }
    ],
    generated_at: "2026-05-27T08:03:30Z",
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
        content_summary: overrides.promptSummary ?? "只展示脱敏后的 Prompt 摘要，默认折叠。",
        folded: true,
        preview_id: "prompt_collection",
        redacted: true,
        run_id: "run_collection",
        title: "Collection prompt"
      }
    ],
    qa_reviews: [
      {
        check_name: "价格证据完整性",
        created_at: "2026-05-27T08:02:30Z",
        evidence_ids: ["ev_trace_price"],
        issue_code: "TIMELY_EVIDENCE_MISSING_ACCESS_TIME",
        message: "价格证据缺少访问时间。",
        related_claim_ids: ["claim_trace_price"],
        required_action: "补齐访问时间。",
        resolved_at: "2026-05-27T08:02:55Z",
        review_task_id: "review_trace_price",
        severity: "warning",
        status: "resolved",
        target_agent: "collection_agent",
        target_id: "ev_trace_price",
        target_type: "evidence",
        task_id: taskId
      }
    ],
    revision_messages: [
      {
        artifact_type: "claim_evidence_check",
        created_at: "2026-05-27T08:02:35Z",
        evidence_ids: ["ev_trace_price"],
        from_agent: "qa_agent",
        message_id: "msg_trace_revision",
        message_type: "revision_request",
        payload: {
          required_action: "补齐访问时间。",
          target_ids: ["ev_trace_price"]
        },
        status: "requires_revision",
        task_id: taskId,
        to_agent: "collection_agent"
      }
    ],
    task_id: taskId,
    task_status: overrides.taskStatus ?? "completed",
    token_usage: [
      {
        agent_name: "collection_agent",
        completion_tokens: 0,
        created_at: "2026-05-27T08:01:20Z",
        model_name: "local_rule_flow",
        prompt_tokens: 0,
        run_id: "run_collection",
        task_id: taskId,
        total_tokens: 0,
        usage_id: "usage_collection"
      },
      {
        agent_name: "writer_agent",
        completion_tokens: 18,
        created_at: "2026-05-27T08:03:20Z",
        model_name: "Doubao-Seed-2.0-lite",
        prompt_tokens: 24,
        run_id: "run_writer",
        task_id: taskId,
        total_tokens: 42,
        usage_id: "usage_writer"
      }
    ],
    tool_calls: [
      {
        arguments_summary: {
          sku_count: 14,
          source: "demo_snapshot"
        },
        duration_ms: 420,
        ended_at: "2026-05-27T08:01:05Z",
        error_message: null,
        run_id: "run_collection",
        started_at: "2026-05-27T08:01:00Z",
        status: "succeeded",
        task_id: taskId,
        tool_call_id: "tool_snapshot_loader",
        tool_name: "snapshot_loader"
      },
      {
        arguments_summary: {
          check_scope: "claim_evidence",
          evidence_count: 14
        },
        duration_ms: 180,
        ended_at: "2026-05-27T08:02:34Z",
        error_message: null,
        run_id: "run_qa",
        started_at: "2026-05-27T08:02:30Z",
        status: "succeeded",
        task_id: taskId,
        tool_call_id: "tool_qa_rules",
        tool_name: "qa_rules"
      }
    ],
    trace_view_id: `trace_${taskId}`,
    workflow_status: overrides.workflowStatus ?? "completed"
  };
}

function productProfileResponse(
  options: {
    brand?: string;
    pricingAccessTime?: string | null;
    pricingRiskFlags?: ProductProfileData["pricing_evidence"]["risk_flags"];
  } = {}
): ProductProfileData {
  const brand = options.brand ?? "小佩";
  const pricingAccessTime =
    "pricingAccessTime" in options ? options.pricingAccessTime : "2026-05-27T08:00:00Z";
  const pricingRiskFlags = options.pricingRiskFlags ?? [];

  return {
    evidence_summaries: [
      {
        access_time: pricingAccessTime,
        access_time_status: pricingAccessTime ? "available" : "missing",
        confidence_level: "medium",
        content_summary: "商品页快照记录目标产品价格、核心卖点和套装信息。",
        evidence_id: "ev_profile_price",
        limitations: "来源为本地脱敏快照，非实时页面。",
        product_id: "prod_target",
        risk_flags: pricingRiskFlags,
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
      task_id: "task_profile_001"
    },
    generated_at: "2026-05-27T08:05:00Z",
    metadata: {
      evidence_count: 1
    },
    pricing_evidence: {
      access_time: pricingAccessTime,
      access_time_status: pricingAccessTime ? "available" : "missing",
      evidence_ids: ["ev_profile_price"],
      risk_flags: pricingRiskFlags
    },
    pricing_model: {
      access_time: pricingAccessTime,
      bundle_description: "主机与基础耗材套装",
      currency: "CNY",
      evidence_ids: ["ev_profile_price"],
      final_price: 1699,
      list_price: 1899,
      price_band: "1500-2000",
      pricing_model_id: "pricing_target",
      product_id: "prod_target",
      promotions: ["直播间优惠"],
      risk_flags: pricingRiskFlags,
      task_id: "task_profile_001"
    },
    product: {
      brand,
      category: "smart_pet_hardware",
      created_at: "2026-05-27T08:00:00Z",
      evidence_ids: ["ev_profile_price"],
      name: "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
      product_id: "prod_target",
      product_url: "https://v.douyin.com/mv8e4KRLLwc/",
      role: "target",
      shop_name: "小佩宠物旗舰店",
      sku_id: "sku_02",
      subcategory: "automatic_litter_box",
      task_id: "task_profile_001",
      tags: ["自动清理", "可视化"]
    },
    profile_id: "profile_task_profile_001_prod_target",
    task_id: "task_profile_001",
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
      task_id: "task_profile_001"
    }
  };
}

function battlefieldResponse(
  options: {
    selectedSlice?: BattlefieldData["selected_slice"];
  } = {}
): BattlefieldData {
  const selectedSlice = options.selectedSlice ?? {
    persona: null,
    price_band: null,
    scenario: null
  };

  return {
    available_slices: [
      {
        edge_count: 1,
        persona: "多猫家庭",
        price_band: "1500-2000",
        scenario: "重除臭",
        top_edge_score: 0.86
      },
      {
        edge_count: 1,
        persona: "预算敏感",
        price_band: "2000-3000",
        scenario: "低维护",
        top_edge_score: 0.74
      }
    ],
    battlefield_id: "battlefield_task_battlefield_001_all",
    decision_chain: [
      {
        average_edge_score: 0.86,
        claim_ids: ["claim_edge_direct"],
        edge_ids: ["edge_direct_001"],
        evidence_ids: ["ev_edge_price"],
        stage: "capability_understanding"
      }
    ],
    evidence_cards: [
      {
        access_time: "2026-05-27T08:00:00Z",
        access_time_status: "available",
        confidence_level: "medium",
        content_summary: "商品页快照显示竞品在除臭和维护体验上形成直接竞争。",
        evidence_id: "ev_edge_price",
        limitations: "来源为本地快照，非实时页面。",
        product_id: "prod_competitor",
        risk_flags: [],
        screenshot_path: "data/raw/sku_01/price.png",
        source_type: "douyin_sku_snapshot",
        source_url: "https://example.com/competitor"
      }
    ],
    generated_at: "2026-05-27T08:05:00Z",
    graph_edges: [
      {
        claim_ids: ["claim_edge_direct"],
        claim_refs: [
          {
            claim_id: "claim_edge_direct",
            confidence: 0.82,
            content: "核心直接竞品在当前切片下与目标产品争夺同一多猫家庭需求。",
            evidence_ids: ["ev_edge_price"],
            is_inference: true,
            risk_flags: [],
            status: "accepted"
          }
        ],
        competition_type: "direct",
        competitor_product_id: "prod_competitor",
        decision_stages: ["capability_understanding", "decision_completion"],
        edge_id: "edge_direct_001",
        edge_score: 0.86,
        evidence_ids: ["ev_edge_price"],
        human_adjusted: false,
        risk_flags: [],
        risk_status: "normal",
        score_breakdown: {
          context_match: 0.84,
          decision_stage_impact: 0.8,
          demand_substitutability: 0.92,
          evidence_confidence: 0.78,
          market_signal_strength: 0.72
        },
        score_explanations: [
          "edge_score=0.8600; competition_type=direct.",
          "demand_substitutability=0.92, context_match=0.84, decision_stage_impact=0.80."
        ],
        slice: {
          persona: "多猫家庭",
          price_band: "1500-2000",
          scenario: "重除臭"
        },
        source: "prod_target",
        target: "prod_competitor",
        target_product_id: "prod_target"
      }
    ],
    graph_nodes: [
      {
        brand: "小佩",
        evidence_ids: ["ev_target"],
        label: "目标自动猫砂盆",
        node_id: "prod_target",
        product_id: "prod_target",
        product_url: "https://example.com/target",
        risk_flags: [],
        role: "target",
        shop_name: "目标旗舰店"
      },
      {
        brand: "竞品品牌",
        evidence_ids: ["ev_edge_price"],
        label: "核心直接竞品",
        node_id: "prod_competitor",
        product_id: "prod_competitor",
        product_url: "https://example.com/competitor",
        risk_flags: [],
        role: "direct_competitor",
        shop_name: "竞品旗舰店"
      }
    ],
    metadata: {
      edge_count: 1,
      node_count: 2
    },
    qa_summary: {
      open_review_task_count: 0,
      qa_status: "passed",
      resolved_review_task_count: 1,
      review_task_count: 1,
      review_task_ids: ["review_price_access_time"],
      revision_message_count: 1,
      risk_claim_ids: [],
      risk_edge_ids: []
    },
    score_explanations: [
      {
        claim_ids: ["claim_edge_direct"],
        edge_id: "edge_direct_001",
        edge_score: 0.86,
        evidence_ids: ["ev_edge_price"],
        explanations: ["五维评分均来自结构化边与证据。"],
        score_breakdown: {
          context_match: 0.84,
          decision_stage_impact: 0.8,
          demand_substitutability: 0.92,
          evidence_confidence: 0.78,
          market_signal_strength: 0.72
        }
      }
    ],
    selected_slice: selectedSlice,
    task_id: "task_battlefield_001"
  };
}

function reportResponse(): ReportData {
  return {
    competitor_findings: {
      claim_ids: ["claim_report_direct"],
      evidence_ids: ["ev_report_price"],
      items: [
        {
          claims: [
            {
              claim_id: "claim_report_direct",
              confidence: 0.82,
              content: "核心直接竞品在当前切片下争夺同一多猫家庭需求。",
              evidence_ids: ["ev_report_price"],
              is_inference: true,
              risk_flags: [],
              status: "accepted"
            }
          ],
          competition_type: "direct",
          competitor: {
            brand: "竞品品牌",
            name: "核心直接竞品",
            product_id: "prod_competitor",
            product_url: "https://example.com/competitor",
            role: "direct_competitor"
          },
          decision_stages: ["capability_understanding"],
          edge_id: "edge_report_direct",
          edge_score: 0.86,
          evidence_ids: ["ev_report_price"],
          risk_flags: [],
          score_breakdown: {
            context_match: 0.84,
            decision_stage_impact: 0.8,
            demand_substitutability: 0.92,
            evidence_confidence: 0.78,
            market_signal_strength: 0.72
          },
          slice: {
            persona: "多猫家庭",
            price_band: "1500-2000",
            scenario: "重除臭"
          }
        }
      ],
      risk_flags: [],
      section_id: "competitor_findings",
      summary: "按竞争评分排序展示核心竞品关系，结论均保留 Claim 与 Evidence 索引。",
      title: "竞品发现"
    },
    decision_chain_analysis: reportSection("decision_chain_analysis", "决策链竞争分析", [
      {
        claim_ids: ["claim_report_direct"],
        decision_stage: "capability_understanding",
        edge_ids: ["edge_report_direct"],
        evidence_ids: ["ev_report_price"]
      }
    ]),
    dynamic_slice_analysis: reportSection("dynamic_slice_analysis", "动态竞争切片", [
      {
        claim_ids: ["claim_report_direct"],
        edge_ids: ["edge_report_direct"],
        evidence_ids: ["ev_report_price"],
        persona: "多猫家庭",
        price_band: "1500-2000",
        scenario: "重除臭",
        top_edge_score: 0.86
      }
    ]),
    evidence_index: {
      claim_ids: [],
      evidence_ids: ["ev_report_price"],
      items: [
        {
          access_time: "2026-05-27T08:00:00Z",
          confidence_level: "medium",
          content_summary: "商品页快照显示竞品在除臭和维护体验上形成直接竞争。",
          evidence_id: "ev_report_price",
          limitations: "来源为本地快照，非实时页面。",
          product_id: "prod_competitor",
          screenshot_path: "data/raw/sku_01/price.png",
          source_type: "douyin_sku_snapshot",
          source_url: "https://example.com/competitor"
        }
      ],
      risk_flags: [],
      section_id: "evidence_index",
      summary: "列出报告中可追溯的证据来源、访问时间、截图和局限性。",
      title: "Evidence 索引"
    },
    executive_summary: reportSection("executive_summary", "执行摘要", [
      {
        claim_ids: ["claim_report_direct"],
        competition_type: "direct",
        competitor_product_id: "prod_competitor",
        edge_id: "edge_report_direct",
        edge_score: 0.86,
        evidence_ids: ["ev_report_price"],
        risk_flags: []
      }
    ]),
    generated_at: "2026-05-27T08:05:00Z",
    product_profile: reportSection("product_profile", "目标产品画像", [
      {
        feature_tree: {
          cleaning_capability: ["自动铲砂"],
          odor_control: ["封闭仓体"]
        },
        pricing_model: {
          final_price: 1699,
          price_band: "1500-2000"
        },
        product: {
          brand: "小佩",
          name: "目标自动猫砂盆",
          product_id: "prod_target",
          shop_name: "目标旗舰店"
        },
        user_persona: {
          is_inference: true,
          personas: ["多猫家庭"]
        }
      }
    ]),
    qa_summary: reportSection("qa_summary", "QA 审查摘要", [
      {
        analysis_recompute: { status: "completed" },
        collection_repair: { repaired_evidence_ids: ["ev_report_price"] },
        qa_agent: { qa_status: "passed" },
        review_task_count: 1,
        revision_message_count: 1,
        risk_claims: []
      }
    ]),
    recommendations: reportSection("recommendations", "可执行建议", [
      {
        basis_edge_id: "edge_report_direct",
        claim_ids: ["claim_report_direct"],
        evidence_ids: ["ev_report_price"],
        is_inference: true,
        recommendation: "优先解释核心直接竞品在当前切片下的竞争关系。"
      }
    ]),
    report_id: "report_task_report_001_001",
    section_order: [
      "executive_summary",
      "product_profile",
      "competitor_findings",
      "dynamic_slice_analysis",
      "decision_chain_analysis",
      "user_research_insights",
      "recommendations",
      "qa_summary",
      "evidence_index"
    ],
    task_id: "task_report_001",
    user_research_insights: reportSection("user_research_insights", "用户研究洞察", [
      {
        confidence_level: "medium",
        evidence_ids: ["ev_report_price"],
        limitations: "评论快照仅作方向参考。",
        product_id: "prod_competitor",
        review_insight_id: "insight_report_001",
        risk_flags: [],
        summary: "用户关注除臭稳定性和维护成本。"
      }
    ])
  };
}

function reportSection(
  sectionId: string,
  title: string,
  items: NonNullable<ReportData["executive_summary"]["items"]>
): ReportData["executive_summary"] {
  return {
    claim_ids: ["claim_report_direct"],
    evidence_ids: ["ev_report_price"],
    items,
    risk_flags: [],
    section_id: sectionId,
    summary: `${title} 摘要`,
    title
  };
}

function markdownReportResponse(): MarkdownReport {
  return {
    file_path: "D:\\pythonproject\\zijieagent\\data\\reports\\task_report_001_report.md",
    generated_at: "2026-05-27T08:06:00Z",
    markdown: "# 竞品分析报告\n\n## 执行摘要\n",
    markdown_report_id: "markdown_report_task_report_001_001",
    metadata: {
      section_count: 9
    },
    report_id: "report_task_report_001_001",
    task_id: "task_report_001"
  };
}

function humanFeedbackResponse(): HumanFeedbackCreateResponse {
  return {
    affected_artifact_ids: ["prod_target"],
    feedback: {
      action: "update_field",
      after_value: {
        field: "brand",
        value: "人工确认品牌"
      },
      before_value: {
        field: "brand",
        value: "小佩"
      },
      created_at: "2026-05-27T08:10:00Z",
      feedback_id: "hf_task_profile_001_001",
      reason: "人工复核品牌字段后修正。",
      target_id: "prod_target",
      target_type: "product",
      task_id: "task_profile_001"
    },
    metadata: {
      local_update_applied: true,
      requires_analysis_recompute: false
    },
    recompute_status: "applied_local_update",
    task_status: "human_reviewing"
  };
}
