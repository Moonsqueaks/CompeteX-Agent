import {
  Alert,
  Button,
  Card,
  Collapse,
  Descriptions,
  Empty,
  Progress,
  Space,
  Steps,
  Tabs,
  Tag,
  Timeline,
  Typography
} from "antd";
import { Activity, ArrowLeft, CheckCircle2, Clock, Cpu, FileText, ShieldAlert } from "lucide-react";
import { type ReactNode, useEffect, useMemo, useRef, useState } from "react";
import {
  Background,
  Controls,
  MarkerType,
  ReactFlow,
  type Edge as FlowEdge,
  type Node as FlowNode
} from "@xyflow/react";

import { navigateTo, routePathForTask, type AppRoute } from "../app/routes";
import {
  RequestStateMessage,
  createErrorState,
  createIdleState,
  createLoadingState,
  createSuccessState
} from "../api";
import type { ApiClient, ApiRequestState, components } from "../api";
import {
  ACCESS_TIME_STATUS_LABELS,
  AGENT_LABELS,
  CLAIM_STATUS_LABELS,
  CONFIDENCE_DETAIL_LABELS,
  CONFIDENCE_LABELS,
  REPORT_FIELD_LABELS,
  REPORT_SECTION_FALLBACK_TITLES,
  REVIEW_SEVERITY_LABELS,
  REVIEW_STATUS_LABELS,
  RUN_STATUS_LABELS,
  SOURCE_TYPE_LABELS,
  TASK_STATUS_LABELS,
  TECHNICAL_MODEL_LABELS,
  TOOL_NAME_LABELS,
  TOOL_STATUS_LABELS,
  TRACE_DIFF_STATUS_LABELS,
  TRACE_NODE_STATUS_LABELS,
  TRACE_RISK_FLAG_LABELS as RISK_FLAG_LABELS,
  TRACE_TAB_LABELS,
  TRACE_TARGET_TYPE_LABELS,
  WORKFLOW_STATUS_LABELS
} from "../domain/labels";
import { MetricHint } from "../components/MetricHint";
import { PageEmptyState } from "../components/PageEmptyState";
import { PageLoadingState } from "../components/PageLoadingState";
import { RiskFlagList } from "../components/RiskFlagList";
import { isRunningTaskStatus, useTaskStatus, useTrace } from "../hooks/useTrace";
import {
  formatDateTime,
  formatDuration,
  isInternalIdentifier,
  isRecordValue,
  stringValue
} from "../utils/format";
import { isSensitiveTraceKey, sanitizeTraceText } from "../utils/sanitize";

const { Paragraph, Text, Title } = Typography;

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
type TaskApiClient = Pick<ApiClient, "get" | "post"> &
  Partial<Pick<ApiClient, "download" | "getBattlefield" | "getOverview">>;

type TraceTabKey = "evidence_chain" | "agent_process" | "quality_records" | "diff_records";

const EMPTY_VALUE_TEXT = "暂无可靠数据";
const FAILED_TASK_STATUSES = new Set<TaskStatus>(["failed", "partial_failed"]);
const TASK_STATUS_STEPS: { key: TaskStatus; title: string }[] = [
  { key: "created", title: "任务创建" },
  { key: "collecting", title: "数据采集" },
  { key: "analyzing", title: "深度分析" },
  { key: "reviewing", title: "QA 质检" },
  { key: "writing", title: "报告生成" },
  { key: "completed", title: "分析完成" }
];

export function TracePage({
  apiClient,
  route,
  taskId
}: {
  apiClient: TaskApiClient;
  route: AppRoute;
  taskId: string | null;
}) {
  const completedTraceRefreshRef = useRef<string | null>(null);
  const taskStatusQuery = useTaskStatus(apiClient, taskId);
  const taskStatus = taskStatusQuery.data;
  const isPolling = taskStatus ? isRunningTaskStatus(taskStatus.status) : false;
  const taskStatusState = toTaskStatusRequestState(taskStatusQuery);
  const traceQuery = useTrace(apiClient, taskId, { isPolling });
  const trace = traceQuery.data;
  const traceState = toQueryRequestState(traceQuery);
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
    <section className="page-surface trace-modern-surface" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">任务状态</p>
        <h3 id="page-title">{route.title}</h3>
        <p>{route.summary}</p>
      </div>

      {taskId ? (
        <div className="trace-modern-page" aria-label="过程追踪">
          {taskStatusState.status === "loading" || taskStatusState.status === "retrying" ? null : (
            <RequestStateMessage
              className="task-status-message"
              loadingText="正在读取任务状态"
              onRetry={() => void taskStatusQuery.refetch()}
              state={taskStatusState}
            />
          )}
          {traceState.status === "loading" || traceState.status === "retrying" ? null : (
            <RequestStateMessage
              className="trace-state-message"
              loadingText="正在读取过程追踪"
              onRetry={() => void traceQuery.refetch()}
              state={traceState}
            />
          )}

          <div className="trace-modern-shell">
            <TraceControlPanel
              isPolling={isPolling}
              taskId={taskId}
              taskStatus={taskStatus}
              trace={trace}
            />
            <main className="trace-modern-main">
              {traceQuery.isFetching && !trace ? (
                <PageLoadingState text="正在读取底层追踪数据" />
              ) : trace ? (
                <TraceWorkspace trace={trace} />
              ) : null}
            </main>
          </div>
        </div>
      ) : (
        <PageEmptyState />
      )}
    </section>
  );
}

function TraceControlPanel({
  isPolling,
  taskId,
  taskStatus,
  trace
}: {
  isPolling: boolean;
  taskId: string;
  taskStatus: TaskStatusResponse | undefined;
  trace: TraceData | undefined;
}) {
  const totalTokens = (trace?.token_usage ?? []).reduce(
    (sum, usage) => sum + usage.total_tokens,
    0
  );
  const activeStepIndex = getActiveTaskStepIndex(taskStatus?.status ?? trace?.task_status);
  const hasFailed = taskStatus ? FAILED_TASK_STATUSES.has(taskStatus.status) : false;

  return (
    <aside className="trace-modern-control" aria-label="流程总控">
      <Card
        className="trace-modern-card trace-modern-control-card"
        title={
          <Space>
            <Activity size={18} />
            流程总控
          </Space>
        }
      >
        <Text type="secondary">当前分析对象</Text>
        <Title level={4}>{taskStatus?.target_product_name ?? "分析任务已恢复"}</Title>
        <Space className="trace-modern-status-row" wrap>
          <Tag color={isPolling ? "processing" : hasFailed ? "error" : "success"}>
            当前状态：{taskStatus ? TASK_STATUS_LABELS[taskStatus.status] : "读取中"}
          </Tag>
          <Tag icon={isPolling ? <Clock size={13} /> : <CheckCircle2 size={13} />}>
            {isPolling ? "持续刷新" : "已停止轮询"}
          </Tag>
        </Space>

        <Steps
          className="trace-modern-steps"
          current={activeStepIndex}
          direction="vertical"
          items={TASK_STATUS_STEPS.map((step) => ({ title: step.title }))}
          status={hasFailed ? "error" : "process"}
        />

        {hasFailed ? (
          <Alert
            message="分析流程没有正常完成"
            description="请查看右侧过程记录中的失败节点、工具调用和差异记录。"
            showIcon
            type="error"
          />
        ) : null}

        {taskStatus?.status === "completed" ? <TaskResultActions taskId={taskId} /> : null}
      </Card>

      <div className="trace-modern-metrics" aria-label="追踪数据摘要">
        <MetricCard label="DAG 节点" value={trace?.dag_nodes?.length ?? 0} />
        <MetricCard label="运行记录" value={trace?.agent_runs?.length ?? 0} />
        <MetricCard
          label="QA 记录"
          value={trace?.quality_records?.length ?? trace?.qa_reviews?.length ?? 0}
        />
        <MetricCard label="Tokens" value={totalTokens} />
      </div>
    </aside>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="trace-modern-metric">
      <span className="trace-modern-metric-label metric-label-with-hint">
        {label}
        <MetricHint metric={label === "Tokens" ? "token_usage" : "metric_count"} />
      </span>
      <strong>{value.toLocaleString()}</strong>
    </div>
  );
}

function TaskResultActions({ taskId }: { taskId: string }) {
  return (
    <div className="task-result-actions trace-modern-actions" aria-label="任务结果入口">
      <Button
        icon={<ArrowLeft size={15} />}
        onClick={() => navigateTo(routePathForTask("/overview", taskId))}
      >
        查看总览
      </Button>
      <Button onClick={() => navigateTo(routePathForTask("/profile", taskId))}>查看画像对比</Button>
      <Button onClick={() => navigateTo(routePathForTask("/battlefield", taskId))}>查看图谱</Button>
      <Button
        icon={<FileText size={15} />}
        onClick={() => navigateTo(routePathForTask("/report", taskId))}
      >
        查看报告
      </Button>
    </div>
  );
}

function TraceWorkspace({ trace }: { trace: TraceData }) {
  const flow = useMemo(() => toTraceFlowElements(trace), [trace]);
  const activeTab = normalizeTraceTab(trace.process_view?.default_tab);
  const totalTokens = (trace.token_usage ?? []).reduce((sum, usage) => sum + usage.total_tokens, 0);

  return (
    <section className="trace-modern-workspace">
      <ReportPlanSummary trace={trace} />
      <Tabs
        defaultActiveKey={activeTab}
        destroyOnHidden
        items={[
          {
            children: <TraceEvidenceChains chains={trace.evidence_chains ?? []} />,
            key: "evidence_chain",
            label: tabLabel("证据链", trace.evidence_chains?.length ?? 0)
          },
          {
            children: <TraceAgentProcess flow={flow} totalTokens={totalTokens} trace={trace} />,
            key: "agent_process",
            label: tabLabel(
              "智能体过程",
              trace.process_view?.agent_run_count ?? trace.agent_runs?.length ?? 0
            )
          },
          {
            children: (
              <TraceQualityRecords
                records={trace.quality_records ?? []}
                reviews={trace.qa_reviews ?? []}
              />
            ),
            key: "quality_records",
            label: tabLabel(
              "质检记录",
              trace.quality_records?.length ?? trace.qa_reviews?.length ?? 0
            )
          },
          {
            children: <TraceDiffView diffs={trace.diffs ?? []} />,
            key: "diff_records",
            label: tabLabel("差异记录", trace.diffs?.length ?? 0)
          }
        ]}
        size="large"
      />
    </section>
  );
}

function ReportPlanSummary({ trace }: { trace: TraceData }) {
  const reportPlan = isRecordValue(trace.metadata?.report_plan) ? trace.metadata.report_plan : null;
  if (!reportPlan) {
    return null;
  }

  const artifactCounts = isRecordValue(reportPlan.artifact_counts)
    ? reportPlan.artifact_counts
    : {};
  const sectionIds = Array.isArray(reportPlan.section_ids)
    ? reportPlan.section_ids.map((item) => stringValue(item)).filter(Boolean)
    : [];

  return (
    <Card className="trace-report-plan-summary" size="small">
      <Space direction="vertical" size={8}>
        <Space wrap>
          <Tag color="blue">正式报告章节 {sectionIds.length}</Tag>
          <Tag>Battlecard {numberValue(artifactCounts.competitor_battlecards)}</Tag>
          <Tag>Gap {numberValue(artifactCounts.gap_matrix_items)}</Tag>
          <Tag>Opportunity {numberValue(artifactCounts.opportunity_items)}</Tag>
          <Tag>用户信号 {numberValue(artifactCounts.review_signal_clusters)}</Tag>
        </Space>
        <Text type="secondary">
          报告计划、QA 打回和报告质量规则分开记录；正文质量问题会进入“质检记录”，证据链问题仍由 QA
          记录追踪。
        </Text>
      </Space>
    </Card>
  );
}

function tabLabel(label: string, count: number) {
  return (
    <Space size={8}>
      <span>{label}</span>
      <Tag>
        {count}
        <MetricHint metric="metric_count" />
      </Tag>
    </Space>
  );
}

function TraceEvidenceChains({ chains }: { chains: TraceEvidenceChain[] }) {
  return (
    <section className="trace-modern-panel" aria-label="证据链">
      <PanelHeading kicker="证据" title="按结论组织证据链" />
      {chains.length > 0 ? (
        <div className="trace-modern-evidence-grid">
          {chains.map((chain) => (
            <Card className="trace-modern-evidence-card" key={chain.chain_id}>
              <div className="trace-evidence-card-header">
                <span className="trace-evidence-card-icon" aria-hidden="true">
                  <FileText size={18} />
                </span>
                <div className="trace-evidence-card-title">
                  <Title level={5}>{formatReportText(chain.claim_content)}</Title>
                  <Space className="trace-evidence-card-tags" wrap>
                    <Tag color="blue">
                      {CLAIM_STATUS_LABELS[chain.claim_status] ?? chain.claim_status}
                    </Tag>
                    <Tag>
                      {formatTraceConfidence(chain.confidence)}
                      <MetricHint metric="claim_confidence" />
                    </Tag>
                    <Tag>{chain.is_inference ? "分析判断" : "事实摘录"}</Tag>
                  </Space>
                </div>
              </div>
              <div className="trace-evidence-chain-meta" aria-label="证据链摘要">
                <div>
                  <span>分析章节</span>
                  <strong>{formatReportSectionList(chain.report_section_ids ?? [])}</strong>
                </div>
                <div>
                  <span>
                    证据数量
                    <MetricHint metric="metric_count" />
                  </span>
                  <strong>{chain.evidence_items?.length ?? 0}</strong>
                </div>
              </div>
              {(chain.risk_flags ?? []).length > 0 ? (
                <RiskFlagList labels={RISK_FLAG_LABELS} riskFlags={chain.risk_flags ?? []} />
              ) : null}
              <TraceEvidenceItemList evidenceItems={chain.evidence_items ?? []} />
            </Card>
          ))}
        </div>
      ) : (
        <Empty description={EMPTY_VALUE_TEXT} />
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
    return <Text type="secondary">{EMPTY_VALUE_TEXT}</Text>;
  }

  return (
    <div className="trace-modern-evidence-items" aria-label="结论引用证据">
      {evidenceItems.map((evidence, index) => (
        <article className="trace-modern-evidence-item" key={evidence.evidence_id}>
          <div className="trace-modern-item-heading">
            <Text strong>
              <span className="trace-evidence-index" aria-hidden="true">
                {index + 1}
              </span>
              <span>{`证据 ${index + 1}`}</span>
            </Text>
            <Tag>
              {formatConfidenceDetail(evidence.confidence_level)}
              <MetricHint metric="evidence_confidence_level" />
            </Tag>
          </div>
          <div className="evidence-paragraphs">
            {buildEvidenceParagraphs(evidence.content_summary, evidence.limitations).map(
              (paragraph, paragraphIndex) => (
                <p key={paragraphIndex}>{paragraph}</p>
              )
            )}
          </div>
          <Descriptions
            className="trace-modern-descriptions"
            column={1}
            items={[
              {
                key: "source",
                label: "来源类型",
                children: formatSourceType(evidence.source_type)
              },
              {
                key: "time",
                label: "访问时间",
                children: formatEvidenceAccessTime(
                  evidence.access_time,
                  evidence.access_time_status
                )
              },
              {
                key: "url",
                label: "来源链接",
                children: evidence.source_url ? (
                  <span className="trace-modern-source-url">{evidence.source_url}</span>
                ) : (
                  EMPTY_VALUE_TEXT
                )
              }
            ]}
            size="small"
          />
          <RiskFlagList labels={RISK_FLAG_LABELS} riskFlags={evidence.risk_flags ?? []} />
        </article>
      ))}
    </div>
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
    <section className="trace-modern-panel" aria-label="智能体过程">
      <PanelHeading kicker="流程" title="多智能体协作网络" />
      <div className="trace-modern-process-grid">
        <section className="trace-modern-graph-panel" aria-label="流程图状态">
          <div className="trace-flow" data-testid="trace-flow">
            <ReactFlow
              edges={flow.edges}
              fitView
              nodes={flow.nodes}
              nodesDraggable={false}
              proOptions={{ hideAttribution: true }}
            >
              <Background gap={20} color="#cbd5e1" />
              <Controls showInteractive={false} />
            </ReactFlow>
          </div>
        </section>

        <aside className="trace-modern-side-panel" aria-label="追踪数据摘要">
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
    <section aria-label="运行记录列表">
      <PanelHeading kicker="运行" title="运行记录" />
      {runs.length > 0 ? (
        <Timeline
          items={runs.map((run) => ({
            color:
              run.status === "failed"
                ? "red"
                : run.status === "requires_revision"
                  ? "orange"
                  : "green",
            children: (
              <Card className="trace-modern-run-card" size="small">
                <div className="trace-modern-item-heading">
                  <Text strong>{AGENT_LABELS[run.agent_name] ?? run.agent_name}</Text>
                  <Tag color={run.status === "requires_revision" ? "warning" : "default"}>
                    {RUN_STATUS_LABELS[run.status] ?? run.status}
                  </Tag>
                </div>
                <Descriptions
                  className="trace-modern-descriptions"
                  column={1}
                  items={[
                    {
                      key: "started",
                      label: "开始",
                      children: formatDateTime(run.started_at, {
                        emptyText: EMPTY_VALUE_TEXT,
                        fallback: formatDisplayText
                      })
                    },
                    {
                      key: "ended",
                      label: "结束",
                      children: formatDateTime(run.ended_at, {
                        emptyText: EMPTY_VALUE_TEXT,
                        fallback: formatDisplayText
                      })
                    },
                    {
                      key: "input",
                      label: "输入摘要",
                      children: formatTraceNullable(run.input_summary)
                    },
                    {
                      key: "output",
                      label: "输出摘要",
                      children: formatTraceNullable(run.output_summary)
                    },
                    ...(run.error_message
                      ? [
                          {
                            key: "error",
                            label: "错误",
                            children: sanitizeTraceText(run.error_message)
                          }
                        ]
                      : [])
                  ]}
                  size="small"
                />
              </Card>
            )
          }))}
        />
      ) : (
        <Empty description={EMPTY_VALUE_TEXT} />
      )}
    </section>
  );
}

function TraceToolCalls({ toolCalls }: { toolCalls: ToolCallLog[] }) {
  return (
    <section className="trace-modern-technical-section" aria-label="工具调用列表">
      <PanelHeading kicker="工具" title="工具调用" />
      {toolCalls.length > 0 ? (
        <div className="trace-modern-list">
          {toolCalls.map((toolCall) => (
            <Card key={toolCall.tool_call_id} size="small">
              <div className="trace-modern-item-heading">
                <Text strong>{formatToolName(toolCall.tool_name)}</Text>
                <Tag>{TOOL_STATUS_LABELS[toolCall.status] ?? toolCall.status}</Tag>
              </div>
              <Descriptions
                className="trace-modern-descriptions"
                column={1}
                items={[
                  {
                    key: "duration",
                    label: "耗时",
                    children: formatDuration(toolCall.duration_ms)
                  },
                  {
                    key: "args",
                    label: "参数摘要",
                    children: renderTraceValue(toolCall.arguments_summary ?? {})
                  },
                  ...(toolCall.error_message
                    ? [
                        {
                          key: "error",
                          label: "错误",
                          children: sanitizeTraceText(toolCall.error_message)
                        }
                      ]
                    : [])
                ]}
                size="small"
              />
            </Card>
          ))}
        </div>
      ) : (
        <Empty description={EMPTY_VALUE_TEXT} />
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
    <section className="trace-modern-technical-section" aria-label="模型用量列表">
      <PanelHeading kicker="用量" title="模型用量" />
      <div className="trace-token-total">总计 {total} 个计量单位</div>
      {tokenUsage.length > 0 ? (
        <div className="trace-modern-list">
          {tokenUsage.map((usage) => (
            <Card key={usage.usage_id} size="small">
              <div className="trace-modern-item-heading">
                <Text strong>{AGENT_LABELS[usage.agent_name] ?? usage.agent_name}</Text>
                <Tag>{formatTechnicalModelName(usage.model_name)}</Tag>
              </div>
              <div className="trace-modern-token-bars">
                <TokenBar label="输入计量" max={usage.total_tokens} value={usage.prompt_tokens} />
                <TokenBar
                  label="输出计量"
                  max={usage.total_tokens}
                  value={usage.completion_tokens}
                />
                <TokenBar label="合计" max={usage.total_tokens} value={usage.total_tokens} />
              </div>
            </Card>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function TokenBar({ label, max, value }: { label: string; max: number; value: number }) {
  const percent = max > 0 ? Math.round((value / max) * 100) : 0;

  return (
    <div className="trace-modern-token-row">
      <span>
        <Text strong>{label}</Text>
        <Text type="secondary">
          {value}
          <MetricHint metric="token_usage" />
        </Text>
      </span>
      <Progress percent={percent} showInfo={false} />
    </div>
  );
}

function TracePromptPreviews({ prompts }: { prompts: TracePromptPreview[] }) {
  return (
    <section className="trace-modern-technical-section" aria-label="提示词摘要">
      <PanelHeading kicker="摘要" title="提示词摘要" />
      {prompts.length > 0 ? (
        <Collapse
          className="trace-modern-prompt-collapse"
          ghost
          items={prompts.map((prompt) => ({
            key: prompt.preview_id,
            label: (
              <Space>
                <Cpu size={14} />
                <span>提示摘要</span>
                {prompt.redacted ? (
                  <Tag color="green">已脱敏</Tag>
                ) : (
                  <Tag color="warning">需复核</Tag>
                )}
              </Space>
            ),
            children: <Paragraph>{sanitizeTraceText(prompt.content_summary)}</Paragraph>
          }))}
        />
      ) : (
        <Empty description="暂无折叠提示词摘要" />
      )}
    </section>
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
    <section className="trace-modern-panel" aria-label="质检记录">
      <PanelHeading kicker="质检" title="质检打回与处理状态" />
      <Alert
        className="trace-modern-alert"
        description="这里记录 QA 智能体发现的问题、打回目标、要求动作，以及系统修复后的闭环结果。"
        message="可观测的自我修复"
        showIcon
        type="info"
      />
      <div className="trace-quality-summary" aria-label="质检状态汇总">
        <MetricCard label="仍需关注" value={attentionCount} />
        <MetricCard label="已解决" value={resolvedCount} />
        <MetricCard label="待处理或豁免" value={pendingCount} />
      </div>
      <Timeline
        items={records.map((record) => {
          const attention = getTraceQualityAttention(record);

          return {
            color: record.needs_attention ? "red" : record.resolved ? "green" : "gray",
            dot: record.needs_attention ? <ShieldAlert size={16} /> : <CheckCircle2 size={16} />,
            children: (
              <Card
                className={`trace-quality-item trace-quality-item-${attention.kind}`}
                size="small"
              >
                <div className="trace-modern-item-heading">
                  <Title level={5}>{sanitizeTraceText(record.check_item)}</Title>
                  <Tag className={attention.className}>{attention.label}</Tag>
                </div>
                <Paragraph>{formatTraceQualityText(record.issue_summary)}</Paragraph>
                <div className="trace-quality-result">
                  <strong>处理结论</strong>
                  {formatTraceQualityText(record.action_result)}
                </div>
                <Descriptions
                  className="trace-modern-descriptions"
                  column={{ lg: 2, sm: 1, xs: 1 }}
                  items={[
                    {
                      key: "severity",
                      label: "问题等级",
                      children: REVIEW_SEVERITY_LABELS[record.severity] ?? record.severity
                    },
                    {
                      key: "attention",
                      label: "是否仍需关注",
                      children: record.needs_attention ? "是，需要继续处理" : "否，当前已闭环"
                    },
                    {
                      key: "target",
                      label: "质检打回对象",
                      children: formatTraceTarget(record.target_type, record.target_id)
                    },
                    {
                      key: "agent",
                      label: "打回目标",
                      children: record.target_agent
                        ? (AGENT_LABELS[record.target_agent] ?? record.target_agent)
                        : EMPTY_VALUE_TEXT
                    },
                    {
                      key: "action",
                      label: "处理要求",
                      children: formatTraceQualityText(record.required_action)
                    },
                    {
                      key: "status",
                      label: "质检状态",
                      children: REVIEW_STATUS_LABELS[record.status] ?? record.status
                    },
                    {
                      key: "issue",
                      label: "问题编码",
                      children: formatIssueCode(record.issue_code)
                    },
                    {
                      key: "claims",
                      label: "关联结论",
                      children: formatTraceReferenceCount(record.related_claim_ids ?? [], "结论")
                    },
                    {
                      key: "evidence",
                      label: "关联证据",
                      children: formatTraceReferenceCount(record.evidence_ids ?? [], "证据")
                    }
                  ]}
                  size="small"
                />
              </Card>
            )
          };
        })}
      />
    </section>
  );
}

function TraceQaReviews({ reviews }: { reviews: ReviewTask[] }) {
  return (
    <section className="trace-modern-panel" aria-label="质检记录">
      <PanelHeading kicker="质检" title="质检记录" />
      {reviews.length > 0 ? (
        <div className="trace-modern-list">
          {reviews.map((review) => (
            <Card key={review.review_task_id} size="small">
              <div className="trace-modern-item-heading">
                <Title level={5}>{review.check_name}</Title>
                <Tag>{REVIEW_SEVERITY_LABELS[review.severity] ?? review.severity}</Tag>
              </div>
              <Paragraph>{sanitizeTraceText(review.message)}</Paragraph>
              <Descriptions
                className="trace-modern-descriptions"
                column={{ lg: 2, sm: 1, xs: 1 }}
                items={[
                  { key: "issue", label: "问题编码", children: formatIssueCode(review.issue_code) },
                  {
                    key: "target",
                    label: "目标",
                    children: formatTraceTarget(review.target_type, review.target_id)
                  },
                  {
                    key: "agent",
                    label: "打回目标",
                    children: review.target_agent
                      ? (AGENT_LABELS[review.target_agent] ?? review.target_agent)
                      : EMPTY_VALUE_TEXT
                  },
                  {
                    key: "status",
                    label: "状态",
                    children: REVIEW_STATUS_LABELS[review.status] ?? review.status
                  },
                  {
                    key: "action",
                    label: "要求",
                    children: sanitizeTraceText(review.required_action)
                  }
                ]}
                size="small"
              />
            </Card>
          ))}
        </div>
      ) : (
        <Empty description={EMPTY_VALUE_TEXT} />
      )}
    </section>
  );
}

function TraceDiffView({ diffs }: { diffs: TraceDiff[] }) {
  return (
    <section className="trace-modern-panel trace-diff-panel" aria-label="差异记录">
      <PanelHeading kicker="变化" title="业务变化影响" />
      {diffs.length > 0 ? (
        <Timeline
          items={diffs.map((diff) => {
            const source = getTraceDiffSource(diff.source);

            return {
              color: source.kind === "human-feedback" ? "purple" : "blue",
              children: (
                <Card
                  className={`trace-diff-item trace-diff-item-${source.kind}`}
                  key={diff.diff_id}
                >
                  <div className="trace-modern-item-heading">
                    <Title level={5}>{source.label}</Title>
                    <Tag className={source.statusClass}>
                      {TRACE_DIFF_STATUS_LABELS[diff.status] ?? sanitizeTraceText(diff.status)}
                    </Tag>
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
                  <TraceDiffDetails diff={diff} sourceLabel={source.label} />
                </Card>
              )
            };
          })}
        />
      ) : (
        <Empty description={EMPTY_VALUE_TEXT} />
      )}
    </section>
  );
}

function TraceDiffDetails({ diff, sourceLabel }: { diff: TraceDiff; sourceLabel: string }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="trace-diff-details">
      <button
        className="trace-diff-summary"
        onClick={() => setIsOpen((current) => !current)}
        type="button"
      >
        查看结构化前后值
      </button>
      {isOpen ? (
        <>
          <Descriptions
            className="trace-modern-descriptions"
            column={1}
            items={[
              { key: "source", label: "变化来源", children: sourceLabel },
              { key: "record", label: "差异记录", children: "已记录" }
            ]}
            size="small"
          />
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
        </>
      ) : null}
    </div>
  );
}

function PanelHeading({ kicker, title }: { kicker: string; title: string }) {
  return (
    <div className="section-heading trace-modern-heading">
      <p className="section-kicker">{kicker}</p>
      <h4>{title}</h4>
    </div>
  );
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
            "trace-modern-flow-node",
            node.current ? "trace-flow-node-current" : "",
            node.failed ? "trace-flow-node-failed" : ""
          ]
            .filter(Boolean)
            .join(" ")}
        >
          <span>{node.node_type === "agent" ? "智能体" : "系统节点"}</span>
          <strong>{formatTraceNodeLabel(node)}</strong>
          <small>{TRACE_NODE_STATUS_LABELS[node.status] ?? node.status}</small>
        </div>
      )
    },
    id: node.node_id,
    position: { x: index * 220, y: node.node_id === "failed" ? 190 : 80 },
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
      stroke: isRevision ? "#dc2626" : "#0f766e",
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
    .replace(/QA/g, "质检")
    .replace(/Writer/g, "报告")
    .replace(/passed/g, "通过")
    .replace(/->/g, "→");
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
      return formatDateTime(value, { emptyText: EMPTY_VALUE_TEXT, fallback: formatDisplayText });
    }

    return formatTraceDisplayValue(value, key);
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return EMPTY_VALUE_TEXT;
    }

    if (value.every((item) => ["string", "number", "boolean"].includes(typeof item))) {
      if (key?.endsWith("_ids") || value.every((item) => isInternalIdentifier(String(item)))) {
        return `${value.length} 条`;
      }
      return value.map((item) => formatTraceDisplayValue(String(item), key)).join("，");
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
    const entries = Object.entries(value).filter(
      ([nestedKey, nestedValue]) =>
        nestedKey !== "metadata" &&
        !nestedKey.endsWith("_id") &&
        !nestedKey.endsWith("_ids") &&
        !isInternalReportValue(nestedValue)
    );
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

  return formatTraceDisplayValue(String(value), key);
}

function formatReportText(value: string) {
  return sanitizeTraceText(value)
    .replace(/\bProduct\b/g, "产品")
    .replace(/\bEvidence\b/g, "证据")
    .replace(/\bClaim\b/g, "分析判断")
    .replace(/\bCompetitionEdge\b/g, "竞争关系")
    .replace(/\bFeatureTree\b/g, "功能能力树")
    .replace(/\bPricingModel\b/g, "价格模型")
    .replace(/\bUserPersona\b/g, "用户人群画像")
    .replace(/\bdirect\b/g, "直接竞品")
    .replace(/\balternative\b/g, "需求替代")
    .replace(/\bchannel\b/g, "渠道替代")
    .replace(/\bclear_judgment\b/g, "判断较明确")
    .replace(/\bmedium\b/g, "中等可信度")
    .replace(/\bmissing_access_time\b/g, "缺少访问时间")
    .replace(/\bmissing_screenshot\b/g, "缺少截图")
    .replace(/\bcompleted\b/g, "已完成")
    .replace(/\bdemo_snapshot\b/g, "本地演示快照")
    .replace(/\bsnapshot_plus_live\b/g, "快照 + 公开页增强")
    .replace(/\bbuiltin_candidates\b/g, "内置候选池")
    .replace(/\bbuiltin_candidate_pool\b/g, "内置候选池")
    .replace(/\bdouyin_sku_snapshot\b/g, "抖音商品快照")
    .replace(/\binternet_ai_assistant\b/g, "互联网产品 / AI 助手")
    .replace(/\bofficial_product_page\b/g, "官方产品页")
    .replace(/\bofficial_help_doc\b/g, "官方帮助文档")
    .replace(/\bapp_store_page\b/g, "应用商店页")
    .replace(/\bofficial_release_note\b/g, "官方发布说明")
    .replace(/\bCNY\b/g, "元")
    .replace(/\bprod_sku_\d+\b/g, "相关产品")
    .replace(/\bedge_[A-Za-z0-9_]+\b/g, "相关竞争关系")
    .replace(/\bclaim_[A-Za-z0-9_]+\b/g, "相关结论")
    .replace(/\bev_[A-Za-z0-9_]+\b/g, "相关证据");
}

function formatDisplayText(value: string) {
  return formatReportText(value)
    .replace(/\bautomatic\b/g, "自动清理")
    .replace(/\bdemo_snapshot\b/g, "本地演示快照")
    .replace(/\bsnapshot_plus_live\b/g, "快照 + 公开页增强")
    .replace(/\bbuiltin_candidates\b/g, "内置候选池")
    .replace(/\bbuiltin_candidate_pool\b/g, "内置候选池")
    .replace(/\bsmart_pet_hardware\b/g, "智能宠物硬件")
    .replace(/\bautomatic_litter_box\b/g, "自动猫砂盆")
    .replace(/\binternet_ai_assistant\b/g, "互联网产品 / AI 助手")
    .replace(/\bofficial_product_page\b/g, "官方产品页")
    .replace(/\bofficial_help_doc\b/g, "官方帮助文档")
    .replace(/\bapp_store_page\b/g, "应用商店页")
    .replace(/\bofficial_release_note\b/g, "官方发布说明")
    .replace(/\btarget\b/g, "目标产品");
}

function formatSourceType(value: string | null | undefined) {
  if (!value) {
    return EMPTY_VALUE_TEXT;
  }

  return SOURCE_TYPE_LABELS[value] ?? formatDisplayText(value);
}

function formatConfidenceDetail(value: string | null | undefined) {
  if (!value) {
    return EMPTY_VALUE_TEXT;
  }

  return CONFIDENCE_DETAIL_LABELS[value] ?? CONFIDENCE_LABELS[value] ?? formatDisplayText(value);
}

function buildEvidenceParagraphs(
  summary: string | null | undefined,
  limitations?: string | null | undefined
) {
  const paragraphs: string[] = [];
  const summaryText = summary ? formatDisplayText(summary) : "";
  const summaryParts = summaryText
    .split(/[；;]\s*/)
    .map(cleanEvidenceDisplayText)
    .filter(Boolean);

  for (const part of summaryParts) {
    if (isInternalEvidenceProcessText(part)) {
      continue;
    }

    let text = part
      .replace(/\s*本地快照[:：]\s*/g, "。商品与价格：")
      .replace(/^核心卖点[:：]\s*/g, "核心卖点：")
      .replace(/^评论摘要[:：]\s*/g, "评论与市场信号：")
      .replace(/^评论洞察/g, "评论洞察")
      .replace(/\bCNY\b/g, "元")
      .trim();

    if (!/[。！？]$/.test(text)) {
      text = `${text}。`;
    }

    paragraphs.push(text);
  }

  const limitationText = limitations
    ? cleanEvidenceDisplayText(formatDisplayText(limitations))
    : "";
  if (limitationText && !isInternalEvidenceProcessText(limitationText)) {
    paragraphs.push(
      `证据边界：${/[。！？]$/.test(limitationText) ? limitationText : `${limitationText}。`}`
    );
  }

  return paragraphs.length > 0 ? paragraphs : [EMPTY_VALUE_TEXT];
}

function cleanEvidenceDisplayText(value: string) {
  return value
    .replace(/\[REDACTED\]/gi, "")
    .replace(/【REDACTED】/gi, "")
    .replace(/（REDACTED）/gi, "")
    .replace(/\(REDACTED\)/gi, "")
    .replace(/，\s*。/g, "。")
    .replace(/,\s*。/g, "。")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[，,]\s*$/g, "")
    .trim();
}

function isInternalEvidenceProcessText(value: string) {
  return /评论洞察尚待后续结构化抽取|QA\s*打回后补齐字段|补齐字段[:：]\s*source\.access_time|Evidence\.access_time|source\.access_time/i.test(
    value
  );
}

function isInternalReportValue(value: unknown) {
  if (typeof value === "string") {
    return isInternalIdentifier(value);
  }

  if (Array.isArray(value) && value.every((item) => typeof item === "string")) {
    return value.length > 0 && value.every(isInternalIdentifier);
  }

  return false;
}

function humanizeReportKey(key: string) {
  return REPORT_FIELD_LABELS[key] ?? key.replace(/_/g, " ");
}

function formatTraceNullable(value: string | null | undefined) {
  return value && value.trim().length > 0 ? formatTraceDisplayValue(value) : EMPTY_VALUE_TEXT;
}

function formatTraceConfidence(value: number) {
  return `${Math.round(value * 100)}%`;
}

function formatTraceTarget(targetType: string, targetId: string) {
  const label = TRACE_TARGET_TYPE_LABELS[targetType] ?? targetType;

  return isInternalIdentifier(targetId) ? `${label}已记录` : label;
}

function formatRevisionMessageList(values: string[]) {
  return values.length > 0 ? `${values.length} 条打回记录` : "无打回记录";
}

function formatAccessTimeStatus(value: string | null | undefined) {
  if (!value) {
    return EMPTY_VALUE_TEXT;
  }

  return ACCESS_TIME_STATUS_LABELS[value] ?? formatDisplayText(value);
}

function formatEvidenceAccessTime(
  accessTime: string | null | undefined,
  status: string | null | undefined
) {
  if (accessTime) {
    return formatDateTime(accessTime, { emptyText: EMPTY_VALUE_TEXT, fallback: formatDisplayText });
  }

  return formatAccessTimeStatus(status);
}

function formatIssueCode(value: string | null | undefined) {
  if (!value) {
    return EMPTY_VALUE_TEXT;
  }

  return (
    {
      KEY_SCREENSHOT_MISSING: "关键截图缺失",
      SENSITIVE_CLAIM_NEEDS_CONSERVATIVE_LANGUAGE: "敏感表达需要保守处理",
      TIMELY_EVIDENCE_MISSING_ACCESS_TIME: "时效证据缺少访问时间"
    }[value] ?? "质检问题已记录"
  );
}

function formatTraceQualityText(value: string | null | undefined) {
  if (!value) {
    return EMPTY_VALUE_TEXT;
  }

  return sanitizeTraceText(value)
    .replace(/QA\s*打回后补齐字段[:：]\s*source\.access_time[。]?/gi, "已补充证据访问时间。")
    .replace(/补齐\s*Evidence\.access_time/gi, "补充证据访问时间")
    .replace(/source\.access_time/gi, "证据访问时间")
    .replace(/Evidence\.access_time/gi, "证据访问时间")
    .replace(/如无法补齐，将相关结论降级为暂无可靠数据。/g, "如果无法补充，相关结论会保持保守。")
    .trim();
}

function formatTraceReferenceCount(values: string[], label: string) {
  return values.length > 0 ? `${values.length} 条${label}` : EMPTY_VALUE_TEXT;
}

function formatReportSectionList(values: string[]) {
  if (values.length === 0) {
    return EMPTY_VALUE_TEXT;
  }

  return values
    .map((value) => REPORT_SECTION_FALLBACK_TITLES[value] ?? formatDisplayText(value))
    .join("，");
}

function formatTechnicalModelName(value: string | null | undefined) {
  if (!value) {
    return EMPTY_VALUE_TEXT;
  }

  return TECHNICAL_MODEL_LABELS[value] ?? formatDisplayText(value);
}

function formatToolName(value: string | null | undefined) {
  if (!value) {
    return EMPTY_VALUE_TEXT;
  }

  return TOOL_NAME_LABELS[value] ?? formatDisplayText(value);
}

function formatTraceDisplayValue(value: string, key?: string) {
  if (isInternalIdentifier(value)) {
    return "已记录";
  }

  if (key === "source_type") {
    return formatSourceType(value);
  }

  if (key === "confidence_level") {
    return formatConfidenceDetail(value);
  }

  if (key === "status") {
    return (
      CLAIM_STATUS_LABELS[value] ??
      RUN_STATUS_LABELS[value] ??
      REVIEW_STATUS_LABELS[value] ??
      WORKFLOW_STATUS_LABELS[value] ??
      formatDisplayText(value)
    );
  }

  if (key === "access_time_status") {
    return formatAccessTimeStatus(value);
  }

  return formatDisplayText(value)
    .replace(/\bProduct\b/g, "产品")
    .replace(/\bEvidence\b/g, "证据")
    .replace(/\bClaim\b/g, "结论")
    .replace(/\bCompetitionEdge\b/g, "竞争关系")
    .replace(/\bFeatureTree\b/g, "功能能力树")
    .replace(/\bPricingModel\b/g, "价格模型")
    .replace(/\bUserPersona\b/g, "用户人群画像")
    .replace(/\bcompleted\b/g, "已完成")
    .replace(/\bsucceeded\b/g, "成功")
    .replace(/\brequires_revision\b/g, "需要修复");
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

function numberValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function getActiveTaskStepIndex(status: string | null | undefined) {
  const index = TASK_STATUS_STEPS.findIndex((step) => step.key === status);
  if (index >= 0) {
    return index;
  }
  return status === "failed" || status === "partial_failed" ? TASK_STATUS_STEPS.length - 1 : 0;
}
