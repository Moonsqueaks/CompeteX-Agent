import {
  Alert,
  Badge,
  Button,
  Card,
  Col,
  Empty,
  Row,
  Select,
  Space,
  Statistic,
  Tag,
  Typography
} from "antd";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  ChevronRight,
  Target,
  Zap
} from "lucide-react";
import { useEffect, useState } from "react";

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
  DISPLAY_STATUS_COLORS,
  OVERVIEW_ACTION_PRIORITY_LABELS,
  OVERVIEW_RELATIONSHIP_LABELS,
  OVERVIEW_RESPONSIBILITY_LABELS,
  OVERVIEW_THREAT_LABELS,
  OVERVIEW_THREAT_TAG_COLORS as THREAT_TAG_COLORS
} from "../domain/labels";
import { MetricHint } from "../components/MetricHint";
import { PageEmptyState } from "../components/PageEmptyState";
import { PageLoadingState } from "../components/PageLoadingState";
import { RiskFlagList } from "../components/RiskFlagList";
import { TermHint } from "../components/TermHint";
import type { TermKey } from "../domain/termExplanations";
import { useOverview, useOverviewSliceOptions } from "../hooks/useOverview";
import { resolveBackendAssetUrl } from "../utils/assets";
import { isRecordValue } from "../utils/format";

const { Paragraph, Text, Title } = Typography;

type BattlefieldData = components["schemas"]["BattlefieldData"];
type BattlefieldAvailableSlice = NonNullable<BattlefieldData["available_slices"]>[number];
type BattlefieldSliceSelection = components["schemas"]["BattlefieldSliceSelection"];
type DisplayStatus = components["schemas"]["DisplayStatus"];
type OverviewActionRecommendation = components["schemas"]["OverviewActionRecommendation"];
type OverviewData = components["schemas"]["OverviewData"];
type OverviewFinding = components["schemas"]["OverviewFinding"];
type OverviewKeyCompetitor = components["schemas"]["OverviewKeyCompetitor"];
type TaskApiClient = Pick<ApiClient, "get" | "post"> &
  Partial<Pick<ApiClient, "download" | "getBattlefield" | "getOverview">>;

export function OverviewPage({
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

  const overviewQuery = useOverview(apiClient, taskId, selectedSlice);
  const overviewFailed = isOverviewTaskFailedError(overviewQuery.error);
  const overviewWaiting = isOverviewNotReadyError(overviewQuery.error) && !overviewFailed;

  useEffect(() => {
    if (!overviewWaiting) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      void overviewQuery.refetch();
    }, 2000);
    return () => window.clearInterval(intervalId);
  }, [overviewQuery, overviewWaiting]);

  const sliceOptionsQuery = useOverviewSliceOptions(apiClient, taskId);
  const overviewState = toQueryRequestState(overviewQuery);
  const showOverviewWaiting =
    overviewWaiting || (!overviewQuery.data && overviewQuery.isFetching);
  const suppressOverviewMessage = showOverviewWaiting || overviewFailed;
  const overviewMessageState = suppressOverviewMessage
    ? createIdleState<OverviewData>()
    : overviewState;
  const overview = overviewQuery.data;
  const availableSlices = Array.isArray(sliceOptionsQuery.data?.available_slices)
    ? sliceOptionsQuery.data.available_slices
    : [];

  return (
    <section className="page-surface overview-page" aria-labelledby="page-title">
      <div className="page-intro overview-page-intro">
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
            state={overviewMessageState}
          />

          {showOverviewWaiting ? (
            <OverviewWaitingState onRetry={() => void overviewQuery.refetch()} />
          ) : null}

          {overviewFailed ? (
            <OverviewFailedState
              error={overviewQuery.error}
              onRetry={() => void overviewQuery.refetch()}
            />
          ) : null}

          {!overviewFailed ? (
            <OverviewSliceControls
              availableSlices={availableSlices}
              onChange={setSelectedSlice}
              selection={selectedSlice}
            />
          ) : null}

          {overview ? <OverviewContent overview={overview} taskId={taskId} /> : null}
        </div>
      ) : (
        <PageEmptyState />
      )}
    </section>
  );
}

function OverviewWaitingState({ onRetry }: { onRetry: () => void }) {
  return (
    <Card className="overview-waiting-card page-loading-with-action">
      <PageLoadingState text="正在生成竞争态势总览" />
      <Text className="overview-waiting-status" type="secondary">
        任务状态同步中
      </Text>
      <Button onClick={onRetry} type="primary">
        重新检查
      </Button>
    </Card>
  );
}

function OverviewFailedState({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const failureReason = readErrorDetail(error, "failure_message");
  const failureType = readErrorDetail(error, "failure_reason");
  const traceId = readErrorTraceId(error);

  return (
    <Card className="overview-waiting-card">
      <Alert
        action={
          <Button onClick={onRetry} size="small" type="primary">
            重新检查
          </Button>
        }
        description={
          <Space orientation="vertical" size={8}>
            <span>
              这次分析任务没有正常完成，所以暂时无法生成竞争态势总览。请先修复任务失败原因，
              然后重新创建或重新运行任务。
            </span>
            {failureReason ? <Text>失败原因：{failureReason}</Text> : null}
            {failureType ? <Text type="secondary">失败类型：{failureType}</Text> : null}
            {traceId ? <Text type="secondary">追踪编号：{traceId}</Text> : null}
          </Space>
        }
        showIcon
        title="任务生成失败"
        type="error"
      />
    </Card>
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

  const updateSelection = (field: keyof BattlefieldSliceSelection, value: string | null) => {
    onChange({
      ...selection,
      [field]: value || null
    });
  };

  return (
    <Card className="overview-slice-panel" size="small">
      <Row align="middle" gutter={[16, 16]} justify="space-between">
        <Col xs={24} xl={7}>
          <Space align="center" className="overview-slice-heading">
            <Target aria-hidden="true" size={18} />
            <div className="overview-slice-heading-copy">
              <Text className="overview-slice-title" strong>
                动态切片
              </Text>
              <Text className="overview-slice-hint" type="secondary">
                <span>按价格带、人群和使用场景刷新判断</span>
                <TermHint term="dynamic_slice" showLabel={false} />
              </Text>
            </div>
          </Space>
        </Col>
        <Col xs={24} xl={17}>
          <Row gutter={[12, 12]}>
            <Col xs={24} md={8}>
              <label className="overview-select-label">
                <span>价格带切片</span>
                <Select
                  allowClear
                  aria-label="价格带切片"
                  onChange={(value) => updateSelection("price_band", value)}
                  options={toSelectOptions(priceBands)}
                  placeholder="全部价格带"
                  value={selection.price_band ?? undefined}
                />
              </label>
            </Col>
            <Col xs={24} md={8}>
              <label className="overview-select-label">
                <span>人群切片</span>
                <Select
                  allowClear
                  aria-label="人群切片"
                  onChange={(value) => updateSelection("persona", value)}
                  options={toSelectOptions(personas)}
                  placeholder="全部人群"
                  value={selection.persona ?? undefined}
                />
              </label>
            </Col>
            <Col xs={24} md={8}>
              <label className="overview-select-label">
                <span>使用场景切片</span>
                <Select
                  allowClear
                  aria-label="使用场景切片"
                  onChange={(value) => updateSelection("scenario", value)}
                  options={toSelectOptions(scenarios)}
                  placeholder="全部场景"
                  value={selection.scenario ?? undefined}
                />
              </label>
            </Col>
          </Row>
        </Col>
      </Row>
    </Card>
  );
}

function OverviewContent({ overview, taskId }: { overview: OverviewData; taskId: string }) {
  const primaryCompetitors = overview.key_competitors ?? [];
  const topAction = overview.action_recommendations?.[0] ?? null;
  const topRisk = overview.risk_points?.[0] ?? null;
  const scope = overview.analysis_scope;

  return (
    <Space className="overview-content" orientation="vertical" size={20}>
      <Row gutter={[20, 20]}>
        <Col xs={24} xl={16}>
          <Card className="overview-judgment-card">
            <Space orientation="vertical" size={16}>
              <Space align="center">
                <Activity aria-hidden="true" size={18} />
                <Text className="section-kicker">核心判断</Text>
              </Space>
              <Title level={3}>{overview.one_sentence_judgment.content}</Title>
              <Alert showIcon title={scope.scope_notice} type="info" />
              <Row gutter={[12, 12]}>
                <Col xs={24} md={8}>
                  <OverviewStatusCard
                    label="判断强度"
                    status={overview.judgment_strength}
                    term="judgment_strength"
                  />
                </Col>
                <Col xs={24} md={8}>
                  <OverviewStatusCard label="决策可用性" status={overview.decision_usability} />
                </Col>
                <Col xs={24} md={8}>
                  <Card className="overview-status-card" size="small">
                    <Statistic
                      title={
                        <span className="metric-label-with-hint">
                          分析范围
                          <MetricHint metric="analysis_scope_counts" />
                        </span>
                      }
                      value={scope.product_count}
                      suffix="个产品"
                    />
                    <Text type="secondary">
                      {scope.sku_count} 个 SKU / {scope.evidence_count} 条证据
                    </Text>
                  </Card>
                </Col>
              </Row>
            </Space>
          </Card>
        </Col>

        <Col xs={24} xl={8}>
          <Space className="overview-side-column" orientation="vertical" size={16}>
            <OverviewActionSummary action={topAction} />
            <OverviewRiskAlert risk={topRisk} />
          </Space>
        </Col>
      </Row>

      <Card
        aria-label="关键竞品与下钻入口"
        className="overview-competitor-section"
        title={
          <Space>
            <Zap aria-hidden="true" size={18} />
            <span>关键竞品</span>
          </Space>
        }
      >
        <Text className="overview-section-subtitle" type="secondary">
          本轮最值得先看的竞争关系
        </Text>
        {primaryCompetitors.length > 0 ? (
          <Row gutter={[16, 16]}>
            {primaryCompetitors.map((competitor) => (
              <Col key={competitor.product_id} lg={12} xl={8} xs={24}>
                <OverviewCompetitorCard competitor={competitor} taskId={taskId} />
              </Col>
            ))}
          </Row>
        ) : (
          <Empty description="暂无关键竞品" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <OverviewFindingPanel
            emptyText="暂无机会点"
            findings={overview.opportunities ?? []}
            title="机会点"
          />
        </Col>
        <Col xs={24} lg={8}>
          <OverviewFindingPanel
            emptyText="暂无新增风险点"
            findings={overview.risk_points ?? []}
            title="风险点"
          />
        </Col>
        <Col xs={24} lg={8}>
          <Card className="overview-drilldown-card">
            <Space orientation="vertical" size={12}>
              <Text className="section-kicker">继续下钻</Text>
              <Title level={5}>从总览进入关系图谱</Title>
              <Paragraph type="secondary">
                进入竞争图谱后，可按价格带、人群和场景继续切片验证本页判断。
              </Paragraph>
              <Button
                icon={<ChevronRight aria-hidden="true" size={16} />}
                iconPlacement="end"
                onClick={() => navigateTo(routePathForTask("/battlefield", taskId))}
                type="primary"
              >
                查看完整竞争图谱
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </Space>
  );
}

function OverviewStatusCard({
  label,
  status,
  term
}: {
  label: string;
  status: DisplayStatus;
  term?: TermKey;
}) {
  return (
    <Card className="overview-status-card" size="small">
      <Space orientation="vertical" size={8}>
        <Text type="secondary">
          {label}
          {term ? <TermHint term={term} showLabel={false} /> : null}
        </Text>
        <Tag color={DISPLAY_STATUS_COLORS[status.value] ?? "blue"}>{status.label}</Tag>
        <Text>{status.reason}</Text>
      </Space>
    </Card>
  );
}

function OverviewActionSummary({ action }: { action: OverviewActionRecommendation | null }) {
  return (
    <Card
      className="overview-action-card"
      title={
        <Space>
          <AlertTriangle aria-hidden="true" size={18} />
          <span>首要行动建议</span>
        </Space>
      }
    >
      {action ? (
        <Space orientation="vertical" size={10}>
          <Space wrap>
            <Tag color="red">{OVERVIEW_ACTION_PRIORITY_LABELS[action.priority] ?? action.priority}</Tag>
            <Tag>
              {OVERVIEW_RESPONSIBILITY_LABELS[action.responsibility_type] ??
                action.responsibility_type}
            </Tag>
          </Space>
          <Title level={5}>{action.title}</Title>
          <Paragraph>{action.description}</Paragraph>
          {action.expected_impact ? (
            <Text type="secondary">预期影响：{action.expected_impact}</Text>
          ) : null}
        </Space>
      ) : (
        <Empty description="暂无可执行建议" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Card>
  );
}

function OverviewRiskAlert({ risk }: { risk: OverviewFinding | null }) {
  if (!risk) {
    return (
      <Alert
        className="overview-risk-alert"
        description="暂无阻断决策的证据风险。"
        icon={<CheckCircle aria-hidden="true" size={18} />}
        showIcon
        title="证据风险提示"
        type="success"
      />
    );
  }

  return (
    <Alert
      className="overview-risk-alert"
      description={
        <Space orientation="vertical" size={8}>
          <span>{risk.description}</span>
          <RiskFlagList color="orange" riskFlags={risk.risk_flags ?? []} useSpace />
        </Space>
      }
      showIcon
      title={risk.title}
      type="warning"
    />
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
    <Card className="overview-finding-panel" title={title}>
      {findings.length > 0 ? (
        <Space orientation="vertical" size={12}>
          {findings.map((finding) => (
            <Card key={finding.finding_id} size="small">
              <Title level={5}>{finding.title}</Title>
              <Paragraph type="secondary">{finding.description}</Paragraph>
              <RiskFlagList color="orange" riskFlags={finding.risk_flags ?? []} useSpace />
            </Card>
          ))}
        </Space>
      ) : (
        <Empty description={emptyText} image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Card>
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
  const relationshipLabel =
    OVERVIEW_RELATIONSHIP_LABELS[competitor.relationship_label] ?? competitor.relationship_label;
  const threatLabel = OVERVIEW_THREAT_LABELS[competitor.threat_level] ?? competitor.threat_level;

  return (
    <Badge.Ribbon color="blue" text={relationshipLabel}>
      <Card className="overview-competitor-card" hoverable>
        <Space orientation="vertical" size={12}>
          <OverviewCompetitorImage competitor={competitor} />
          <div>
            <Text type="secondary">{competitor.brand ?? competitor.sku_id ?? "关键竞品"}</Text>
            <Title level={5}>{competitor.product_name}</Title>
          </div>
          <Space wrap>
            <Tag color={THREAT_TAG_COLORS[competitor.threat_level] ?? "default"}>
              {threatLabel}
              <MetricHint metric="threat_rating" />
            </Tag>
            <Tag color="green">
              证据：{competitor.evidence_credibility.label}
              <MetricHint metric="evidence_confidence_level" />
            </Tag>
          </Space>
          <Paragraph className="overview-competitor-reason" ellipsis={{ rows: 3 }} type="secondary">
            {competitor.inclusion_reason}
          </Paragraph>
          <Button
            icon={<ArrowRight aria-hidden="true" size={15} />}
            iconPlacement="end"
            onClick={() => navigateTo(routePathForTask("/battlefield", taskId, { edge_id: edgeId }))}
            type="link"
          >
            查看竞争关系
          </Button>
        </Space>
      </Card>
    </Badge.Ribbon>
  );
}

function OverviewCompetitorImage({ competitor }: { competitor: OverviewKeyCompetitor }) {
  const [hasImageError, setHasImageError] = useState(false);
  const imagePath = resolveBackendAssetUrl(competitor.primary_image_path);

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

function getSliceSelectionFromLocation(): BattlefieldSliceSelection {
  const params = new URLSearchParams(window.location.search);
  return {
    persona: normalizeOptionalText(params.get("persona") ?? ""),
    price_band: normalizeOptionalText(params.get("price_band") ?? ""),
    scenario: normalizeOptionalText(params.get("scenario") ?? "")
  };
}

function isOverviewNotReadyError(error: unknown) {
  return isApiClientError(error) && error.code === "OVERVIEW_NOT_READY";
}

function isOverviewTaskFailedError(error: unknown) {
  return isOverviewNotReadyError(error) && readErrorDetail(error, "status") === "failed";
}

function readErrorDetail(error: unknown, key: string) {
  if (!isApiClientError(error)) {
    return null;
  }

  const value = error.details[key];
  return typeof value === "string" ? value : null;
}

function readErrorTraceId(error: unknown) {
  return isApiClientError(error) && typeof error.traceId === "string" ? error.traceId : null;
}

function isApiClientError(
  error: unknown
): error is { code: string; details: Record<string, unknown>; traceId?: string } {
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    "details" in error &&
    typeof (error as { code?: unknown }).code === "string" &&
    isRecordValue((error as { details?: unknown }).details)
  );
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

function toSelectOptions(values: string[]) {
  return values.map((value) => ({ label: value, value }));
}

function normalizeOptionalText(value: string) {
  const stripped = value.trim();
  return stripped.length > 0 ? stripped : null;
}
