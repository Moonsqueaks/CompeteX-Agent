import {
  Alert,
  Card,
  Drawer,
  Empty,
  FloatButton,
  List,
  Progress,
  Select,
  Space,
  Switch,
  Tabs,
  Tag,
  Timeline,
  Tour,
  Typography
} from "antd";
import { QuestionOutlined } from "@ant-design/icons";
import { Activity, CheckCircle, Network, ShieldAlert, SlidersHorizontal, Zap } from "lucide-react";
import { useMemo, useState, type Ref } from "react";
import { useLocation } from "react-router-dom";
import {
  Background,
  Controls,
  MarkerType,
  Position,
  ReactFlow,
  type Edge as FlowEdge,
  type Node as FlowNode
} from "@xyflow/react";

import type { AppRoute } from "../app/routes";
import {
  RequestStateMessage,
  createErrorState,
  createIdleState,
  createLoadingState,
  createSuccessState
} from "../api";
import type { ApiClient, ApiRequestState, components } from "../api";
import {
  BATTLEFIELD_CLAIM_STATUS_LABELS as CLAIM_STATUS_LABELS,
  BATTLEFIELD_THREAT_TAG_COLORS as THREAT_TAG_COLORS,
  COMPETITION_TYPE_LABELS,
  DECISION_STAGE_LABELS,
  OVERVIEW_RELATIONSHIP_LABELS,
  OVERVIEW_THREAT_LABELS,
  SCORE_BREAKDOWN_DESCRIPTIONS,
  SCORE_BREAKDOWN_LABELS
} from "../domain/labels";
import { isTermKey } from "../domain/termExplanations";
import { EvidenceCard } from "../components/EvidenceCard";
import { MetricHint } from "../components/MetricHint";
import { PageEmptyState } from "../components/PageEmptyState";
import { PageLoadingState } from "../components/PageLoadingState";
import { RiskFlagList } from "../components/RiskFlagList";
import { StatusBadge } from "../components/StatusBadge";
import { TermHint } from "../components/TermHint";
import { useBattlefield } from "../hooks/useBattlefield";
import { formatDateTime } from "../utils/format";

const { Paragraph, Text, Title } = Typography;

type BattlefieldData = components["schemas"]["BattlefieldData"];
type BattlefieldEvidenceCard = components["schemas"]["BattlefieldEvidenceCard"];
type BattlefieldGraphEdge = components["schemas"]["BattlefieldGraphEdge"];
type BattlefieldGraphNode = components["schemas"]["BattlefieldGraphNode"];
type BattlefieldKeyRelation = components["schemas"]["BattlefieldKeyRelation"];
type BattlefieldSliceSelection = components["schemas"]["BattlefieldSliceSelection"];
type TaskApiClient = Pick<ApiClient, "get" | "post"> &
  Partial<Pick<ApiClient, "download" | "getBattlefield" | "getOverview">>;

const EMPTY_VALUE_TEXT = "暂无可靠数据";
const BATTLEFIELD_FLOW_NODE_WIDTH = 190;
const BATTLEFIELD_FLOW_NODE_HEIGHT = 98;

export function BattlefieldPage({
  apiClient,
  route,
  taskId
}: {
  apiClient: TaskApiClient;
  route: AppRoute;
  taskId: string | null;
}) {
  const location = useLocation();
  const locationEdgeId = useMemo(
    () => new URLSearchParams(location.search).get("edge_id"),
    [location.search]
  );
  const [selectedSlice, setSelectedSlice] = useState<BattlefieldSliceSelection>({});
  const [includeAllRelations, setIncludeAllRelations] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);
  const [keyRelationsNode, setKeyRelationsNode] = useState<HTMLDivElement | null>(null);
  const [sliceHudNode, setSliceHudNode] = useState<HTMLDivElement | null>(null);
  const [selectedEdgeSelection, setSelectedEdgeSelection] = useState(() => ({
    edgeId: locationEdgeId,
    search: location.search
  }));
  const tourSteps = useMemo(
    () => [
      {
        description: "这里提取了当前场景下威胁最大的核心竞品，点击卡片可查看详细拆解。",
        target: keyRelationsNode ? () => keyRelationsNode : null,
        title: "1. 先看结论"
      },
      {
        description:
          "您可以随时切换价格、人群或场景。下方图谱中的连线和分数会随之产生动态推演。",
        target: sliceHudNode ? () => sliceHudNode : null,
        title: "2. 动态切片沙盘"
      },
      {
        description: "点击画布中任意一条高亮的连接线，即可从右侧滑出详细的评分逻辑和底层证据。",
        title: "3. 探索图谱"
      }
    ],
    [keyRelationsNode, sliceHudNode]
  );
  const battlefieldQuery = useBattlefield(apiClient, taskId, selectedSlice, includeAllRelations);
  const battlefieldState = toQueryRequestState(battlefieldQuery);
  const battlefield = battlefieldQuery.data;
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
  const selectedEdgeId =
    selectedEdgeSelection.search === location.search ? selectedEdgeSelection.edgeId : locationEdgeId;
  const selectedEdge =
    visibleGraphEdges.find((edge) => edge.edge_id === selectedEdgeId) ??
    battlefield?.graph_edges?.find((edge) => edge.edge_id === selectedEdgeId) ??
    null;

  function openEdgeInsight(edgeId: string) {
    setSelectedEdgeSelection({ edgeId, search: location.search });
  }

  function closeEdgeInsight() {
    setSelectedEdgeSelection({ edgeId: null, search: location.search });
  }

  function updateSlice(field: keyof BattlefieldSliceSelection, value: string | null) {
    closeEdgeInsight();
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
    closeEdgeInsight();
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
        <div className="battlefield-modern-page">
          {battlefieldState.status === "loading" || battlefieldState.status === "retrying" ? (
            <PageLoadingState
              text={battlefieldState.status === "retrying" ? "正在重新读取竞争图谱" : "正在读取竞争图谱"}
            />
          ) : (
            <RequestStateMessage
              className="profile-state-message"
              loadingText="正在读取竞争图谱"
              onRetry={() => void battlefieldQuery.refetch()}
              state={battlefieldState}
            />
          )}

          {battlefield ? (
            <div className="battlefield-modern-shell">
              <aside className="battlefield-modern-outline" aria-label="竞争图谱分析大纲">
                <QASummaryCard data={battlefield} />
                <div ref={setKeyRelationsNode}>
                  <KeyRelationsCard
                    onSelectEdge={openEdgeInsight}
                    relations={battlefield.key_relations ?? []}
                    selectedEdgeId={selectedEdgeId}
                  />
                </div>
                <DecisionChainCard data={battlefield} />
              </aside>

              <div className="battlefield-modern-canvas">
                <SliceHud
                  data={battlefield}
                  includeAllRelations={includeAllRelations}
                  rootRef={setSliceHudNode}
                  selectedSlice={selectedSlice}
                  setIncludeAllRelations={updateRelationScope}
                  updateSlice={updateSlice}
                />
                <CompetitionGraph
                  edges={graph.edges}
                  nodes={graph.nodes}
                  onSelectEdge={openEdgeInsight}
                />
              </div>

              <InsightDrawer
                data={battlefield}
                onClose={closeEdgeInsight}
                open={Boolean(selectedEdgeId)}
                selectedEdge={selectedEdge}
              />
              <Tour onClose={() => setTourOpen(false)} open={tourOpen} steps={tourSteps} />
              <FloatButton
                aria-label="新手引导"
                icon={<QuestionOutlined />}
                onClick={() => setTourOpen(true)}
                tooltip="新手引导"
              />
            </div>
          ) : null}
        </div>
      ) : (
        <PageEmptyState />
      )}
    </section>
  );
}

function QASummaryCard({ data }: { data: BattlefieldData }) {
  const qa = data.qa_summary;
  const isPassed = qa.qa_status === "passed";

  return (
    <Card
      className="battlefield-modern-card battlefield-modern-qa"
      size="small"
      styles={{ body: { padding: 16 } }}
    >
      <Space align="start">
        {isPassed ? (
          <CheckCircle color="#16a34a" size={20} />
        ) : (
          <ShieldAlert color="#dc2626" size={20} />
        )}
        <div>
          <Text strong>{isPassed ? "图谱质检已通过" : "图谱包含需关注风险"}</Text>
          <div className="battlefield-modern-muted">
            ReviewTask {qa.review_task_count} 条，开放 {qa.open_review_task_count} 条，已解决{" "}
            {qa.resolved_review_task_count} 条
            <MetricHint metric="qa_review_counts" />
          </div>
          <div className="battlefield-modern-muted">
            打回消息 {qa.revision_message_count} 条，风险边{" "}
            {qa.risk_edge_ids?.length ? `${qa.risk_edge_ids.length} 条` : "无"}
          </div>
        </div>
      </Space>
    </Card>
  );
}

function KeyRelationsCard({
  onSelectEdge,
  relations,
  selectedEdgeId
}: {
  onSelectEdge: (edgeId: string) => void;
  relations: BattlefieldKeyRelation[];
  selectedEdgeId: string | null;
}) {
  return (
    <Card
      aria-label="关键竞争关系"
      className="battlefield-modern-card"
      size="small"
      title={
        <Space>
          <Zap color="#d97706" size={16} />
          关键关系速览
        </Space>
      }
      styles={{ body: { padding: "12px 16px" } }}
    >
      <List
        dataSource={relations}
        locale={{ emptyText: "当前切片下无关键关系" }}
        renderItem={(relation) => (
          <button
            aria-label={`查看深研：${relation.competitor_product_name}`}
            className={
              relation.edge_id === selectedEdgeId
                ? "battlefield-modern-relation battlefield-modern-relation-active"
                : "battlefield-modern-relation"
            }
            onClick={() => onSelectEdge(relation.edge_id)}
            type="button"
          >
            <span className="battlefield-modern-relation-heading">
              <Text strong>{relation.competitor_product_name}</Text>
              <span className="battlefield-modern-relation-tags">
                <Tag color={THREAT_TAG_COLORS[relation.threat_level] ?? "blue"}>
                  {OVERVIEW_THREAT_LABELS[relation.threat_level] ?? relation.threat_level}
                  <MetricHint metric="threat_rating" />
                </Tag>
                <Tag color="green">
                  {relation.evidence_credibility.label}
                  <MetricHint metric="evidence_confidence_level" />
                </Tag>
              </span>
            </span>
            <span className="battlefield-modern-muted">
              {OVERVIEW_RELATIONSHIP_LABELS[relation.relationship_label] ??
                relation.relationship_label}
            </span>
            <span className="battlefield-modern-muted">{relation.inclusion_reason}</span>
            <span className="secondary-action key-relation-action">
              <span>查看深研</span>
              <strong>{relation.competitor_product_name}</strong>
            </span>
          </button>
        )}
        size="small"
      />
    </Card>
  );
}

function DecisionChainCard({ data }: { data: BattlefieldData }) {
  const items = (data.decision_chain ?? []).map((stage) => ({
    children: (
      <div className="battlefield-modern-timeline-item">
        <span>
          <Text strong>{DECISION_STAGE_LABELS[stage.stage] ?? stage.stage}</Text>
          <Text type="secondary">
            {Math.round(stage.average_edge_score * 100)} 分
            <MetricHint metric="decision_stage_average_score" />
          </Text>
        </span>
        <Text type="secondary">
          关系 {stage.edge_ids?.length ?? 0} | 结论 {stage.claim_ids?.length ?? 0} | 证据{" "}
          {stage.evidence_ids?.length ?? 0}
        </Text>
      </div>
    ),
    color: stage.average_edge_score > 0.5 ? "blue" : "gray"
  }));

  return (
    <Card
      className="battlefield-modern-card"
      size="small"
      title={
        <Space>
          <Activity size={16} />
          决策链影响分布
        </Space>
      }
      styles={{ body: { padding: 16 } }}
    >
      <Timeline items={items} />
    </Card>
  );
}

function SliceHud({
  data,
  includeAllRelations,
  rootRef,
  selectedSlice,
  setIncludeAllRelations,
  updateSlice
}: {
  data: BattlefieldData;
  includeAllRelations: boolean;
  rootRef: Ref<HTMLDivElement>;
  selectedSlice: BattlefieldSliceSelection;
  setIncludeAllRelations: (includeAllRelations: boolean) => void;
  updateSlice: (field: keyof BattlefieldSliceSelection, value: string | null) => void;
}) {
  return (
    <div className="battlefield-modern-hud" aria-label="切片拨盘" ref={rootRef}>
      <span className="battlefield-modern-hud-title">
        <SlidersHorizontal size={16} />
        <Text className="battlefield-modern-hud-title-text" strong>
          动态切片
        </Text>
        <Text className="battlefield-modern-hud-subtitle" type="secondary">
          按价格带、人群和使用场景刷新判断
        </Text>
        <TermHint term="dynamic_slice" showLabel={false} />
      </span>
      <Select
        allowClear
        aria-label="价格带"
        className="battlefield-modern-select"
        onChange={(value) => updateSlice("price_band", value)}
        options={selectOptions(data.available_slices ?? [], "price_band")}
        placeholder="全价格带"
        value={selectedSlice.price_band || undefined}
        variant="borderless"
      />
      <Select
        allowClear
        aria-label="用户人群"
        className="battlefield-modern-select"
        onChange={(value) => updateSlice("persona", value)}
        options={selectOptions(data.available_slices ?? [], "persona")}
        placeholder="全人群"
        value={selectedSlice.persona || undefined}
        variant="borderless"
      />
      <Select
        allowClear
        aria-label="使用场景"
        className="battlefield-modern-select"
        onChange={(value) => updateSlice("scenario", value)}
        options={selectOptions(data.available_slices ?? [], "scenario")}
        placeholder="全场景"
        value={selectedSlice.scenario || undefined}
        variant="borderless"
      />
      {data.relation_filter ? (
        <Space className="battlefield-modern-switch" size={8}>
          <Switch
            aria-label="展开全部关系"
            checked={includeAllRelations}
            disabled={!data.relation_filter.can_expand_all && !includeAllRelations}
            onChange={setIncludeAllRelations}
            size="small"
          />
          <Text type="secondary">
            {data.relation_filter.visible_relation_count} /{" "}
            {data.relation_filter.total_relation_count} 条
          </Text>
        </Space>
      ) : null}
      <Text className="battlefield-modern-slice-summary" type="secondary">
        {formatSelectedSlice(selectedSlice)}
      </Text>
    </div>
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
    <section className="battlefield-modern-graph" aria-label="竞争关系图">
      <div className="competition-flow" data-testid="competition-flow">
        <ReactFlow
          edges={edges}
          fitView
          nodes={nodes}
          nodesDraggable={false}
          onEdgeClick={(_, edge) => onSelectEdge(edge.id)}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={20} color="#cbd5e1" />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </section>
  );
}

function InsightDrawer({
  data,
  onClose,
  open,
  selectedEdge
}: {
  data: BattlefieldData;
  onClose: () => void;
  open: boolean;
  selectedEdge: BattlefieldGraphEdge | null;
}) {
  const selectedRelation =
    selectedEdge && data.key_relations
      ? (data.key_relations.find((relation) => relation.edge_id === selectedEdge.edge_id) ?? null)
      : null;
  const edgeEvidenceCards = selectedEdge
    ? (data.evidence_cards ?? []).filter((card) =>
        (selectedEdge.evidence_ids ?? []).includes(card.evidence_id)
      )
    : [];

  return (
    <Drawer
      mask={false}
      onClose={onClose}
      open={open}
      placement="right"
      rootClassName="battlefield-modern-insight-drawer"
      styles={{ body: { background: "#f8fafc", padding: 0 } }}
      title={
        <Space>
          <Network color="#0f766e" size={18} />
          边关系深研面板
        </Space>
      }
      width="min(520px, 100vw)"
    >
      <aside aria-label="竞争边详情" className="battlefield-modern-drawer" role="complementary">
        {selectedEdge ? (
          <>
            <Card size="small" title="关系详情">
              <div
                className={
                  selectedEdge.risk_status === "at_risk"
                    ? "edge-score edge-score-risk"
                    : "edge-score"
                }
              >
                <span>
                  {COMPETITION_TYPE_LABELS[selectedEdge.competition_type]}
                  <small>综合得分</small>
                </span>
                <span className="edge-score-value">
                  <strong>{Math.round(selectedEdge.edge_score * 100)}</strong>
                  <MetricHint metric="edge_score" />
                  <RatingBadge score={selectedEdge.edge_score} />
                </span>
              </div>
              <p className="edge-readable-name">{formatSelectedRelationName(selectedRelation)}</p>
              <Text type="secondary">竞争边解释</Text>
              <div className="battlefield-modern-quick-sections" aria-label="深研内容索引">
                <Text>结论依据</Text>
                <Text>证据卡片</Text>
                <Text>质检打回记录</Text>
                <Tag>
                  {data.qa_summary.review_task_count} 条
                  <MetricHint metric="qa_review_counts" />
                </Tag>
              </div>
            </Card>

            <Tabs
              className="battlefield-modern-tabs"
              defaultActiveKey="score"
              items={[
                {
                  children: <ScoreBreakdown edge={selectedEdge} />,
                  key: "score",
                  label: "多维评分"
                },
                {
                  children: <ClaimList edge={selectedEdge} />,
                  key: "claims",
                  label: (
                    <span className="metric-label-with-hint">
                      分析结论 ({selectedEdge.claim_refs?.length ?? 0})
                      <MetricHint metric="metric_count" />
                    </span>
                  )
                },
                {
                  children: <EvidenceList cards={edgeEvidenceCards} />,
                  key: "evidence",
                  label: (
                    <span className="metric-label-with-hint">
                      底层证据 ({selectedEdge.evidence_ids?.length ?? 0})
                      <MetricHint metric="metric_count" />
                    </span>
                  )
                },
                {
                  children: <FourPartExplanation relation={selectedRelation} />,
                  key: "explanation",
                  label: "四段解释"
                }
              ]}
            />
          </>
        ) : (
          <Empty description="请选择一条竞争关系" />
        )}
        <QASummaryCard data={data} />
      </aside>
    </Drawer>
  );
}

function ScoreBreakdown({ edge }: { edge: BattlefieldGraphEdge }) {
  return (
    <div aria-label="评分拆解" className="battlefield-modern-tab-body">
      <div className="battlefield-modern-score-heading">
        <Title level={2} style={{ color: "#0f766e", margin: 0 }}>
          {Math.round(edge.edge_score * 100)}
          <span className="battlefield-modern-score-suffix">
            /100 综合得分
            <MetricHint metric="edge_score" />
          </span>
        </Title>
        <RatingBadge score={edge.edge_score} />
      </div>
      {Object.entries(edge.score_breakdown).map(([key, value]) => (
        <div className="battlefield-modern-score-row" key={key}>
          <span>
            <span className="battlefield-modern-score-label">
              <Text strong>{SCORE_BREAKDOWN_LABELS[key] ?? key}</Text>
              {isTermKey(key) ? <TermHint term={key} showLabel={false} /> : null}
              <MetricHint metric="score_breakdown_value" />
            </span>
            <Text>{Math.round(value * 100)}</Text>
          </span>
          <Text className="battlefield-modern-score-description" type="secondary">
            {SCORE_BREAKDOWN_DESCRIPTIONS[key] ?? "暂无可靠数据"}
          </Text>
          <Progress percent={Math.round(value * 100)} showInfo={false} strokeColor="#0ea5e9" />
        </div>
      ))}
    </div>
  );
}

function RatingBadge({ score }: { score: number }) {
  const hint = <MetricHint metric="threat_rating" />;

  if (score >= 0.8) {
    return <StatusBadge color="error" label={<span className="metric-label-with-hint">致命威胁 (优先应对){hint}</span>} />;
  }

  if (score >= 0.6) {
    return <StatusBadge color="warning" label={<span className="metric-label-with-hint">高度警惕 (持续观察){hint}</span>} />;
  }

  return <StatusBadge color="success" label={<span className="metric-label-with-hint">低度威胁 (暂无大碍){hint}</span>} />;
}

function ClaimList({ edge }: { edge: BattlefieldGraphEdge }) {
  return (
    <section className="battlefield-modern-tab-body" aria-label="结论与证据">
      <Title level={5}>结论与证据</Title>
      {(edge.claim_refs ?? []).length > 0 ? (
        (edge.claim_refs ?? []).map((claim) => (
        <Card key={claim.claim_id} size="small" style={{ marginBottom: 12 }}>
          <Space style={{ marginBottom: 8 }}>
            <Tag color="purple">
              置信度 {Math.round(claim.confidence * 100)}%
              <MetricHint metric="claim_confidence" />
            </Tag>
            <Text type="secondary">
              {CLAIM_STATUS_LABELS[claim.status] ?? formatReadableText(claim.status)}
            </Text>
          </Space>
          <Paragraph>{formatReadableText(claim.content)}</Paragraph>
          <RiskFlagList
            className="battlefield-modern-risk-tags"
            color="error"
            riskFlags={claim.risk_flags ?? []}
          />
        </Card>
        ))
      ) : (
        <Empty description="暂无直接关联的分析结论" />
      )}
    </section>
  );
}

function EvidenceList({ cards }: { cards: BattlefieldEvidenceCard[] }) {
  return (
    <section className="battlefield-modern-tab-body" aria-label="证据卡片">
      {cards.length > 0 ? (
        cards.map((card, index) => (
        <EvidenceCard
          accessTimeText={
            card.access_time_status === "available"
              ? formatDateTime(card.access_time, { emptyText: EMPTY_VALUE_TEXT, style: "localized" })
              : EMPTY_VALUE_TEXT
          }
          accessTimeStatus={card.access_time_status}
          className="battlefield-evidence-card"
          confidenceLevel={card.confidence_level}
          contentSummary={card.content_summary}
          emptyText={EMPTY_VALUE_TEXT}
          formatText={formatReadableText}
          key={card.evidence_id}
          limitations={card.limitations}
          riskFlags={card.risk_flags ?? []}
          sourceType={card.source_type}
          style={{ marginBottom: 12 }}
          title={`证据 ${index + 1}`}
        />
        ))
      ) : (
        <Empty description="暂无直接绑定的底层证据" />
      )}
    </section>
  );
}

function FourPartExplanation({ relation }: { relation: BattlefieldKeyRelation | null }) {
  const [selectedBasis, setSelectedBasis] = useState<{
    label: string;
    segment: BattlefieldKeyRelation["four_part_explanation"]["why_competitor"];
  } | null>(null);

  if (!relation) {
    return <Empty description="暂无可追溯的四段式解释" />;
  }

  const segments = [
    ["为什么是竞品", relation.four_part_explanation.why_competitor],
    ["强在哪", relation.four_part_explanation.strength],
    ["影响哪个决策阶段", relation.four_part_explanation.decision_stage_impact],
    ["应对建议", relation.four_part_explanation.response_suggestion]
  ] as const;

  return (
    <div aria-label="四段式竞争解释" className="battlefield-modern-tab-body">
      {segments.map(([label, segment]) => (
        <Card key={label} size="small" style={{ marginBottom: 12 }}>
          <Text strong>{label}</Text>
          {segment.is_analysis_suggestion ? <Tag color="blue">分析建议</Tag> : null}
          <Paragraph style={{ marginTop: 8 }}>{segment.text}</Paragraph>
          <RiskFlagList
            className="battlefield-modern-risk-tags"
            color="error"
            riskFlags={segment.risk_flags ?? []}
          />
          <Alert
            className="battlefield-modern-basis"
            title="解释依据详情"
            showIcon
            type={segment.evidence_ids?.length ? "info" : "warning"}
            description={`相关结论 ${segment.claim_ids?.length ?? 0} 条 / 相关证据 ${
              segment.evidence_ids?.length ?? 0
            } 条`}
          />
          <button
            className="secondary-action battlefield-modern-basis-action"
            onClick={() => setSelectedBasis({ label, segment })}
            type="button"
          >
            查看依据
          </button>
        </Card>
      ))}
      {selectedBasis ? (
        <section aria-label="解释依据详情" className="battlefield-modern-basis-detail">
          <Text strong>{selectedBasis.label}的依据</Text>
          <Space size={8}>
            <Tag>{selectedBasis.segment.claim_ids?.length ?? 0} 条结论</Tag>
            <Tag>{selectedBasis.segment.evidence_ids?.length ?? 0} 条证据</Tag>
          </Space>
        </section>
      ) : null}
    </div>
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
    position: isTarget
      ? { x: 20, y: 180 }
      : { x: 360 + competitorColumn * 260, y: 40 + competitorRow * 140 },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    type: "default",
    width
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
      stroke: edge.risk_status === "at_risk" ? "#c2410c" : "#0f766e",
      strokeWidth: 2 + edge.edge_score * 2
    },
    target: edge.target,
    type: "smoothstep"
  };
}

function selectOptions(
  slices: NonNullable<BattlefieldData["available_slices"]>,
  field: keyof NonNullable<BattlefieldData["available_slices"]>[number]
) {
  return Array.from(
    new Set(
      slices
        .map((slice) => slice[field])
        .filter((value): value is string => typeof value === "string" && value.length > 0)
    )
  ).map((value) => ({ label: value, value }));
}

function formatSelectedRelationName(relation: BattlefieldKeyRelation | null) {
  if (!relation) {
    return "当前竞争关系";
  }

  return `${relation.competitor_product_name} 与目标产品的${
    OVERVIEW_RELATIONSHIP_LABELS[relation.relationship_label] ?? "竞争关系"
  }`;
}

function formatReadableText(value: string | null | undefined) {
  return value && value.trim().length > 0 ? value : EMPTY_VALUE_TEXT;
}

function formatSelectedSlice(slice: BattlefieldSliceSelection) {
  return `价格带 ${slice.price_band ?? "全部"} / ${slice.persona ?? "全部人群"} / ${
    slice.scenario ?? "全部场景"
  }`;
}
