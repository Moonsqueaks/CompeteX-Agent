import "@xyflow/react/dist/style.css";
import "./App.css";

import { QueryClient, QueryClientProvider, useMutation, useQuery } from "@tanstack/react-query";
import {
  Background,
  Controls,
  MarkerType,
  Position,
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
import { TermHint } from "./TermHint";
import type { TermKey } from "./termExplanations";

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
type DisplayStatus = components["schemas"]["DisplayStatus"];
type OverviewActionRecommendation = components["schemas"]["OverviewActionRecommendation"];
type OverviewData = components["schemas"]["OverviewData"];
type OverviewFinding = components["schemas"]["OverviewFinding"];
type OverviewKeyCompetitor = components["schemas"]["OverviewKeyCompetitor"];
type ProductProfileData = components["schemas"]["ProductProfileData"];
type ProductProfileComparison = components["schemas"]["ProductProfileComparison"];
type ProfileComparisonDimension = components["schemas"]["ProfileComparisonDimension"];
type ProfileComparisonProduct = components["schemas"]["ProfileComparisonProduct"];
type ProfileComparisonSlot = components["schemas"]["ProfileComparisonSlot"];
type TargetComparisonStatus = components["schemas"]["TargetComparisonStatus"];
type BattlefieldData = components["schemas"]["BattlefieldData"];
type BattlefieldEvidenceCard = components["schemas"]["BattlefieldEvidenceCard"];
type BattlefieldExplanationSegment = components["schemas"]["BattlefieldExplanationSegment"];
type BattlefieldGraphEdge = components["schemas"]["BattlefieldGraphEdge"];
type BattlefieldGraphNode = components["schemas"]["BattlefieldGraphNode"];
type BattlefieldKeyRelation = components["schemas"]["BattlefieldKeyRelation"];
type BattlefieldExplanationKey = keyof components["schemas"]["BattlefieldFourPartExplanation"];
type BattlefieldAvailableSlice = NonNullable<BattlefieldData["available_slices"]>[number];
type BattlefieldSliceSelection = components["schemas"]["BattlefieldSliceSelection"];
type HumanFeedbackCreateRequest = components["schemas"]["HumanFeedbackCreateRequest"];
type HumanFeedbackCreateResponse = components["schemas"]["HumanFeedbackCreateResponse"];
type ReportData = components["schemas"]["ReportData"];
type ReportSection = components["schemas"]["ReportSection"];
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
type TraceEvidenceChain = components["schemas"]["TraceEvidenceChain"];
type TraceQualityRecord = components["schemas"]["TraceQualityRecord"];
type TracePromptPreview = components["schemas"]["TracePromptPreview"];
type DataSourceMode = components["schemas"]["DataSourceMode"];
type TaskApiClient = Pick<ApiClient, "get" | "post"> &
  Partial<Pick<ApiClient, "download" | "getBattlefield" | "getOverview">>;

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
const OVERVIEW_RELATIONSHIP_LABELS: Record<string, string> = {
  content_seeding_competition: "内容种草竞争",
  head_to_head: "正面竞争",
  low_price_interception: "低价拦截",
  scenario_substitute: "场景替代",
  trust_suppression: "信任压制"
};
const OVERVIEW_THREAT_LABELS: Record<string, string> = {
  high_score_needs_review: "高分需复核",
  high_threat: "高威胁",
  low_threat: "低威胁",
  medium_threat: "中威胁"
};
const OVERVIEW_ACTION_PRIORITY_LABELS: Record<string, string> = {
  p0_immediate: "P0 立即处理",
  p1_current_iteration: "P1 本轮优化",
  p2_follow_up_validation: "P2 后续验证"
};
const OVERVIEW_RESPONSIBILITY_LABELS: Record<string, string> = {
  content_expression: "内容表达",
  evidence_research: "证据补研",
  pricing_strategy: "价格策略",
  product_feature: "产品功能"
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
  context_match: "上下文匹配度",
  decision_stage_impact: "决策阶段影响力",
  demand_substitutability: "需求替代性",
  evidence_confidence: "证据置信度",
  market_signal_strength: "市场信号强度"
};
const SCORE_BREAKDOWN_DESCRIPTIONS: Record<string, string> = {
  context_match: "衡量竞品和目标产品是否处在同一价格、人群与使用场景切片。",
  decision_stage_impact: "衡量竞品会影响用户认知、信任或下单决策的阶段强度。",
  demand_substitutability: "衡量竞品是否满足同一核心需求，用户是否可能二选一。",
  evidence_confidence: "衡量当前评分背后的证据完整度、来源和可追溯性。",
  market_signal_strength: "衡量价格、内容、评价或销量等市场信号的支撑强度。"
};
const BATTLEFIELD_FLOW_NODE_WIDTH = 190;
const BATTLEFIELD_FLOW_NODE_HEIGHT = 98;
const SCORE_BREAKDOWN_TERM_KEYS: Record<string, TermKey> = {
  context_match: "context_match",
  decision_stage_impact: "decision_stage_impact",
  demand_substitutability: "demand_substitutability",
  evidence_confidence: "evidence_confidence",
  market_signal_strength: "market_signal_strength"
};
const FOUR_PART_EXPLANATION_KEYS: BattlefieldExplanationKey[] = [
  "why_competitor",
  "strength",
  "decision_stage_impact",
  "response_suggestion"
];
const FOUR_PART_EXPLANATION_LABELS: Record<BattlefieldExplanationKey, string> = {
  decision_stage_impact: "影响哪个决策阶段",
  response_suggestion: "应对建议",
  strength: "强在哪",
  why_competitor: "为什么是竞品"
};
const CONFIDENCE_LABELS: Record<string, string> = {
  high: "高",
  low: "低",
  medium: "中",
  unknown: "未知"
};
const PROFILE_COMPARISON_SLOT_ORDER: ProfileComparisonSlot[] = [
  "target",
  "highest_threat_direct_competitor",
  "highest_threat_alternative"
];
const PROFILE_COMPARISON_SLOT_LABELS: Record<ProfileComparisonSlot, string> = {
  highest_threat_alternative: "最高威胁替代竞品",
  highest_threat_direct_competitor: "最高威胁直接竞品",
  target: "目标产品"
};
const PROFILE_COMPARISON_EMPTY_LABELS: Record<ProfileComparisonSlot, string> = {
  highest_threat_alternative: "暂无可用于对比的替代竞品",
  highest_threat_direct_competitor: "暂无可用于对比的直接竞品",
  target: "暂无目标产品"
};
const PROFILE_COMPARISON_STATUS_LABELS: Record<TargetComparisonStatus, string> = {
  advantage: "优势",
  insufficient_evidence: "证据不足",
  parity: "持平",
  weakness: "短板"
};
const AGENT_LABELS: Record<string, string> = {
  analysis_agent: "分析智能体",
  collection_agent: "采集智能体",
  human: "人工复核",
  orchestrator: "流程编排",
  qa_agent: "质检智能体",
  writer_agent: "报告智能体"
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
const TRACE_TARGET_TYPE_LABELS: Record<string, string> = {
  claim: "结论",
  competition_edge: "竞争关系",
  evidence: "证据",
  feature_tree: "功能树",
  pricing_model: "价格模型",
  product: "产品",
  product_profile: "产品画像",
  user_persona: "用户人群"
};
const TRACE_DIFF_STATUS_LABELS: Record<string, string> = {
  applied: "已应用",
  partial: "部分处理",
  recomputed: "已重算",
  repaired: "已修复",
  resolved: "已解决",
  updated: "已更新"
};
const CLAIM_STATUS_LABELS: Record<string, string> = {
  accepted: "已采纳",
  draft: "草稿",
  needs_review: "需复核",
  rejected: "不采纳"
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
const TRACE_TAB_LABELS = {
  evidence_chain: "证据链",
  quality_records: "质检记录",
  agent_process: "智能体过程",
  diff_records: "差异记录"
} as const;
type TraceTabKey = keyof typeof TRACE_TAB_LABELS;
const REPORT_SECTION_KEYS = [
  "conclusion_summary",
  "competitive_landscape_judgment",
  "core_competitor_analysis",
  "user_decision_chain_analysis",
  "target_opportunities_and_risks",
  "product_strategy_recommendations",
  "evidence_quality_appendix",
  "analysis_process_appendix"
] as const;
const REPORT_FIELD_LABELS: Record<string, string> = {
  access_time: "访问时间",
  analysis_recompute: "分析智能体重算",
  basis_edge_id: "依据竞争边",
  brand: "品牌",
  claim_ids: "Claim 索引",
  claims: "Claims",
  collection_repair: "采集智能体修复",
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
  qa_agent: "质检智能体",
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
  analysis_process_appendix: "分析流程与系统能力附录",
  competitive_landscape_judgment: "竞争格局判断",
  conclusion_summary: "结论摘要",
  core_competitor_analysis: "核心竞品拆解",
  evidence_quality_appendix: "证据与质检附录",
  product_strategy_recommendations: "产品策略建议",
  target_opportunities_and_risks: "目标产品机会与风险",
  user_decision_chain_analysis: "用户决策链分析"
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
    path: "/overview",
    label: "竞争态势总览",
    title: "竞争态势总览",
    eyebrow: "决策工作台",
    summary: "围绕当前任务查看结论、状态、关键竞品和下钻入口。",
    sections: ["核心判断", "关键竞品", "行动建议", "证据风险"]
  },
  {
    path: "/profile",
    label: "产品与竞品画像",
    title: "产品与竞品画像",
    eyebrow: "横向画像",
    summary: "查看目标产品与核心竞品的基础信息、价格模型、人群和证据状态。",
    sections: ["目标产品", "核心竞品", "价格模型", "用户人群"]
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
    sections: ["结论摘要", "核心竞品拆解", "产品策略建议", "证据与质检附录"]
  },
  {
    path: "/trace",
    label: "证据与过程追踪",
    title: "证据与过程追踪",
    eyebrow: "证据链路",
    summary: "展示证据链、质检打回、运行记录、工具调用和差异记录。",
    sections: ["证据链", "质检记录", "运行记录", "差异记录"]
  }
];
const NAV_ROUTES = ROUTES.filter((route) => route.path !== "/");

function getRoute(pathname: string) {
  return ROUTES.find((route) => route.path === pathname) ?? ROUTES[0];
}

function navigateTo(path: string) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new Event("popstate"));
}

function routePathForTask(
  path: string,
  taskId: string | null,
  query: Record<string, string | null | undefined> = {}
) {
  const params = new URLSearchParams();
  if (taskId && path !== "/") {
    params.set("task_id", taskId);
  }
  for (const [key, value] of Object.entries(query)) {
    if (value) {
      params.set(key, value);
    }
  }
  const queryString = params.toString();

  if (!queryString) {
    return path;
  }

  return `${path}?${queryString}`;
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
          {NAV_ROUTES.map((route) => {
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
            {currentRoute.path === "/overview"
              ? "总览数据就绪"
              : currentRoute.path === "/trace"
                ? "追踪数据就绪"
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
        ) : currentRoute.path === "/overview" ? (
          <OverviewPage apiClient={taskApiClient} route={currentRoute} taskId={currentTaskId} />
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

function OverviewPage({
  apiClient,
  route,
  taskId
}: {
  apiClient: TaskApiClient;
  route: AppRoute;
  taskId: string | null;
}) {
  const [selectedSlice, setSelectedSlice] = useState<BattlefieldSliceSelection>(
    getSliceSelectionFromLocation
  );

  const overviewQuery = useQuery({
    enabled: Boolean(taskId),
    queryFn: () => getOverviewData(apiClient, taskId ?? "", selectedSlice),
    queryKey: [
      "task-overview",
      taskId,
      selectedSlice.price_band,
      selectedSlice.persona,
      selectedSlice.scenario
    ],
    retry: false
  });
  const sliceOptionsQuery = useQuery({
    enabled: Boolean(taskId),
    queryFn: () => getBattlefieldData(apiClient, taskId ?? "", { include_all_relations: true }),
    queryKey: ["overview-slice-options", taskId],
    retry: false
  });
  const overviewState = toQueryRequestState(overviewQuery);
  const overview = overviewQuery.data;
  const availableSlices = Array.isArray(sliceOptionsQuery.data?.available_slices)
    ? sliceOptionsQuery.data.available_slices
    : [];

  return (
    <section className="page-surface" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">{route.eyebrow}</p>
        <h3 id="page-title">{route.title}</h3>
        <p>{route.summary}</p>
      </div>

      {taskId ? (
        <div className="overview-workbench" aria-label="竞争态势总览首屏">
          <RequestStateMessage
            className="overview-state-message"
            loadingText="正在读取竞争态势总览"
            onRetry={() => void overviewQuery.refetch()}
            state={overviewState}
          />

          <OverviewSliceControls
            availableSlices={availableSlices}
            onChange={setSelectedSlice}
            selection={selectedSlice}
          />

          {overview ? <OverviewContent overview={overview} taskId={taskId} /> : null}
        </div>
      ) : (
        <div className="empty-task-state" role="status">
          暂无任务 ID。请先从任务输入页创建任务，或访问 /overview?task_id=&lt;task_id&gt; 恢复总览。
        </div>
      )}
    </section>
  );
}

function OverviewSliceControls({
  availableSlices,
  onChange,
  selection
}: {
  availableSlices: BattlefieldAvailableSlice[];
  onChange: (selection: BattlefieldSliceSelection) => void;
  selection: BattlefieldSliceSelection;
}) {
  const priceBands = uniqueOverviewSliceValues(availableSlices, "price_band");
  const personas = uniqueOverviewSliceValues(availableSlices, "persona");
  const scenarios = uniqueOverviewSliceValues(availableSlices, "scenario");

  const updateSelection = (field: keyof BattlefieldSliceSelection, value: string) => {
    onChange({
      ...selection,
      [field]: value || null
    });
  };

  return (
    <section className="overview-slice-panel" aria-label="总览切片控制">
      <div>
        <p className="section-kicker">动态切片</p>
        <h4>
          按价格带、人群和使用场景刷新总览判断
          <TermHint term="dynamic_slice" />
        </h4>
      </div>
      <div className="overview-slice-controls">
        <label>
          <span>价格带切片</span>
          <select
            className="field-control"
            onChange={(event) => updateSelection("price_band", event.target.value)}
            value={selection.price_band ?? ""}
          >
            <option value="">全部价格带</option>
            {priceBands.map((priceBand) => (
              <option key={priceBand} value={priceBand}>
                {priceBand}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>人群切片</span>
          <select
            className="field-control"
            onChange={(event) => updateSelection("persona", event.target.value)}
            value={selection.persona ?? ""}
          >
            <option value="">全部人群</option>
            {personas.map((persona) => (
              <option key={persona} value={persona}>
                {persona}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>使用场景切片</span>
          <select
            className="field-control"
            onChange={(event) => updateSelection("scenario", event.target.value)}
            value={selection.scenario ?? ""}
          >
            <option value="">全部场景</option>
            {scenarios.map((scenario) => (
              <option key={scenario} value={scenario}>
                {scenario}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}

function OverviewContent({ overview, taskId }: { overview: OverviewData; taskId: string }) {
  const primaryCompetitors = overview.key_competitors ?? [];
  const topAction = overview.action_recommendations?.[0] ?? null;
  const topRisk = overview.risk_points?.[0] ?? null;
  const scope = overview.analysis_scope;

  return (
    <div className="overview-content">
      <section className="overview-hero" aria-label="核心判断">
        <div className="overview-hero-main">
          <p className="section-kicker">核心判断</p>
          <h4>{overview.one_sentence_judgment.content}</h4>
          <p className="overview-scope-note">{scope.scope_notice}</p>
          <div className="overview-status-strip" aria-label="决策可用状态">
            <OverviewStatusItem
              label="判断强度"
              status={overview.judgment_strength}
              term="judgment_strength"
            />
            <OverviewStatusItem label="决策可用性" status={overview.decision_usability} />
            <div className="overview-status-item">
              <span>分析范围</span>
              <strong>{scope.product_count} 个产品</strong>
              <small>
                {scope.sku_count} 个 SKU / {scope.evidence_count} 条证据
              </small>
            </div>
          </div>
        </div>

        <aside className="overview-hero-aside" aria-label="首要行动建议">
          <p className="section-kicker">首要行动建议</p>
          {topAction ? (
            <OverviewActionSummary action={topAction} />
          ) : (
            <p className="muted-copy">暂无可执行建议</p>
          )}
          <OverviewRiskAlert risk={topRisk} />
        </aside>
      </section>

      <section className="overview-main-grid" aria-label="关键竞品与下钻入口">
        <div className="overview-competitors">
          <div className="section-heading">
            <p className="section-kicker">关键竞品</p>
            <h4>本轮最值得先看的竞争关系</h4>
          </div>
          {primaryCompetitors.length > 0 ? (
            <div className="overview-competitor-list">
              {primaryCompetitors.map((competitor) => (
                <OverviewCompetitorCard
                  competitor={competitor}
                  key={competitor.product_id}
                  taskId={taskId}
                />
              ))}
            </div>
          ) : (
            <p className="muted-copy">暂无关键竞品</p>
          )}
        </div>

        <aside className="overview-side-stack">
          <OverviewFindingPanel
            emptyText="暂无机会点"
            findings={overview.opportunities ?? []}
            title="机会点"
          />
          <OverviewFindingPanel
            emptyText="暂无新增风险点"
            findings={overview.risk_points ?? []}
            title="风险点"
          />
          <div className="overview-drilldown-panel">
            <p className="section-kicker">继续下钻</p>
            <h4>从总览进入关系图谱</h4>
            <p>保留当前 task_id，进入竞争图谱后可按价格带、人群和场景继续切片验证本页判断。</p>
            <button
              className="secondary-action"
              onClick={() => navigateTo(routePathForTask("/battlefield", taskId))}
              type="button"
            >
              查看完整竞争图谱
            </button>
          </div>
        </aside>
      </section>
    </div>
  );
}

function OverviewStatusItem({
  label,
  status,
  term
}: {
  label: string;
  status: DisplayStatus;
  term?: TermKey;
}) {
  return (
    <div className="overview-status-item">
      <span>
        <span>{label}</span>
        {term ? <TermHint term={term} /> : null}
      </span>
      <strong>{status.label}</strong>
      <small>{status.reason}</small>
    </div>
  );
}

function OverviewActionSummary({ action }: { action: OverviewActionRecommendation }) {
  return (
    <div className="overview-action-summary">
      <div className="overview-chip-row">
        <span>{OVERVIEW_ACTION_PRIORITY_LABELS[action.priority] ?? action.priority}</span>
        <span>
          {OVERVIEW_RESPONSIBILITY_LABELS[action.responsibility_type] ?? action.responsibility_type}
        </span>
      </div>
      <h5>{action.title}</h5>
      <p>{action.description}</p>
      {action.expected_impact ? <small>{action.expected_impact}</small> : null}
    </div>
  );
}

function OverviewRiskAlert({ risk }: { risk: OverviewFinding | null }) {
  return (
    <div
      className={risk ? "overview-risk-alert" : "overview-risk-alert overview-risk-ok"}
      role="status"
    >
      <span>证据风险提醒</span>
      {risk ? (
        <>
          <strong>{risk.title}</strong>
          <p>{risk.description}</p>
          <RiskFlagList riskFlags={risk.risk_flags ?? []} />
        </>
      ) : (
        <p>暂无阻断决策的证据风险。</p>
      )}
    </div>
  );
}

function OverviewFindingPanel({
  emptyText,
  findings,
  title
}: {
  emptyText: string;
  findings: OverviewFinding[];
  title: string;
}) {
  return (
    <section className="overview-finding-panel">
      <p className="section-kicker">{title}</p>
      {findings.length > 0 ? (
        <div className="overview-finding-list">
          {findings.map((finding) => (
            <article key={finding.finding_id}>
              <h5>{finding.title}</h5>
              <p>{finding.description}</p>
              <RiskFlagList riskFlags={finding.risk_flags ?? []} />
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">{emptyText}</p>
      )}
    </section>
  );
}

function OverviewCompetitorCard({
  competitor,
  taskId
}: {
  competitor: OverviewKeyCompetitor;
  taskId: string;
}) {
  const battlefieldRef = competitor.drilldown_refs?.find(
    (reference) => reference.reference_type === "battlefield"
  );
  const edgeId = battlefieldRef?.target_id;

  return (
    <article className="overview-competitor-card">
      <OverviewCompetitorImage competitor={competitor} />
      <div className="overview-competitor-body">
        <div className="overview-competitor-heading">
          <p>{competitor.brand ?? competitor.sku_id ?? "关键竞品"}</p>
          <h5>{competitor.product_name}</h5>
        </div>
        <dl className="overview-competitor-meta">
          <div>
            <dt>关系标签</dt>
            <dd>
              {OVERVIEW_RELATIONSHIP_LABELS[competitor.relationship_label] ??
                competitor.relationship_label}
            </dd>
          </div>
          <div>
            <dt>
              威胁等级
              <TermHint term="threat_level" />
            </dt>
            <dd>{OVERVIEW_THREAT_LABELS[competitor.threat_level] ?? competitor.threat_level}</dd>
          </div>
          <div>
            <dt>
              证据可信度
              <TermHint term="evidence_credibility" />
            </dt>
            <dd>{competitor.evidence_credibility.label}</dd>
          </div>
        </dl>
        <p className="overview-competitor-reason">{competitor.inclusion_reason}</p>
        <button
          className="secondary-action overview-drilldown-button"
          onClick={() => navigateTo(routePathForTask("/battlefield", taskId, { edge_id: edgeId }))}
          type="button"
        >
          查看竞争关系
        </button>
      </div>
    </article>
  );
}

function OverviewCompetitorImage({ competitor }: { competitor: OverviewKeyCompetitor }) {
  const [hasImageError, setHasImageError] = useState(false);
  const imagePath = competitor.primary_image_path;

  if (!imagePath || hasImageError) {
    return (
      <div className="overview-thumb overview-thumb-missing" role="img" aria-label="暂无可靠图片">
        暂无可靠图片
      </div>
    );
  }

  return (
    <div className="overview-thumb">
      <img
        alt={`${competitor.product_name} 缩略图`}
        onError={() => setHasImageError(true)}
        src={imagePath}
      />
    </div>
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
            <p>页面刷新后会从 URL 中的 task_id 恢复任务，并同步轮询任务状态与追踪数据。</p>
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
                  任务执行失败，请保留当前 task_id 并查看过程追踪或日志定位原因。
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
          暂无任务 ID。请先从任务输入页创建任务，或访问 /trace?task_id=&lt;task_id&gt; 恢复追踪。
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
        onClick={() => navigateTo(routePathForTask("/overview", taskId))}
        type="button"
      >
        查看总览
      </button>
      <button
        className="secondary-action"
        onClick={() => navigateTo(routePathForTask("/profile", taskId))}
        type="button"
      >
        查看画像对比
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
  const [activeTab, setActiveTab] = useState<TraceTabKey>(
    normalizeTraceTab(trace.process_view?.default_tab)
  );

  return (
    <div className="trace-content">
      <section className="trace-summary-card">
        <div className="section-heading">
          <p className="section-kicker">过程追踪</p>
          <h4>追踪概览</h4>
        </div>
        <dl className="summary-list trace-summary-list">
          <div>
            <dt>追踪视图</dt>
            <dd>{trace.trace_view_id}</dd>
          </div>
          <div>
            <dt>流程状态</dt>
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
            <dt>运行记录</dt>
            <dd>{trace.agent_runs?.length ?? 0}</dd>
          </div>
          <div>
            <dt>模型用量</dt>
            <dd>{totalTokens}</dd>
          </div>
        </dl>
      </section>

      <TraceTabs activeTab={activeTab} onChange={setActiveTab} trace={trace} />

      {activeTab === "evidence_chain" ? (
        <TraceEvidenceChains chains={trace.evidence_chains ?? []} />
      ) : null}
      {activeTab === "quality_records" ? (
        <TraceQualityRecords
          records={trace.quality_records ?? []}
          reviews={trace.qa_reviews ?? []}
        />
      ) : null}
      {activeTab === "agent_process" ? (
        <TraceAgentProcess flow={flow} totalTokens={totalTokens} trace={trace} />
      ) : null}
      {activeTab === "diff_records" ? <TraceDiffView diffs={trace.diffs ?? []} /> : null}
    </div>
  );
}

function TraceTabs({
  activeTab,
  onChange,
  trace
}: {
  activeTab: TraceTabKey;
  onChange: (tab: TraceTabKey) => void;
  trace: TraceData;
}) {
  const tabCounts: Record<TraceTabKey, number> = {
    agent_process: trace.process_view?.agent_run_count ?? trace.agent_runs?.length ?? 0,
    diff_records: trace.diffs?.length ?? 0,
    evidence_chain: trace.evidence_chains?.length ?? 0,
    quality_records: trace.quality_records?.length ?? trace.qa_reviews?.length ?? 0
  };

  return (
    <div className="trace-tabs" aria-label="证据与过程追踪分区" role="tablist">
      {(Object.keys(TRACE_TAB_LABELS) as TraceTabKey[]).map((tabKey) => (
        <button
          aria-selected={activeTab === tabKey}
          className={activeTab === tabKey ? "trace-tab trace-tab-active" : "trace-tab"}
          key={tabKey}
          onClick={() => onChange(tabKey)}
          role="tab"
          type="button"
        >
          <span>{TRACE_TAB_LABELS[tabKey]}</span>
          <strong>{tabCounts[tabKey]}</strong>
        </button>
      ))}
    </div>
  );
}

function TraceEvidenceChains({ chains }: { chains: TraceEvidenceChain[] }) {
  return (
    <section className="trace-panel" aria-label="证据链">
      <div className="section-heading">
        <p className="section-kicker">证据链</p>
        <h4>按结论组织证据链</h4>
      </div>
      {chains.length > 0 ? (
        <div className="trace-list">
          {chains.map((chain) => (
            <article className="trace-list-item" key={chain.chain_id}>
              <div className="trace-item-heading">
                <h5>{sanitizeTraceText(chain.claim_content)}</h5>
                <span className={`trace-status trace-status-${chain.claim_status}`}>
                  {CLAIM_STATUS_LABELS[chain.claim_status] ?? chain.claim_status}
                </span>
              </div>
              <dl className="trace-fields trace-evidence-chain-fields">
                <div>
                  <dt>判断强度</dt>
                  <dd>{formatTraceConfidence(chain.confidence)}</dd>
                </div>
                <div>
                  <dt>推断标记</dt>
                  <dd>{chain.is_inference ? "分析判断" : "事实摘录"}</dd>
                </div>
                <div>
                  <dt>报告章节</dt>
                  <dd>{formatTraceList(chain.report_section_ids ?? [])}</dd>
                </div>
                <div>
                  <dt>证据数量</dt>
                  <dd>{chain.evidence_items?.length ?? 0}</dd>
                </div>
              </dl>
              <RiskFlagList riskFlags={chain.risk_flags ?? []} />
              <TraceEvidenceItemList evidenceItems={chain.evidence_items ?? []} />
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>
      )}
    </section>
  );
}

function TraceEvidenceItemList({
  evidenceItems
}: {
  evidenceItems: NonNullable<TraceEvidenceChain["evidence_items"]>;
}) {
  if (evidenceItems.length === 0) {
    return <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>;
  }

  return (
    <div className="trace-evidence-items" aria-label="结论引用证据">
      {evidenceItems.map((evidence) => (
        <article className="trace-evidence-item" key={evidence.evidence_id}>
          <div className="trace-item-heading">
            <h6>{evidence.evidence_id}</h6>
            <span>{CONFIDENCE_LABELS[evidence.confidence_level] ?? evidence.confidence_level}</span>
          </div>
          <p>{sanitizeTraceText(evidence.content_summary)}</p>
          <dl className="trace-fields trace-token-fields">
            <div>
              <dt>来源类型</dt>
              <dd>{evidence.source_type}</dd>
            </div>
            <div>
              <dt>访问时间</dt>
              <dd>{evidence.access_time_status}</dd>
            </div>
            <div>
              <dt>局限性</dt>
              <dd>{sanitizeTraceText(evidence.limitations)}</dd>
            </div>
            <div>
              <dt>来源链接</dt>
              <dd>{evidence.source_url ?? EMPTY_VALUE_TEXT}</dd>
            </div>
          </dl>
          <RiskFlagList riskFlags={evidence.risk_flags ?? []} />
        </article>
      ))}
    </div>
  );
}

function TraceQualityRecords({
  records,
  reviews
}: {
  records: TraceQualityRecord[];
  reviews: ReviewTask[];
}) {
  if (records.length === 0) {
    return <TraceQaReviews reviews={reviews} />;
  }

  const attentionCount = records.filter((record) => record.needs_attention).length;
  const resolvedCount = records.filter(
    (record) => record.resolved && !record.needs_attention
  ).length;
  const pendingCount = records.length - attentionCount - resolvedCount;

  return (
    <section className="trace-panel" aria-label="质检记录">
      <div className="section-heading">
        <p className="section-kicker">质检记录</p>
        <h4>质检打回与处理状态</h4>
      </div>
      <div className="trace-quality-summary" aria-label="质检状态汇总">
        <span className="trace-quality-summary-item trace-quality-summary-attention">
          <strong>{attentionCount}</strong>
          <small>仍需关注</small>
        </span>
        <span className="trace-quality-summary-item trace-quality-summary-resolved">
          <strong>{resolvedCount}</strong>
          <small>已解决</small>
        </span>
        <span className="trace-quality-summary-item trace-quality-summary-pending">
          <strong>{pendingCount}</strong>
          <small>待处理或豁免</small>
        </span>
      </div>
      <div className="trace-list">
        {records.map((record) => {
          const attention = getTraceQualityAttention(record);

          return (
            <article
              className={`trace-list-item trace-quality-item trace-quality-item-${attention.kind}`}
              key={record.quality_record_id}
            >
              <div className="trace-item-heading">
                <h5>{sanitizeTraceText(record.check_item)}</h5>
                <span className={`trace-status ${attention.className}`}>{attention.label}</span>
              </div>
              <p>{sanitizeTraceText(record.issue_summary)}</p>
              <p className="trace-quality-result">
                <strong>处理结论</strong>
                {sanitizeTraceText(record.action_result)}
              </p>
              <dl className="trace-fields trace-quality-fields">
                <div>
                  <dt>问题等级</dt>
                  <dd>{REVIEW_SEVERITY_LABELS[record.severity] ?? record.severity}</dd>
                </div>
                <div>
                  <dt>是否仍需关注</dt>
                  <dd>{record.needs_attention ? "是，需要继续处理" : "否，当前已闭环"}</dd>
                </div>
                <div>
                  <dt>质检打回对象</dt>
                  <dd>{formatTraceTarget(record.target_type, record.target_id)}</dd>
                </div>
                <div>
                  <dt>打回目标</dt>
                  <dd>
                    {record.target_agent
                      ? (AGENT_LABELS[record.target_agent] ?? record.target_agent)
                      : EMPTY_VALUE_TEXT}
                  </dd>
                </div>
                <div>
                  <dt>处理要求</dt>
                  <dd>{sanitizeTraceText(record.required_action)}</dd>
                </div>
                <div>
                  <dt>质检状态</dt>
                  <dd>{REVIEW_STATUS_LABELS[record.status] ?? record.status}</dd>
                </div>
                <div>
                  <dt>问题编码</dt>
                  <dd>{sanitizeTraceText(record.issue_code)}</dd>
                </div>
                <div>
                  <dt>关联结论</dt>
                  <dd>{formatTraceList(record.related_claim_ids ?? [])}</dd>
                </div>
                <div>
                  <dt>关联证据</dt>
                  <dd>{formatTraceList(record.evidence_ids ?? [])}</dd>
                </div>
              </dl>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function TraceAgentProcess({
  flow,
  totalTokens,
  trace
}: {
  flow: ReturnType<typeof toTraceFlowElements>;
  totalTokens: number;
  trace: TraceData;
}) {
  return (
    <section className="trace-process-section" aria-label="智能体过程">
      <div className="trace-layout">
        <section className="trace-graph-panel" aria-label="流程图状态">
          <div className="section-heading">
            <p className="section-kicker">智能体过程</p>
            <h4>协作流程图</h4>
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

        <aside className="trace-side-panel" aria-label="追踪数据摘要">
          <TraceAgentRuns runs={trace.agent_runs ?? []} />
          <details className="trace-technical-details">
            <summary>技术详情</summary>
            <TraceToolCalls toolCalls={trace.tool_calls ?? []} />
            <TraceTokenUsage tokenUsage={trace.token_usage ?? []} totalTokens={totalTokens} />
            <TracePromptPreviews prompts={trace.prompt_previews ?? []} />
          </details>
        </aside>
      </div>
    </section>
  );
}

function TraceAgentRuns({ runs }: { runs: AgentRunLog[] }) {
  return (
    <section className="trace-panel" aria-label="运行记录列表">
      <div className="section-heading">
        <p className="section-kicker">运行记录</p>
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
                  <dt>运行编号</dt>
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
    <section className="trace-panel" aria-label="工具调用列表">
      <div className="section-heading">
        <p className="section-kicker">工具调用</p>
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
                  <dt>运行编号</dt>
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

function TraceTokenUsage({
  tokenUsage,
  totalTokens
}: {
  tokenUsage: TokenUsageLog[];
  totalTokens?: number;
}) {
  const total = totalTokens ?? tokenUsage.reduce((sum, usage) => sum + usage.total_tokens, 0);

  return (
    <section className="trace-panel" aria-label="模型用量列表">
      <div className="section-heading">
        <p className="section-kicker">模型用量</p>
        <h4>模型用量</h4>
      </div>
      <div className="trace-token-total">总计 {total} 个计量单位</div>
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
                  <dt>输入计量</dt>
                  <dd>{usage.prompt_tokens}</dd>
                </div>
                <div>
                  <dt>输出计量</dt>
                  <dd>{usage.completion_tokens}</dd>
                </div>
                <div>
                  <dt>合计</dt>
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
    <section className="trace-panel" aria-label="质检记录列表">
      <div className="section-heading">
        <p className="section-kicker">质检记录</p>
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
                  <dt>问题编码</dt>
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

function TraceDiffView({ diffs }: { diffs: TraceDiff[] }) {
  return (
    <section className="trace-panel trace-diff-panel" aria-label="差异记录">
      <div className="section-heading">
        <p className="section-kicker">差异记录</p>
        <h4>业务变化影响</h4>
      </div>
      {diffs.length > 0 ? (
        <div className="trace-list">
          {diffs.map((diff) => {
            const source = getTraceDiffSource(diff.source);

            return (
              <article
                className={`trace-list-item trace-diff-item trace-diff-item-${source.kind}`}
                key={diff.diff_id}
              >
                <div className="trace-item-heading">
                  <h5>{source.label}</h5>
                  <span className={`trace-status ${source.statusClass}`}>
                    {TRACE_DIFF_STATUS_LABELS[diff.status] ?? sanitizeTraceText(diff.status)}
                  </span>
                </div>
                <div className="trace-diff-meta" aria-label="差异来源与对象">
                  <span>
                    <strong>变化来源</strong>
                    {source.description}
                  </span>
                  <span>
                    <strong>影响对象</strong>
                    {formatTraceTarget(diff.target_type, diff.target_id)}
                  </span>
                  <span>
                    <strong>关联打回</strong>
                    {formatRevisionMessageList(diff.revision_message_ids ?? [])}
                  </span>
                </div>
                <p className="trace-business-impact">
                  <strong>业务影响</strong>
                  {sanitizeTraceText(diff.business_impact)}
                </p>
                <details className="trace-diff-details">
                  <summary>查看结构化前后值</summary>
                  <dl className="trace-fields">
                    <div>
                      <dt>原始记录来源</dt>
                      <dd>{sanitizeTraceText(diff.source)}</dd>
                    </div>
                    <div>
                      <dt>差异编号</dt>
                      <dd>{sanitizeTraceText(diff.diff_id)}</dd>
                    </div>
                  </dl>
                  <div className="trace-diff-grid">
                    <div>
                      <span>变更前</span>
                      {renderTraceValue(diff.before ?? {})}
                    </div>
                    <div>
                      <span>变更后</span>
                      {renderTraceValue(diff.after ?? {})}
                    </div>
                  </div>
                </details>
              </article>
            );
          })}
        </div>
      ) : (
        <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>
      )}
    </section>
  );
}

function TracePromptPreviews({ prompts }: { prompts: TracePromptPreview[] }) {
  return (
    <section className="trace-panel trace-prompt-panel" aria-label="提示摘要">
      <div className="section-heading">
        <p className="section-kicker">提示摘要</p>
        <h4>提示摘要</h4>
      </div>
      {prompts.length > 0 ? (
        <div className="trace-list">
          {prompts.map((prompt) => (
            <details className="trace-prompt-details" key={prompt.preview_id}>
              <summary>
                <span>{formatPromptPreviewTitle(prompt.title)}</span>
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
                <ProfileComparisonWorkbench profile={profile} taskId={taskId} />
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

function ProfileComparisonWorkbench({
  profile,
  taskId
}: {
  profile: ProductProfileData;
  taskId: string;
}) {
  const comparison = profile.horizontal_comparison ?? createTargetOnlyProfileComparison(profile);
  const productsBySlot = new Map(
    (comparison.compared_products ?? []).map((product) => [product.slot, product])
  );
  const orderedSlots = PROFILE_COMPARISON_SLOT_ORDER;
  const visibleProducts = orderedSlots.map((slot) => productsBySlot.get(slot) ?? null);

  return (
    <article className="profile-panel profile-panel-wide profile-comparison-workbench">
      <div className="section-heading">
        <p className="section-kicker">横向对比</p>
        <h4>目标产品与核心竞品对比</h4>
      </div>
      <div className="profile-comparison-grid" role="table" aria-label="目标产品与核心竞品横向对比">
        {orderedSlots.map((slot, index) => (
          <ProfileComparisonColumn key={slot} product={visibleProducts[index]} slot={slot} />
        ))}
      </div>
      <div className="profile-comparison-dimensions">
        {(comparison.dimensions ?? []).map((dimension) => (
          <ProfileComparisonDimensionRow
            dimension={dimension}
            key={dimension.dimension_key}
            products={visibleProducts}
            taskId={taskId}
          />
        ))}
      </div>
    </article>
  );
}

function ProfileComparisonColumn({
  product,
  slot
}: {
  product: ProfileComparisonProduct | null;
  slot: ProfileComparisonSlot;
}) {
  return (
    <section
      className={product ? "profile-comparison-column" : "profile-comparison-column is-empty"}
      role="columnheader"
    >
      <ProfileComparisonImage product={product} slot={slot} />
      <div>
        <p>{PROFILE_COMPARISON_SLOT_LABELS[slot]}</p>
        <h5>{product?.product_name ?? PROFILE_COMPARISON_EMPTY_LABELS[slot]}</h5>
        {product ? <small>{formatNullable(product.brand)}</small> : <small>未发现可靠关系</small>}
      </div>
    </section>
  );
}

function ProfileComparisonImage({
  product,
  slot
}: {
  product: ProfileComparisonProduct | null;
  slot: ProfileComparisonSlot;
}) {
  const [hasImageError, setHasImageError] = useState(false);
  const imagePath = product?.primary_image_path;

  if (!imagePath || hasImageError) {
    return (
      <div
        className="profile-comparison-image profile-comparison-image-missing"
        role="img"
        aria-label={product ? "暂无可靠图片" : PROFILE_COMPARISON_EMPTY_LABELS[slot]}
      >
        {product ? "暂无可靠图片" : "暂无竞品"}
      </div>
    );
  }

  return (
    <div className="profile-comparison-image">
      <img
        alt={`${product.product_name} 缩略图`}
        onError={() => setHasImageError(true)}
        src={imagePath}
      />
    </div>
  );
}

function ProfileComparisonDimensionRow({
  dimension,
  products,
  taskId
}: {
  dimension: ProfileComparisonDimension;
  products: Array<ProfileComparisonProduct | null>;
  taskId: string;
}) {
  const valuesByProduct = new Map(
    (dimension.values ?? []).map((value) => [value.product_id, value.value])
  );
  const evidenceIds = dimension.evidence_ids ?? [];

  return (
    <section className="profile-comparison-dimension" role="row">
      <div className="profile-comparison-dimension-heading">
        <div>
          <p>{dimension.dimension_label}</p>
          <span className={`profile-status-pill profile-status-${dimension.target_status}`}>
            {PROFILE_COMPARISON_STATUS_LABELS[dimension.target_status]}
          </span>
        </div>
        <p>{dimension.status_reason}</p>
        <button
          className="inline-link-button"
          onClick={() =>
            navigateTo(
              routePathForTask("/trace", taskId, {
                evidence_id: evidenceIds[0],
                tab: "evidence"
              })
            )
          }
          type="button"
        >
          查看依据
        </button>
      </div>
      <div className="profile-comparison-values">
        {products.map((product, index) => (
          <div className="profile-comparison-value" key={product?.product_id ?? index}>
            {product
              ? (valuesByProduct.get(product.product_id) ?? EMPTY_VALUE_TEXT)
              : EMPTY_VALUE_TEXT}
          </div>
        ))}
      </div>
      <RiskFlagList riskFlags={dimension.risk_flags ?? []} />
    </section>
  );
}

function ProductBasicsCard({ profile }: { profile: ProductProfileData }) {
  const product = profile.product;

  return (
    <article className="profile-panel">
      <div className="section-heading">
        <p className="section-kicker">目标产品</p>
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
        <p className="section-kicker">能力拆解</p>
        <h4>功能能力树</h4>
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
        <p className="section-kicker">价格模型</p>
        <h4>价格与证据</h4>
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
        <p className="section-kicker">用户理解</p>
        <h4>用户人群画像</h4>
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
        <p className="section-kicker">证据摘要</p>
        <h4>证据摘要</h4>
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
  const [includeAllRelations, setIncludeAllRelations] = useState(false);
  const battlefieldQuery = useQuery({
    enabled: Boolean(taskId),
    queryFn: () =>
      getBattlefieldData(apiClient, taskId ?? "", {
        ...compactSliceQuery(selectedSlice),
        ...(includeAllRelations ? { include_all_relations: true } : {})
      }),
    queryKey: [
      "battlefield",
      taskId,
      selectedSlice.price_band,
      selectedSlice.persona,
      selectedSlice.scenario,
      includeAllRelations
    ],
    placeholderData: (previousData) => previousData,
    retry: false
  });
  const battlefieldState = toQueryRequestState(battlefieldQuery);
  const battlefield = battlefieldQuery.data;
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);
  const visibleGraphEdges = useMemo(
    () => (battlefield ? getVisibleBattlefieldEdges(battlefield) : []),
    [battlefield]
  );
  const visibleGraphNodes = useMemo(
    () => (battlefield ? getVisibleBattlefieldNodes(battlefield, visibleGraphEdges) : []),
    [battlefield, visibleGraphEdges]
  );
  const graph = useMemo(
    () => toBattlefieldFlowElements(visibleGraphNodes, visibleGraphEdges),
    [visibleGraphEdges, visibleGraphNodes]
  );
  const selectedEdge =
    visibleGraphEdges.find((edge) => edge.edge_id === selectedEdgeId) ??
    visibleGraphEdges[0] ??
    null;

  function updateSlice(field: keyof BattlefieldSliceSelection, value: string) {
    setSelectedEdgeId(null);
    setIncludeAllRelations(false);
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

  function updateRelationScope(nextIncludeAllRelations: boolean) {
    setSelectedEdgeId(null);
    setIncludeAllRelations(nextIncludeAllRelations);
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
                  includeAllRelations={includeAllRelations}
                  selectedSlice={selectedSlice}
                  setIncludeAllRelations={updateRelationScope}
                  updateSlice={updateSlice}
                />
                <KeyRelationsPanel
                  onSelectEdge={setSelectedEdgeId}
                  relations={battlefield.key_relations ?? []}
                  selectedEdgeId={selectedEdge?.edge_id ?? null}
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
  includeAllRelations,
  selectedSlice,
  setIncludeAllRelations,
  updateSlice
}: {
  data: BattlefieldData;
  includeAllRelations: boolean;
  selectedSlice: BattlefieldSliceSelection;
  setIncludeAllRelations: (includeAllRelations: boolean) => void;
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
      {data.relation_filter ? (
        <label className="relation-toggle">
          <input
            checked={includeAllRelations}
            disabled={!data.relation_filter.can_expand_all && !includeAllRelations}
            onChange={(event) => setIncludeAllRelations(event.target.checked)}
            type="checkbox"
          />
          <span>展开全部关系</span>
          <small>
            当前显示 {data.relation_filter.visible_relation_count} /{" "}
            {data.relation_filter.total_relation_count} 条
          </small>
        </label>
      ) : null}
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

function KeyRelationsPanel({
  onSelectEdge,
  relations,
  selectedEdgeId
}: {
  onSelectEdge: (edgeId: string) => void;
  relations: BattlefieldKeyRelation[];
  selectedEdgeId: string | null;
}) {
  return (
    <section className="battlefield-panel key-relations-panel" aria-label="关键竞争关系">
      <div className="section-heading">
        <p className="section-kicker">关键关系</p>
        <h4>默认阅读层</h4>
      </div>
      {relations.length > 0 ? (
        <div className="key-relation-list">
          {relations.map((relation) => (
            <article
              className={
                relation.edge_id === selectedEdgeId
                  ? "key-relation-card key-relation-card-active"
                  : "key-relation-card"
              }
              key={relation.edge_id}
            >
              <div className="key-relation-heading">
                <div>
                  <p>{relation.competitor_brand ?? relation.competitor_product_id}</p>
                  <h5>{relation.competitor_product_name}</h5>
                </div>
                {!relation.is_default_visible ? <span>扩展关系</span> : null}
              </div>
              <dl className="key-relation-meta">
                <div>
                  <dt>关系标签</dt>
                  <dd>
                    {OVERVIEW_RELATIONSHIP_LABELS[relation.relationship_label] ??
                      relation.relationship_label}
                  </dd>
                </div>
                <div>
                  <dt>
                    威胁等级
                    <TermHint term="threat_level" />
                  </dt>
                  <dd>{OVERVIEW_THREAT_LABELS[relation.threat_level] ?? relation.threat_level}</dd>
                </div>
                <div>
                  <dt>
                    证据可信状态
                    <TermHint term="evidence_credibility" />
                  </dt>
                  <dd>{relation.evidence_credibility.label}</dd>
                </div>
              </dl>
              <p>{relation.inclusion_reason}</p>
              <small>{relation.relationship_label_explanation}</small>
              <button
                className="secondary-action"
                onClick={() => onSelectEdge(relation.edge_id)}
                type="button"
              >
                查看评分拆解
              </button>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-copy">暂无关键关系</p>
      )}
    </section>
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
  const [activeBasisSelection, setActiveBasisSelection] = useState<{
    edgeId: string;
    key: BattlefieldExplanationKey;
  } | null>(null);
  const selectedRelation =
    selectedEdge && data.key_relations
      ? (data.key_relations.find((relation) => relation.edge_id === selectedEdge.edge_id) ?? null)
      : null;
  const edgeEvidenceCards = selectedEdge
    ? (data.evidence_cards ?? []).filter((card) =>
        (selectedEdge.evidence_ids ?? []).includes(card.evidence_id)
      )
    : [];
  const activeBasisKey =
    selectedEdge && activeBasisSelection?.edgeId === selectedEdge.edge_id
      ? activeBasisSelection.key
      : null;
  const activeBasis =
    selectedRelation && activeBasisKey
      ? {
          label: FOUR_PART_EXPLANATION_LABELS[activeBasisKey],
          segment: selectedRelation.four_part_explanation[activeBasisKey]
        }
      : null;

  return (
    <aside className="battlefield-side" aria-label="竞争边详情">
      <section className="battlefield-panel">
        <div className="section-heading">
          <p className="section-kicker">关系详情</p>
          <h4>竞争边解释</h4>
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
            <FourPartExplanationList
              activeKey={activeBasisKey}
              onSelectBasis={(key) =>
                setActiveBasisSelection({
                  edgeId: selectedEdge.edge_id,
                  key
                })
              }
              relation={selectedRelation}
            />
            {activeBasis ? (
              <ExplanationBasisPanel
                evidenceCards={
                  edgeEvidenceCards.length > 0 ? edgeEvidenceCards : data.evidence_cards
                }
                label={activeBasis.label}
                segment={activeBasis.segment}
              />
            ) : null}
            <ScoreBreakdownList edge={selectedEdge} />
            <FeatureList title="评分计算说明" items={selectedEdge.score_explanations ?? []} />
            <RiskFlagList riskFlags={selectedEdge.risk_flags ?? []} />
          </>
        ) : (
          <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>
        )}
      </section>

      <section className="battlefield-panel">
        <div className="section-heading">
          <p className="section-kicker">结论依据</p>
          <h4>结论与证据</h4>
        </div>
        {selectedEdge?.claim_refs?.length ? (
          <div className="claim-list">
            {selectedEdge.claim_refs.map((claim) => (
              <article className="claim-card" key={claim.claim_id}>
                <p className="evidence-id">{claim.claim_id}</p>
                <p>{claim.content}</p>
                <small>
                  置信度 {Math.round(claim.confidence * 100)}% / 状态 {claim.status} / 证据{" "}
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
          <p className="section-kicker">证据</p>
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

function FourPartExplanationList({
  activeKey,
  onSelectBasis,
  relation
}: {
  activeKey: BattlefieldExplanationKey | null;
  onSelectBasis: (key: BattlefieldExplanationKey) => void;
  relation: BattlefieldKeyRelation | null;
}) {
  if (!relation) {
    return <p className="muted-copy">暂无可追溯的四段式解释</p>;
  }

  return (
    <div className="edge-explanation-list" aria-label="四段式竞争解释">
      {FOUR_PART_EXPLANATION_KEYS.map((key) => {
        const segment = relation.four_part_explanation[key];
        const label = FOUR_PART_EXPLANATION_LABELS[key];

        return (
          <article
            className={
              key === activeKey
                ? "edge-explanation-card edge-explanation-card-active"
                : "edge-explanation-card"
            }
            key={key}
          >
            <div className="edge-explanation-heading">
              <h5>{label}</h5>
              {segment.is_analysis_suggestion ? <span>分析建议</span> : null}
            </div>
            <p>{segment.text}</p>
            <button className="secondary-action" onClick={() => onSelectBasis(key)} type="button">
              查看依据
            </button>
          </article>
        );
      })}
    </div>
  );
}

function ExplanationBasisPanel({
  evidenceCards,
  label,
  segment
}: {
  evidenceCards?: BattlefieldEvidenceCard[];
  label: string;
  segment: BattlefieldExplanationSegment;
}) {
  const claimIds = segment.claim_ids ?? [];
  const evidenceIds = segment.evidence_ids ?? [];
  const relatedEvidenceCards =
    evidenceIds.length > 0
      ? (evidenceCards ?? []).filter((card) => evidenceIds.includes(card.evidence_id))
      : (evidenceCards ?? []);

  return (
    <div className="edge-basis-panel" aria-label="解释依据详情">
      <div>
        <h5>{label}的依据</h5>
        <dl className="edge-basis-meta">
          <div>
            <dt>相关结论</dt>
            <dd>{claimIds.length > 0 ? claimIds.join("，") : EMPTY_VALUE_TEXT}</dd>
          </div>
          <div>
            <dt>相关证据</dt>
            <dd>{evidenceIds.length > 0 ? evidenceIds.join("，") : EMPTY_VALUE_TEXT}</dd>
          </div>
        </dl>
      </div>
      <RiskFlagList riskFlags={segment.risk_flags ?? []} />
      <EvidenceCardList cards={relatedEvidenceCards} />
    </div>
  );
}

function ScoreBreakdownList({ edge }: { edge: BattlefieldGraphEdge }) {
  return (
    <div className="score-breakdown" aria-label="评分拆解">
      {Object.entries(edge.score_breakdown).map(([key, value]) => (
        <div className="score-row" key={key}>
          <span>
            <span>{SCORE_BREAKDOWN_LABELS[key] ?? key}</span>
            {SCORE_BREAKDOWN_TERM_KEYS[key] ? (
              <TermHint term={SCORE_BREAKDOWN_TERM_KEYS[key]} />
            ) : null}
          </span>
          <meter max={1} min={0} value={value} />
          <strong>{Math.round(value * 100)}</strong>
          <p>{SCORE_BREAKDOWN_DESCRIPTIONS[key] ?? "该维度解释来自后端评分结果。"}</p>
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
              <dt>
                置信度
                <TermHint term="evidence_confidence" />
              </dt>
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
    <section className="battlefield-panel" aria-label="质检打回记录">
      <div className="section-heading">
        <p className="section-kicker">质检</p>
        <div className="term-heading">
          <h4>质检打回记录</h4>
          <TermHint term="quality_review" />
        </div>
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
          当前任务还没有进入 completed 状态，网页报告会在报告生成完成后开放。
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
  const [printView, setPrintView] = useState(false);
  useEffect(() => {
    if (printView) {
      document.body.dataset.reportView = "print";
    } else if (document.body.dataset.reportView === "print") {
      delete document.body.dataset.reportView;
    }

    return () => {
      if (document.body.dataset.reportView === "print") {
        delete document.body.dataset.reportView;
      }
    };
  }, [printView]);
  const wordExportMutation = useMutation({
    mutationFn: async () => {
      const fileName = `${taskId}_${report.report_id}.docx`;
      if (!apiClient.download) {
        throw new Error("当前 API 客户端不支持 Word 下载。");
      }
      const blob = await apiClient.download(`/tasks/${encodeURIComponent(taskId)}/report/docx`);
      triggerFileDownload(blob, fileName);
      return { fileName };
    }
  });
  const reportSections = getOrderedReportSections(report);

  return (
    <div className={printView ? "report-workbench report-print-mode" : "report-workbench"}>
      <div className="report-toolbar" aria-label="报告工作台工具栏">
        <dl className="summary-list report-meta">
          <div>
            <dt>报告编号</dt>
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
            disabled={wordExportMutation.isPending}
            onClick={() => wordExportMutation.mutate()}
            type="button"
          >
            {wordExportMutation.isPending ? "下载中" : "下载 Word 报告"}
          </button>
          <button className="secondary-action" onClick={() => window.print()} type="button">
            打印或另存 PDF
          </button>
          <button
            className="secondary-action"
            onClick={() => setPrintView((current) => !current)}
            type="button"
          >
            {printView ? "返回工作台视图" : "切换打印视图"}
          </button>
          {wordExportMutation.isSuccess ? (
            <div className="review-success" role="status">
              Word 报告已下载：{wordExportMutation.data.fileName}
            </div>
          ) : null}
          {wordExportMutation.isError ? (
            <RequestStateMessage
              className="review-error"
              state={createErrorState(wordExportMutation.error)}
            />
          ) : null}
        </div>
      </div>

      <section className="report-static-graph" aria-label="静态图谱摘要">
        <div>
          <p className="section-kicker">静态图谱摘要</p>
          <h4>核心竞争关系摘要</h4>
          <p>打印视图保留核心关系、证据和质检附录，便于离线评审。</p>
        </div>
        <span>{reportSections.length} 个章节</span>
      </section>

      <div className="report-section-grid" aria-label="报告章节">
        {reportSections.map((section) => (
          <ReportSectionCard key={section.section_id} section={section} taskId={taskId} />
        ))}
      </div>
    </div>
  );
}

function ReportSectionCard({ section, taskId }: { section: ReportSection; taskId: string }) {
  return (
    <article className="report-section-card">
      <div className="section-heading">
        <p className="section-kicker">{sanitizeTraceText(section.section_id)}</p>
        <h4>{sanitizeTraceText(section.title)}</h4>
      </div>
      <p className="report-section-summary">{sanitizeTraceText(section.summary)}</p>
      <ReportItemList items={section.items ?? []} sectionId={section.section_id} />
      <ReportReferenceStrip section={section} taskId={taskId} />
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
        <div className="report-item" key={`${sectionId}-${index}`}>
          <ReportItemTitle item={item} index={index} sectionId={sectionId} />
          <dl>{renderReportItemFields(item, sectionId)}</dl>
        </div>
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

function ReportReferenceStrip({ section, taskId }: { section: ReportSection; taskId: string }) {
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
      <div className="report-drilldown-actions" aria-label={`${section.title}下钻入口`}>
        <button
          className="inline-link-button"
          disabled={evidenceIds.length === 0}
          onClick={() =>
            navigateTo(
              routePathForTask("/trace", taskId, {
                evidence_id: evidenceIds[0],
                tab: "evidence"
              })
            )
          }
          type="button"
        >
          查看依据
        </button>
        <button
          className="inline-link-button"
          disabled={claimIds.length === 0}
          onClick={() =>
            navigateTo(
              routePathForTask("/trace", taskId, {
                claim_id: claimIds[0],
                tab: "process"
              })
            )
          }
          type="button"
        >
          查看过程
        </button>
      </div>
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
    <aside className="human-review-panel" aria-label="修正画像">
      <div className="section-heading">
        <p className="section-kicker">受控复核</p>
        <h4>修正画像</h4>
      </div>
      <p className="review-boundary">
        仅允许修正画像结构化字段；标记不采纳与补充证据备注也通过受控反馈保存 before/after/reason。
      </p>
      <div className="review-action-strip" aria-label="可用人工复核动作">
        <span>修正画像</span>
        <span>标记不采纳</span>
        <span>补充证据备注</span>
      </div>

      <form onSubmit={submitReview}>
        <label className="field-label" htmlFor="review-field">
          画像字段
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
          修正后的值
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
          修正原因
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
            修正画像已提交，相关结果已刷新。
          </div>
        ) : null}

        <button className="primary-action" disabled={feedbackMutation.isPending} type="submit">
          {feedbackMutation.isPending ? "提交中" : "提交修正画像"}
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
      navigateTo(`/overview?task_id=${encodeURIComponent(response.task_id)}`);
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
              <dd>竞争态势总览</dd>
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

function getSliceSelectionFromLocation(): BattlefieldSliceSelection {
  const params = new URLSearchParams(window.location.search);
  return {
    persona: normalizeOptionalText(params.get("persona") ?? ""),
    price_band: normalizeOptionalText(params.get("price_band") ?? ""),
    scenario: normalizeOptionalText(params.get("scenario") ?? "")
  };
}

function getOverviewData(
  apiClient: TaskApiClient,
  taskId: string,
  selection: BattlefieldSliceSelection
) {
  const query = compactSliceQuery(selection);
  if (apiClient.getOverview) {
    return apiClient.getOverview(taskId, query);
  }

  return apiClient.get<OverviewData>(
    `/tasks/${encodeURIComponent(taskId)}/overview`,
    Object.keys(query).length > 0 ? { query } : undefined
  );
}

function getBattlefieldData(
  apiClient: TaskApiClient,
  taskId: string,
  query: {
    include_all_relations?: boolean;
    persona?: string;
    price_band?: string;
    scenario?: string;
  } = {}
) {
  if (apiClient.getBattlefield) {
    return apiClient.getBattlefield(taskId, query);
  }

  return apiClient.get<BattlefieldData>(`/tasks/${encodeURIComponent(taskId)}/battlefield`, {
    query
  });
}

function compactSliceQuery(selection: BattlefieldSliceSelection) {
  const query: Record<string, string> = {};
  if (selection.price_band) {
    query.price_band = selection.price_band;
  }
  if (selection.persona) {
    query.persona = selection.persona;
  }
  if (selection.scenario) {
    query.scenario = selection.scenario;
  }
  return query;
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

function getVisibleBattlefieldEdges(data: BattlefieldData) {
  const relationIds = new Set((data.key_relations ?? []).map((relation) => relation.edge_id));
  const graphEdges = data.graph_edges ?? [];
  if (relationIds.size === 0) {
    return graphEdges;
  }

  return graphEdges.filter((edge) => relationIds.has(edge.edge_id));
}

function getVisibleBattlefieldNodes(
  data: BattlefieldData,
  visibleGraphEdges: BattlefieldGraphEdge[]
) {
  const visibleNodeIds = new Set(
    visibleGraphEdges.flatMap((edge) => [edge.source, edge.target, edge.target_product_id])
  );
  const graphNodes = data.graph_nodes ?? [];
  if (visibleNodeIds.size === 0) {
    return graphNodes;
  }

  return graphNodes.filter((node) => visibleNodeIds.has(node.node_id));
}

function toBattlefieldFlowElements(
  graphNodes: BattlefieldGraphNode[],
  graphEdges: BattlefieldGraphEdge[]
): {
  edges: FlowEdge[];
  nodes: FlowNode[];
} {
  const nodes = graphNodes.map((node, index) => toBattlefieldFlowNode(node, index));
  const edges = graphEdges.map((edge) => toBattlefieldFlowEdge(edge));

  return { edges, nodes };
}

function toBattlefieldFlowNode(node: BattlefieldGraphNode, index: number): FlowNode {
  const isTarget = node.role === "target";
  const competitorIndex = Math.max(0, index - 1);
  const competitorColumn = competitorIndex % 2;
  const competitorRow = Math.floor(competitorIndex / 2);
  const width = BATTLEFIELD_FLOW_NODE_WIDTH;
  const height = BATTLEFIELD_FLOW_NODE_HEIGHT;

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
    handles: [
      {
        height: 1,
        position: Position.Left,
        type: "target",
        width: 1,
        x: 0,
        y: height / 2
      },
      {
        height: 1,
        position: Position.Right,
        type: "source",
        width: 1,
        x: width,
        y: height / 2
      }
    ],
    height,
    id: node.node_id,
    initialHeight: height,
    initialWidth: width,
    sourcePosition: Position.Right,
    position: isTarget
      ? { x: 20, y: 180 }
      : { x: 360 + competitorColumn * 260, y: 40 + competitorRow * 140 },
    targetPosition: Position.Left,
    width,
    type: "default"
  };
}

function toBattlefieldFlowEdge(edge: BattlefieldGraphEdge): FlowEdge {
  return {
    animated: edge.risk_status === "at_risk",
    data: { edgeId: edge.edge_id },
    id: edge.edge_id,
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
          <span>{node.node_type === "agent" ? "智能体" : "终态"}</span>
          <strong>{formatTraceNodeLabel(node)}</strong>
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
    label: formatTraceEdgeLabel(edge.label),
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

function formatTraceNodeLabel(node: TraceDagNode) {
  if (node.agent_name) {
    return AGENT_LABELS[node.agent_name] ?? node.agent_name;
  }
  if (node.node_id === "failed") {
    return "失败结束";
  }
  if (node.node_id === "end") {
    return "完成结束";
  }
  return node.label;
}

function formatTraceEdgeLabel(label: string) {
  return label
    .replace(/Collection Agent/g, "采集智能体")
    .replace(/Analysis Agent/g, "分析智能体")
    .replace(/QA Agent/g, "质检智能体")
    .replace(/Writer Agent/g, "报告智能体")
    .replace(/Collection/g, "采集")
    .replace(/Analysis/g, "分析")
    .replace(/Writer/g, "报告")
    .replace(/QA passed/g, "质检通过")
    .replace(/QA/g, "质检")
    .replace(/->/g, "→");
}

function createTargetOnlyProfileComparison(profile: ProductProfileData): ProductProfileComparison {
  const evidenceIds = profile.product.evidence_ids ?? [];
  return {
    compared_products: [
      {
        brand: profile.product.brand,
        primary_image_path: profile.product.primary_image_path,
        product_id: profile.product.product_id,
        product_name: profile.product.name,
        product_url: profile.product.product_url,
        slot: "target"
      }
    ],
    dimensions: [
      {
        dimension_key: "price_band",
        dimension_label: "价格带",
        evidence_ids: profile.pricing_model.evidence_ids ?? evidenceIds,
        risk_flags: profile.pricing_model.risk_flags ?? [],
        status_reason: "仅有目标产品画像，竞品对比需要等待关系筛选结果。",
        target_status: "insufficient_evidence",
        trace_refs: [`profile:${profile.task_id}:price_band`],
        values: [
          {
            evidence_ids: profile.pricing_model.evidence_ids ?? evidenceIds,
            product_id: profile.product.product_id,
            value: profile.pricing_model.price_band || EMPTY_VALUE_TEXT
          }
        ]
      },
      {
        dimension_key: "core_selling_points",
        dimension_label: "核心卖点",
        evidence_ids: profile.feature_tree.evidence_ids ?? evidenceIds,
        risk_flags: profile.feature_tree.risk_flags ?? [],
        status_reason: "仅展示目标产品卖点，缺少竞品侧结构化对比。",
        target_status: "insufficient_evidence",
        trace_refs: [`profile:${profile.task_id}:core_selling_points`],
        values: [
          {
            evidence_ids: profile.feature_tree.evidence_ids ?? evidenceIds,
            product_id: profile.product.product_id,
            value:
              [
                ...(profile.feature_tree.cleaning_capability ?? []),
                ...(profile.feature_tree.odor_control ?? []),
                ...(profile.feature_tree.safety_features ?? []),
                ...(profile.feature_tree.smart_features ?? [])
              ]
                .slice(0, 4)
                .join("、") || EMPTY_VALUE_TEXT
          }
        ]
      },
      {
        dimension_key: "persona",
        dimension_label: "主要人群",
        evidence_ids: profile.user_persona.evidence_ids ?? evidenceIds,
        risk_flags: profile.user_persona.risk_flags ?? [],
        status_reason: "人群画像来自目标产品证据，竞品人群对照暂不可用。",
        target_status: "insufficient_evidence",
        trace_refs: [`profile:${profile.task_id}:persona`],
        values: [
          {
            evidence_ids: profile.user_persona.evidence_ids ?? evidenceIds,
            product_id: profile.product.product_id,
            value: (profile.user_persona.personas ?? []).join("、") || EMPTY_VALUE_TEXT
          }
        ]
      },
      {
        dimension_key: "scenario",
        dimension_label: "使用场景",
        evidence_ids: profile.user_persona.evidence_ids ?? evidenceIds,
        risk_flags: profile.user_persona.risk_flags ?? [],
        status_reason: "使用场景来自目标产品画像，竞品场景对照暂不可用。",
        target_status: "insufficient_evidence",
        trace_refs: [`profile:${profile.task_id}:scenario`],
        values: [
          {
            evidence_ids: profile.user_persona.evidence_ids ?? evidenceIds,
            product_id: profile.product.product_id,
            value: (profile.user_persona.scenarios ?? []).join("、") || EMPTY_VALUE_TEXT
          }
        ]
      },
      {
        dimension_key: "evidence_credibility",
        dimension_label: "证据可信状态",
        evidence_ids: evidenceIds,
        risk_flags: profile.pricing_evidence.risk_flags ?? [],
        status_reason: "未获得竞品横向证据，当前仅能查看目标产品证据状态。",
        target_status: "insufficient_evidence",
        trace_refs: [`profile:${profile.task_id}:evidence_credibility`],
        values: [
          {
            evidence_ids: evidenceIds,
            product_id: profile.product.product_id,
            value:
              profile.pricing_evidence.access_time_status === "available" ? "谨慎参考" : "证据不足"
          }
        ]
      }
    ],
    target_product_id: profile.product.product_id
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

function triggerFileDownload(blob: Blob, fileName: string) {
  if (
    typeof document === "undefined" ||
    (typeof navigator !== "undefined" && navigator.userAgent.includes("jsdom")) ||
    typeof URL === "undefined" ||
    typeof URL.createObjectURL !== "function"
  ) {
    return;
  }

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  anchor.style.display = "none";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
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
        <dt>{safeReportFieldLabel(key)}</dt>
        <dd>{renderReportValue(value, key)}</dd>
      </div>
    ));
}

function renderReportValue(value: unknown, key?: string): ReactNode {
  if (isSensitiveTraceKey(key)) {
    return "[已脱敏]";
  }

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
    return key === "access_time" || key === "generated_at"
      ? formatDateTime(value)
      : sanitizeTraceText(value);
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return EMPTY_VALUE_TEXT;
    }

    if (value.every((item) => ["string", "number", "boolean"].includes(typeof item))) {
      return value.map((item) => sanitizeTraceText(String(item))).join("，");
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
            <dt>{safeReportFieldLabel(nestedKey)}</dt>
            <dd>{renderReportValue(nestedValue, nestedKey)}</dd>
          </div>
        ))}
      </dl>
    );
  }

  return sanitizeTraceText(String(value));
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
    const title =
      stringValue(item.competitor.name) ??
      stringValue(item.competitor.product_id) ??
      `竞品发现 ${index + 1}`;
    return sanitizeTraceText(title);
  }

  if (sectionId === "recommendations") {
    return sanitizeTraceText(stringValue(item.recommendation) ?? `建议 ${index + 1}`);
  }

  if (sectionId === "evidence_index") {
    return sanitizeTraceText(stringValue(item.evidence_id) ?? `Evidence ${index + 1}`);
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

function safeReportFieldLabel(key: string) {
  return isSensitiveTraceKey(key) ? "敏感字段" : sanitizeTraceText(humanizeReportKey(key));
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

function uniqueOverviewSliceValues(
  slices: BattlefieldAvailableSlice[],
  field: keyof BattlefieldAvailableSlice
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

function formatTraceConfidence(value: number) {
  return `${Math.round(value * 100)}%`;
}

function formatTraceList(values: string[]) {
  return values.length > 0 ? values.join("，") : EMPTY_VALUE_TEXT;
}

function formatTraceTarget(targetType: string, targetId: string) {
  const label = TRACE_TARGET_TYPE_LABELS[targetType] ?? targetType;

  return `${label} / ${sanitizeTraceText(targetId)}`;
}

function formatRevisionMessageList(values: string[]) {
  return values.length > 0 ? values.join("，") : "无打回消息";
}

function formatPromptPreviewTitle(title: string) {
  const sanitized = sanitizeTraceText(title);
  const match = sanitized.match(/^(Collection|Analysis|QA|Writer|Orchestrator|Human)\s+prompt$/i);

  if (!match) {
    return sanitized
      .replace(/\bprompt\b/gi, "提示摘要")
      .replace(/\bAgent\b/g, "智能体")
      .replace(/\bTrace\b/g, "过程追踪");
  }

  const agentKey = `${match[1].toLowerCase()}_agent`;
  const agentLabel = AGENT_LABELS[agentKey] ?? match[1];

  return `${agentLabel}提示摘要`;
}

function getTraceQualityAttention(record: TraceQualityRecord) {
  if (record.needs_attention) {
    return {
      className: "trace-status-attention",
      kind: "attention",
      label: "仍需关注"
    };
  }

  if (record.resolved) {
    return {
      className: "trace-status-resolved",
      kind: "resolved",
      label: "已解决"
    };
  }

  return {
    className: "trace-status-pending",
    kind: "pending",
    label: "待处理"
  };
}

function getTraceDiffSource(source: string) {
  if (source.includes("human_feedback")) {
    return {
      description: "人工复核提交的受控结构化修正。",
      kind: "human-feedback",
      label: "人工修正差异",
      statusClass: "trace-status-resolved"
    };
  }

  if (source.includes("analysis_agent_recompute")) {
    return {
      description: "QA 打回后触发分析重算，影响结论或竞争分。",
      kind: "qa-recompute",
      label: "QA 打回后的分析重算",
      statusClass: "trace-status-requires_revision"
    };
  }

  if (source.includes("collection_agent_repair")) {
    return {
      description: "QA 打回后补齐或降级证据，影响结论可采纳程度。",
      kind: "qa-repair",
      label: "QA 打回修复",
      statusClass: "trace-status-requires_revision"
    };
  }

  return {
    description: "流程中记录的结构化变化。",
    kind: "process",
    label: "流程差异",
    statusClass: "trace-status-pending"
  };
}

function normalizeTraceTab(value: string | null | undefined): TraceTabKey {
  if (value === "quality_record") {
    return "quality_records";
  }
  if (value === "agent_process" || value === "process") {
    return "agent_process";
  }
  if (value === "diff_record" || value === "diff") {
    return "diff_records";
  }
  if (value && value in TRACE_TAB_LABELS) {
    return value as TraceTabKey;
  }
  return "evidence_chain";
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
