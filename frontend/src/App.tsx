import "@xyflow/react/dist/style.css";
import "./App.css";

import { QueryClient, QueryClientProvider, useMutation, useQuery } from "@tanstack/react-query";
import {
  Background,
  Controls,
  MarkerType,
  ReactFlow,
  type Edge as FlowEdge,
  type Node as FlowNode
} from "@xyflow/react";
import { type FormEvent, type ReactNode, useEffect, useMemo, useRef, useState } from "react";

import {
  RequestStateMessage,
  createApiClient,
  createErrorState,
  createIdleState,
  createLoadingState,
  createSuccessState
} from "./api";
import type { ApiClient, ApiRequestState, components } from "./api";

type AppRoute = {
  path: string;
  label: string;
  title: string;
  eyebrow: string;
  summary: string;
  sections: string[];
};

type TaskCreateRequest = components["schemas"]["TaskCreateRequest"];
type TaskCreateResponse = components["schemas"]["TaskCreateResponse"];
type ProductProfileData = components["schemas"]["ProductProfileData"];
type BattlefieldData = components["schemas"]["BattlefieldData"];
type BattlefieldEvidenceCard = components["schemas"]["BattlefieldEvidenceCard"];
type BattlefieldGraphEdge = components["schemas"]["BattlefieldGraphEdge"];
type BattlefieldGraphNode = components["schemas"]["BattlefieldGraphNode"];
type BattlefieldSliceSelection = components["schemas"]["BattlefieldSliceSelection"];
type HumanFeedbackCreateRequest = components["schemas"]["HumanFeedbackCreateRequest"];
type HumanFeedbackCreateResponse = components["schemas"]["HumanFeedbackCreateResponse"];
type MarkdownReport = components["schemas"]["MarkdownReport"];
type ReportData = components["schemas"]["ReportData"];
type ReportSection = components["schemas"]["ReportSection"];
type AgentMessage = components["schemas"]["AgentMessage"];
type AgentRunLog = components["schemas"]["AgentRunLog"];
type ReviewTask = components["schemas"]["ReviewTask"];
type TaskStatus = components["schemas"]["TaskStatus"];
type TaskStatusResponse = components["schemas"]["TaskStatusResponse"];
type TokenUsageLog = components["schemas"]["TokenUsageLog"];
type ToolCallLog = components["schemas"]["ToolCallLog"];
type TraceDagEdge = components["schemas"]["TraceDagEdge"];
type TraceDagNode = components["schemas"]["TraceDagNode"];
type TraceData = components["schemas"]["TraceData"];
type TraceDiff = components["schemas"]["TraceDiff"];
type TracePromptPreview = components["schemas"]["TracePromptPreview"];
type DataSourceMode = components["schemas"]["DataSourceMode"];
type TaskApiClient = Pick<ApiClient, "get" | "post">;

type TaskInputForm = {
  category: string;
  data_source_mode: DataSourceMode;
  research_text: string;
  subcategory: string;
  target_product_name: string;
  target_product_url: string;
};

type FieldErrors = Partial<Record<keyof TaskInputForm, string>>;

const DEFAULT_TASK_FORM: TaskInputForm = {
  category: "smart_pet_hardware",
  data_source_mode: "demo_snapshot",
  research_text: "",
  subcategory: "automatic_litter_box",
  target_product_name: "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
  target_product_url: "https://v.douyin.com/mv8e4KRLLwc/"
};

const CATEGORY_OPTIONS = [{ label: "智能宠物硬件", value: "smart_pet_hardware" }];
const SUBCATEGORY_OPTIONS = [{ label: "自动猫砂盆", value: "automatic_litter_box" }];
const TASK_STATUS_REFETCH_INTERVAL_MS = 1000;
const RUNNING_TASK_STATUSES = new Set<TaskStatus>([
  "created",
  "collecting",
  "analyzing",
  "reviewing",
  "writing"
]);
const FAILED_TASK_STATUSES = new Set<TaskStatus>(["failed", "partial_failed"]);
const EMPTY_VALUE_TEXT = "暂无可靠数据";
const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  analyzing: "分析中",
  collecting: "采集中",
  completed: "已完成",
  created: "已创建",
  failed: "失败",
  human_reviewing: "人工复核中",
  partial_failed: "部分失败",
  reviewing: "质检中",
  writing: "报告生成中"
};
const RISK_FLAG_LABELS: Record<string, string> = {
  conflicting_analysis: "分析冲突",
  missing_access_time: "缺少访问时间",
  missing_evidence: "缺少证据",
  missing_screenshot: "缺少截图",
  sensitive_claim: "敏感表达",
  single_review_overgeneralized: "单条评论过度概括",
  unreliable_data: "数据不可靠",
  unsupported_inference: "推断待补证"
};
const COMPETITION_TYPE_LABELS: Record<string, string> = {
  alternative: "需求替代",
  channel: "渠道替代",
  content_cooccurrence: "内容共现",
  direct: "直接竞品",
  direct_competitor: "直接竞品",
  channel_alternative: "渠道替代",
  reference: "参考对象"
};
const DECISION_STAGE_LABELS: Record<string, string> = {
  capability_understanding: "能力理解",
  decision_completion: "决策完成",
  information_reach: "信息触达",
  interest_formation: "兴趣形成",
  trust_building: "信任建立"
};
const SCORE_BREAKDOWN_LABELS: Record<string, string> = {
  context_match: "上下文匹配",
  decision_stage_impact: "决策阶段影响",
  demand_substitutability: "需求替代性",
  evidence_confidence: "证据置信度",
  market_signal_strength: "市场信号强度"
};
const CONFIDENCE_LABELS: Record<string, string> = {
  high: "高",
  low: "低",
  medium: "中",
  unknown: "未知"
};
const AGENT_LABELS: Record<string, string> = {
  analysis_agent: "Analysis Agent",
  collection_agent: "Collection Agent",
  human: "Human",
  orchestrator: "Orchestrator",
  qa_agent: "QA Agent",
  writer_agent: "Writer Agent"
};
const RUN_STATUS_LABELS: Record<string, string> = {
  failed: "失败",
  requires_revision: "需要打回",
  running: "运行中",
  skipped: "跳过",
  started: "已开始",
  succeeded: "成功"
};
const TOOL_STATUS_LABELS: Record<string, string> = {
  failed: "失败",
  skipped: "跳过",
  succeeded: "成功"
};
const REVIEW_SEVERITY_LABELS: Record<string, string> = {
  blocker: "阻断",
  error: "错误",
  info: "提示",
  warning: "警告"
};
const REVIEW_STATUS_LABELS: Record<string, string> = {
  open: "未处理",
  resolved: "已解决",
  waived: "已豁免"
};
const TRACE_NODE_STATUS_LABELS: Record<string, string> = {
  completed: "已完成",
  created: "已创建",
  failed: "失败",
  pending: "等待中",
  requires_revision: "需要打回",
  running: "运行中",
  skipped: "跳过",
  succeeded: "成功"
};
const REPORT_SECTION_KEYS = [
  "executive_summary",
  "product_profile",
  "competitor_findings",
  "dynamic_slice_analysis",
  "decision_chain_analysis",
  "user_research_insights",
  "recommendations",
  "qa_summary",
  "evidence_index"
] as const;
const REPORT_FIELD_LABELS: Record<string, string> = {
  access_time: "访问时间",
  analysis_recompute: "Analysis 重算",
  basis_edge_id: "依据竞争边",
  brand: "品牌",
  claim_ids: "Claim 索引",
  claims: "Claims",
  collection_repair: "Collection 修复",
  competitor: "竞品",
  competition_type: "竞争类型",
  confidence: "置信度",
  confidence_level: "置信度",
  content: "正文",
  content_summary: "内容摘要",
  decision_factors: "决策因素",
  decision_stage: "决策阶段",
  decision_stages: "决策阶段",
  edge_id: "竞争边",
  edge_ids: "竞争边",
  edge_score: "竞争分",
  evidence_ids: "Evidence 索引",
  feature_tree: "功能树",
  final_price: "到手价",
  is_inference: "推断标识",
  limitations: "局限性",
  list_price: "标价",
  pain_points: "痛点",
  persona: "人群",
  personas: "目标人群",
  price_band: "价格带",
  pricing_model: "价格模型",
  product: "产品",
  product_id: "产品 ID",
  product_url: "商品链接",
  qa_agent: "QA Agent",
  recommendation: "建议",
  review_task_count: "ReviewTask",
  revision_message_count: "打回消息",
  risk_claims: "风险 Claim",
  risk_flags: "风险标记",
  scenario: "使用场景",
  score_breakdown: "评分拆解",
  screenshot_path: "截图路径",
  shop_name: "店铺",
  slice: "切片",
  source_type: "来源类型",
  source_url: "来源链接",
  status: "状态",
  summary: "摘要",
  top_edge_score: "最高竞争分",
  user_persona: "用户人群"
};
const REPORT_SECTION_FALLBACK_TITLES: Record<(typeof REPORT_SECTION_KEYS)[number], string> = {
  competitor_findings: "竞品发现",
  decision_chain_analysis: "决策链竞争分析",
  dynamic_slice_analysis: "动态竞争切片",
  evidence_index: "Evidence 索引",
  executive_summary: "执行摘要",
  product_profile: "目标产品画像",
  qa_summary: "QA 审查摘要",
  recommendations: "可执行建议",
  user_research_insights: "用户研究洞察"
};

const ROUTES: AppRoute[] = [
  {
    path: "/",
    label: "任务输入",
    title: "分析任务输入",
    eyebrow: "任务启动",
    summary: "创建自动猫砂盆分析任务，并确认本次演示使用的数据范围。",
    sections: ["目标产品", "数据模式", "研究文本"]
  },
  {
    path: "/profile",
    label: "产品画像",
    title: "产品画像",
    eyebrow: "结构化视图",
    summary: "查看目标产品的基础信息、价格模型、用户人群和证据状态。",
    sections: ["基础信息", "功能树", "价格模型", "用户人群"]
  },
  {
    path: "/battlefield",
    label: "竞争图谱",
    title: "竞争关系图谱",
    eyebrow: "关系网络",
    summary: "按价格带、人群、场景、评分和证据覆盖查看竞争关系。",
    sections: ["切片控制", "关系图谱", "评分解释", "证据卡片"]
  },
  {
    path: "/report",
    label: "分析报告",
    title: "分析报告",
    eyebrow: "汇报输出",
    summary: "承载最终结论、质检摘要和证据索引的网页报告结构。",
    sections: ["执行摘要", "竞争发现", "行动建议", "证据索引"]
  },
  {
    path: "/trace",
    label: "过程追踪",
    title: "智能体过程追踪",
    eyebrow: "过程证明",
    summary: "展示多智能体流程、运行日志、工具调用、质检打回和差异记录。",
    sections: ["流程状态", "运行记录", "质检打回", "差异视图"]
  }
];

function getRoute(pathname: string) {
  return ROUTES.find((route) => route.path === pathname) ?? ROUTES[0];
}

function navigateTo(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new Event("popstate"));
}

function routePathForTask(path: string, taskId: string | null) {
  if (!taskId || path === "/") {
    return path;
  }

  return `${path}?task_id=${encodeURIComponent(taskId)}`;
}

type AppProps = {
  apiClient?: TaskApiClient;
};

export default function App({ apiClient }: AppProps = {}) {
  const [queryClient] = useState(createTaskQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      <WorkspaceApp apiClient={apiClient} />
    </QueryClientProvider>
  );
}

function WorkspaceApp({ apiClient }: AppProps = {}) {
  const [pathname, setPathname] = useState(window.location.pathname);
  const currentRoute = getRoute(pathname);
  const currentTaskId = getTaskIdFromLocation();
  const taskApiClient = useMemo(() => apiClient ?? createApiClient(), [apiClient]);

  useEffect(() => {
    const updatePathname = () => setPathname(window.location.pathname);

    window.addEventListener("popstate", updatePathname);
    return () => window.removeEventListener("popstate", updatePathname);
  }, []);

  return (
    <main className="workspace-shell">
      <aside className="workspace-sidebar" aria-label="主导航">
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">
            竞析
          </span>
          <div>
            <p className="brand-kicker">竞析智能体</p>
            <h1 className="brand-title">竞品关系重建系统</h1>
          </div>
        </div>

        <nav className="workspace-nav">
          {ROUTES.map((route) => {
            const isActive = route.path === currentRoute.path;

            return (
              <button
                aria-current={isActive ? "page" : undefined}
                className={isActive ? "nav-item nav-item-active" : "nav-item"}
                key={route.path}
                onClick={() => navigateTo(routePathForTask(route.path, currentTaskId))}
                type="button"
              >
                {route.label}
              </button>
            );
          })}
        </nav>
      </aside>

      <section className="workspace-main">
        <header className="workspace-header">
          <div>
            <p className="page-eyebrow">{currentRoute.eyebrow}</p>
            <h2>{currentRoute.title}</h2>
          </div>
          <div className="status-pill">
            {currentRoute.path === "/trace"
              ? "Trace 数据就绪"
              : currentRoute.path === "/"
                ? "任务输入就绪"
                : currentRoute.path === "/profile"
                  ? "画像数据就绪"
                  : currentRoute.path === "/battlefield"
                    ? "图谱数据就绪"
                    : currentRoute.path === "/report"
                      ? "报告数据就绪"
                      : "待接入数据"}
          </div>
        </header>

        {currentRoute.path === "/" ? (
          <TaskInputPage apiClient={taskApiClient} route={currentRoute} />
        ) : currentRoute.path === "/profile" ? (
          <ProductProfilePage
            apiClient={taskApiClient}
            route={currentRoute}
            taskId={currentTaskId}
          />
        ) : currentRoute.path === "/battlefield" ? (
          <BattlefieldPage apiClient={taskApiClient} route={currentRoute} taskId={currentTaskId} />
        ) : currentRoute.path === "/report" ? (
          <ReportPage apiClient={taskApiClient} route={currentRoute} taskId={currentTaskId} />
        ) : currentRoute.path === "/trace" ? (
          <TraceTaskStatusPage
            apiClient={taskApiClient}
            route={currentRoute}
            taskId={currentTaskId}
          />
        ) : (
          <RoutePlaceholder route={currentRoute} />
        )}
      </section>
    </main>
  );
}

function TraceTaskStatusPage({
  apiClient,
  route,
  taskId
}: {
  apiClient: TaskApiClient;
  route: AppRoute;
  taskId: string | null;
}) {
  const completedTraceRefreshRef = useRef<string | null>(null);
  const taskStatusQuery = useQuery({
    enabled: Boolean(taskId),
    queryFn: () => apiClient.get<TaskStatusResponse>(`/tasks/${encodeURIComponent(taskId ?? "")}`),
    queryKey: ["task-status", taskId],
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && isRunningTaskStatus(status) ? TASK_STATUS_REFETCH_INTERVAL_MS : false;
    },
    retry: false
  });
  const taskStatusState = toTaskStatusRequestState(taskStatusQuery);
  const taskStatus = taskStatusQuery.data;
  const isPolling = taskStatus ? isRunningTaskStatus(taskStatus.status) : false;
  const traceQuery = useQuery({
    enabled: Boolean(taskId),
    queryFn: () => apiClient.get<TraceData>(`/tasks/${encodeURIComponent(taskId ?? "")}/trace`),
    queryKey: ["task-trace", taskId],
    refetchInterval: () => (isPolling ? TASK_STATUS_REFETCH_INTERVAL_MS : false),
    retry: false
  });
  const traceState = toQueryRequestState(traceQuery);
  const trace = traceQuery.data;
  const { refetch: refetchTrace } = traceQuery;

  useEffect(() => {
    if (!taskId || taskStatus?.status !== "completed") {
      return;
    }

    const refreshKey = `${taskId}:${taskStatus.updated_at}`;
    if (completedTraceRefreshRef.current === refreshKey) {
      return;
    }

    completedTraceRefreshRef.current = refreshKey;
    void refetchTrace();
  }, [refetchTrace, taskId, taskStatus?.status, taskStatus?.updated_at]);

  return (
    <section className="page-surface" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">任务状态</p>
        <h3 id="page-title">{route.title}</h3>
        <p>{route.summary}</p>
      </div>

      {taskId ? (
        <div className="trace-page-layout" aria-label="过程追踪">
          <section className="task-status-card" aria-label="当前任务">
            <p className="section-kicker">当前任务</p>
            <h4>{taskId}</h4>
            <p>页面刷新后会从 URL 中的 task_id 恢复任务，并同步轮询任务状态与 Trace。</p>
          </section>

          <RequestStateMessage
            className="task-status-message"
            loadingText="正在读取任务状态"
            onRetry={() => void taskStatusQuery.refetch()}
            state={taskStatusState}
          />

          {taskStatus ? (
            <div className="task-status-detail">
              <div className={`task-status-badge task-status-${taskStatus.status}`} role="status">
                当前状态：{TASK_STATUS_LABELS[taskStatus.status]}
              </div>
              <dl className="summary-list">
                <div>
                  <dt>目标产品</dt>
                  <dd>{taskStatus.target_product_name}</dd>
                </div>
                <div>
                  <dt>数据模式</dt>
                  <dd>
                    {taskStatus.data_source_mode === "demo_snapshot" ? "本地快照" : "快照增强占位"}
                  </dd>
                </div>
                <div>
                  <dt>更新时间</dt>
                  <dd>{taskStatus.updated_at}</dd>
                </div>
                <div>
                  <dt>轮询状态</dt>
                  <dd>{isPolling ? "运行中，持续刷新" : "已停止轮询"}</dd>
                </div>
              </dl>
              {FAILED_TASK_STATUSES.has(taskStatus.status) ? (
                <div className="task-status-alert" role="alert">
                  任务执行失败，请保留当前 task_id 并查看后端 Trace 或日志定位原因。
                </div>
              ) : null}
              {taskStatus.status === "completed" ? <TaskResultActions taskId={taskId} /> : null}
            </div>
          ) : null}

          <RequestStateMessage
            className="trace-state-message"
            loadingText="正在读取过程追踪"
            onRetry={() => void traceQuery.refetch()}
            state={traceState}
          />

          {trace ? <TraceContent trace={trace} /> : null}
        </div>
      ) : (
        <div className="empty-task-state" role="status">
          暂无任务 ID。请先从任务输入页创建任务，或访问 /trace?task_id=&lt;task_id&gt; 恢复状态。
        </div>
      )}
    </section>
  );
}

function TaskResultActions({ taskId }: { taskId: string }) {
  return (
    <div className="task-result-actions" aria-label="任务结果入口">
      <button
        className="secondary-action"
        onClick={() => navigateTo(routePathForTask("/profile", taskId))}
        type="button"
      >
        查看画像
      </button>
      <button
        className="secondary-action"
        onClick={() => navigateTo(routePathForTask("/battlefield", taskId))}
        type="button"
      >
        查看图谱
      </button>
      <button
        className="secondary-action"
        onClick={() => navigateTo(routePathForTask("/report", taskId))}
        type="button"
      >
        查看报告
      </button>
    </div>
  );
}

function TraceContent({ trace }: { trace: TraceData }) {
  const flow = useMemo(() => toTraceFlowElements(trace), [trace]);
  const totalTokens = (trace.token_usage ?? []).reduce((sum, usage) => sum + usage.total_tokens, 0);

  return (
    <div className="trace-content">
      <section className="trace-summary-card">
        <div className="section-heading">
          <p className="section-kicker">Trace</p>
          <h4>Trace 概览</h4>
        </div>
        <dl className="summary-list trace-summary-list">
          <div>
            <dt>Trace View</dt>
            <dd>{trace.trace_view_id}</dd>
          </div>
          <div>
            <dt>Workflow</dt>
            <dd>{trace.workflow_status}</dd>
          </div>
          <div>
            <dt>任务状态</dt>
            <dd>{TASK_STATUS_LABELS[trace.task_status as TaskStatus] ?? trace.task_status}</dd>
          </div>
          <div>
            <dt>生成时间</dt>
            <dd>{formatDateTime(trace.generated_at)}</dd>
          </div>
          <div>
            <dt>Agent Run</dt>
            <dd>{trace.agent_runs?.length ?? 0}</dd>
          </div>
          <div>
            <dt>Token</dt>
            <dd>{totalTokens}</dd>
          </div>
        </dl>
      </section>

      <div className="trace-layout">
        <section className="trace-graph-panel" aria-label="LangGraph DAG 状态">
          <div className="section-heading">
            <p className="section-kicker">LangGraph DAG</p>
            <h4>流程图</h4>
          </div>
          <div className="trace-flow" data-testid="trace-flow">
            <ReactFlow
              edges={flow.edges}
              fitView
              nodes={flow.nodes}
              nodesDraggable={false}
              proOptions={{ hideAttribution: true }}
            >
              <Background gap={20} />
              <Controls showInteractive={false} />
            </ReactFlow>
          </div>
        </section>

        <aside className="trace-side-panel" aria-label="Trace 数据摘要">
          <TraceAgentRuns runs={trace.agent_runs ?? []} />
          <TraceToolCalls toolCalls={trace.tool_calls ?? []} />
          <TraceTokenUsage tokenUsage={trace.token_usage ?? []} />
        </aside>
      </div>

      <div className="trace-detail-grid">
        <TraceQaReviews reviews={trace.qa_reviews ?? []} />
        <TraceRevisionMessages messages={trace.revision_messages ?? []} />
        <TraceDiffView diffs={trace.diffs ?? []} />
        <TracePromptPreviews prompts={trace.prompt_previews ?? []} />
      </div>
    </div>
  );
}

function TraceAgentRuns({ runs }: { runs: AgentRunLog[] }) {
  return (
    <section className="trace-panel" aria-label="Agent Run 列表">
      <div className="section-heading">
        <p className="section-kicker">Agent Run</p>
        <h4>运行记录</h4>
      </div>
      {runs.length > 0 ? (
        <div className="trace-list">
          {runs.map((run) => (
            <article className="trace-list-item" key={run.run_id}>
              <div className="trace-item-heading">
                <h5>{AGENT_LABELS[run.agent_name] ?? run.agent_name}</h5>
                <span className={`trace-status trace-status-${run.status}`}>
                  {RUN_STATUS_LABELS[run.status] ?? run.status}
                </span>
              </div>
              <dl className="trace-fields">
                <div>
                  <dt>Run ID</dt>
                  <dd>{run.run_id}</dd>
                </div>
                <div>
                  <dt>开始</dt>
                  <dd>{formatDateTime(run.started_at)}</dd>
                </div>
                <div>
                  <dt>结束</dt>
                  <dd>{formatDateTime(run.ended_at)}</dd>
                </div>
                <div>
                  <dt>输入摘要</dt>
                  <dd>{formatTraceNullable(run.input_summary)}</dd>
                </div>
                <div>
                  <dt>输出摘要</dt>
                  <dd>{formatTraceNullable(run.output_summary)}</dd>
                </div>
                {run.error_message ? (
                  <div>
                    <dt>错误</dt>
                    <dd>{sanitizeTraceText(run.error_message)}</dd>
                  </div>
                ) : null}
              </dl>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>
      )}
    </section>
  );
}

function TraceToolCalls({ toolCalls }: { toolCalls: ToolCallLog[] }) {
  return (
    <section className="trace-panel" aria-label="Tool Call 列表">
      <div className="section-heading">
        <p className="section-kicker">Tool Call</p>
        <h4>工具调用</h4>
      </div>
      {toolCalls.length > 0 ? (
        <div className="trace-list">
          {toolCalls.map((toolCall) => (
            <article className="trace-list-item" key={toolCall.tool_call_id}>
              <div className="trace-item-heading">
                <h5>{toolCall.tool_name}</h5>
                <span className={`trace-status trace-status-${toolCall.status}`}>
                  {TOOL_STATUS_LABELS[toolCall.status] ?? toolCall.status}
                </span>
              </div>
              <dl className="trace-fields">
                <div>
                  <dt>Run ID</dt>
                  <dd>{toolCall.run_id}</dd>
                </div>
                <div>
                  <dt>耗时</dt>
                  <dd>{formatDuration(toolCall.duration_ms)}</dd>
                </div>
                <div>
                  <dt>参数摘要</dt>
                  <dd>{renderTraceValue(toolCall.arguments_summary ?? {})}</dd>
                </div>
                {toolCall.error_message ? (
                  <div>
                    <dt>错误</dt>
                    <dd>{sanitizeTraceText(toolCall.error_message)}</dd>
                  </div>
                ) : null}
              </dl>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>
      )}
    </section>
  );
}

function TraceTokenUsage({ tokenUsage }: { tokenUsage: TokenUsageLog[] }) {
  const total = tokenUsage.reduce((sum, usage) => sum + usage.total_tokens, 0);

  return (
    <section className="trace-panel" aria-label="Token Usage 列表">
      <div className="section-heading">
        <p className="section-kicker">Token</p>
        <h4>Token Usage</h4>
      </div>
      <div className="trace-token-total">总计 {total} tokens</div>
      {tokenUsage.length > 0 ? (
        <div className="trace-list">
          {tokenUsage.map((usage) => (
            <article className="trace-list-item" key={usage.usage_id}>
              <div className="trace-item-heading">
                <h5>{AGENT_LABELS[usage.agent_name] ?? usage.agent_name}</h5>
                <span>{usage.model_name}</span>
              </div>
              <dl className="trace-fields trace-token-fields">
                <div>
                  <dt>Prompt</dt>
                  <dd>{usage.prompt_tokens}</dd>
                </div>
                <div>
                  <dt>Completion</dt>
                  <dd>{usage.completion_tokens}</dd>
                </div>
                <div>
                  <dt>Total</dt>
                  <dd>{usage.total_tokens}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function TraceQaReviews({ reviews }: { reviews: ReviewTask[] }) {
  return (
    <section className="trace-panel" aria-label="QA Review 列表">
      <div className="section-heading">
        <p className="section-kicker">QA Review</p>
        <h4>质检记录</h4>
      </div>
      {reviews.length > 0 ? (
        <div className="trace-list">
          {reviews.map((review) => (
            <article className="trace-list-item" key={review.review_task_id}>
              <div className="trace-item-heading">
                <h5>{review.check_name}</h5>
                <span className={`trace-status trace-severity-${review.severity}`}>
                  {REVIEW_SEVERITY_LABELS[review.severity] ?? review.severity}
                </span>
              </div>
              <p>{sanitizeTraceText(review.message)}</p>
              <dl className="trace-fields">
                <div>
                  <dt>Issue</dt>
                  <dd>{sanitizeTraceText(review.issue_code)}</dd>
                </div>
                <div>
                  <dt>目标</dt>
                  <dd>
                    {review.target_type} / {review.target_id}
                  </dd>
                </div>
                <div>
                  <dt>打回目标</dt>
                  <dd>
                    {review.target_agent
                      ? (AGENT_LABELS[review.target_agent] ?? review.target_agent)
                      : EMPTY_VALUE_TEXT}
                  </dd>
                </div>
                <div>
                  <dt>状态</dt>
                  <dd>{REVIEW_STATUS_LABELS[review.status] ?? review.status}</dd>
                </div>
                <div>
                  <dt>要求</dt>
                  <dd>{sanitizeTraceText(review.required_action)}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>
      )}
    </section>
  );
}

function TraceRevisionMessages({ messages }: { messages: AgentMessage[] }) {
  return (
    <section className="trace-panel" aria-label="QA 打回消息">
      <div className="section-heading">
        <p className="section-kicker">Revision</p>
        <h4>QA 打回记录</h4>
      </div>
      {messages.length > 0 ? (
        <div className="trace-list">
          {messages.map((message) => (
            <article className="trace-list-item" key={message.message_id}>
              <div className="trace-item-heading">
                <h5>{message.message_id}</h5>
                <span className={`trace-status trace-status-${message.status}`}>
                  {message.status}
                </span>
              </div>
              <dl className="trace-fields">
                <div>
                  <dt>路径</dt>
                  <dd>
                    {AGENT_LABELS[message.from_agent] ?? message.from_agent} →{" "}
                    {AGENT_LABELS[message.to_agent] ?? message.to_agent}
                  </dd>
                </div>
                <div>
                  <dt>类型</dt>
                  <dd>{message.message_type}</dd>
                </div>
                <div>
                  <dt>Artifact</dt>
                  <dd>{message.artifact_type}</dd>
                </div>
                <div>
                  <dt>Payload</dt>
                  <dd>{renderTraceValue(message.payload ?? {})}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>
      )}
    </section>
  );
}

function TraceDiffView({ diffs }: { diffs: TraceDiff[] }) {
  return (
    <section className="trace-panel trace-diff-panel" aria-label="Diff View">
      <div className="section-heading">
        <p className="section-kicker">Diff View</p>
        <h4>打回前后差异</h4>
      </div>
      {diffs.length > 0 ? (
        <div className="trace-list">
          {diffs.map((diff) => (
            <article className="trace-list-item" key={diff.diff_id}>
              <div className="trace-item-heading">
                <h5>
                  {diff.target_type} / {diff.target_id}
                </h5>
                <span className={`trace-status trace-status-${diff.status}`}>{diff.status}</span>
              </div>
              <p>{sanitizeTraceText(diff.source)}</p>
              <div className="trace-diff-grid">
                <div>
                  <span>Before</span>
                  {renderTraceValue(diff.before ?? {})}
                </div>
                <div>
                  <span>After</span>
                  {renderTraceValue(diff.after ?? {})}
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>
      )}
    </section>
  );
}

function TracePromptPreviews({ prompts }: { prompts: TracePromptPreview[] }) {
  return (
    <section className="trace-panel trace-prompt-panel" aria-label="Prompt 预览">
      <div className="section-heading">
        <p className="section-kicker">Prompt</p>
        <h4>Prompt 预览</h4>
      </div>
      {prompts.length > 0 ? (
        <div className="trace-list">
          {prompts.map((prompt) => (
            <details className="trace-prompt-details" key={prompt.preview_id}>
              <summary>
                <span>{sanitizeTraceText(prompt.title)}</span>
                <strong>
                  {AGENT_LABELS[prompt.agent_name] ?? prompt.agent_name}
                  {prompt.redacted ? " / 已脱敏" : ""}
                </strong>
              </summary>
              <p>{sanitizeTraceText(prompt.content_summary)}</p>
            </details>
          ))}
        </div>
      ) : (
        <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>
      )}
    </section>
  );
}

function ProductProfilePage({
  apiClient,
  route,
  taskId
}: {
  apiClient: TaskApiClient;
  route: AppRoute;
  taskId: string | null;
}) {
  const profileQuery = useQuery({
    enabled: Boolean(taskId),
    queryFn: () =>
      apiClient.get<ProductProfileData>(`/tasks/${encodeURIComponent(taskId ?? "")}/profile`),
    queryKey: ["product-profile", taskId],
    retry: false
  });
  const profileState = toQueryRequestState(profileQuery);
  const profile = profileQuery.data;

  return (
    <section className="page-surface" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">产品画像</p>
        <h3 id="page-title">{route.title}</h3>
        <p>{route.summary}</p>
      </div>

      {taskId ? (
        <div className="profile-page-grid">
          <RequestStateMessage
            className="profile-state-message"
            loadingText="正在读取产品画像"
            onRetry={() => void profileQuery.refetch()}
            state={profileState}
          />

          {profile ? (
            <>
              <div className="profile-content">
                <ProductBasicsCard profile={profile} />
                <FeatureTreeCard profile={profile} />
                <PricingModelCard profile={profile} />
                <UserPersonaCard profile={profile} />
                <EvidenceSummaryCard profile={profile} />
              </div>
              <HumanReviewPanel
                apiClient={apiClient}
                onSubmitted={() => void profileQuery.refetch()}
                profile={profile}
                taskId={taskId}
              />
            </>
          ) : null}
        </div>
      ) : (
        <div className="empty-task-state" role="status">
          暂无任务 ID。请从过程追踪页或任务状态 URL 进入 /profile?task_id=&lt;task_id&gt;
          查看产品画像。
        </div>
      )}
    </section>
  );
}

function ProductBasicsCard({ profile }: { profile: ProductProfileData }) {
  const product = profile.product;

  return (
    <article className="profile-panel">
      <div className="section-heading">
        <p className="section-kicker">Target</p>
        <h4>基础信息</h4>
      </div>
      <dl className="profile-description">
        <div>
          <dt>SKU 名称</dt>
          <dd>{product.name}</dd>
        </div>
        <div>
          <dt>品牌</dt>
          <dd>{formatNullable(product.brand)}</dd>
        </div>
        <div>
          <dt>店铺</dt>
          <dd>{formatNullable(product.shop_name)}</dd>
        </div>
        <div>
          <dt>品类</dt>
          <dd>{product.category}</dd>
        </div>
        <div>
          <dt>子类</dt>
          <dd>{product.subcategory}</dd>
        </div>
        <div>
          <dt>商品链接</dt>
          <dd>{formatNullable(product.product_url)}</dd>
        </div>
      </dl>
      <TagList items={product.tags ?? []} emptyText="暂无标签" />
    </article>
  );
}

function FeatureTreeCard({ profile }: { profile: ProductProfileData }) {
  const featureTree = profile.feature_tree;

  return (
    <article className="profile-panel">
      <div className="section-heading">
        <p className="section-kicker">Capabilities</p>
        <h4>FeatureTree</h4>
      </div>
      <div className="feature-grid">
        <FeatureList title="清洁能力" items={featureTree.cleaning_capability ?? []} />
        <FeatureList title="除臭能力" items={featureTree.odor_control ?? []} />
        <FeatureList title="安全能力" items={featureTree.safety_features ?? []} />
        <FeatureList title="智能能力" items={featureTree.smart_features ?? []} />
        <FeatureList title="维护成本" items={featureTree.maintenance_cost ?? []} />
      </div>
      <RiskFlagList riskFlags={featureTree.risk_flags ?? []} />
    </article>
  );
}

function PricingModelCard({ profile }: { profile: ProductProfileData }) {
  const pricing = profile.pricing_model;
  const pricingEvidence = profile.pricing_evidence;
  const hasAccessTime =
    pricingEvidence.access_time_status === "available" && pricingEvidence.access_time;

  return (
    <article className="profile-panel">
      <div className="section-heading">
        <p className="section-kicker">Price</p>
        <h4>PricingModel</h4>
      </div>
      <dl className="profile-description compact-description">
        <div>
          <dt>价格带</dt>
          <dd>{pricing.price_band}</dd>
        </div>
        <div>
          <dt>标价</dt>
          <dd>{formatPrice(pricing.list_price, pricing.currency)}</dd>
        </div>
        <div>
          <dt>到手价</dt>
          <dd>{formatPrice(pricing.final_price, pricing.currency)}</dd>
        </div>
        <div>
          <dt>套装</dt>
          <dd>{formatNullable(pricing.bundle_description)}</dd>
        </div>
      </dl>
      <FeatureList title="优惠信息" items={pricing.promotions ?? []} />
      <div className={hasAccessTime ? "evidence-status" : "evidence-status evidence-status-risk"}>
        价格证据：{hasAccessTime ? formatDateTime(pricingEvidence.access_time) : EMPTY_VALUE_TEXT}
      </div>
      <RiskFlagList riskFlags={pricingEvidence.risk_flags ?? pricing.risk_flags ?? []} />
    </article>
  );
}

function UserPersonaCard({ profile }: { profile: ProductProfileData }) {
  const persona = profile.user_persona;

  return (
    <article className="profile-panel">
      <div className="section-heading">
        <p className="section-kicker">Audience</p>
        <h4>UserPersona</h4>
      </div>
      <div className="feature-grid">
        <FeatureList title="目标人群" items={persona.personas ?? []} />
        <FeatureList title="痛点" items={persona.pain_points ?? []} />
        <FeatureList title="使用场景" items={persona.scenarios ?? []} />
        <FeatureList title="决策因素" items={persona.decision_factors ?? []} />
      </div>
      <div className="inference-note">
        {persona.is_inference ? "人群画像含推断内容，已保留推断标记。" : "人群画像来自直接证据。"}
      </div>
      <RiskFlagList riskFlags={persona.risk_flags ?? []} />
    </article>
  );
}

function EvidenceSummaryCard({ profile }: { profile: ProductProfileData }) {
  return (
    <article className="profile-panel profile-panel-wide">
      <div className="section-heading">
        <p className="section-kicker">Evidence</p>
        <h4>Evidence 摘要</h4>
      </div>
      <div className="evidence-list">
        {(profile.evidence_summaries ?? []).map((evidence) => (
          <section className="evidence-item" key={evidence.evidence_id}>
            <div>
              <p className="evidence-id">{evidence.evidence_id}</p>
              <p>{evidence.content_summary}</p>
              <small>{evidence.limitations}</small>
            </div>
            <dl>
              <div>
                <dt>来源</dt>
                <dd>{evidence.source_type}</dd>
              </div>
              <div>
                <dt>置信度</dt>
                <dd>{evidence.confidence_level}</dd>
              </div>
              <div>
                <dt>访问时间</dt>
                <dd>
                  {evidence.access_time_status === "available"
                    ? formatDateTime(evidence.access_time)
                    : EMPTY_VALUE_TEXT}
                </dd>
              </div>
            </dl>
            <RiskFlagList riskFlags={evidence.risk_flags ?? []} />
          </section>
        ))}
      </div>
    </article>
  );
}

function BattlefieldPage({
  apiClient,
  route,
  taskId
}: {
  apiClient: TaskApiClient;
  route: AppRoute;
  taskId: string | null;
}) {
  const [selectedSlice, setSelectedSlice] = useState<BattlefieldSliceSelection>({});
  const battlefieldQuery = useQuery({
    enabled: Boolean(taskId),
    queryFn: () =>
      apiClient.get<BattlefieldData>(`/tasks/${encodeURIComponent(taskId ?? "")}/battlefield`, {
        query: selectedSlice
      }),
    queryKey: [
      "battlefield",
      taskId,
      selectedSlice.price_band,
      selectedSlice.persona,
      selectedSlice.scenario
    ],
    placeholderData: (previousData) => previousData,
    retry: false
  });
  const battlefieldState = toQueryRequestState(battlefieldQuery);
  const battlefield = battlefieldQuery.data;
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const graph = useMemo(
    () => (battlefield ? toBattlefieldFlowElements(battlefield) : { edges: [], nodes: [] }),
    [battlefield]
  );
  const selectedEdge =
    battlefield?.graph_edges?.find((edge) => edge.edge_id === selectedEdgeId) ??
    battlefield?.graph_edges?.[0] ??
    null;

  function updateSlice(field: keyof BattlefieldSliceSelection, value: string) {
    setSelectedEdgeId(null);
    setSelectedSlice((currentSlice) => {
      const nextSlice = {
        ...(currentSlice.persona ? { persona: currentSlice.persona } : {}),
        ...(currentSlice.price_band ? { price_band: currentSlice.price_band } : {}),
        ...(currentSlice.scenario ? { scenario: currentSlice.scenario } : {})
      };

      if (value) {
        return { ...nextSlice, [field]: value };
      }

      delete nextSlice[field];
      return nextSlice;
    });
  }

  return (
    <section className="page-surface" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">竞争图谱</p>
        <h3 id="page-title">{route.title}</h3>
        <p>{route.summary}</p>
      </div>

      {taskId ? (
        <div className="battlefield-layout">
          <RequestStateMessage
            className="profile-state-message"
            loadingText="正在读取竞争图谱"
            onRetry={() => void battlefieldQuery.refetch()}
            state={battlefieldState}
          />

          {battlefield ? (
            <>
              <div className="battlefield-main">
                <SliceDial
                  data={battlefield}
                  selectedSlice={selectedSlice}
                  updateSlice={updateSlice}
                />
                <CompetitionGraph
                  edges={graph.edges}
                  nodes={graph.nodes}
                  onSelectEdge={setSelectedEdgeId}
                />
                <DecisionChainPanel data={battlefield} />
              </div>
              <BattlefieldInsightPanel data={battlefield} selectedEdge={selectedEdge} />
            </>
          ) : null}
        </div>
      ) : (
        <div className="empty-task-state" role="status">
          暂无任务 ID。请访问 /battlefield?task_id=&lt;task_id&gt; 查看竞争图谱。
        </div>
      )}
    </section>
  );
}

function SliceDial({
  data,
  selectedSlice,
  updateSlice
}: {
  data: BattlefieldData;
  selectedSlice: BattlefieldSliceSelection;
  updateSlice: (field: keyof BattlefieldSliceSelection, value: string) => void;
}) {
  const priceBands = uniqueSliceValues(data.available_slices ?? [], "price_band");
  const personas = uniqueSliceValues(data.available_slices ?? [], "persona");
  const scenarios = uniqueSliceValues(data.available_slices ?? [], "scenario");

  return (
    <section className="battlefield-panel" aria-label="切片拨盘">
      <div className="section-heading">
        <p className="section-kicker">Slice Dial</p>
        <h4>切片拨盘</h4>
      </div>
      <div className="slice-controls">
        <SliceSelect
          label="价格带"
          onChange={(value) => updateSlice("price_band", value)}
          options={priceBands}
          value={selectedSlice.price_band ?? ""}
        />
        <SliceSelect
          label="用户人群"
          onChange={(value) => updateSlice("persona", value)}
          options={personas}
          value={selectedSlice.persona ?? ""}
        />
        <SliceSelect
          label="使用场景"
          onChange={(value) => updateSlice("scenario", value)}
          options={scenarios}
          value={selectedSlice.scenario ?? ""}
        />
      </div>
      <div className="slice-summary" role="status">
        当前切片：{formatSelectedSlice(selectedSlice)}
      </div>
    </section>
  );
}

function SliceSelect({
  label,
  onChange,
  options,
  value
}: {
  label: string;
  onChange: (value: string) => void;
  options: string[];
  value: string;
}) {
  return (
    <label>
      <span>{label}</span>
      <select
        className="field-control"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        <option value="">全部</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function CompetitionGraph({
  edges,
  nodes,
  onSelectEdge
}: {
  edges: FlowEdge[];
  nodes: FlowNode[];
  onSelectEdge: (edgeId: string) => void;
}) {
  return (
    <section className="battlefield-panel graph-panel" aria-label="竞争关系图">
      <div className="section-heading">
        <p className="section-kicker">Graph</p>
        <h4>竞争关系图</h4>
      </div>
      <div className="competition-flow" data-testid="competition-flow">
        <ReactFlow
          edges={edges}
          fitView
          nodes={nodes}
          nodesDraggable={false}
          onEdgeClick={(_, edge) => onSelectEdge(edge.id)}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={16} />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </section>
  );
}

function DecisionChainPanel({ data }: { data: BattlefieldData }) {
  return (
    <section className="battlefield-panel" aria-label="决策链">
      <div className="section-heading">
        <p className="section-kicker">Decision Chain</p>
        <h4>决策链</h4>
      </div>
      <div className="decision-chain">
        {(data.decision_chain ?? []).map((stage) => (
          <article className="decision-stage" key={stage.stage}>
            <div>
              <strong>{DECISION_STAGE_LABELS[stage.stage] ?? stage.stage}</strong>
              <span>{Math.round(stage.average_edge_score * 100)} 分</span>
            </div>
            <p>
              边 {stage.edge_ids?.length ?? 0} 条 / Claim {stage.claim_ids?.length ?? 0} 条 /
              Evidence {stage.evidence_ids?.length ?? 0} 条
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}

function BattlefieldInsightPanel({
  data,
  selectedEdge
}: {
  data: BattlefieldData;
  selectedEdge: BattlefieldGraphEdge | null;
}) {
  const edgeEvidenceCards = selectedEdge
    ? (data.evidence_cards ?? []).filter((card) =>
        (selectedEdge.evidence_ids ?? []).includes(card.evidence_id)
      )
    : [];

  return (
    <aside className="battlefield-side" aria-label="竞争边详情">
      <section className="battlefield-panel">
        <div className="section-heading">
          <p className="section-kicker">Edge Detail</p>
          <h4>评分解释</h4>
        </div>
        {selectedEdge ? (
          <>
            <div
              className={
                selectedEdge.risk_status === "at_risk" ? "edge-score edge-score-risk" : "edge-score"
              }
            >
              <span>{COMPETITION_TYPE_LABELS[selectedEdge.competition_type]}</span>
              <strong>{Math.round(selectedEdge.edge_score * 100)}</strong>
            </div>
            <p className="edge-id">{selectedEdge.edge_id}</p>
            <ScoreBreakdownList edge={selectedEdge} />
            <FeatureList title="评分说明" items={selectedEdge.score_explanations ?? []} />
            <RiskFlagList riskFlags={selectedEdge.risk_flags ?? []} />
          </>
        ) : (
          <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>
        )}
      </section>

      <section className="battlefield-panel">
        <div className="section-heading">
          <p className="section-kicker">Claims</p>
          <h4>Claim 与 Evidence</h4>
        </div>
        {selectedEdge?.claim_refs?.length ? (
          <div className="claim-list">
            {selectedEdge.claim_refs.map((claim) => (
              <article className="claim-card" key={claim.claim_id}>
                <p className="evidence-id">{claim.claim_id}</p>
                <p>{claim.content}</p>
                <small>
                  置信度 {Math.round(claim.confidence * 100)}% / 状态 {claim.status} / Evidence{" "}
                  {(claim.evidence_ids ?? []).join("，") || EMPTY_VALUE_TEXT}
                </small>
                <RiskFlagList riskFlags={claim.risk_flags ?? []} />
              </article>
            ))}
          </div>
        ) : (
          <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>
        )}
      </section>

      <section className="battlefield-panel">
        <div className="section-heading">
          <p className="section-kicker">Evidence</p>
          <h4>证据卡片</h4>
        </div>
        <EvidenceCardList
          cards={edgeEvidenceCards.length > 0 ? edgeEvidenceCards : (data.evidence_cards ?? [])}
        />
      </section>

      <QASummaryPanel data={data} />
    </aside>
  );
}

function ScoreBreakdownList({ edge }: { edge: BattlefieldGraphEdge }) {
  return (
    <div className="score-breakdown" aria-label="评分拆解">
      {Object.entries(edge.score_breakdown).map(([key, value]) => (
        <div className="score-row" key={key}>
          <span>{SCORE_BREAKDOWN_LABELS[key] ?? key}</span>
          <meter max={1} min={0} value={value} />
          <strong>{Math.round(value * 100)}</strong>
        </div>
      ))}
    </div>
  );
}

function EvidenceCardList({ cards }: { cards: BattlefieldEvidenceCard[] }) {
  if (cards.length === 0) {
    return <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>;
  }

  return (
    <div className="battlefield-evidence-list">
      {cards.map((card) => (
        <article className="battlefield-evidence-card" key={card.evidence_id}>
          <p className="evidence-id">{card.evidence_id}</p>
          <p>{card.content_summary}</p>
          <dl>
            <div>
              <dt>来源</dt>
              <dd>{card.source_type}</dd>
            </div>
            <div>
              <dt>置信度</dt>
              <dd>{CONFIDENCE_LABELS[card.confidence_level] ?? card.confidence_level}</dd>
            </div>
            <div>
              <dt>访问时间</dt>
              <dd>
                {card.access_time_status === "available"
                  ? formatDateTime(card.access_time)
                  : EMPTY_VALUE_TEXT}
              </dd>
            </div>
          </dl>
          <small>{card.limitations}</small>
          <RiskFlagList riskFlags={card.risk_flags ?? []} />
        </article>
      ))}
    </div>
  );
}

function QASummaryPanel({ data }: { data: BattlefieldData }) {
  const qa = data.qa_summary;

  return (
    <section className="battlefield-panel" aria-label="QA 打回记录">
      <div className="section-heading">
        <p className="section-kicker">QA</p>
        <h4>QA 打回记录</h4>
      </div>
      <dl className="summary-list">
        <div>
          <dt>QA 状态</dt>
          <dd>{qa.qa_status === "passed" ? "已通过" : "需关注"}</dd>
        </div>
        <div>
          <dt>ReviewTask</dt>
          <dd>
            共 {qa.review_task_count} 条，开放 {qa.open_review_task_count} 条，已解决{" "}
            {qa.resolved_review_task_count} 条
          </dd>
        </div>
        <div>
          <dt>打回消息</dt>
          <dd>{qa.revision_message_count} 条</dd>
        </div>
        <div>
          <dt>风险边</dt>
          <dd>{qa.risk_edge_ids?.join("，") || "无"}</dd>
        </div>
      </dl>
    </section>
  );
}

function ReportPage({
  apiClient,
  route,
  taskId
}: {
  apiClient: TaskApiClient;
  route: AppRoute;
  taskId: string | null;
}) {
  const reportQuery = useQuery({
    enabled: Boolean(taskId),
    queryFn: () => apiClient.get<ReportData>(`/tasks/${encodeURIComponent(taskId ?? "")}/report`),
    queryKey: ["report", taskId],
    retry: false
  });
  const reportState = toQueryRequestState(reportQuery);
  const reportMessageState = isReportNotReadyError(reportQuery.error)
    ? createIdleState<ReportData>()
    : reportState;
  const report = reportQuery.data;

  return (
    <section className="page-surface" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">网页报告</p>
        <h3 id="page-title">{route.title}</h3>
        <p>{route.summary}</p>
      </div>

      {taskId ? (
        <div className="report-layout">
          <RequestStateMessage
            className="profile-state-message"
            loadingText="正在读取分析报告"
            onRetry={() => void reportQuery.refetch()}
            state={reportMessageState}
          />

          {isReportNotReadyError(reportQuery.error) ? (
            <ReportWaitingState
              onRetry={() => void reportQuery.refetch()}
              status={readErrorDetail(reportQuery.error, "status")}
            />
          ) : null}

          {report ? <ReportContent apiClient={apiClient} report={report} taskId={taskId} /> : null}
        </div>
      ) : (
        <div className="empty-task-state" role="status">
          暂无任务 ID。请访问 /report?task_id=&lt;task_id&gt; 查看分析报告。
        </div>
      )}
    </section>
  );
}

function ReportWaitingState({ onRetry, status }: { onRetry: () => void; status: string | null }) {
  return (
    <section className="report-waiting" role="status">
      <div>
        <p className="section-kicker">Waiting</p>
        <h4>报告尚未生成</h4>
        <p>
          当前任务还没有进入 completed 状态，网页报告会在 Writer Agent 完成后开放。
          {status ? ` 当前状态：${TASK_STATUS_LABELS[status as TaskStatus] ?? status}。` : ""}
        </p>
      </div>
      <button className="secondary-action" onClick={onRetry} type="button">
        重新检查
      </button>
    </section>
  );
}

function ReportContent({
  apiClient,
  report,
  taskId
}: {
  apiClient: TaskApiClient;
  report: ReportData;
  taskId: string;
}) {
  const markdownMutation = useMutation({
    mutationFn: () =>
      apiClient.get<MarkdownReport>(`/tasks/${encodeURIComponent(taskId)}/report/markdown`)
  });
  const reportSections = getOrderedReportSections(report);

  return (
    <>
      <div className="report-toolbar">
        <dl className="summary-list report-meta">
          <div>
            <dt>Report ID</dt>
            <dd>{report.report_id}</dd>
          </div>
          <div>
            <dt>生成时间</dt>
            <dd>{formatDateTime(report.generated_at)}</dd>
          </div>
          <div>
            <dt>章节数量</dt>
            <dd>{reportSections.length}</dd>
          </div>
        </dl>
        <div className="report-export">
          <button
            className="primary-action"
            disabled={markdownMutation.isPending}
            onClick={() => markdownMutation.mutate()}
            type="button"
          >
            {markdownMutation.isPending ? "导出中" : "导出 Markdown"}
          </button>
          {markdownMutation.isSuccess ? (
            <div className="review-success" role="status">
              Markdown 已导出：{markdownMutation.data.file_path}
            </div>
          ) : null}
          {markdownMutation.isError ? (
            <RequestStateMessage
              className="review-error"
              state={createErrorState(markdownMutation.error)}
            />
          ) : null}
        </div>
      </div>

      <div className="report-section-grid" aria-label="报告章节">
        {reportSections.map((section) => (
          <ReportSectionCard key={section.section_id} section={section} />
        ))}
      </div>
    </>
  );
}

function ReportSectionCard({ section }: { section: ReportSection }) {
  return (
    <article className="report-section-card">
      <div className="section-heading">
        <p className="section-kicker">{section.section_id}</p>
        <h4>{section.title}</h4>
      </div>
      <p className="report-section-summary">{section.summary}</p>
      <ReportItemList items={section.items ?? []} sectionId={section.section_id} />
      <ReportReferenceStrip section={section} />
    </article>
  );
}

function ReportItemList({
  items,
  sectionId
}: {
  items: NonNullable<ReportSection["items"]>;
  sectionId: string;
}) {
  if (items.length === 0) {
    return <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>;
  }

  return (
    <div className="report-item-list">
      {items.map((item, index) => (
        <article className="report-item" key={`${sectionId}-${index}`}>
          <ReportItemTitle item={item} index={index} sectionId={sectionId} />
          <dl>{renderReportItemFields(item, sectionId)}</dl>
        </article>
      ))}
    </div>
  );
}

function ReportItemTitle({
  index,
  item,
  sectionId
}: {
  index: number;
  item: Record<string, unknown>;
  sectionId: string;
}) {
  const title = getReportItemTitle(item, sectionId, index);

  return title ? <h5>{title}</h5> : null;
}

function ReportReferenceStrip({ section }: { section: ReportSection }) {
  const claimIds = section.claim_ids ?? [];
  const evidenceIds = section.evidence_ids ?? [];

  return (
    <div className="report-reference-strip">
      <div>
        <span>Claim</span>
        <strong>{claimIds.length > 0 ? claimIds.join("，") : EMPTY_VALUE_TEXT}</strong>
      </div>
      <div>
        <span>Evidence</span>
        <strong>{evidenceIds.length > 0 ? evidenceIds.join("，") : EMPTY_VALUE_TEXT}</strong>
      </div>
      <RiskFlagList riskFlags={section.risk_flags ?? []} />
    </div>
  );
}

function HumanReviewPanel({
  apiClient,
  onSubmitted,
  profile,
  taskId
}: {
  apiClient: TaskApiClient;
  onSubmitted: () => void;
  profile: ProductProfileData;
  taskId: string;
}) {
  const reviewOptions = useMemo(() => buildHumanReviewOptions(profile), [profile]);
  const [selectedOptionKey, setSelectedOptionKey] = useState(reviewOptions[0]?.key ?? "");
  const [reviewValue, setReviewValue] = useState("");
  const [reviewReason, setReviewReason] = useState("");
  const [reviewError, setReviewError] = useState<string | null>(null);
  const selectedOption = reviewOptions.find((option) => option.key === selectedOptionKey);
  const feedbackMutation = useMutation({
    mutationFn: (payload: HumanFeedbackCreateRequest) =>
      apiClient.post<HumanFeedbackCreateResponse>(
        `/tasks/${encodeURIComponent(taskId)}/feedback`,
        payload
      ),
    onSuccess: () => {
      setReviewValue("");
      setReviewReason("");
      onSubmitted();
    }
  });

  function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedOption) {
      setReviewError("请选择修正字段。");
      return;
    }
    if (!reviewValue.trim()) {
      setReviewError("请输入修正值。");
      return;
    }
    if (!reviewReason.trim()) {
      setReviewError("请输入修正理由。");
      return;
    }

    setReviewError(null);
    const payload: HumanFeedbackCreateRequest = {
      action: "update_field",
      after_value: {
        field: selectedOption.field,
        value: selectedOption.isList ? splitListValue(reviewValue) : reviewValue.trim()
      },
      reason: reviewReason.trim(),
      target_id: selectedOption.targetId,
      target_type: selectedOption.targetType
    };
    feedbackMutation.mutate(payload);
  }

  return (
    <aside className="human-review-panel" aria-label="有限人工修正">
      <div className="section-heading">
        <p className="section-kicker">Human Review</p>
        <h4>有限人工修正</h4>
      </div>
      <p className="review-boundary">
        仅允许修正产品画像结构化字段；提交后后端会保存 HumanFeedback 并刷新相关分析结果。
      </p>

      <form onSubmit={submitReview}>
        <label className="field-label" htmlFor="review-field">
          修正字段
        </label>
        <select
          className="field-control"
          id="review-field"
          onChange={(event) => {
            setSelectedOptionKey(event.target.value);
            setReviewValue("");
            setReviewError(null);
          }}
          value={selectedOptionKey}
        >
          {reviewOptions.map((option) => (
            <option key={option.key} value={option.key}>
              {option.label}
            </option>
          ))}
        </select>

        <label className="field-label" htmlFor="review-value">
          修正值
        </label>
        <textarea
          className="field-control text-area-control"
          id="review-value"
          onChange={(event) => setReviewValue(event.target.value)}
          placeholder={selectedOption ? formatReviewValue(selectedOption.currentValue) : undefined}
          rows={4}
          value={reviewValue}
        />

        <label className="field-label" htmlFor="review-reason">
          修正理由
        </label>
        <textarea
          className="field-control text-area-control"
          id="review-reason"
          onChange={(event) => setReviewReason(event.target.value)}
          rows={3}
          value={reviewReason}
        />

        {reviewError ? (
          <div className="review-error" role="alert">
            {reviewError}
          </div>
        ) : null}
        {feedbackMutation.isError ? (
          <RequestStateMessage
            className="review-error"
            state={createErrorState(feedbackMutation.error)}
          />
        ) : null}
        {feedbackMutation.isSuccess ? (
          <div className="review-success" role="status">
            人工修正已提交，相关结果已刷新。
          </div>
        ) : null}

        <button className="primary-action" disabled={feedbackMutation.isPending} type="submit">
          {feedbackMutation.isPending ? "提交中" : "提交人工修正"}
        </button>
      </form>
    </aside>
  );
}

function TaskInputPage({ apiClient, route }: { apiClient: TaskApiClient; route: AppRoute }) {
  const [form, setForm] = useState<TaskInputForm>(DEFAULT_TASK_FORM);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submissionState, setSubmissionState] =
    useState<ApiRequestState<TaskCreateResponse>>(createIdleState<TaskCreateResponse>());
  const isSubmitting =
    submissionState.status === "loading" || submissionState.status === "retrying";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors = validateTaskForm(form);
    setFieldErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    const payload = toTaskCreateRequest(form);
    setSubmissionState((previousState) => createLoadingState(previousState));

    try {
      const response = await apiClient.post<TaskCreateResponse>("/tasks", payload);
      setSubmissionState(createSuccessState(response));
      navigateTo(`/trace?task_id=${encodeURIComponent(response.task_id)}`);
    } catch (error) {
      setSubmissionState((previousState) => createErrorState(error, previousState));
    }
  }

  function updateForm<FieldName extends keyof TaskInputForm>(
    field: FieldName,
    value: TaskInputForm[FieldName]
  ) {
    setForm((currentForm) => ({ ...currentForm, [field]: value }));
    if (fieldErrors[field]) {
      setFieldErrors((currentErrors) => ({ ...currentErrors, [field]: undefined }));
    }
  }

  return (
    <section className="page-surface" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">Demo 任务</p>
        <h3 id="page-title">{route.title}</h3>
        <p>{route.summary}</p>
      </div>

      <form className="task-form" onSubmit={handleSubmit} noValidate>
        <div className="task-form-main">
          <div className="form-section" aria-labelledby="target-section-title">
            <div className="section-heading">
              <p className="section-kicker">目标产品</p>
              <h4 id="target-section-title">任务对象</h4>
            </div>

            <label className="field-label" htmlFor="target-product-name">
              目标产品名称
            </label>
            <input
              aria-describedby={
                fieldErrors.target_product_name ? "target-product-name-error" : undefined
              }
              aria-invalid={fieldErrors.target_product_name ? "true" : "false"}
              className="field-control"
              id="target-product-name"
              name="target_product_name"
              onChange={(event) => updateForm("target_product_name", event.target.value)}
              required
              type="text"
              value={form.target_product_name}
            />
            {fieldErrors.target_product_name ? (
              <p className="field-error" id="target-product-name-error">
                {fieldErrors.target_product_name}
              </p>
            ) : null}

            <label className="field-label" htmlFor="target-product-url">
              商品链接
            </label>
            <input
              className="field-control"
              id="target-product-url"
              name="target_product_url"
              onChange={(event) => updateForm("target_product_url", event.target.value)}
              type="url"
              value={form.target_product_url}
            />

            <div className="field-grid">
              <div>
                <label className="field-label" htmlFor="category">
                  品类
                </label>
                <select
                  aria-describedby={fieldErrors.category ? "category-error" : undefined}
                  aria-invalid={fieldErrors.category ? "true" : "false"}
                  className="field-control"
                  id="category"
                  name="category"
                  onChange={(event) => updateForm("category", event.target.value)}
                  required
                  value={form.category}
                >
                  {CATEGORY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                {fieldErrors.category ? (
                  <p className="field-error" id="category-error">
                    {fieldErrors.category}
                  </p>
                ) : null}
              </div>

              <div>
                <label className="field-label" htmlFor="subcategory">
                  子类
                </label>
                <select
                  aria-describedby={fieldErrors.subcategory ? "subcategory-error" : undefined}
                  aria-invalid={fieldErrors.subcategory ? "true" : "false"}
                  className="field-control"
                  id="subcategory"
                  name="subcategory"
                  onChange={(event) => updateForm("subcategory", event.target.value)}
                  required
                  value={form.subcategory}
                >
                  {SUBCATEGORY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                {fieldErrors.subcategory ? (
                  <p className="field-error" id="subcategory-error">
                    {fieldErrors.subcategory}
                  </p>
                ) : null}
              </div>
            </div>
          </div>

          <div className="form-section" aria-labelledby="data-section-title">
            <div className="section-heading">
              <p className="section-kicker">数据范围</p>
              <h4 id="data-section-title">快照模式</h4>
            </div>

            <fieldset className="mode-fieldset">
              <legend>数据模式</legend>
              <label className="mode-option">
                <input
                  checked={form.data_source_mode === "demo_snapshot"}
                  name="data_source_mode"
                  onChange={() => updateForm("data_source_mode", "demo_snapshot")}
                  type="radio"
                  value="demo_snapshot"
                />
                <span>
                  <strong>本地快照</strong>
                  <small>使用脱敏 SKU 快照运行稳定 Demo。</small>
                </span>
              </label>
              <label className="mode-option">
                <input
                  checked={form.data_source_mode === "snapshot_plus_live"}
                  name="data_source_mode"
                  onChange={() => updateForm("data_source_mode", "snapshot_plus_live")}
                  type="radio"
                  value="snapshot_plus_live"
                />
                <span>
                  <strong>快照 + 公开页增强</strong>
                  <small>MVP 中记录该模式，并继续以本地快照兜底。</small>
                </span>
              </label>
            </fieldset>

            {form.data_source_mode === "snapshot_plus_live" ? (
              <div className="stability-note" role="status">
                公开页增强可能受页面可访问性影响；本次 MVP 会自动降级使用本地快照。
              </div>
            ) : null}

            <label className="field-label" htmlFor="research-text">
              用户研究文本
            </label>
            <textarea
              className="field-control text-area-control"
              id="research-text"
              name="research_text"
              onChange={(event) => updateForm("research_text", event.target.value)}
              rows={6}
              value={form.research_text}
            />
          </div>
        </div>

        <aside className="task-form-side" aria-label="任务提交摘要">
          <dl className="summary-list">
            <div>
              <dt>默认目标</dt>
              <dd>{DEFAULT_TASK_FORM.target_product_name}</dd>
            </div>
            <div>
              <dt>提交后页面</dt>
              <dd>过程追踪</dd>
            </div>
            <div>
              <dt>当前模式</dt>
              <dd>{form.data_source_mode === "demo_snapshot" ? "本地快照" : "快照增强占位"}</dd>
            </div>
          </dl>

          <RequestStateMessage
            className="submission-state"
            loadingText="正在创建任务"
            state={submissionState}
          />

          <button className="primary-action" disabled={isSubmitting} type="submit">
            {isSubmitting ? "创建中" : "启动分析任务"}
          </button>
        </aside>
      </form>
    </section>
  );
}

function RoutePlaceholder({ route }: { route: AppRoute }) {
  return (
    <section className="page-surface" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">页面骨架</p>
        <h3 id="page-title">{route.title}</h3>
        <p>{route.summary}</p>
      </div>

      <div className="module-grid" aria-label={`${route.title}模块`}>
        {route.sections.map((section) => (
          <article className="module-card" key={section}>
            <p>模块</p>
            <h4>{section}</h4>
          </article>
        ))}
      </div>
    </section>
  );
}

function createTaskQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        gcTime: 0,
        refetchOnWindowFocus: false
      }
    }
  });
}

function getTaskIdFromLocation() {
  const taskId = new URLSearchParams(window.location.search).get("task_id")?.trim();
  return taskId && taskId.length > 0 ? taskId : null;
}

function isRunningTaskStatus(status: TaskStatus) {
  return RUNNING_TASK_STATUSES.has(status);
}

function toTaskStatusRequestState(query: {
  data?: TaskStatusResponse;
  error: Error | null;
  isError: boolean;
  isFetching: boolean;
  isPending: boolean;
}): ApiRequestState<TaskStatusResponse> {
  if (query.isPending || (query.isFetching && !query.data)) {
    return createLoadingState();
  }

  if (query.isError) {
    return createErrorState(query.error);
  }

  if (query.data) {
    return createSuccessState(query.data);
  }

  return createIdleState();
}

function toQueryRequestState<TData>(query: {
  data?: TData;
  error: Error | null;
  isError: boolean;
  isFetching: boolean;
  isPending: boolean;
}): ApiRequestState<TData> {
  if (query.isPending || (query.isFetching && !query.data)) {
    return createLoadingState();
  }

  if (query.isError) {
    return createErrorState(query.error);
  }

  if (query.data) {
    return createSuccessState(query.data);
  }

  return createIdleState();
}

function toBattlefieldFlowElements(data: BattlefieldData): {
  edges: FlowEdge[];
  nodes: FlowNode[];
} {
  const nodes = (data.graph_nodes ?? []).map((node, index) => toBattlefieldFlowNode(node, index));
  const edges = (data.graph_edges ?? []).map((edge) => toBattlefieldFlowEdge(edge));

  return { edges, nodes };
}

function toBattlefieldFlowNode(node: BattlefieldGraphNode, index: number): FlowNode {
  const isTarget = node.role === "target";
  const competitorIndex = Math.max(0, index - 1);
  const competitorColumn = competitorIndex % 2;
  const competitorRow = Math.floor(competitorIndex / 2);

  return {
    data: {
      label: (
        <div className={isTarget ? "flow-node flow-node-target" : "flow-node"}>
          <span>{isTarget ? "目标" : (COMPETITION_TYPE_LABELS[node.role] ?? "竞品")}</span>
          <strong>{node.label}</strong>
          <small>{node.brand || node.shop_name || EMPTY_VALUE_TEXT}</small>
        </div>
      )
    },
    id: node.node_id,
    position: isTarget
      ? { x: 20, y: 180 }
      : { x: 360 + competitorColumn * 260, y: 40 + competitorRow * 140 },
    type: "default"
  };
}

function toBattlefieldFlowEdge(edge: BattlefieldGraphEdge): FlowEdge {
  const score = Math.round(edge.edge_score * 100);

  return {
    animated: edge.risk_status === "at_risk",
    data: { edgeId: edge.edge_id },
    id: edge.edge_id,
    label: `${score}`,
    markerEnd: {
      type: MarkerType.ArrowClosed
    },
    source: edge.source,
    style: {
      stroke: edge.risk_status === "at_risk" ? "#c2410c" : "#2f766d",
      strokeWidth: 2 + edge.edge_score * 2
    },
    target: edge.target,
    type: "smoothstep"
  };
}

function toTraceFlowElements(trace: TraceData): {
  edges: FlowEdge[];
  nodes: FlowNode[];
} {
  const visibleNodes = (trace.dag_nodes ?? []).filter((node) => node.visible);

  return {
    edges: (trace.dag_edges ?? []).map((edge) => toTraceFlowEdge(edge)),
    nodes: visibleNodes.map((node, index) => toTraceFlowNode(node, index))
  };
}

function toTraceFlowNode(node: TraceDagNode, index: number): FlowNode {
  return {
    data: {
      label: (
        <div
          className={[
            "trace-flow-node",
            node.current ? "trace-flow-node-current" : "",
            node.failed ? "trace-flow-node-failed" : ""
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <span>{node.node_type}</span>
          <strong>{node.label}</strong>
          <small>{TRACE_NODE_STATUS_LABELS[node.status] ?? node.status}</small>
        </div>
      )
    },
    id: node.node_id,
    position: { x: index * 210, y: node.node_id === "failed" ? 190 : 80 },
    type: "default"
  };
}

function toTraceFlowEdge(edge: TraceDagEdge): FlowEdge {
  const isRevision = edge.condition?.includes("revision") || edge.label.includes("打回");

  return {
    animated: Boolean(isRevision),
    id: edge.edge_id,
    label: edge.label,
    markerEnd: {
      type: MarkerType.ArrowClosed
    },
    source: edge.source,
    style: {
      stroke: isRevision ? "#c2410c" : "#2f766d",
      strokeWidth: isRevision ? 3 : 2
    },
    target: edge.target,
    type: "smoothstep"
  };
}

function getOrderedReportSections(report: ReportData): ReportSection[] {
  const sectionsById = new Map<string, ReportSection>();
  for (const sectionId of [...report.section_order, ...REPORT_SECTION_KEYS]) {
    const section = report[sectionId as keyof ReportData];
    if (isReportSection(section)) {
      sectionsById.set(section.section_id, section);
    }
  }

  return REPORT_SECTION_KEYS.map(
    (sectionId) => sectionsById.get(sectionId) ?? createFallbackReportSection(sectionId)
  );
}

function createFallbackReportSection(sectionId: (typeof REPORT_SECTION_KEYS)[number]) {
  return {
    claim_ids: [],
    evidence_ids: [],
    items: [],
    risk_flags: [],
    section_id: sectionId,
    summary: EMPTY_VALUE_TEXT,
    title: REPORT_SECTION_FALLBACK_TITLES[sectionId]
  };
}

function isReportSection(value: unknown): value is ReportSection {
  return (
    typeof value === "object" &&
    value !== null &&
    "section_id" in value &&
    "title" in value &&
    "summary" in value
  );
}

function renderReportItemFields(item: Record<string, unknown>, sectionId: string): ReactNode[] {
  const hiddenKeys = new Set(["metadata"]);
  if (sectionId === "competitor_findings") {
    hiddenKeys.add("competitor");
  }
  if (sectionId === "recommendations") {
    hiddenKeys.add("recommendation");
  }
  if (sectionId === "evidence_index") {
    hiddenKeys.add("evidence_id");
  }

  return Object.entries(item)
    .filter(([key]) => !hiddenKeys.has(key))
    .map(([key, value]) => (
      <div key={key}>
        <dt>{humanizeReportKey(key)}</dt>
        <dd>{renderReportValue(value, key)}</dd>
      </div>
    ));
}

function renderReportValue(value: unknown, key?: string): ReactNode {
  if (value === null || value === undefined || value === "") {
    return EMPTY_VALUE_TEXT;
  }

  if (typeof value === "boolean") {
    return value ? "是" : "否";
  }

  if (typeof value === "number") {
    return key?.includes("score") || key === "confidence" ? formatScore(value) : value;
  }

  if (typeof value === "string") {
    return key === "access_time" || key === "generated_at" ? formatDateTime(value) : value;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return EMPTY_VALUE_TEXT;
    }

    if (value.every((item) => ["string", "number", "boolean"].includes(typeof item))) {
      return value.map((item) => String(item)).join("，");
    }

    return (
      <div className="report-nested-list">
        {value.map((item, index) => (
          <div className="report-nested-item" key={index}>
            {renderReportValue(item)}
          </div>
        ))}
      </div>
    );
  }

  if (isRecordValue(value)) {
    const entries = Object.entries(value).filter(([nestedKey]) => nestedKey !== "metadata");
    if (entries.length === 0) {
      return EMPTY_VALUE_TEXT;
    }

    return (
      <dl className="report-nested-fields">
        {entries.map(([nestedKey, nestedValue]) => (
          <div key={nestedKey}>
            <dt>{humanizeReportKey(nestedKey)}</dt>
            <dd>{renderReportValue(nestedValue, nestedKey)}</dd>
          </div>
        ))}
      </dl>
    );
  }

  return String(value);
}

function renderTraceValue(value: unknown, key?: string): ReactNode {
  if (isSensitiveTraceKey(key)) {
    return "[已脱敏]";
  }

  if (value === null || value === undefined || value === "") {
    return EMPTY_VALUE_TEXT;
  }

  if (typeof value === "string") {
    if (key && /(_at|_time)$/.test(key)) {
      return formatDateTime(value);
    }

    return sanitizeTraceText(value);
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return EMPTY_VALUE_TEXT;
    }

    if (value.every((item) => ["string", "number", "boolean"].includes(typeof item))) {
      return value.map((item) => sanitizeTraceText(String(item))).join("，");
    }

    return (
      <div className="trace-nested-list">
        {value.map((item, index) => (
          <div className="trace-nested-item" key={index}>
            {renderTraceValue(item)}
          </div>
        ))}
      </div>
    );
  }

  if (isRecordValue(value)) {
    const entries = Object.entries(value);
    if (entries.length === 0) {
      return EMPTY_VALUE_TEXT;
    }

    return (
      <dl className="trace-nested-fields">
        {entries.map(([nestedKey, nestedValue]) => (
          <div key={nestedKey}>
            <dt>{humanizeReportKey(nestedKey)}</dt>
            <dd>{renderTraceValue(nestedValue, nestedKey)}</dd>
          </div>
        ))}
      </dl>
    );
  }

  return sanitizeTraceText(String(value));
}

function getReportItemTitle(item: Record<string, unknown>, sectionId: string, index: number) {
  if (sectionId === "competitor_findings" && isRecordValue(item.competitor)) {
    return (
      stringValue(item.competitor.name) ??
      stringValue(item.competitor.product_id) ??
      `竞品发现 ${index + 1}`
    );
  }

  if (sectionId === "recommendations") {
    return stringValue(item.recommendation) ?? `建议 ${index + 1}`;
  }

  if (sectionId === "evidence_index") {
    return stringValue(item.evidence_id) ?? `Evidence ${index + 1}`;
  }

  return null;
}

function formatScore(value: number) {
  if (value >= 0 && value <= 1) {
    return `${Math.round(value * 100)}%`;
  }

  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

function formatDuration(durationMs: number | null | undefined) {
  if (durationMs === null || durationMs === undefined) {
    return EMPTY_VALUE_TEXT;
  }

  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }

  return `${(durationMs / 1000).toFixed(1)} s`;
}

function humanizeReportKey(key: string) {
  return REPORT_FIELD_LABELS[key] ?? key.replace(/_/g, " ");
}

function isReportNotReadyError(error: unknown) {
  return isApiClientError(error) && error.code === "REPORT_NOT_READY";
}

function readErrorDetail(error: unknown, key: string) {
  if (!isApiClientError(error)) {
    return null;
  }

  const value = error.details[key];
  return typeof value === "string" ? value : null;
}

function isApiClientError(
  error: unknown
): error is { code: string; details: Record<string, unknown> } {
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    "details" in error &&
    typeof (error as { code?: unknown }).code === "string" &&
    isRecordValue((error as { details?: unknown }).details)
  );
}

function isRecordValue(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringValue(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function sanitizeTraceText(value: string) {
  return value
    .replace(/sk-[A-Za-z0-9_-]{8,}/g, "[已脱敏]")
    .replace(/AKIA[0-9A-Z]{16}/g, "[已脱敏]")
    .replace(/\b[A-Z][A-Z0-9_]*(API_KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*\b/g, "[已脱敏]")
    .replace(/bearer\s+[A-Za-z0-9._-]+/gi, "Bearer [已脱敏]")
    .replace(
      /(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*([^\s,;]+)/gi,
      "凭据=[已脱敏]"
    )
    .replace(/(^|[^\d])1[3-9]\d{9}(?!\d)/g, "$1[已脱敏]")
    .replace(/\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b/g, "[已脱敏]")
    .replace(
      /\b(account[_-]?id|acct[_-]?id|open[_-]?id|openid|union[_-]?id|unionid|user[_-]?id|userid|uid)\b\s*[:=]\s*[A-Za-z0-9._:-]{4,}/gi,
      "账号=[已脱敏]"
    )
    .replace(/(账号|账户|用户ID|用户编号)\s*[:：=]\s*[\w.\-:]{4,}/g, "账号=[已脱敏]")
    .replace(/\b(address|addr)\b\s*[:=]\s*[^,;\n]+/gi, "地址=[已脱敏]")
    .replace(/(地址|住址|收货地址)\s*[:：=]\s*[^,，;；\n]+/g, "地址=[已脱敏]");
}

function isSensitiveTraceKey(key: string | undefined) {
  return Boolean(
    key &&
    /^(api[_-]?key|apikey|token|secret|password|authorization|access[_-]?token|refresh[_-]?token|account[_-]?ids?|acct[_-]?ids?|open[_-]?ids?|openid|union[_-]?ids?|unionid|user[_-]?ids?|userid|uids?|phone|phone_number|phone_numbers|mobile|mobile_phone|address|addresses|addr)$/i.test(
      key
    )
  );
}

function FeatureList({ items, title }: { items: string[]; title: string }) {
  return (
    <section className="feature-list">
      <h5>{title}</h5>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>{EMPTY_VALUE_TEXT}</p>
      )}
    </section>
  );
}

function TagList({ emptyText, items }: { emptyText: string; items: string[] }) {
  return (
    <div className="tag-list">
      {items.length > 0 ? (
        items.map((item) => <span key={item}>{item}</span>)
      ) : (
        <span>{emptyText}</span>
      )}
    </div>
  );
}

function RiskFlagList({ riskFlags }: { riskFlags: string[] }) {
  if (riskFlags.length === 0) {
    return null;
  }

  return (
    <div className="risk-flag-list" aria-label="风险标记">
      {riskFlags.map((riskFlag) => (
        <span key={riskFlag}>{RISK_FLAG_LABELS[riskFlag] ?? riskFlag}</span>
      ))}
    </div>
  );
}

type HumanReviewOption = {
  currentValue: string | string[] | null | undefined;
  field: string;
  isList?: boolean;
  key: string;
  label: string;
  targetId: string;
  targetType: HumanFeedbackCreateRequest["target_type"];
};

function buildHumanReviewOptions(profile: ProductProfileData): HumanReviewOption[] {
  return [
    {
      currentValue: profile.product.brand,
      field: "brand",
      key: "product.brand",
      label: "品牌",
      targetId: profile.product.product_id,
      targetType: "product"
    },
    {
      currentValue: profile.product.shop_name,
      field: "shop_name",
      key: "product.shop_name",
      label: "店铺",
      targetId: profile.product.product_id,
      targetType: "product"
    },
    {
      currentValue: profile.product.product_url,
      field: "product_url",
      key: "product.product_url",
      label: "商品链接",
      targetId: profile.product.product_id,
      targetType: "product"
    },
    {
      currentValue: profile.product.tags,
      field: "tags",
      isList: true,
      key: "product.tags",
      label: "产品标签",
      targetId: profile.product.product_id,
      targetType: "product"
    },
    {
      currentValue: profile.feature_tree.cleaning_capability,
      field: "cleaning_capability",
      isList: true,
      key: "feature.cleaning_capability",
      label: "清洁能力",
      targetId: profile.feature_tree.feature_tree_id,
      targetType: "feature_tree"
    },
    {
      currentValue: profile.feature_tree.odor_control,
      field: "odor_control",
      isList: true,
      key: "feature.odor_control",
      label: "除臭能力",
      targetId: profile.feature_tree.feature_tree_id,
      targetType: "feature_tree"
    },
    {
      currentValue: profile.feature_tree.safety_features,
      field: "safety_features",
      isList: true,
      key: "feature.safety_features",
      label: "安全能力",
      targetId: profile.feature_tree.feature_tree_id,
      targetType: "feature_tree"
    },
    {
      currentValue: profile.pricing_model.price_band,
      field: "price_band",
      key: "pricing.price_band",
      label: "价格带",
      targetId: profile.pricing_model.pricing_model_id,
      targetType: "pricing_model"
    },
    {
      currentValue: profile.pricing_model.promotions,
      field: "promotions",
      isList: true,
      key: "pricing.promotions",
      label: "优惠信息",
      targetId: profile.pricing_model.pricing_model_id,
      targetType: "pricing_model"
    },
    {
      currentValue: profile.pricing_model.bundle_description,
      field: "bundle_description",
      key: "pricing.bundle_description",
      label: "套装说明",
      targetId: profile.pricing_model.pricing_model_id,
      targetType: "pricing_model"
    },
    {
      currentValue: profile.user_persona.personas,
      field: "personas",
      isList: true,
      key: "persona.personas",
      label: "目标人群",
      targetId: profile.user_persona.persona_id,
      targetType: "user_persona"
    },
    {
      currentValue: profile.user_persona.pain_points,
      field: "pain_points",
      isList: true,
      key: "persona.pain_points",
      label: "痛点",
      targetId: profile.user_persona.persona_id,
      targetType: "user_persona"
    },
    {
      currentValue: profile.user_persona.scenarios,
      field: "scenarios",
      isList: true,
      key: "persona.scenarios",
      label: "使用场景",
      targetId: profile.user_persona.persona_id,
      targetType: "user_persona"
    },
    {
      currentValue: profile.user_persona.decision_factors,
      field: "decision_factors",
      isList: true,
      key: "persona.decision_factors",
      label: "决策因素",
      targetId: profile.user_persona.persona_id,
      targetType: "user_persona"
    }
  ];
}

function splitListValue(value: string) {
  return value
    .split(/[\n,，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function uniqueSliceValues(
  slices: NonNullable<BattlefieldData["available_slices"]>,
  field: keyof NonNullable<BattlefieldData["available_slices"]>[number]
) {
  return Array.from(
    new Set(
      slices
        .map((slice) => slice[field])
        .filter((value): value is string => typeof value === "string" && value.length > 0)
    )
  );
}

function formatSelectedSlice(slice: BattlefieldSliceSelection) {
  return [
    slice.price_band ? `价格带 ${slice.price_band}` : "全部价格带",
    slice.persona ? `人群 ${slice.persona}` : "全部人群",
    slice.scenario ? `场景 ${slice.scenario}` : "全部场景"
  ].join(" / ");
}

function formatReviewValue(value: HumanReviewOption["currentValue"]) {
  if (Array.isArray(value)) {
    return value.length > 0 ? value.join("，") : EMPTY_VALUE_TEXT;
  }

  return formatNullable(value);
}

function formatNullable(value: string | null | undefined) {
  return value && value.trim().length > 0 ? value : EMPTY_VALUE_TEXT;
}

function formatTraceNullable(value: string | null | undefined) {
  return value && value.trim().length > 0 ? sanitizeTraceText(value) : EMPTY_VALUE_TEXT;
}

function formatPrice(value: number | null | undefined, currency: string) {
  if (value === null || value === undefined) {
    return EMPTY_VALUE_TEXT;
  }

  return `${currency} ${value.toFixed(0)}`;
}

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return EMPTY_VALUE_TEXT;
  }

  return value.replace("T", " ").replace(/Z$/, " UTC");
}

function validateTaskForm(form: TaskInputForm): FieldErrors {
  const errors: FieldErrors = {};

  if (!form.target_product_name.trim()) {
    errors.target_product_name = "请输入目标产品名称。";
  }

  if (!form.category.trim()) {
    errors.category = "请选择品类。";
  }

  if (!form.subcategory.trim()) {
    errors.subcategory = "请选择子类。";
  }

  return errors;
}

function toTaskCreateRequest(form: TaskInputForm): TaskCreateRequest {
  return {
    category: form.category.trim(),
    data_source_mode: form.data_source_mode,
    research_text: normalizeOptionalText(form.research_text),
    subcategory: form.subcategory.trim(),
    target_product_name: form.target_product_name.trim(),
    target_product_url: normalizeOptionalText(form.target_product_url)
  };
}

function normalizeOptionalText(value: string) {
  const stripped = value.trim();
  return stripped.length > 0 ? stripped : null;
}
