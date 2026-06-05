import "@testing-library/jest-dom/vitest";

import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { ApiClientError } from "./api";
import type { ApiClient, components } from "./api";

type TaskCreateResponse = components["schemas"]["TaskCreateResponse"];
type OverviewData = components["schemas"]["OverviewData"];
type ProductProfileData = components["schemas"]["ProductProfileData"];
type BattlefieldData = components["schemas"]["BattlefieldData"];
type BattlefieldGraphEdge = components["schemas"]["BattlefieldGraphEdge"];
type BattlefieldKeyRelation = components["schemas"]["BattlefieldKeyRelation"];
type HumanFeedbackCreateResponse = components["schemas"]["HumanFeedbackCreateResponse"];
type ReportData = components["schemas"]["ReportData"];
type ReportSection = components["schemas"]["ReportSection"];
type TaskStatus = components["schemas"]["TaskStatus"];
type TaskStatusResponse = components["schemas"]["TaskStatusResponse"];
type TraceData = components["schemas"]["TraceData"];
type MockApiClient = Pick<ApiClient, "get" | "post"> &
  Partial<Pick<ApiClient, "download">> & {
    download?: ReturnType<typeof vi.fn>;
    get: ReturnType<typeof vi.fn>;
    post: ReturnType<typeof vi.fn>;
  };

const ROUTE_TITLES = [
  ["任务输入", "/", "分析任务输入"],
  ["竞争态势总览", "/overview", "竞争态势总览"],
  ["竞争图谱", "/battlefield", "竞争关系图谱"],
  ["产品与竞品画像", "/profile", "产品与竞品画像"],
  ["分析报告", "/report", "分析报告"],
  ["证据与过程追踪", "/trace", "证据与过程追踪"]
] as const;
const NAV_ROUTE_TITLES = [
  ["竞争态势总览", "/overview", "竞争态势总览"],
  ["竞争图谱", "/battlefield", "竞争关系图谱"],
  ["产品与竞品画像", "/profile", "产品与竞品画像"],
  ["分析报告", "/report", "分析报告"],
  ["证据与过程追踪", "/trace", "证据与过程追踪"]
] as const;

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

type MockGetOptions = { query?: Record<string, unknown> };

function createMockApiClient(
  resolveGet: (path: string, options?: MockGetOptions) => unknown
): MockApiClient {
  return {
    get: vi.fn(<TData,>(path: string, options?: MockGetOptions) =>
      Promise.resolve(resolveGet(path, options) as TData)
    ),
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

    for (const [label, , title] of NAV_ROUTE_TITLES) {
      fireEvent.click(screen.getByRole("button", { name: label }));

      expect(screen.getByRole("heading", { level: 2, name: title })).toBeTruthy();
      expect(screen.getByRole("button", { name: label })).toHaveAttribute("aria-current", "page");
    }
  });

  it("renders the primary navigation landmark", () => {
    render(<App />);

    expect(screen.getByLabelText("主导航")).toBeTruthy();
  });

  it("renders the five 2.0 navigation entries without English process terms", () => {
    render(<App />);

    const nav = screen.getByLabelText("主导航");
    expect(within(nav).getAllByRole("button")).toHaveLength(5);
    for (const [label] of NAV_ROUTE_TITLES) {
      expect(within(nav).getByRole("button", { name: label })).toBeInTheDocument();
    }
    expect(nav).not.toHaveTextContent(/Trace|Agent/);
  });

  it("keeps default user-facing workspace copy in Chinese", async () => {
    const apiClient = createMockApiClient((path: string) => {
      if (path.endsWith("/profile")) {
        return productProfileResponse();
      }
      if (path.endsWith("/trace")) {
        return traceResponse();
      }
      return taskStatusResponse("task_i18n_001", "completed");
    });

    window.history.pushState({}, "", "/profile?task_id=task_i18n_001");
    render(<App apiClient={apiClient} />);

    expect(
      await screen.findByRole("heading", { level: 4, name: "功能能力树" })
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "价格与证据" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "用户人群画像" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "证据摘要" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "证据与过程追踪" }));

    fireEvent.click(await screen.findByRole("tab", { name: /智能体过程/ }));
    fireEvent.click(screen.getByText("技术详情"));
    expect(screen.queryByText("采集智能体提示摘要")).not.toBeInTheDocument();

    const visibleText = document.body.textContent ?? "";
    expect(visibleText).not.toMatch(
      /\b(Agent Run|Tool Call|Token Usage|Payload|Diff View|QA Review|FeatureTree|PricingModel|UserPersona|Evidence 摘要|Collection prompt|Prompt)\b/
    );
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

  it("creates a task from a valid form and navigates to the overview page", async () => {
    const apiClient = createMockApiClient((path: string) => {
      if (path.endsWith("/overview")) {
        return overviewResponse({ taskId: "task_frontend_001" });
      }
      if (path.includes("/battlefield")) {
        return battlefieldResponse();
      }
      return taskStatusResponse("task_frontend_001", "created");
    });
    apiClient.post.mockResolvedValue(taskCreateResponse("task_frontend_001"));
    render(<App apiClient={apiClient} />);

    fireEvent.change(screen.getByLabelText("用户研究文本"), {
      target: { value: "多猫家庭关注除臭和维护成本。" }
    });
    fireEvent.click(screen.getByRole("button", { name: "启动分析任务" }));

    expect(await screen.findByRole("heading", { level: 2, name: "竞争态势总览" })).toBeTruthy();
    expect(window.location.pathname).toBe("/overview");
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
      if (path.endsWith("/overview")) {
        return overviewResponse({ taskId: "task_flow_001" });
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
    fireEvent.click(screen.getByRole("button", { name: "查看总览" }));
    expect(window.location.pathname).toBe("/overview");
    expect(window.location.search).toBe("?task_id=task_flow_001");
    expect(
      await screen.findByRole("heading", { level: 2, name: "竞争态势总览" })
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "产品与竞品画像" }));
    expect(window.location.pathname).toBe("/profile");
    expect(window.location.search).toBe("?task_id=task_flow_001");
    expect(await screen.findByRole("heading", { level: 4, name: "基础信息" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "价格与证据" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "竞争图谱" }));
    expect(window.location.pathname).toBe("/battlefield");
    expect(window.location.search).toBe("?task_id=task_flow_001");
    expect(await screen.findByText("核心直接竞品 与目标产品的正面竞争")).toBeInTheDocument();
    expect(screen.getAllByText("核心直接竞品").length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: "分析报告" }));
    expect(window.location.pathname).toBe("/report");
    expect(window.location.search).toBe("?task_id=task_flow_001");
    expect(await screen.findByText("自动猫砂盆竞品分析报告")).toBeInTheDocument();
  });

  it("keeps the task id across primary navigation entries", () => {
    window.history.pushState({}, "", "/overview?task_id=task_nav_001");

    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "竞争图谱" }));
    expect(window.location.pathname).toBe("/battlefield");
    expect(window.location.search).toBe("?task_id=task_nav_001");

    fireEvent.click(screen.getByRole("button", { name: "证据与过程追踪" }));
    expect(window.location.pathname).toBe("/trace");
    expect(window.location.search).toBe("?task_id=task_nav_001");
  });

  it("renders the overview first-screen decision workspace from the Overview API", async () => {
    const apiClient = createMockApiClient((path: string) => {
      if (path.endsWith("/overview")) {
        return overviewResponse();
      }

      return taskStatusResponse("task_overview_001", "completed");
    });
    window.history.pushState({}, "", "/overview?task_id=task_overview_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("核心直接竞品正在争夺同一多猫家庭需求。")).toBeInTheDocument();
    expect(screen.getByText("可用于初步决策")).toBeInTheDocument();
    expect(screen.getAllByText("核心直接竞品").length).toBeGreaterThan(0);
    expect(screen.getByText("优先补强关键竞品对比表达")).toBeInTheDocument();
    expect(screen.getAllByText("证据风险提示").length).toBeGreaterThan(0);
    expect(screen.getByText(/脱敏 SKU 快照/)).toBeInTheDocument();
    expect(screen.getByText(/不代表实时全网数据/)).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_overview_001/overview", undefined);
  });

  it("shows a waiting state and refetches when overview is not ready yet", async () => {
    let overviewCalls = 0;
    const apiClient = createMockApiClient((path: string) => {
      if (path.endsWith("/overview")) {
        overviewCalls += 1;
        if (overviewCalls === 1) {
          return Promise.reject(
            new ApiClientError({
              code: "OVERVIEW_NOT_READY",
              details: { status: "writing", task_id: "task_overview_waiting" },
              message: "Overview data is only available after completion or human review.",
              status: 409,
              traceId: "trace_overview_waiting"
            })
          );
        }
        return overviewResponse({ taskId: "task_overview_waiting" });
      }
      if (path.includes("/battlefield")) {
        return battlefieldResponse();
      }

      return taskStatusResponse("task_overview_waiting", "writing");
    });
    window.history.pushState({}, "", "/overview?task_id=task_overview_waiting");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("竞争态势还在生成")).toBeInTheDocument();
    expect(screen.queryByText("OVERVIEW_NOT_READY")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "重新检查" }));

    expect(await screen.findByText("核心直接竞品正在争夺同一多猫家庭需求。")).toBeInTheDocument();
    expect(overviewCalls).toBe(2);
  });

  it("shows the reliable image fallback when an overview competitor has no thumbnail", async () => {
    const apiClient = createMockApiClient((path: string) => {
      if (path.endsWith("/overview")) {
        return overviewResponse({ primaryImagePath: null });
      }

      return taskStatusResponse("task_overview_001", "completed");
    });
    window.history.pushState({}, "", "/overview?task_id=task_overview_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByLabelText("暂无可靠图片")).toHaveTextContent("暂无可靠图片");
  });

  it("opens the competitor battlefield drilldown while preserving task id", async () => {
    const apiClient = createMockApiClient((path: string) => {
      if (path.endsWith("/overview")) {
        return overviewResponse();
      }
      if (path.includes("/battlefield")) {
        return battlefieldResponse();
      }

      return taskStatusResponse("task_overview_001", "completed");
    });
    window.history.pushState({}, "", "/overview?task_id=task_overview_001");

    render(<App apiClient={apiClient} />);

    fireEvent.click(await screen.findByRole("button", { name: "查看竞争关系" }));

    expect(window.location.pathname).toBe("/battlefield");
    expect(window.location.search).toContain("task_id=task_overview_001");
    expect(window.location.search).toContain("edge_id=edge_direct_001");
    expect(await screen.findByText("核心直接竞品 与目标产品的正面竞争")).toBeInTheDocument();
  });

  it("renders overview slice controls with available options", async () => {
    const apiClient = createMockApiClient((path: string) => {
      if (path.endsWith("/overview")) {
        return overviewResponse();
      }
      if (path.includes("/battlefield")) {
        return battlefieldResponse();
      }

      return taskStatusResponse("task_overview_001", "completed");
    });
    window.history.pushState({}, "", "/overview?task_id=task_overview_001");

    render(<App apiClient={apiClient} />);

    const priceBandSelect = await screen.findByRole("combobox", { name: "价格带切片" });
    await screen.findByRole("option", { name: "2000-3000" });
    const personaSelect = screen.getByRole("combobox", { name: "人群切片" });
    const scenarioSelect = screen.getByRole("combobox", { name: "使用场景切片" });

    expect(within(priceBandSelect).getByRole("option", { name: "1500-2000" })).toBeInTheDocument();
    expect(within(priceBandSelect).getByRole("option", { name: "2000-3000" })).toBeInTheDocument();
    expect(within(personaSelect).getByRole("option", { name: "多猫家庭" })).toBeInTheDocument();
    expect(within(personaSelect).getByRole("option", { name: "预算敏感" })).toBeInTheDocument();
    expect(within(scenarioSelect).getByRole("option", { name: "重除臭" })).toBeInTheDocument();
    expect(within(scenarioSelect).getByRole("option", { name: "低维护" })).toBeInTheDocument();
  });

  it("requests overview data again when the overview slice changes", async () => {
    const apiClient = createMockApiClient((path: string) => {
      if (path.endsWith("/overview")) {
        return overviewResponse();
      }
      if (path.includes("/battlefield")) {
        return battlefieldResponse();
      }

      return taskStatusResponse("task_overview_001", "completed");
    });
    window.history.pushState({}, "", "/overview?task_id=task_overview_001");

    render(<App apiClient={apiClient} />);

    await screen.findByRole("option", { name: "2000-3000" });
    fireEvent.change(await screen.findByRole("combobox", { name: "价格带切片" }), {
      target: { value: "2000-3000" }
    });

    await waitFor(() =>
      expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_overview_001/overview", {
        query: { price_band: "2000-3000" }
      })
    );
  });

  it("refreshes overview judgment and recommendation content after slice changes", async () => {
    const apiClient = createMockApiClient((path: string, options?: MockGetOptions) => {
      if (path.endsWith("/overview")) {
        if (options?.query?.price_band === "2000-3000") {
          return overviewResponse({
            actionTitle: "调整高价切片表达",
            competitorName: "高价位竞品",
            judgmentContent: "高价位切片下高价位竞品成为首要竞争对象。",
            opportunityTitle: "高价切片机会",
            riskTitle: "高价切片风险",
            selectedSlice: {
              persona: null,
              price_band: "2000-3000",
              scenario: null
            }
          });
        }

        return overviewResponse();
      }
      if (path.includes("/battlefield")) {
        return battlefieldResponse();
      }

      return taskStatusResponse("task_overview_001", "completed");
    });
    window.history.pushState({}, "", "/overview?task_id=task_overview_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("核心直接竞品正在争夺同一多猫家庭需求。")).toBeInTheDocument();
    await screen.findByRole("option", { name: "2000-3000" });
    fireEvent.change(screen.getByRole("combobox", { name: "价格带切片" }), {
      target: { value: "2000-3000" }
    });

    expect(await screen.findByText("高价位切片下高价位竞品成为首要竞争对象。")).toBeInTheDocument();
    expect(screen.getByText("高价位竞品")).toBeInTheDocument();
    expect(screen.getByText("高价切片机会")).toBeInTheDocument();
    expect(screen.getAllByText("高价切片风险").length).toBeGreaterThan(0);
    expect(screen.getByText("调整高价切片表达")).toBeInTheDocument();
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
    expect(screen.getByRole("alert")).toHaveTextContent("分析流程没有正常完成");
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
    expect(screen.getAllByText("小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆").length).toBeGreaterThan(
      0
    );
    expect(screen.queryByText("task_restore_001")).not.toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_restore_001");
  });

  it("renders the real trace DAG and agent run details from the Trace API", async () => {
    const apiClient = createMockApiClient((path: string) =>
      path.endsWith("/trace") ? traceResponse() : taskStatusResponse("task_trace_001", "completed")
    );
    window.history.pushState({}, "", "/trace?task_id=task_trace_001");

    render(<App apiClient={apiClient} />);

    expect(
      (await screen.findAllByText("小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆")).length
    ).toBeGreaterThan(0);
    expect(screen.getByRole("tab", { name: /证据链/ })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("核心直接竞品在当前切片下形成价格与除臭竞争。")).toBeInTheDocument();
    expect(screen.getAllByText("证据 1").length).toBeGreaterThan(0);
    expect(screen.getAllByText("2026/05/23 16:00").length).toBeGreaterThan(0);
    expect(screen.queryByText(/\[REDACTED\]/)).not.toBeInTheDocument();
    expect(screen.queryByText(/评论洞察尚待后续结构化抽取/)).not.toBeInTheDocument();
    expect(screen.queryByText(/source\.access_time/)).not.toBeInTheDocument();
    expect(screen.queryByText(/QA 打回后补齐字段/)).not.toBeInTheDocument();
    expect(screen.queryByText("trace_task_trace_001")).not.toBeInTheDocument();
    expect(screen.queryByText("ev_trace_price")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: /智能体过程/ }));

    const dag = screen.getByLabelText("流程图状态");
    expect(dag).toBeInTheDocument();
    const agentRuns = screen.getByLabelText("运行记录列表");
    expect(within(agentRuns).getByText("采集智能体")).toBeInTheDocument();
    expect(within(agentRuns).getByText("分析智能体")).toBeInTheDocument();
    expect(within(agentRuns).getByText("质检智能体")).toBeInTheDocument();
    expect(within(agentRuns).getByText("报告智能体")).toBeInTheDocument();
    expect(within(agentRuns).getByText("读取本地 SKU 快照并生成结构化证据。")).toBeInTheDocument();
    expect(screen.getByText("技术详情").closest("details")).not.toHaveAttribute("open");
    fireEvent.click(screen.getByText("技术详情"));
    expect(
      within(screen.getByLabelText("工具调用列表")).getByText("读取本地商品快照")
    ).toBeInTheDocument();
    expect(screen.queryByText("snapshot_loader")).not.toBeInTheDocument();
    expect(
      within(screen.getByLabelText("模型用量列表")).getByText("总计 42 个计量单位")
    ).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_trace_001/trace");
  });

  it("renders QA revision records and diff view from the Trace API", async () => {
    const apiClient = createMockApiClient((path: string) =>
      path.endsWith("/trace") ? traceResponse() : taskStatusResponse("task_trace_001", "completed")
    );
    window.history.pushState({}, "", "/trace?task_id=task_trace_001");

    render(<App apiClient={apiClient} />);

    fireEvent.click(await screen.findByRole("tab", { name: /质检记录/ }));
    expect(await screen.findByText("价格证据完整性")).toBeInTheDocument();
    expect(screen.getByText("时效证据缺少访问时间")).toBeInTheDocument();
    expect(screen.queryByText("TIMELY_EVIDENCE_MISSING_ACCESS_TIME")).not.toBeInTheDocument();
    expect(screen.getByLabelText("质检状态汇总")).toHaveTextContent("仍需关注");
    expect(screen.getByText("否，当前已闭环")).toBeInTheDocument();
    expect(screen.getByText("访问时间已补齐，结论可进入复核。")).toBeInTheDocument();
    expect(screen.queryByText(/source\.access_time/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: /差异记录/ }));
    expect(screen.getAllByText("QA 打回修复").length).toBeGreaterThan(0);
    expect(screen.getByText("QA 打回后补齐或降级证据，影响结论可采纳程度。")).toBeInTheDocument();
    expect(screen.getByText("补齐访问时间后，相关结论可以进入可复核状态。")).toBeInTheDocument();
    expect(screen.getByText("2026/05/23 16:00")).not.toBeVisible();
    fireEvent.click(screen.getByText("查看结构化前后值"));
    expect(screen.getByText("补齐访问时间后，相关结论可以进入可复核状态。")).toBeInTheDocument();
    expect(screen.getByText("变更前")).toBeInTheDocument();
    expect(screen.getByText("变更后")).toBeInTheDocument();
    expect(screen.getByText("2026/05/23 16:00")).toBeInTheDocument();
  });

  it("distinguishes unresolved QA attention and human feedback diffs in trace view", async () => {
    const apiClient = createMockApiClient((path: string) =>
      path.endsWith("/trace")
        ? traceResponse({
            extraDiffs: [
              {
                after: {
                  price_band: "中高价格带"
                },
                before: {
                  price_band: "高价格带"
                },
                business_impact: "人工修正价格带后，画像页和报告中的定位判断会同步刷新。",
                diff_id: "human_feedback_diff_trace",
                metadata: {
                  feedback_id: "feedback_trace_price_band"
                },
                revision_message_ids: [],
                source: "human_feedback",
                status: "updated",
                target_id: "pricing_trace_target",
                target_type: "pricing_model"
              }
            ],
            extraQualityRecords: [
              {
                action_result: "仍缺少截图，暂不能作为高可信证据。",
                check_item: "截图证据完整性",
                evidence_ids: ["ev_trace_missing_screenshot"],
                issue_code: "KEY_SCREENSHOT_MISSING",
                issue_summary: "关键价格证据缺少截图。",
                needs_attention: true,
                quality_record_id: "quality_trace_screenshot",
                related_claim_ids: ["claim_trace_price"],
                required_action: "补齐价格截图或降级为谨慎参考。",
                resolved: false,
                review_task_id: "review_trace_screenshot",
                severity: "error",
                status: "open",
                target_agent: "collection_agent",
                target_id: "ev_trace_missing_screenshot",
                target_type: "evidence"
              }
            ]
          })
        : taskStatusResponse("task_trace_001", "completed")
    );
    window.history.pushState({}, "", "/trace?task_id=task_trace_001");

    render(<App apiClient={apiClient} />);

    fireEvent.click(await screen.findByRole("tab", { name: /质检记录/ }));
    expect(screen.getByText("截图证据完整性")).toBeInTheDocument();
    expect(screen.getByText("是，需要继续处理")).toBeInTheDocument();
    expect(screen.getByText("仍缺少截图，暂不能作为高可信证据。")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: /差异记录/ }));
    expect(screen.getAllByText("人工修正差异").length).toBeGreaterThan(0);
    expect(screen.getByText("人工复核提交的受控结构化修正。")).toBeInTheDocument();
    expect(
      screen.getByText("人工修正价格带后，画像页和报告中的定位判断会同步刷新。")
    ).toBeInTheDocument();
  });

  it("hides prompt previews and redacts sensitive trace text", async () => {
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

    fireEvent.click(await screen.findByRole("tab", { name: /智能体过程/ }));
    fireEvent.click(screen.getByText("技术详情"));
    expect(screen.queryByText("采集智能体提示摘要")).not.toBeInTheDocument();
    expect(screen.queryByText("只展示脱敏后的提示摘要，默认折叠。")).not.toBeInTheDocument();
    expect(screen.queryByText("sk-test-secret-token")).not.toBeInTheDocument();
    expect(screen.queryByText("internal-secret")).not.toBeInTheDocument();
    expect(screen.queryByText("13800138000")).not.toBeInTheDocument();
    expect(screen.queryByText("acct-private-001")).not.toBeInTheDocument();
    expect(screen.queryByText("北京市朝阳区幸福路88号3单元501室")).not.toBeInTheDocument();
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
    expect(
      screen.getByRole("heading", { level: 4, name: "目标产品与核心竞品对比" })
    ).toBeInTheDocument();
    expect(screen.getAllByText("目标产品").length).toBeGreaterThan(0);
    expect(screen.getByText("最高威胁直接竞品")).toBeInTheDocument();
    expect(screen.getByText("最高威胁替代竞品")).toBeInTheDocument();
    expect(screen.getByText("核心直接竞品")).toBeInTheDocument();
    expect(screen.getByText("场景替代竞品")).toBeInTheDocument();
    expect(screen.getByText("价格低于核心竞品，形成进入门槛优势。")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "功能能力树" })).toBeInTheDocument();
    expect(screen.getByText(/这部分判断目标产品能否减少日常铲屎和清理负担/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "价格与证据" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "用户人群画像" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 4, name: "证据摘要" })).toBeInTheDocument();
    expect(screen.getByText("抖音商品快照")).toBeInTheDocument();
    expect(screen.getByText("中等可信度")).toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_profile_001/profile");
  });

  it("shows empty competitor slots when the profile comparison lacks competitors", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(productProfileResponse({ comparisonMode: "targetOnly" })),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/profile?task_id=task_profile_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("暂无可用于对比的直接竞品")).toBeInTheDocument();
    expect(screen.getByText("暂无可用于对比的替代竞品")).toBeInTheDocument();
    expect(screen.getAllByText("暂无可靠数据").length).toBeGreaterThan(0);
  });

  it("opens profile comparison evidence from target judgments", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(productProfileResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/profile?task_id=task_profile_001");

    render(<App apiClient={apiClient} />);

    fireEvent.click(
      await screen.findAllByRole("button", { name: "查看依据" }).then((buttons) => buttons[0])
    );

    expect(window.location.pathname).toBe("/trace");
    expect(window.location.search).toContain("task_id=task_profile_001");
    expect(window.location.search).toContain("tab=evidence");
    expect(window.location.search).toContain("evidence_id=ev_profile_price");
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

    const reviewPanel = await screen.findByLabelText("修正画像");
    const fieldSelect = within(reviewPanel).getByLabelText("画像字段");

    expect(within(reviewPanel).getByRole("heading", { name: "修正画像" })).toBeInTheDocument();
    expect(within(reviewPanel).getByText("标记不采纳")).toBeInTheDocument();
    expect(within(reviewPanel).getByText("补充证据备注")).toBeInTheDocument();
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

    const reviewPanel = await screen.findByLabelText("修正画像");
    fireEvent.change(within(reviewPanel).getByLabelText("修正后的值"), {
      target: { value: "人工确认品牌" }
    });
    fireEvent.change(within(reviewPanel).getByLabelText("修正原因"), {
      target: { value: "人工复核品牌字段后修正。" }
    });
    fireEvent.click(within(reviewPanel).getByRole("button", { name: "提交修正画像" }));

    expect(
      await within(reviewPanel).findByText("修正画像已提交，相关结果已刷新。")
    ).toBeInTheDocument();
    await waitFor(() => expect(apiClient.get).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getAllByText("人工确认品牌").length).toBeGreaterThan(0));
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
    expect(screen.getAllByText("核心直接竞品").length).toBeGreaterThan(0);
    expect(screen.getByTestId("competition-flow")).toBeInTheDocument();
    expect(screen.getByLabelText("竞争边详情")).toHaveTextContent("核心直接竞品 与目标产品的正面竞争");
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

  it("defaults the battlefield graph to backend-selected key relations", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(battlefieldResponse({ includeHiddenGraphRelation: true })),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/battlefield?task_id=task_battlefield_001");

    render(<App apiClient={apiClient} />);

    expect((await screen.findAllByText("核心直接竞品")).length).toBeGreaterThan(0);
    expect(screen.queryByText("预算型竞品")).not.toBeInTheDocument();
  });

  it("expands all battlefield relations when the relation toggle is enabled", async () => {
    const apiClient = createMockApiClient((path: string, options?: MockGetOptions) => {
      if (path.includes("/battlefield")) {
        return battlefieldResponse({
          includeExpandedRelation: Boolean(options?.query?.include_all_relations),
          includeHiddenGraphRelation: true
        });
      }

      return taskStatusResponse("task_battlefield_001", "completed");
    });
    window.history.pushState({}, "", "/battlefield?task_id=task_battlefield_001");

    render(<App apiClient={apiClient} />);

    const relationToggle = await screen.findByRole("checkbox", { name: /展开全部关系/ });
    fireEvent.click(relationToggle);

    expect((await screen.findAllByText("预算型竞品")).length).toBeGreaterThan(0);
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_battlefield_001/battlefield", {
      query: { include_all_relations: true }
    });
  });

  it("shows PM labels, threat, evidence credibility, and inclusion reason for key relations", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(battlefieldResponse({ includeHiddenGraphRelation: true })),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/battlefield?task_id=task_battlefield_001");

    render(<App apiClient={apiClient} />);

    const relationPanel = await screen.findByLabelText("关键竞争关系");
    expect(within(relationPanel).getByText("正面竞争")).toBeInTheDocument();
    expect(within(relationPanel).getByText("高威胁")).toBeInTheDocument();
    expect(within(relationPanel).getByText("可直接采纳")).toBeInTheDocument();
    expect(
      within(relationPanel).getByText("关系分最高，且与目标产品争夺同一多猫家庭需求。")
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

    expect(within(detailPanel).getByText("竞争边解释")).toBeInTheDocument();
    expect(within(detailPanel).getByText("需求替代性")).toBeInTheDocument();
    expect(within(detailPanel).getByText("结论与证据")).toBeInTheDocument();
    expect(within(detailPanel).getByText("证据 1")).toBeInTheDocument();
    expect(within(detailPanel).getByText("抖音商品快照")).toBeInTheDocument();
    expect(within(detailPanel).getByText("中等可信度")).toBeInTheDocument();
    expect(within(detailPanel).getByText("质检打回记录")).toBeInTheDocument();
    expect(within(detailPanel).getByText("1 条")).toBeInTheDocument();
  });

  it("renders the full four-part explanation for the selected edge", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(battlefieldResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/battlefield?task_id=task_battlefield_001");

    render(<App apiClient={apiClient} />);

    const explanation = await screen.findByLabelText("四段式竞争解释");

    expect(within(explanation).getByText("为什么是竞品")).toBeInTheDocument();
    expect(within(explanation).getByText("同一多猫家庭需求下形成正面竞争。")).toBeInTheDocument();
    expect(within(explanation).getByText("强在哪")).toBeInTheDocument();
    expect(within(explanation).getByText("证据完整且关系分高。")).toBeInTheDocument();
    expect(within(explanation).getByText("影响哪个决策阶段")).toBeInTheDocument();
    expect(within(explanation).getByText("主要影响用户能力理解和决策完成。")).toBeInTheDocument();
    expect(within(explanation).getByText("应对建议")).toBeInTheDocument();
    expect(within(explanation).getByText("分析建议")).toBeInTheDocument();
  });

  it("shows one-sentence explanations for all five score dimensions", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(battlefieldResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/battlefield?task_id=task_battlefield_001");

    render(<App apiClient={apiClient} />);

    const scoreBreakdown = await screen.findByLabelText("评分拆解");

    expect(within(scoreBreakdown).getByText("需求替代性")).toBeInTheDocument();
    expect(within(scoreBreakdown).getByText("场景匹配度")).toBeInTheDocument();
    expect(within(scoreBreakdown).getByText("购买路径影响")).toBeInTheDocument();
    expect(within(scoreBreakdown).getByText("证据支撑度")).toBeInTheDocument();
    expect(within(scoreBreakdown).getByText("市场信号强度")).toBeInTheDocument();
    expect(
      within(scoreBreakdown).getByText("看用户是否会把两款产品当成同一个需求下的二选一方案。")
    ).toBeInTheDocument();
    expect(
      within(scoreBreakdown).getByText("看当前判断背后有多少可追溯证据，证据是否完整、可信。")
    ).toBeInTheDocument();
  });

  it("opens evidence details from a four-part explanation basis entry", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(battlefieldResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/battlefield?task_id=task_battlefield_001");

    render(<App apiClient={apiClient} />);

    const explanation = await screen.findByLabelText("四段式竞争解释");
    fireEvent.click(within(explanation).getAllByRole("button", { name: "查看依据" })[0]);

    const basisPanel = screen.getByLabelText("解释依据详情");
    expect(within(basisPanel).getByText("为什么是竞品的依据")).toBeInTheDocument();
    expect(within(basisPanel).getByText("1 条结论")).toBeInTheDocument();
    expect(within(basisPanel).getAllByText("1 条证据").length).toBeGreaterThan(0);
  });

  it("uses natural Chinese copy in the default battlefield detail panel", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(battlefieldResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/battlefield?task_id=task_battlefield_001");

    render(<App apiClient={apiClient} />);

    const detailPanel = await screen.findByLabelText("竞争边详情");

    expect(within(detailPanel).getByText("关系详情")).toBeInTheDocument();
    expect(within(detailPanel).getByText("结论依据")).toBeInTheDocument();
    expect(within(detailPanel).getByText("证据卡片")).toBeInTheDocument();
    expect(within(detailPanel).getByText("质检打回记录")).toBeInTheDocument();
    expect(within(detailPanel).queryByText("Edge Detail")).not.toBeInTheDocument();
    expect(within(detailPanel).queryByText("Claims")).not.toBeInTheDocument();
    expect(within(detailPanel).queryByText("Evidence")).not.toBeInTheDocument();
  });

  it("renders the 2.0 report workbench with eight sections from the report API", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(reportResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    const reportSections = await screen.findByLabelText("报告章节");

    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "结论摘要" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "竞争格局判断" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "核心竞品拆解" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "用户决策链分析" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "目标产品机会与风险" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "产品策略建议" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "证据与质检附录" })
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByRole("heading", { level: 4, name: "分析流程与系统能力附录" })
    ).toBeInTheDocument();
    expect(within(reportSections).getAllByRole("article")).toHaveLength(8);
    expect(screen.getByLabelText("报告工作台工具栏")).toBeInTheDocument();
    expect(screen.getByText("核心竞争关系摘要")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "打印或另存 PDF" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "切换打印视图" })).toBeInTheDocument();
    expect(screen.queryByText(/Markdown/)).not.toBeInTheDocument();
    expect(screen.getByText("自动猫砂盆竞品分析报告")).toBeInTheDocument();
    expect(screen.getAllByText("证据材料").length).toBeGreaterThan(0);
    expect(within(reportSections).getByText(/当前主要压力来自 核心直接竞品/)).toBeInTheDocument();
    expect(within(reportSections).getByText(/重点切片：1500-2000 元价格带/)).toBeInTheDocument();
    expect(within(reportSections).getByText(/核心直接竞品：直接竞品/)).toBeInTheDocument();
    expect(within(reportSections).getByText(/在能力理解阶段，用户正在确认的问题是/)).toBeInTheDocument();
    expect(within(reportSections).queryByText(/基于本地快照规则评分/)).not.toBeInTheDocument();
    expect(within(reportSections).queryByText(/依据：/)).not.toBeInTheDocument();
    expect(within(reportSections).queryByText(/证据不足处保守处理/)).not.toBeInTheDocument();
    expect(apiClient.get).toHaveBeenCalledWith("/tasks/task_report_001/report");
  });

  it("keeps evidence and process drilldown entries on the report workbench", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(reportResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    const reportSections = await screen.findByLabelText("报告章节");
    fireEvent.click(within(reportSections).getAllByRole("button", { name: "查看依据" })[0]);

    expect(window.location.pathname).toBe("/trace");
    expect(window.location.search).toContain("task_id=task_report_001");
    expect(window.location.search).toContain("tab=evidence");
    expect(window.location.search).toContain("evidence_id=ev_report_price");
  });

  it("uses LLM-generated report paragraphs when they are available", async () => {
    const report = reportResponse();
    const [firstCoreItem] = report.core_competitor_analysis.items ?? [];
    expect(firstCoreItem).toBeDefined();
    firstCoreItem!.llm_paragraphs = {
      action: "下一步要把容量、除臭和维护成本讲清楚。",
      conclusion: "核心直接竞品是当前最需要优先回应的对象。",
      reason: "用户会把两者放在同一使用场景里比较。"
    };
    const apiClient = {
      get: vi.fn().mockResolvedValue(report),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    const reportSections = await screen.findByLabelText("报告章节");
    expect(
      within(reportSections).getByText("核心直接竞品是当前最需要优先回应的对象。")
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByText("用户会把两者放在同一使用场景里比较。")
    ).toBeInTheDocument();
    expect(
      within(reportSections).getByText("下一步要把容量、除臭和维护成本讲清楚。")
    ).toBeInTheDocument();
  });

  it("uses expanded LLM analysis paragraphs before short report paragraphs", async () => {
    const report = reportResponse();
    const [firstCoreItem] = report.core_competitor_analysis.items ?? [];
    expect(firstCoreItem).toBeDefined();
    firstCoreItem!.llm_paragraphs = {
      action: "短行动建议不应优先展示。",
      conclusion: "短结论不应优先展示。",
      reason: "短原因不应优先展示。"
    };
    firstCoreItem!.llm_expanded_analysis = [
      "扩增后的分析会先解释用户为什么把目标产品和核心竞品放在同一组候选中比较，并明确当前证据只能支持围绕清理负担、除臭和维护成本展开判断。",
      "扩增后的行动建议会把内部评分转化成用户能理解的购买理由，同时保留证据不足处需要复核的边界。"
    ];
    const apiClient = {
      get: vi.fn().mockResolvedValue(report),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    const reportSections = await screen.findByLabelText("报告章节");
    expect(
      within(reportSections).getByText(/扩增后的分析会先解释用户为什么/)
    ).toBeInTheDocument();
    expect(within(reportSections).queryByText("短结论不应优先展示。")).not.toBeInTheDocument();
  });

  it("reuses the generated report when returning to the report page", async () => {
    let reportCalls = 0;
    const apiClient = createMockApiClient((path: string) => {
      if (path.endsWith("/report")) {
        reportCalls += 1;
        return reportResponse();
      }
      if (path.endsWith("/overview")) {
        return overviewResponse({ taskId: "task_report_001" });
      }
      return taskStatusResponse("task_report_001", "completed");
    });
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByLabelText("报告章节")).toBeInTheDocument();
    expect(reportCalls).toBe(1);

    window.history.pushState({}, "", "/overview?task_id=task_report_001");
    fireEvent(window, new Event("popstate"));
    expect(
      await screen.findByRole("heading", { level: 2, name: "竞争态势总览" })
    ).toBeInTheDocument();

    window.history.pushState({}, "", "/report?task_id=task_report_001");
    fireEvent(window, new Event("popstate"));

    expect(await screen.findByLabelText("报告章节")).toBeInTheDocument();
    expect(reportCalls).toBe(1);
  });

  it("redacts sensitive patterns before rendering report fields", async () => {
    const report = reportResponse();
    report.product_strategy_recommendations.items = [
      {
        priority: "p1_current_iteration",
        recommendation:
          "api_key=sk-test-secret-token token=internal-secret 手机 13800138000 " +
          "account_id=acct-private-001 地址=北京市朝阳区幸福路88号3单元501室 Bearer should-not-leak"
      }
    ];
    const apiClient = {
      get: vi.fn().mockResolvedValue(report),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    await screen.findByLabelText("报告章节");

    expect(screen.queryByText(/sk-test-secret-token/i)).not.toBeInTheDocument();
    expect(screen.queryByText("internal-secret")).not.toBeInTheDocument();
    expect(screen.queryByText("13800138000")).not.toBeInTheDocument();
    expect(screen.queryByText("acct-private-001")).not.toBeInTheDocument();
    expect(screen.queryByText("北京市朝阳区幸福路88号3单元501室")).not.toBeInTheDocument();
    expect(screen.queryByText(/api[_-]?key/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/\[已脱敏\]/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/凭据=\[已脱敏\]/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/地址=\[已脱敏\]/).length).toBeGreaterThan(0);
  });

  it("switches the report page into print view without hiding report sections", async () => {
    const apiClient = {
      get: vi.fn().mockResolvedValue(reportResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("自动猫砂盆竞品分析报告")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "切换打印视图" }));

    expect(screen.getByRole("button", { name: "返回工作台视图" })).toBeInTheDocument();
    expect(screen.getByLabelText("静态图谱摘要")).toBeInTheDocument();
    expect(screen.getByLabelText("报告章节")).toBeInTheDocument();
    expect(document.body).toHaveAttribute("data-report-view", "print");
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

    expect(await screen.findByText("报告正在生成")).toBeInTheDocument();
    expect(screen.getByText(/当前状态：报告生成中/)).toBeInTheDocument();
    expect(screen.queryByLabelText("报告章节")).not.toBeInTheDocument();
  });

  it("automatically checks again when the report is still being generated", async () => {
    let reportCalls = 0;
    const apiClient = createMockApiClient((path: string) => {
        if (path.endsWith("/report")) {
          reportCalls += 1;
          if (reportCalls === 1) {
            return Promise.reject(
              new ApiClientError({
                code: "REPORT_NOT_READY",
                details: { status: "writing", task_id: "task_report_waiting" },
                message: "Report is only available after the task is completed.",
                status: 409,
                traceId: "trace_report_waiting"
              })
            );
          }
          return reportResponse();
        }
        return taskStatusResponse("task_report_waiting", "writing");
      });
    window.history.pushState({}, "", "/report?task_id=task_report_waiting");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("报告正在生成")).toBeInTheDocument();

    await waitFor(() => expect(reportCalls).toBeGreaterThanOrEqual(2), { timeout: 3500 });
    expect(await screen.findByLabelText("报告章节")).toBeInTheDocument();
  }, 8000);

  it("downloads word report from the report page", async () => {
    const apiClient = {
      download: vi.fn().mockResolvedValue(new Blob(["docx"])),
      get: vi.fn().mockResolvedValueOnce(reportResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("自动猫砂盆竞品分析报告")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "下载 Word 报告" }));

    expect(await screen.findByText(/Word 报告已下载/)).toBeInTheDocument();
    expect(apiClient.download).toHaveBeenCalledWith("/tasks/task_report_001/report/docx");
  });

  it("shows word export errors without hiding the web report", async () => {
    const apiClient = {
      download: vi.fn().mockRejectedValue(
        new ApiClientError({
          code: "WORD_REPORT_EXPORT_FAILED",
          message: "Word export failed",
          status: 500,
          traceId: "trace_word_failed"
        })
      ),
      get: vi.fn().mockResolvedValueOnce(reportResponse()),
      post: vi.fn()
    };
    window.history.pushState({}, "", "/report?task_id=task_report_001");

    render(<App apiClient={apiClient} />);

    expect(await screen.findByText("自动猫砂盆竞品分析报告")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "下载 Word 报告" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Word export failed");
    expect(screen.getByLabelText("报告章节")).toBeInTheDocument();
    expect(screen.getByText("错误码：WORD_REPORT_EXPORT_FAILED")).toBeInTheDocument();
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

function overviewResponse(
  options: {
    actionTitle?: string;
    competitorName?: string;
    judgmentContent?: string;
    opportunityTitle?: string;
    primaryImagePath?: string | null;
    riskTitle?: string;
    selectedSlice?: OverviewData["current_slice"];
    taskId?: string;
  } = {}
): OverviewData {
  const taskId = options.taskId ?? "task_overview_001";
  const competitorName = options.competitorName ?? "核心直接竞品";
  const selectedSlice = options.selectedSlice ?? {
    persona: null,
    price_band: null,
    scenario: null
  };
  const primaryImagePath =
    "primaryImagePath" in options ? options.primaryImagePath : "/assets/raw/sku_01/main.png";

  return {
    action_recommendations: [
      {
        action_id: "action_competitor_expression",
        description: "把核心竞品的除臭与维护成本证据放到首屏对比，减少用户跳出。",
        drilldown_refs: [],
        evidence_ids: ["ev_overview_competitor"],
        expected_impact: "提升用户对差异点的理解效率",
        missing_reference_reason: null,
        priority: "p1_current_iteration",
        responsibility_type: "content_expression",
        risk_flags: [],
        title: options.actionTitle ?? "优先补强关键竞品对比表达",
        trace_refs: ["analysis_agent:edge_direct_001"]
      }
    ],
    analysis_scope: {
      access_time_range: "2026-05-23 至 2026-05-27",
      category: "smart_pet_hardware",
      data_source_label: "本地快照",
      data_source_mode: "demo_snapshot",
      evidence_count: 6,
      evidence_ids: ["ev_overview_competitor", "ev_overview_risk"],
      missing_fields: [],
      platform_label: "抖音",
      platforms: ["douyin"],
      product_count: 3,
      scope_notice: "本报告基于用户提供的脱敏 SKU 快照，不代表实时全网数据。",
      sku_count: 3,
      snapshot_date: "2026-05-27",
      snapshot_version: "demo_v2",
      source_description: "用户提供的脱敏 SKU 快照",
      subcategory: "automatic_litter_box",
      task_id: taskId
    },
    current_slice: selectedSlice,
    decision_usability: {
      evidence_ids: ["ev_overview_competitor"],
      label: "可用于初步决策",
      reason: "核心判断已有可追溯证据支撑",
      risk_flags: [],
      trace_refs: ["qa_agent:passed"],
      value: "ready_for_initial_decision"
    },
    drilldown_refs: [],
    generated_at: "2026-05-27T08:05:00Z",
    judgment_strength: {
      evidence_ids: ["ev_overview_competitor"],
      label: "明确判断",
      reason: "最高分关系与行动建议方向一致",
      risk_flags: [],
      trace_refs: ["analysis_agent:edge_direct_001"],
      value: "clear_judgment"
    },
    key_competitors: [
      {
        brand: "竞品品牌",
        competitor_type: "highest_threat_direct_competitor",
        drilldown_refs: [
          {
            label: "查看竞争关系",
            reference_type: "battlefield",
            route: `/tasks/${taskId}/battlefield?edge_id=edge_direct_001`,
            target_id: "edge_direct_001"
          }
        ],
        evidence_credibility: {
          evidence_ids: ["ev_overview_competitor"],
          label: "可直接采纳",
          reason: "证据来自本地脱敏 SKU 快照并有访问时间",
          risk_flags: [],
          trace_refs: ["qa_agent:passed"],
          value: "directly_adoptable"
        },
        evidence_ids: ["ev_overview_competitor"],
        inclusion_reason: "关系分最高，且与目标产品争夺同一多猫家庭需求。",
        missing_reference_reason: null,
        primary_image_path: primaryImagePath,
        product_id: "prod_competitor",
        product_name: competitorName,
        relationship_label: "head_to_head",
        risk_flags: [],
        sku_id: "sku_01",
        threat_level: "high_threat",
        trace_refs: ["analysis_agent:edge_direct_001"]
      }
    ],
    metadata: {
      evidence_count: 6
    },
    one_sentence_judgment: {
      content: options.judgmentContent ?? "核心直接竞品正在争夺同一多猫家庭需求。",
      drilldown_refs: [],
      evidence_ids: ["ev_overview_competitor"],
      missing_reference_reason: null,
      risk_flags: [],
      trace_refs: ["analysis_agent:edge_direct_001"]
    },
    opportunities: [
      {
        description: "把当前切片下的场景痛点转成更明确的对比表达。",
        drilldown_refs: [],
        evidence_ids: ["ev_overview_competitor"],
        finding_id: "opp_overview_content",
        finding_type: "expression_opportunity",
        missing_reference_reason: null,
        risk_flags: [],
        title: options.opportunityTitle ?? "强化关键卖点证据表达",
        trace_refs: ["analysis_agent:edge_direct_001"]
      }
    ],
    overview_id: `overview_${taskId}`,
    risk_points: [
      {
        description: "部分截图仍需关注访问时间，使用时应保留证据链说明。",
        drilldown_refs: [],
        evidence_ids: ["ev_overview_risk"],
        finding_id: "risk_overview_access_time",
        finding_type: "evidence_risk",
        missing_reference_reason: null,
        risk_flags: ["missing_access_time"],
        title: options.riskTitle ?? "证据风险提示",
        trace_refs: ["qa_agent:review"]
      }
    ],
    status_reasons: ["证据链已覆盖首要竞品关系"],
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
    extraDiffs?: TraceData["diffs"];
    extraQualityRecords?: TraceData["quality_records"];
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
        output_summary: "生成网页报告与 Word 导出元信息。",
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
        business_impact: "补齐访问时间后，相关结论可以进入可复核状态。",
        diff_id: "collection_repair_diff_001",
        metadata: {
          target_evidence_id: "ev_trace_price"
        },
        revision_message_ids: ["msg_trace_revision"],
        source: "collection_agent_repair",
        status: "repaired",
        target_id: "ev_trace_price_repaired",
        target_type: "evidence"
      },
      ...(overrides.extraDiffs ?? [])
    ],
    evidence_chains: [
      {
        chain_id: "chain_trace_price",
        claim_content: "核心直接竞品在当前切片下形成价格与除臭竞争。",
        claim_id: "claim_trace_price",
        claim_status: "accepted",
        confidence: 0.82,
        evidence_items: [
          {
            access_time: "2026-05-23T16:00:00Z",
            access_time_status: "available",
            confidence_level: "medium",
            content_summary:
              "商品页快照显示竞品价格与除臭卖点；评论洞察尚待后续结构化抽取，[REDACTED]。",
            evidence_id: "ev_trace_price",
            limitations: "QA 打回后补齐字段：source.access_time。",
            product_id: "prod_competitor",
            risk_flags: [],
            source_type: "douyin_sku_snapshot",
            source_url: "https://example.com/competitor"
          }
        ],
        is_inference: true,
        report_section_ids: ["conclusion_summary"],
        risk_flags: [],
        trace_refs: ["analysis_agent:edge_trace_price"]
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
    quality_records: [
      {
        action_result: "访问时间已补齐，结论可进入复核。",
        check_item: "价格证据完整性",
        evidence_ids: ["ev_trace_price"],
        issue_code: "TIMELY_EVIDENCE_MISSING_ACCESS_TIME",
        issue_summary: "价格证据缺少访问时间。",
        needs_attention: false,
        quality_record_id: "quality_trace_price",
        related_claim_ids: ["claim_trace_price"],
        required_action: "补齐访问时间。",
        resolved: true,
        review_task_id: "review_trace_price",
        severity: "warning",
        status: "resolved",
        target_agent: "collection_agent",
        target_id: "ev_trace_price",
        target_type: "evidence"
      },
      ...(overrides.extraQualityRecords ?? [])
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
    comparisonMode?: "full" | "targetOnly";
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
    horizontal_comparison: {
      compared_products: [
        {
          brand,
          primary_image_path: null,
          product_id: "prod_target",
          product_name: "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
          product_url: "https://v.douyin.com/mv8e4KRLLwc/",
          slot: "target"
        },
        ...(options.comparisonMode === "targetOnly"
          ? []
          : [
              {
                brand: "竞品品牌",
                primary_image_path: null,
                product_id: "prod_competitor",
                product_name: "核心直接竞品",
                product_url: "https://example.com/direct",
                slot: "highest_threat_direct_competitor" as const
              },
              {
                brand: "替代品牌",
                primary_image_path: null,
                product_id: "prod_alternative",
                product_name: "场景替代竞品",
                product_url: "https://example.com/alternative",
                slot: "highest_threat_alternative" as const
              }
            ])
      ],
      dimensions: [
        {
          dimension_key: "price_band",
          dimension_label: "价格带",
          evidence_ids: ["ev_profile_price"],
          risk_flags: [],
          status_reason: "价格低于核心竞品，形成进入门槛优势。",
          target_status: "advantage",
          trace_refs: ["profile:task_profile_001:price_band"],
          values: [
            {
              evidence_ids: ["ev_profile_price"],
              product_id: "prod_target",
              value: "1500-2000"
            },
            ...(options.comparisonMode === "targetOnly"
              ? []
              : [
                  {
                    evidence_ids: ["ev_direct_price"],
                    product_id: "prod_competitor",
                    value: "2000-3000"
                  },
                  {
                    evidence_ids: ["ev_alternative_price"],
                    product_id: "prod_alternative",
                    value: "1500-2000"
                  }
                ])
          ]
        },
        {
          dimension_key: "core_selling_points",
          dimension_label: "核心卖点",
          evidence_ids: ["ev_profile_price"],
          risk_flags: [],
          status_reason: "目标产品与核心竞品均强调清洁和除臭，暂按持平处理。",
          target_status: "parity",
          trace_refs: ["profile:task_profile_001:core_selling_points"],
          values: [
            {
              evidence_ids: ["ev_profile_price"],
              product_id: "prod_target",
              value: "自动铲砂、封闭仓体、应用提醒"
            },
            ...(options.comparisonMode === "targetOnly"
              ? []
              : [
                  {
                    evidence_ids: ["ev_direct_feature"],
                    product_id: "prod_competitor",
                    value: "除臭模块、低维护套装"
                  },
                  {
                    evidence_ids: ["ev_alternative_feature"],
                    product_id: "prod_alternative",
                    value: "低价套装、基础自动清理"
                  }
                ])
          ]
        },
        {
          dimension_key: "persona",
          dimension_label: "主要人群",
          evidence_ids: ["ev_profile_price"],
          risk_flags: [],
          status_reason: "三类产品都覆盖多猫家庭，需要结合场景差异继续判断。",
          target_status: "parity",
          trace_refs: ["profile:task_profile_001:persona"],
          values: [
            {
              evidence_ids: ["ev_profile_price"],
              product_id: "prod_target",
              value: "多猫家庭"
            },
            ...(options.comparisonMode === "targetOnly"
              ? []
              : [
                  {
                    evidence_ids: ["ev_direct_persona"],
                    product_id: "prod_competitor",
                    value: "多猫家庭、重除臭用户"
                  },
                  {
                    evidence_ids: ["ev_alternative_persona"],
                    product_id: "prod_alternative",
                    value: "预算敏感家庭"
                  }
                ])
          ]
        },
        {
          dimension_key: "scenario",
          dimension_label: "使用场景",
          evidence_ids: ["ev_profile_price"],
          risk_flags: [],
          status_reason: "目标产品的小户型客厅场景证据较完整。",
          target_status: "advantage",
          trace_refs: ["profile:task_profile_001:scenario"],
          values: [
            {
              evidence_ids: ["ev_profile_price"],
              product_id: "prod_target",
              value: "小户型客厅"
            },
            ...(options.comparisonMode === "targetOnly"
              ? []
              : [
                  {
                    evidence_ids: ["ev_direct_scenario"],
                    product_id: "prod_competitor",
                    value: "重除臭"
                  },
                  {
                    evidence_ids: ["ev_alternative_scenario"],
                    product_id: "prod_alternative",
                    value: "低维护"
                  }
                ])
          ]
        },
        {
          dimension_key: "evidence_credibility",
          dimension_label: "证据可信状态",
          evidence_ids: ["ev_profile_price"],
          risk_flags: pricingRiskFlags,
          status_reason: pricingAccessTime
            ? "目标产品证据有访问时间，竞品证据可追溯。"
            : "目标产品价格证据缺少访问时间。",
          target_status: pricingAccessTime ? "parity" : "insufficient_evidence",
          trace_refs: ["profile:task_profile_001:evidence_credibility"],
          values: [
            {
              evidence_ids: ["ev_profile_price"],
              product_id: "prod_target",
              value: pricingAccessTime ? "谨慎参考" : "证据不足"
            },
            ...(options.comparisonMode === "targetOnly"
              ? []
              : [
                  {
                    evidence_ids: ["ev_direct_price"],
                    product_id: "prod_competitor",
                    value: "可直接采纳"
                  },
                  {
                    evidence_ids: ["ev_alternative_price"],
                    product_id: "prod_alternative",
                    value: "谨慎参考"
                  }
                ])
          ]
        }
      ],
      target_product_id: "prod_target"
    },
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
      primary_image_status: "missing",
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
    includeHiddenGraphRelation?: boolean;
    includeExpandedRelation?: boolean;
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
      },
      ...(options.includeExpandedRelation || options.includeHiddenGraphRelation
        ? [
            {
              access_time: "2026-05-27T08:01:00Z",
              access_time_status: "available" as const,
              confidence_level: "medium" as const,
              content_summary: "预算型竞品快照显示低维护套装形成价格拦截。",
              evidence_id: "ev_edge_budget",
              limitations: "来源为本地快照，非实时页面。",
              product_id: "prod_budget_competitor",
              risk_flags: [],
              screenshot_path: "data/raw/sku_03/price.png",
              source_type: "douyin_sku_snapshot" as const,
              source_url: "https://example.com/budget"
            }
          ]
        : [])
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
      },
      ...(options.includeExpandedRelation || options.includeHiddenGraphRelation
        ? [
            {
              claim_ids: ["claim_edge_budget"],
              claim_refs: [
                {
                  claim_id: "claim_edge_budget",
                  confidence: 0.68,
                  content: "预算型竞品在低维护场景下形成价格拦截。",
                  evidence_ids: ["ev_edge_budget"],
                  is_inference: true,
                  risk_flags: [],
                  status: "accepted"
                }
              ],
              competition_type: "channel",
              competitor_product_id: "prod_budget_competitor",
              decision_stages: ["interest_formation"],
              edge_id: "edge_budget_002",
              edge_score: 0.62,
              evidence_ids: ["ev_edge_budget"],
              human_adjusted: false,
              risk_flags: [],
              risk_status: "normal",
              score_breakdown: {
                context_match: 0.64,
                decision_stage_impact: 0.58,
                demand_substitutability: 0.7,
                evidence_confidence: 0.6,
                market_signal_strength: 0.56
              },
              score_explanations: ["预算型竞品在低维护切片中提供价格拦截参考。"],
              slice: {
                persona: "预算敏感",
                price_band: "2000-3000",
                scenario: "低维护"
              },
              source: "prod_target",
              target: "prod_budget_competitor",
              target_product_id: "prod_target"
            } as BattlefieldGraphEdge
          ]
        : [])
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
      },
      ...(options.includeExpandedRelation || options.includeHiddenGraphRelation
        ? [
            {
              brand: "预算品牌",
              evidence_ids: ["ev_edge_budget"],
              label: "预算型竞品",
              node_id: "prod_budget_competitor",
              product_id: "prod_budget_competitor",
              product_url: "https://example.com/budget",
              risk_flags: [],
              role: "channel_alternative" as const,
              shop_name: "预算旗舰店"
            }
          ]
        : [])
    ],
    key_relations: [
      {
        action_suggestion: "优先解释核心直接竞品的除臭与维护差异。",
        claim_ids: ["claim_edge_direct"],
        competitor_brand: "竞品品牌",
        competitor_primary_image_path: null,
        competitor_product_id: "prod_competitor",
        competitor_product_name: "核心直接竞品",
        edge_id: "edge_direct_001",
        evidence_credibility: {
          evidence_ids: ["ev_edge_price"],
          label: "可直接采纳",
          reason: "证据具备来源和访问时间。",
          risk_flags: [],
          trace_refs: ["qa_agent:passed"],
          value: "directly_adoptable"
        },
        evidence_ids: ["ev_edge_price"],
        four_part_explanation: {
          decision_stage_impact: {
            claim_ids: ["claim_edge_direct"],
            evidence_ids: ["ev_edge_price"],
            is_analysis_suggestion: false,
            risk_flags: [],
            text: "主要影响用户能力理解和决策完成。",
            trace_refs: ["analysis_agent:edge_direct_001"]
          },
          response_suggestion: {
            claim_ids: ["claim_edge_direct"],
            evidence_ids: ["ev_edge_price"],
            is_analysis_suggestion: true,
            risk_flags: [],
            text: "优先补强除臭和维护成本对比表达。",
            trace_refs: ["analysis_agent:edge_direct_001"]
          },
          strength: {
            claim_ids: ["claim_edge_direct"],
            evidence_ids: ["ev_edge_price"],
            is_analysis_suggestion: false,
            risk_flags: [],
            text: "证据完整且关系分高。",
            trace_refs: ["analysis_agent:edge_direct_001"]
          },
          why_competitor: {
            claim_ids: ["claim_edge_direct"],
            evidence_ids: ["ev_edge_price"],
            is_analysis_suggestion: false,
            risk_flags: [],
            text: "同一多猫家庭需求下形成正面竞争。",
            trace_refs: ["analysis_agent:edge_direct_001"]
          }
        },
        inclusion_reason: "关系分最高，且与目标产品争夺同一多猫家庭需求。",
        is_default_visible: true,
        relationship_label: "head_to_head",
        relationship_label_explanation: "正面争夺同一需求和同一决策场景。",
        risk_flags: [],
        target_product_id: "prod_target",
        threat_level: "high_threat",
        trace_refs: ["analysis_agent:edge_direct_001"]
      },
      ...(options.includeExpandedRelation
        ? [
            {
              action_suggestion: "作为扩展关系保留，用于补充低维护切片判断。",
              claim_ids: ["claim_edge_budget"],
              competitor_brand: "预算品牌",
              competitor_primary_image_path: null,
              competitor_product_id: "prod_budget_competitor",
              competitor_product_name: "预算型竞品",
              edge_id: "edge_budget_002",
              evidence_credibility: {
                evidence_ids: ["ev_edge_budget"],
                label: "谨慎参考",
                reason: "证据可追溯，但仍需后续复核。",
                risk_flags: [],
                trace_refs: ["qa_agent:passed"],
                value: "cautious_reference"
              },
              evidence_ids: ["ev_edge_budget"],
              four_part_explanation: {
                decision_stage_impact: {
                  claim_ids: ["claim_edge_budget"],
                  evidence_ids: ["ev_edge_budget"],
                  is_analysis_suggestion: false,
                  risk_flags: [],
                  text: "主要影响兴趣形成。",
                  trace_refs: ["analysis_agent:edge_budget_002"]
                },
                response_suggestion: {
                  claim_ids: ["claim_edge_budget"],
                  evidence_ids: ["ev_edge_budget"],
                  is_analysis_suggestion: true,
                  risk_flags: [],
                  text: "后续补充低维护成本证据。",
                  trace_refs: ["analysis_agent:edge_budget_002"]
                },
                strength: {
                  claim_ids: ["claim_edge_budget"],
                  evidence_ids: ["ev_edge_budget"],
                  is_analysis_suggestion: false,
                  risk_flags: [],
                  text: "价格拦截信号中等。",
                  trace_refs: ["analysis_agent:edge_budget_002"]
                },
                why_competitor: {
                  claim_ids: ["claim_edge_budget"],
                  evidence_ids: ["ev_edge_budget"],
                  is_analysis_suggestion: false,
                  risk_flags: [],
                  text: "在预算敏感人群中形成渠道替代。",
                  trace_refs: ["analysis_agent:edge_budget_002"]
                }
              },
              inclusion_reason: "作为扩展关系，补充预算敏感人群下的低维护拦截。",
              is_default_visible: false,
              relationship_label: "low_price_interception",
              relationship_label_explanation: "通过价格或套装形成拦截。",
              risk_flags: [],
              target_product_id: "prod_target",
              threat_level: "medium_threat",
              trace_refs: ["analysis_agent:edge_budget_002"]
            } as BattlefieldKeyRelation
          ]
        : [])
    ],
    relation_filter: {
      can_expand_all: !options.includeExpandedRelation,
      default_limit: 5,
      include_all_relations: Boolean(options.includeExpandedRelation),
      total_relation_count: 2,
      visible_relation_count: options.includeExpandedRelation ? 2 : 1
    },
    metadata: {
      edge_count: options.includeExpandedRelation || options.includeHiddenGraphRelation ? 2 : 1,
      node_count: options.includeExpandedRelation || options.includeHiddenGraphRelation ? 3 : 2
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
      },
      ...(options.includeExpandedRelation || options.includeHiddenGraphRelation
        ? [
            {
              claim_ids: ["claim_edge_budget"],
              edge_id: "edge_budget_002",
              edge_score: 0.62,
              evidence_ids: ["ev_edge_budget"],
              explanations: ["预算型竞品在低维护切片中提供价格拦截参考。"],
              score_breakdown: {
                context_match: 0.64,
                decision_stage_impact: 0.58,
                demand_substitutability: 0.7,
                evidence_confidence: 0.6,
                market_signal_strength: 0.56
              }
            }
          ]
        : [])
    ],
    selected_slice: selectedSlice,
    task_id: "task_battlefield_001"
  };
}

function reportResponse(): ReportData {
  const coreCompetitorAnalysis: ReportSection = {
    claim_ids: ["claim_report_direct"],
    evidence_ids: ["ev_report_price"],
    items: [
      {
        claims: [
          {
            claim_id: "claim_report_direct",
            confidence: 0.82,
            content:
              "基于本地快照规则评分，核心直接竞品在 1500-2000/多猫家庭/重除臭切片下与目标产品存在 direct 竞争关系；该判断为推断，评分 0.86。",
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
    section_id: "core_competitor_analysis",
    summary: "按竞争评分排序展示核心竞品关系，结论均保留 Claim 与 Evidence 索引。",
    title: "核心竞品拆解"
  };

  return {
    analysis_process_appendix: reportSection(
      "analysis_process_appendix",
      "分析流程与系统能力附录",
      [
        {
          agent_count: 4,
          appendix_type: "workflow",
          revision_message_count: 1
        }
      ]
    ),
    competitive_landscape_judgment: reportSection(
      "competitive_landscape_judgment",
      "竞争格局判断",
      [
        {
          claim_ids: ["claim_report_direct"],
          edge_ids: ["edge_report_direct"],
          evidence_ids: ["ev_report_price"],
          persona: "多猫家庭",
          price_band: "1500-2000",
          scenario: "重除臭",
          top_edge_score: 0.86
        }
      ]
    ),
    competitor_findings: {
      ...coreCompetitorAnalysis,
      section_id: "competitor_findings",
      title: "竞品发现"
    },
    conclusion_summary: reportSection("conclusion_summary", "结论摘要", [
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
    core_competitor_analysis: coreCompetitorAnalysis,
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
    evidence_quality_appendix: reportSection("evidence_quality_appendix", "证据与质检附录", [
      {
        analysis_recompute: { status: "completed" },
        collection_repair: { repaired_evidence_ids: ["ev_report_price"] },
        qa_agent: { qa_status: "passed" },
        review_task_count: 1,
        revision_message_count: 1,
        risk_claims: []
      }
    ]),
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
    product_strategy_recommendations: reportSection(
      "product_strategy_recommendations",
      "产品策略建议",
      [
        {
          basis_edge_id: "edge_report_direct",
          claim_ids: ["claim_report_direct"],
          evidence_ids: ["ev_report_price"],
          is_inference: true,
          priority: "p1_current_iteration",
          recommendation: "优先解释核心直接竞品在当前切片下的竞争关系。",
          responsibility_type: "content_expression"
        }
      ]
    ),
    report_id: "report_task_report_001_001",
    section_order: [
      "conclusion_summary",
      "competitive_landscape_judgment",
      "core_competitor_analysis",
      "user_decision_chain_analysis",
      "target_opportunities_and_risks",
      "product_strategy_recommendations",
      "evidence_quality_appendix",
      "analysis_process_appendix"
    ],
    target_opportunities_and_risks: reportSection(
      "target_opportunities_and_risks",
      "目标产品机会与风险",
      [
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
      ]
    ),
    task_id: "task_report_001",
    user_decision_chain_analysis: reportSection("user_decision_chain_analysis", "用户决策链分析", [
      {
        claim_ids: ["claim_report_direct"],
        decision_stage: "capability_understanding",
        edge_ids: ["edge_report_direct"],
        evidence_ids: ["ev_report_price"]
      }
    ]),
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
  items: NonNullable<ReportSection["items"]>
): ReportSection {
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
