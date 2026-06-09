import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Anchor,
  Button,
  Card,
  Collapse,
  Space,
  Typography
} from "antd";
import { ArrowLeft, Download, FileText, Printer, RefreshCw } from "lucide-react";
import { type ReactNode, useEffect, useState } from "react";

import {
  RequestStateMessage,
  createErrorState,
  createIdleState,
  createLoadingState,
  createSuccessState
} from "../api";
import type { ApiClient, ApiRequestState, components } from "../api";
import { navigateTo, routePathForTask, type AppRoute } from "../app/routes";
import {
  CLAIM_STATUS_LABELS,
  COMPETITION_TYPE_LABELS,
  CONFIDENCE_DETAIL_LABELS,
  CONFIDENCE_LABELS,
  DECISION_STAGE_LABELS,
  DECISION_STAGE_REPORT_GUIDANCE,
  REPORT_FIELD_LABELS,
  REPORT_SECTION_FALLBACK_TITLES,
  REPORT_SECTION_PREVIEW_LIMITS,
  RUN_STATUS_LABELS,
  SOURCE_TYPE_LABELS,
  TASK_STATUS_LABELS
} from "../domain/labels";
import { MetricHint } from "../components/MetricHint";
import { PageEmptyState } from "../components/PageEmptyState";
import { PageLoadingState } from "../components/PageLoadingState";
import { WarningRiskFlagList } from "../components/RiskFlagList";
import { useReport, type CompletedReportCache } from "../hooks/useReport";
import {
  formatDateTime,
  formatScore,
  isInternalIdentifier,
  isRecordValue,
  stringValue
} from "../utils/format";
import { isSensitiveTraceKey, sanitizeTraceText } from "../utils/sanitize";

export type { CompletedReportCache } from "../hooks/useReport";

const { Paragraph, Text, Title } = Typography;

type TaskApiClient = Pick<ApiClient, "get" | "post"> & Partial<Pick<ApiClient, "download">>;
type ReportData = components["schemas"]["ReportData"];
type ReportSection = components["schemas"]["ReportSection"];
type TaskStatus = components["schemas"]["TaskStatus"];

type ReportEdgeDetail = {
  competitionType?: string;
  name: string;
  sliceLabel?: string;
};

type NarrativeReportSection = {
  paragraphs: string[];
  section_id: string;
  title: string;
};

type ReportContext = {
  edgeDetails: Record<string, ReportEdgeDetail>;
  productNames: Record<string, string>;
  targetName: string;
};

const EMPTY_VALUE_TEXT = "暂无可靠数据";
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

export function ReportPage({
  apiClient,
  completedReportCache,
  route,
  taskId
}: {
  apiClient: TaskApiClient;
  completedReportCache: CompletedReportCache;
  route: AppRoute;
  taskId: string | null;
}) {
  const queryClient = useQueryClient();
  const { reportQuery, reportQueryKey } = useReport(apiClient, taskId, completedReportCache);
  const reportWaiting = isReportNotReadyError(reportQuery.error);
  const { data: report, refetch: refetchReport } = reportQuery;

  useEffect(() => {
    if (taskId && report && !reportWaiting) {
      completedReportCache.set(taskId, report);
    }
  }, [completedReportCache, report, reportWaiting, taskId]);

  useEffect(() => {
    if (!reportWaiting) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      void refetchReport();
    }, 2000);
    return () => window.clearInterval(intervalId);
  }, [refetchReport, reportWaiting]);

  const reportState = toQueryRequestState(reportQuery);
  const reportMessageState = reportWaiting ? createIdleState<ReportData>() : reportState;

  function handleReportRegenerated(nextReport: ReportData) {
    if (!taskId) {
      return;
    }

    completedReportCache.set(taskId, nextReport);
    queryClient.setQueryData(reportQueryKey, nextReport);
  }

  return (
    <section className="page-surface report-page-surface" aria-labelledby="page-title">
      <div className="page-intro">
        <p className="page-kicker">网页报告</p>
        <h3 id="page-title">{route.title}</h3>
        <p>{route.summary}</p>
      </div>

      {taskId ? (
        <div className="report-layout">
          {reportMessageState.status === "loading" || reportMessageState.status === "retrying" ? (
            <PageLoadingState
              text={reportMessageState.status === "retrying" ? "正在重新读取分析报告" : "正在读取分析报告"}
            />
          ) : (
            <RequestStateMessage
              className="profile-state-message"
              loadingText="正在读取分析报告"
              onRetry={() => void refetchReport()}
              state={reportMessageState}
            />
          )}

          {reportWaiting ? (
            <ReportWaitingState
              onRetry={() => void refetchReport()}
              status={readErrorDetail(reportQuery.error, "status")}
            />
          ) : null}

          {report ? (
            <ReportDocument
              apiClient={apiClient}
              onReportRegenerated={handleReportRegenerated}
              report={report}
              taskId={taskId}
            />
          ) : null}
        </div>
      ) : (
        <PageEmptyState />
      )}
    </section>
  );
}

function ReportWaitingState({ onRetry, status }: { onRetry: () => void; status: string | null }) {
  return (
    <div className="page-loading-with-action" role="status">
      <PageLoadingState
        text={`报告正在生成${
          status ? `，当前状态：${TASK_STATUS_LABELS[status as TaskStatus] ?? status}` : ""
        }`}
      />
      <Button onClick={onRetry} type="primary">
        重新检查
      </Button>
    </div>
  );
}

function ReportDocument({
  apiClient,
  onReportRegenerated,
  report,
  taskId
}: {
  apiClient: TaskApiClient;
  onReportRegenerated: (report: ReportData) => void;
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
  const reportRegenerateMutation = useMutation({
    mutationFn: () =>
      apiClient.post<ReportData>(`/tasks/${encodeURIComponent(taskId)}/report/regenerate`),
    onSuccess: onReportRegenerated
  });
  const narrativeSections = getNarrativeReportSections(report);
  const reportSections = getOrderedReportSections(report);
  const reportContext = createReportContext(report);
  const reportDisplayName = createReportDisplayName(reportContext.targetName);
  const anchorItems =
    narrativeSections.length > 0
      ? narrativeSections.map((section, index) => ({
          href: `#${section.section_id}`,
          key: section.section_id,
          title: `${String(index + 1).padStart(2, "0")} ${section.title}`
        }))
      : reportSections.map((section, index) => ({
          href: `#${section.section_id}`,
          key: section.section_id,
          title: `${String(index + 1).padStart(2, "0")} ${formatReportSectionTitle(section)}`
        }));

  return (
    <div className={printView ? "report-document-shell report-print-mode" : "report-document-shell"}>
      <main className="report-document" aria-label="竞品分析白皮书">
        <div className="report-toolbar no-print" aria-label="报告工作台工具栏">
          <Button
            icon={<ArrowLeft size={16} />}
            onClick={() => navigateTo(routePathForTask("/overview", taskId))}
            type="text"
          >
            返回总览
          </Button>
          <Space wrap>
            <Button icon={<Printer size={16} />} onClick={() => window.print()}>
              打印或另存 PDF
            </Button>
            <Button onClick={() => setPrintView((current) => !current)}>
              {printView ? "返回工作台视图" : "切换打印视图"}
            </Button>
            <Button
              icon={<RefreshCw size={16} />}
              loading={reportRegenerateMutation.isPending}
              onClick={() => reportRegenerateMutation.mutate()}
            >
              重新生成报告
            </Button>
            <Button
              icon={<Download size={16} />}
              loading={wordExportMutation.isPending}
              onClick={() => wordExportMutation.mutate()}
              type="primary"
            >
              下载 Word 报告
            </Button>
          </Space>
        </div>

        <ReportMutationState
          reportRegenerateMutation={reportRegenerateMutation}
          wordExportMutation={wordExportMutation}
        />

        <ReportCover report={report} reportDisplayName={reportDisplayName} />

        <section className="report-static-graph" aria-label="静态图谱摘要">
          <div>
            <p className="section-kicker">静态图谱摘要</p>
            <h4>核心竞争关系摘要</h4>
            <p>打印视图保留核心关系、证据和质检附录，便于离线评审。</p>
          </div>
          <span>{narrativeSections.length || reportSections.length} 个章节</span>
        </section>

        <div className="report-section-list" aria-label="报告章节">
          {narrativeSections.length > 0
            ? narrativeSections.map((section, index) => (
                <NarrativeReportSectionArticle
                  index={index}
                  key={section.section_id}
                  section={section}
                />
              ))
            : reportSections.map((section, index) => (
                <ReportSectionArticle
                  context={reportContext}
                  index={index}
                  key={section.section_id}
                  section={section}
                  taskId={taskId}
                />
              ))}
        </div>
      </main>

      <aside className="report-anchor-panel no-print" aria-label="文档目录">
        <Title level={5}>文档目录</Title>
        <Anchor affix={false} items={anchorItems} targetOffset={60} />
      </aside>
    </div>
  );
}

function ReportMutationState({
  reportRegenerateMutation,
  wordExportMutation
}: {
  reportRegenerateMutation: ReturnType<typeof useMutation<ReportData, Error, void>>;
  wordExportMutation: ReturnType<typeof useMutation<{ fileName: string }, Error, void>>;
}) {
  return (
    <div className="report-mutation-state no-print">
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
      {reportRegenerateMutation.isSuccess ? (
        <div className="review-success" role="status">
          报告已重新生成：{reportRegenerateMutation.data.report_id}
        </div>
      ) : null}
      {reportRegenerateMutation.isError ? (
        <RequestStateMessage
          className="review-error"
          state={createErrorState(reportRegenerateMutation.error)}
        />
      ) : null}
    </div>
  );
}

function ReportCover({
  report,
  reportDisplayName
}: {
  report: ReportData;
  reportDisplayName: string;
}) {
  return (
    <header className="report-cover">
      <Text className="report-cover-kicker">竞品分析报告 / Competitive Analysis</Text>
      <Title level={1}>{reportDisplayName}</Title>
      <Space className="report-cover-meta" separator={<span aria-hidden="true">/</span>} wrap>
        <Text>报告流水号：{formatReportId(report.report_id)}</Text>
        <Text>
          生成时间：
          {formatDateTime(report.generated_at, {
            emptyText: EMPTY_VALUE_TEXT,
            fallback: formatDisplayText
          })}
        </Text>
      </Space>
      <Alert
        className="report-cover-notice"
        description="本报告由智能体基于数据快照与证据链自动化生成。存在风险或证据不足的结论已作保守降级处理，具体证据和质检记录可在附录或过程追踪页复核。"
        showIcon
        title="阅读须知"
        type="info"
      />
    </header>
  );
}

function NarrativeReportSectionArticle({
  index,
  section
}: {
  index: number;
  section: NarrativeReportSection;
}) {
  return (
    <article className="report-section-card narrative-report-section" id={section.section_id}>
      <div className="report-section-heading">
        <Text className="report-section-number">{String(index + 1).padStart(2, "0")}</Text>
        <div>
          <p className="section-kicker">正式报告章节</p>
          <Title level={4}>{section.title}</Title>
        </div>
      </div>
      <div className="report-analysis-paragraphs">
        {section.paragraphs.map((paragraph, paragraphIndex) => (
          <Paragraph key={paragraphIndex}>{paragraph}</Paragraph>
        ))}
      </div>
    </article>
  );
}

function ReportSectionArticle({
  context,
  index,
  section,
  taskId
}: {
  context: ReportContext;
  index: number;
  section: ReportSection;
  taskId: string;
}) {
  return (
    <article className="report-section-card" id={section.section_id}>
      <div className="report-section-heading">
        <Text className="report-section-number">{String(index + 1).padStart(2, "0")}</Text>
        <div>
          <p className="section-kicker">分析章节</p>
          <Title level={4}>{formatReportSectionTitle(section)}</Title>
        </div>
      </div>
      <p className="report-section-summary">{formatReportSectionSummary(section)}</p>
      <ReportItemList context={context} items={section.items ?? []} section={section} />
      <ReportEvidenceCollapse section={section} taskId={taskId} />
    </article>
  );
}

function formatReportSectionSummary(section: ReportSection) {
  switch (section.section_id) {
    case "conclusion_summary":
      return "先看一句话结论：谁带来压力、主要比较什么、依据是否足够。";
    case "competitive_landscape_judgment":
    case "dynamic_slice_analysis":
      return "按价格带、人群和场景找出最需要优先看的竞争压力。";
    case "core_competitor_analysis":
    case "competitor_findings":
      return "只展开最容易被用户放进同一候选集比较的竞品。";
    case "user_decision_chain_analysis":
    case "decision_chain_analysis":
      return "说明用户在哪个决策环节最容易改变选择。";
    case "target_opportunities_and_risks":
    case "product_profile":
      return "梳理目标产品当前可讲清的机会和仍需补证的风险。";
    case "product_strategy_recommendations":
    case "recommendations":
      return "给出下一步最值得优先调整的表达和证据动作。";
    case "evidence_index":
      return "集中查看支撑报告判断的证据材料。";
    case "evidence_quality_appendix":
      return "说明哪些结论证据较足，哪些需要保守处理。";
    case "analysis_process_appendix":
      return "保留生成流程摘要，技术细节仍放在过程追踪页。";
    default:
      return formatReportText(section.summary);
  }
}

function ReportItemList({
  context,
  items,
  section
}: {
  context: ReportContext;
  items: NonNullable<ReportSection["items"]>;
  section: ReportSection;
}) {
  if (items.length === 0) {
    return <p className="muted-copy">{EMPTY_VALUE_TEXT}</p>;
  }

  if (section.section_id === "conclusion_summary") {
    return <ReportConclusionSummary context={context} items={items} />;
  }

  const previewLimit = REPORT_SECTION_PREVIEW_LIMITS[section.section_id] ?? items.length;
  const visibleItems = items.slice(0, previewLimit);
  const hiddenCount = Math.max(0, items.length - visibleItems.length);

  return (
    <div className="report-item-list">
      {visibleItems.map((item, index) => (
        <ReportAnalysisItem
          context={context}
          index={index}
          item={item}
          key={`${section.section_id}-${index}`}
          sectionId={section.section_id}
        />
      ))}
      {hiddenCount > 0 ? (
        <p className="muted-copy">
          另有 {hiddenCount} 条关系已纳入本章统计，正文只展开最需要优先看的判断。
        </p>
      ) : null}
    </div>
  );
}

function ReportConclusionSummary({
  context,
  items
}: {
  context: ReportContext;
  items: NonNullable<ReportSection["items"]>;
}) {
  const competitorNames = items
    .map((item, index) => getReportCompetitorName(item, context, index))
    .filter((name) => name !== EMPTY_VALUE_TEXT)
    .slice(0, 3);
  const relationTypes = uniqueReportValues(
    items
      .map((item) => stringValue(item.competition_type))
      .filter((value): value is string => Boolean(value))
      .map((value) => formatReportEnumValue(value, "competition_type"))
  );
  const competitorText = joinReportList(competitorNames, "同类竞品");
  const relationText = joinReportList(relationTypes, "直接竞品");

  const firstItem = items[0] ?? {};
  const largestThreat = stringValue(firstItem.largest_threat);
  const largestOpportunity = stringValue(firstItem.largest_opportunity);
  const firstAction = stringValue(firstItem.first_action);
  const evidenceBoundary = stringValue(firstItem.evidence_boundary);

  if (largestThreat || largestOpportunity || firstAction) {
    return (
      <Card className="report-analysis-card report-conclusion-card" size="small">
        <Title level={5}>总体判断</Title>
        <div className="report-analysis-paragraphs">
          <p>
            {context.targetName} 当前最需要优先关注的是
            {largestThreat ? ` ${sanitizeTraceText(largestThreat)}` : " 核心竞品"}。
            {stringValue(firstItem.why_it_matters)
              ? ` ${formatReportText(stringValue(firstItem.why_it_matters) ?? "")}`
              : ""}
          </p>
          <p>
            最大机会是
            {largestOpportunity ? ` ${sanitizeTraceText(largestOpportunity)}` : "先把核心卖点讲清楚"}；
            首要动作是
            {firstAction ? ` ${formatReportText(firstAction)}` : "补齐证据后再做确定判断"}。
          </p>
          {evidenceBoundary ? <p>{formatReportText(evidenceBoundary)}</p> : null}
        </div>
      </Card>
    );
  }

  return (
    <Card className="report-analysis-card report-conclusion-card" size="small">
      <Title level={5}>总体判断</Title>
      <div className="report-analysis-paragraphs">
        <p>
          {context.targetName} 当前主要压力来自 {competitorText}；关系以{relationText}
          为主，核心比较点是省心清理、除臭容量和价格解释。
        </p>
      </div>
    </Card>
  );
}

function ReportAnalysisItem({
  context,
  index,
  item,
  sectionId
}: {
  context: ReportContext;
  index: number;
  item: Record<string, unknown>;
  sectionId: string;
}) {
  const title = getReportItemTitle(item, sectionId, index, context);
  const paragraphs = buildReportItemParagraphs(item, sectionId, index, context);

  if (paragraphs.length > 0) {
    return (
      <Card className="report-analysis-card" size="small">
        {title ? <Title level={5}>{title}</Title> : null}
        <div className="report-analysis-paragraphs">
          {paragraphs.map((paragraph, paragraphIndex) => (
            <Paragraph key={paragraphIndex}>{paragraph}</Paragraph>
          ))}
        </div>
        <WarningRiskFlagList riskFlags={readRiskFlags(item)} />
      </Card>
    );
  }

  return (
    <Card className="report-item" size="small">
      {title ? <Title level={5}>{title}</Title> : null}
      <dl>{renderReportItemFields(item, sectionId)}</dl>
    </Card>
  );
}

function ReportEvidenceCollapse({ section, taskId }: { section: ReportSection; taskId: string }) {
  const claimIds = section.claim_ids ?? [];
  const evidenceIds = section.evidence_ids ?? [];

  return (
    <Collapse
      className="report-evidence-collapse"
      ghost
      items={[
        {
          children: (
            <div className="report-reference-strip">
              <div>
                <span>
                  分析判断
                  <MetricHint metric="metric_count" />
                </span>
                <strong>{claimIds.length > 0 ? `${claimIds.length} 条` : EMPTY_VALUE_TEXT}</strong>
              </div>
              <div>
                <span>
                  证据材料
                  <MetricHint metric="metric_count" />
                </span>
                <strong>
                  {evidenceIds.length > 0 ? `${evidenceIds.length} 条` : EMPTY_VALUE_TEXT}
                </strong>
              </div>
              <WarningRiskFlagList riskFlags={section.risk_flags ?? []} />
              <div className="report-drilldown-actions" aria-label={`${section.title}下钻入口`}>
                <Button
                  disabled={evidenceIds.length === 0}
                  onClick={() =>
                    navigateTo(
                      routePathForTask("/trace", taskId, {
                        evidence_id: evidenceIds[0],
                        tab: "evidence"
                      })
                    )
                  }
                  size="small"
                  type="link"
                >
                  查看依据
                </Button>
                <Button
                  disabled={claimIds.length === 0}
                  onClick={() =>
                    navigateTo(
                      routePathForTask("/trace", taskId, {
                        claim_id: claimIds[0],
                        tab: "process"
                      })
                    )
                  }
                  size="small"
                  type="link"
                >
                  查看过程
                </Button>
              </div>
            </div>
          ),
          key: "evidence",
          label: (
            <Space>
              <FileText size={16} />
              <span>
                证据材料与质检记录（{evidenceIds.length} 条证据 / {claimIds.length} 条结论）
              </span>
            </Space>
          )
        }
      ]}
    />
  );
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

function getNarrativeReportSections(report: ReportData): NarrativeReportSection[] {
  const narrativeReport = (report as unknown as { narrative_report?: unknown }).narrative_report;
  if (!isRecordValue(narrativeReport) || !Array.isArray(narrativeReport.sections)) {
    return [];
  }

  return narrativeReport.sections
    .filter(isRecordValue)
    .map((section) => {
      const sectionId = stringValue(section.section_id);
      const title = stringValue(section.title);
      const paragraphs = Array.isArray(section.paragraphs)
        ? section.paragraphs
            .map((paragraph) => stringValue(paragraph))
            .filter((paragraph): paragraph is string => Boolean(paragraph))
            .map(formatReportText)
        : [];

      if (!sectionId || !title || paragraphs.length === 0) {
        return null;
      }

      return {
        paragraphs,
        section_id: sectionId,
        title
      };
    })
    .filter((section): section is NarrativeReportSection => Boolean(section));
}

function formatReportSectionTitle(section: ReportSection) {
  return (
    REPORT_SECTION_FALLBACK_TITLES[section.section_id as (typeof REPORT_SECTION_KEYS)[number]] ??
    formatDisplayText(section.title)
      .replace(/\bEvidence\b/g, "证据")
      .replace(/\bQA\b/g, "质检")
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

function createReportContext(report: ReportData): ReportContext {
  const productNames: Record<string, string> = {};
  const edgeDetails: Record<string, ReportEdgeDetail> = {};
  let targetName = "目标产品";

  const visit = (value: unknown) => {
    if (Array.isArray(value)) {
      value.forEach(visit);
      return;
    }

    if (!isRecordValue(value)) {
      return;
    }

    const productId = stringValue(value.product_id);
    const productName = stringValue(value.name);
    if (productId && productName) {
      productNames[productId] = productName;
      if (value.role === "target") {
        targetName = productName;
      }
    }

    const product = value.product;
    if (isRecordValue(product)) {
      const nestedProductId = stringValue(product.product_id);
      const nestedProductName = stringValue(product.name);
      if (nestedProductId && nestedProductName) {
        productNames[nestedProductId] = nestedProductName;
        if (product.role === "target") {
          targetName = nestedProductName;
        }
      }
    }

    const competitor = value.competitor;
    if (isRecordValue(competitor)) {
      const competitorId = stringValue(competitor.product_id);
      const competitorName = stringValue(competitor.name);
      if (competitorId && competitorName) {
        productNames[competitorId] = competitorName;
      }

      const edgeId = stringValue(value.edge_id);
      if (edgeId) {
        edgeDetails[edgeId] = {
          competitionType: stringValue(value.competition_type) ?? undefined,
          name: competitorName ?? competitorId ?? "核心竞品",
          sliceLabel: formatReportItemSliceLabel(value)
        };
      }
    }

    Object.values(value).forEach(visit);
  };

  visit(report);

  return {
    edgeDetails,
    productNames,
    targetName
  };
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

function renderReportItemFields(item: Record<string, unknown>, sectionId: string): ReactNode {
  const index = 0;
  const hiddenKeys = new Set([
    "metadata",
    "basis_edge_id",
    "claim_id",
    "claim_ids",
    "edge_id",
    "edge_ids",
    "evidence_id",
    "evidence_ids",
    "product_id",
    "screenshot_path"
  ]);
  if (sectionId === "competitor_findings") {
    hiddenKeys.add("competitor");
  }
  if (sectionId === "target_opportunities_and_risks" && stringValue(item.dimension)) {
    return sanitizeTraceText(stringValue(item.dimension) ?? `差距 ${index + 1}`);
  }

  if (sectionId === "product_strategy_recommendations" && stringValue(item.title)) {
    return sanitizeTraceText(stringValue(item.title) ?? `机会 ${index + 1}`);
  }

  if (sectionId === "recommendations") {
    hiddenKeys.add("recommendation");
  }

  return Object.entries(item)
    .filter(([key]) => !hiddenKeys.has(key) && !key.endsWith("_id") && !key.endsWith("_ids"))
    .filter(([, value]) => !isInternalReportValue(value))
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
    if (key === "access_time" || key === "generated_at") {
      return formatDateTime(value, { emptyText: EMPTY_VALUE_TEXT, fallback: formatDisplayText });
    }
    return formatReportEnumValue(value, key);
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return EMPTY_VALUE_TEXT;
    }

    if (value.every((item) => ["string", "number", "boolean"].includes(typeof item))) {
      if (key?.endsWith("_ids") || key === "claim_ids" || key === "evidence_ids") {
        return `${value.length} 条`;
      }
      return value.map((item) => formatReportEnumValue(String(item), key)).join("，");
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

function buildReportItemParagraphs(
  item: Record<string, unknown>,
  sectionId: string,
  index: number,
  context: ReportContext
) {
  const expandedParagraphs = readExpandedReportParagraphs(item);
  if (expandedParagraphs.length > 0) {
    return expandedParagraphs;
  }

  const llmParagraphs = readLlmReportParagraphs(item);
  if (llmParagraphs.length > 0) {
    return llmParagraphs;
  }

  const competitorName = getReportCompetitorName(item, context, index);
  const competitionType = formatReportEnumValue(
    stringValue(item.competition_type) ??
      context.edgeDetails[stringValue(item.edge_id) ?? ""]?.competitionType,
    "competition_type"
  );
  const sliceLabel = formatReportItemSliceLabel(item);
  const edgeCount = countReportEdges(item);
  const edgeNames = getReportEdgeNames(item, context);
  const edgeNameText = joinReportList(edgeNames, "当前切片中的相关竞品");

  if (sectionId === "core_competitor_analysis" && stringValue(item.why_users_compare)) {
    const strengths = stringArrayValue(item.competitor_strengths);
    const weaknesses = stringArrayValue(item.competitor_weaknesses);
    return [
      `为什么是竞品：${formatReportText(stringValue(item.why_users_compare) ?? "")}`,
      strengths.length > 0
        ? `竞品强项：${strengths.map(formatReportText).join("；")}`
        : "竞品强项：暂无可靠数据。",
      `我方回应：${formatReportText(
        stringValue(item.target_response) ?? "建议先补齐证据后再判断回应。"
      )}`,
      weaknesses.length > 0
        ? `风险边界：${weaknesses.map(formatReportText).join("；")}`
        : `应答话术：${formatReportText(
            stringValue(item.response_talk_track) ?? "证据不足处建议复核。"
          )}`
    ];
  }

  if (sectionId === "target_opportunities_and_risks" && stringValue(item.dimension)) {
    return [
      `差距维度：${formatReportText(stringValue(item.dimension) ?? "")}。${formatReportText(
        stringValue(item.target_status) ?? "暂无可靠数据。"
      )}`,
      `决策影响：${formatReportText(
        stringValue(item.impact_on_decision) ?? "该差距会影响用户对目标产品的理解。"
      )}`,
      `下一步：${formatReportText(
        stringValue(item.recommendation) ?? "建议补齐证据后再做确定判断。"
      )}`
    ];
  }

  if (sectionId === "product_strategy_recommendations" && stringValue(item.opportunity_id)) {
    return [
      `机会：${formatReportText(stringValue(item.title) ?? "未命名机会")}。${formatReportText(
        stringValue(item.recommendation) ?? "建议围绕核心竞品比较点优化表达。"
      )}`,
      `预期影响：${formatReportText(
        stringValue(item.expected_impact) ?? "暂无可靠数据。"
      )} 责任方向：${formatReportEnumValue(stringValue(item.owner) ?? "", "responsibility_type")}。`,
      `证据边界：${formatReportText(
        stringValue(item.evidence_boundary) ?? "证据不足处建议复核。"
      )}`
    ];
  }

  if (sectionId === "competitive_landscape_judgment" && stringValue(item.competition_meaning)) {
    return [
      formatReportText(stringValue(item.competition_meaning) ?? ""),
      formatReportText(stringValue(item.why_now) ?? "该切片适合优先阅读。")
    ];
  }

  switch (sectionId) {
    case "competitive_landscape_judgment":
    case "dynamic_slice_analysis":
      return [
        `切片：${sliceLabel || "当前分析场景"}；对象：${edgeNameText}。`,
        `压力：${edgeCount} 条关系，${formatReportScorePhrase(item.top_edge_score)}；重点看省心清理、除臭容量和价格解释。`
      ];
    case "core_competitor_analysis":
    case "competitor_findings":
      return [
        `${competitorName}：${competitionType}${sliceLabel ? `，切片为${sliceLabel}` : ""}。`,
        `强度：${formatReportScorePhrase(item.edge_score)}；影响${formatReportDecisionStageList(
          item.decision_stages
        )}。目标产品要直接回应差异点。`
      ];
    case "user_decision_chain_analysis":
    case "decision_chain_analysis": {
      const stageKey = stringValue(item.decision_stage);
      const stage = formatReportEnumValue(stageKey, "decision_stage");
      return [
        `在${stage}阶段，用户正在确认的问题是：${formatDecisionStageFocus(stageKey)}。当前有 ${edgeCount} 条竞争关系会影响这个判断，主要涉及${edgeNameText}。`,
        `对${context.targetName}来说，这一阶段需要${formatDecisionStageAction(stageKey)}；如果表达不够清楚，用户会转向更容易理解或更可信的竞品。`
      ];
    }
    case "target_opportunities_and_risks":
    case "product_profile": {
      const product = isRecordValue(item.product) ? item.product : undefined;
      const profileName = stringValue(product?.name) ?? context.targetName;
      return [
        `${profileName}的机会主要来自自动清理和智能体验表达：这类卖点容易被多猫家庭、希望减少清理负担的用户关注。`,
        "风险在于安全、除臭、维护成本等能力如果缺少可靠证据，就不能写成确定优势；报告会把这类内容保守处理为待复核信息。"
      ];
    }
    case "product_strategy_recommendations":
    case "recommendations":
      return [
        formatReportText(
          stringValue(item.recommendation) ??
            "建议优先围绕核心竞品解释差异化卖点，并补充能支撑判断的证据。"
        ),
        `优先级：${formatReportEnumValue(
          stringValue(item.priority),
          "priority"
        )}。执行时建议把“为什么用户会比较它”和“目标产品如何回应这个比较”写清楚。`
      ];
    case "evidence_index":
      return buildEvidenceParagraphs(stringValue(item.content_summary), stringValue(item.limitations));
    case "evidence_quality_appendix":
      return [
        `质检结论：本节记录报告生成前的证据检查和修复情况。当前共有 ${Number(
          item.review_task_count ?? 0
        )} 个质检问题、${Number(item.revision_message_count ?? 0)} 条打回或修复记录。`,
        "阅读建议：这里主要用于判断报告是否可以被采纳。只要证据仍有缺口，正文就会保守写成“暂无可靠数据”或“建议复核”，不会把推断当成事实。"
      ];
    case "analysis_process_appendix":
      return [
        "系统先整理本地脱敏商品快照，再分析竞品关系、执行 QA 检查，最后生成可下载的网页与 Word 报告。",
        `本次流程涉及 ${Number(
          item.agent_count ?? 4
        )} 类智能体协作。技术细节会留在过程追踪里，报告正文只保留用户需要理解的分析结果。`
      ];
    default:
      return [];
  }
}

function readExpandedReportParagraphs(item: Record<string, unknown>) {
  const paragraphs = item.llm_expanded_analysis;
  if (!Array.isArray(paragraphs)) {
    return [];
  }

  return paragraphs
    .map((value) => stringValue(value))
    .filter((value): value is string => Boolean(value))
    .map(formatReportText);
}

function readLlmReportParagraphs(item: Record<string, unknown>) {
  const paragraphs = item.llm_paragraphs;
  if (!isRecordValue(paragraphs)) {
    return [];
  }

  return (["conclusion", "reason", "action"] as const)
    .map((key) => stringValue(paragraphs[key]))
    .filter((value): value is string => Boolean(value))
    .map(formatReportText);
}

function getReportItemTitle(
  item: Record<string, unknown>,
  sectionId: string,
  index: number,
  context: ReportContext
) {
  if (sectionId === "competitive_landscape_judgment" || sectionId === "dynamic_slice_analysis") {
    const sliceLabel = formatReportItemSliceLabel(item);
    if (sliceLabel) {
      return sanitizeTraceText(`重点切片：${sliceLabel}`);
    }

    const edgeName = getReportEdgeNames(item, context)[0];
    if (edgeName) {
      return sanitizeTraceText(`重点关系：${edgeName}`);
    }

    return `重点切片 ${index + 1}`;
  }

  if (sectionId === "competitor_findings" || sectionId === "core_competitor_analysis") {
    return getReportCompetitorName(item, context, index);
  }

  if (sectionId === "recommendations") {
    return sanitizeTraceText(stringValue(item.recommendation) ?? `建议 ${index + 1}`);
  }

  if (sectionId === "evidence_index") {
    return `证据 ${index + 1}`;
  }

  return null;
}

function getReportCompetitorName(
  item: Record<string, unknown>,
  context: ReportContext,
  index: number
) {
  if (isRecordValue(item.competitor)) {
    return sanitizeTraceText(stringValue(item.competitor.name) ?? `核心竞品 ${index + 1}`);
  }

  const competitorProductId = stringValue(item.competitor_product_id);
  if (competitorProductId && context.productNames[competitorProductId]) {
    return sanitizeTraceText(context.productNames[competitorProductId]);
  }

  const edgeId = stringValue(item.edge_id);
  if (edgeId && context.edgeDetails[edgeId]) {
    return sanitizeTraceText(context.edgeDetails[edgeId].name);
  }

  if (Array.isArray(item.edge_ids)) {
    const edgeName = item.edge_ids
      .map((value) => (typeof value === "string" ? context.edgeDetails[value]?.name : null))
      .find((value): value is string => Boolean(value));
    if (edgeName) {
      return sanitizeTraceText(edgeName);
    }
  }

  return `分析项 ${index + 1}`;
}

function getReportEdgeNames(item: Record<string, unknown>, context: ReportContext) {
  const names: string[] = [];

  if (isRecordValue(item.competitor)) {
    const competitorName = stringValue(item.competitor.name);
    if (competitorName) {
      names.push(competitorName);
    }
  }

  const competitorProductId = stringValue(item.competitor_product_id);
  if (competitorProductId && context.productNames[competitorProductId]) {
    names.push(context.productNames[competitorProductId]);
  }

  const edgeId = stringValue(item.edge_id);
  if (edgeId && context.edgeDetails[edgeId]) {
    names.push(context.edgeDetails[edgeId].name);
  }

  if (Array.isArray(item.edge_ids)) {
    for (const value of item.edge_ids) {
      if (typeof value === "string" && context.edgeDetails[value]?.name) {
        names.push(context.edgeDetails[value].name);
      }
    }
  }

  return uniqueReportValues(names).filter((name) => !/^分析项\s+\d+$/.test(name));
}

function formatReportItemSliceLabel(item: Record<string, unknown>) {
  const nestedSlice = formatSliceLabel(item.slice);
  if (nestedSlice) {
    return nestedSlice;
  }

  return formatSliceLabel({
    persona: item.persona,
    price_band: item.price_band,
    scenario: item.scenario
  });
}

function formatSliceLabel(value: unknown) {
  if (!isRecordValue(value)) {
    return "";
  }

  const parts = [
    stringValue(value.price_band) ? `${value.price_band} 元价格带` : null,
    stringValue(value.persona) ? formatReportText(String(value.persona)) : null,
    stringValue(value.scenario) ? formatReportText(String(value.scenario)) : null
  ].filter((part): part is string => Boolean(part));

  return parts.join("、");
}

function joinReportList(values: string[], fallback: string) {
  const cleanValues = uniqueReportValues(values.map(formatReportText)).filter(
    (value) => value !== EMPTY_VALUE_TEXT
  );

  if (cleanValues.length === 0) {
    return fallback;
  }
  if (cleanValues.length === 1) {
    return cleanValues[0];
  }

  return `${cleanValues.slice(0, -1).join("、")}和${cleanValues[cleanValues.length - 1]}`;
}

function formatReportScorePhrase(value: unknown) {
  const score = typeof value === "number" ? value : Number(value);
  if (Number.isFinite(score) && score > 0) {
    return `综合竞争强度约为 ${formatScore(score)}`;
  }

  return "竞争强度仍需结合更多证据复核";
}

function formatReportDecisionStageList(value: unknown) {
  if (!Array.isArray(value) || value.length === 0) {
    return "用户从理解能力到最终下单的多个环节";
  }

  const stages = value
    .filter((item): item is string => typeof item === "string")
    .map((item) => formatReportEnumValue(item, "decision_stage"));

  return joinReportList(stages, "用户从理解能力到最终下单的多个环节");
}

function formatDecisionStageFocus(stage: string | null) {
  return stage
    ? (DECISION_STAGE_REPORT_GUIDANCE[stage]?.focus ?? "用户是否能获得足够清晰的购买理由")
    : "用户是否能获得足够清晰的购买理由";
}

function formatDecisionStageAction(stage: string | null) {
  return stage
    ? (DECISION_STAGE_REPORT_GUIDANCE[stage]?.action ?? "把竞争差异、证据边界和购买理由讲清楚")
    : "把竞争差异、证据边界和购买理由讲清楚";
}

function formatReportEnumValue(value: unknown, key?: string) {
  if (value === null || value === undefined || value === "") {
    return EMPTY_VALUE_TEXT;
  }

  const text = String(value);
  if (isInternalIdentifier(text)) {
    return "已记录";
  }

  if (key === "competition_type" || key === "role") {
    return COMPETITION_TYPE_LABELS[text] ?? formatReportText(text);
  }

  if (key === "decision_stage" || key === "decision_stages") {
    return DECISION_STAGE_LABELS[text] ?? formatReportText(text);
  }

  if (key === "confidence_level") {
    return formatConfidenceDetail(text);
  }

  if (key === "source_type") {
    return formatSourceType(text);
  }

  if (key === "status") {
    return CLAIM_STATUS_LABELS[text] ?? RUN_STATUS_LABELS[text] ?? formatReportText(text);
  }

  if (key === "priority") {
    return (
      {
        p0_immediate: "优先处理",
        p1_current_iteration: "本轮优化",
        p1_next: "下一步处理",
        p2_follow_up_validation: "后续验证",
        p2_watch: "持续观察"
      }[text] ?? formatReportText(text)
    );
  }

  return formatReportText(text);
}

function formatReportText(value: string) {
  return sanitizeTraceText(value)
    .replace(/\bProduct\b/g, "产品")
    .replace(/\bEvidence\b/g, "证据")
    .replace(/\bClaim\b/g, "分析判断")
    .replace(/\bCompetitionEdge\b/g, "竞争关系")
    .replace(/\bdirect\b/g, "直接竞品")
    .replace(/\balternative\b/g, "需求替代")
    .replace(/\bchannel\b/g, "渠道替代")
    .replace(/\bmedium\b/g, "中等可信度")
    .replace(/\bmissing_access_time\b/g, "缺少访问时间")
    .replace(/\bmissing_screenshot\b/g, "缺少截图")
    .replace(/\bcompleted\b/g, "已完成")
    .replace(/\bdemo_snapshot\b/g, "本地演示快照")
    .replace(/\bdouyin_sku_snapshot\b/g, "抖音商品快照")
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
    .replace(/\bsmart_pet_hardware\b/g, "智能宠物硬件")
    .replace(/\bautomatic_litter_box\b/g, "自动猫砂盆")
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
    .split(/；|;\s*/)
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

  const limitationText = limitations ? cleanEvidenceDisplayText(formatDisplayText(limitations)) : "";
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
    .replace(/[，,；;]\s*$/g, "")
    .trim();
}

function isInternalEvidenceProcessText(value: string) {
  return /评论洞察尚待后续结构化抽取|QA\s*打回后补齐字段|补齐字段[:：]\s*source\.access_time|Evidence\.access_time|source\.access_time/i.test(
    value
  );
}

function createReportDisplayName(targetName: string) {
  const cleanTargetName = sanitizeTraceText(targetName).trim();
  if (!cleanTargetName || cleanTargetName === "目标产品") {
    return "自动猫砂盆竞品分析报告";
  }

  return `${cleanTargetName}竞品分析报告`;
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

function countReportEdges(item: Record<string, unknown>) {
  if (Array.isArray(item.edge_ids)) {
    return item.edge_ids.length;
  }
  return stringValue(item.edge_id) ? 1 : 0;
}

function uniqueReportValues(values: string[]) {
  return Array.from(new Set(values.filter((value) => value !== EMPTY_VALUE_TEXT)));
}

function safeReportFieldLabel(key: string) {
  return isSensitiveTraceKey(key) ? "敏感字段" : sanitizeTraceText(humanizeReportKey(key));
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

function readRiskFlags(item: Record<string, unknown>) {
  return Array.isArray(item.risk_flags)
    ? item.risk_flags.filter((riskFlag): riskFlag is string => typeof riskFlag === "string")
    : [];
}

function stringArrayValue(value: unknown) {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string" && item.trim().length > 0);
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

function formatReportId(value: string | null | undefined) {
  return value ? sanitizeTraceText(value).slice(0, 18) : "N/A";
}
