from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

from app.graph import build_analysis_workflow, create_initial_state
from app.graph.workflow import ANALYSIS_NODE, COLLECTION_NODE, QA_NODE, WRITER_NODE
from app.schemas import (
    AgentMessage,
    AgentMessageType,
    AgentName,
    AgentRunLog,
    AnalysisTask,
    Claim,
    Evidence,
    ReportData,
    ReportQualityCheck,
    ReviewSeverity,
    ReviewStatus,
    ReviewTargetType,
    ReviewTask,
    TaskStatus,
    TokenUsageLog,
    ToolCallLog,
)
from app.schemas.common import JsonObject
from app.schemas.trace import (
    TraceDagEdge,
    TraceDagNode,
    TraceData,
    TraceDiff,
    TraceDrilldownTarget,
    TraceEvidenceChain,
    TraceEvidenceItem,
    TraceProcessView,
    TracePromptPreview,
    TraceQualityRecord,
)
from app.security import redact_sensitive_value
from app.storage import ArtifactRepository, TaskRepository

TRACE_ARTIFACT_TYPE = "trace_data"
_TRACE_CACHEABLE_STATUSES = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.HUMAN_REVIEWING}

FAILED_NODE = "failed"
END_NODE = "end"
MAX_PROMPT_SUMMARY_CHARS = 180
MAX_EVIDENCE_SUMMARY_CHARS = 220

WorkflowFactory = Callable[[], Any]


class TraceServiceError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class TraceService:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        artifact_repository: ArtifactRepository,
        workflow_factory: WorkflowFactory = build_analysis_workflow,
    ) -> None:
        self.task_repository = task_repository
        self.artifact_repository = artifact_repository
        self.workflow_factory = workflow_factory

    def get_trace(self, task_id: str) -> TraceData:
        task = self.task_repository.get(task_id)
        if task is None:
            raise TraceServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task_id},
            )

        if task.status in _TRACE_CACHEABLE_STATUSES:
            cached = self.artifact_repository.get(
                task_id,
                TRACE_ARTIFACT_TYPE,
                _trace_artifact_id(task_id),
                TraceData,
            )
            if cached is not None:
                return TraceData.model_validate(cached)
            if task.status in {TaskStatus.FAILED, TaskStatus.HUMAN_REVIEWING}:
                return _build_trace_data(
                    task=task,
                    state=None,
                    trace_view_id=_trace_artifact_id(task_id),
                )
            return self._generate_and_cache_trace(task)

        return _build_trace_data(
            task=task,
            state=None,
            trace_view_id=_trace_artifact_id(task_id),
        )

    def _generate_and_cache_trace(self, task: AnalysisTask) -> TraceData:
        try:
            workflow = self.workflow_factory()
            state = create_initial_state(task)
            result = workflow.invoke(state)
        except Exception as exc:
            raise TraceServiceError(
                "TRACE_GENERATION_FAILED",
                "Trace generation failed",
                status_code=500,
                details={"task_id": task.task_id, "reason": exc.__class__.__name__},
            ) from exc

        trace = _build_trace_data(
            task=task,
            state=result,
            trace_view_id=_trace_artifact_id(task.task_id),
        )
        self.artifact_repository.save(TRACE_ARTIFACT_TYPE, trace.trace_view_id, trace)
        return trace


def _build_trace_data(
    *,
    task: AnalysisTask,
    state: Mapping[str, Any] | None,
    trace_view_id: str,
) -> TraceData:
    workflow_metadata = _workflow_metadata(state)
    task_status = _state_task_status(task, state)
    workflow_status = str(workflow_metadata.get("status") or task_status)
    agent_runs = _model_list(state, "run_logs", AgentRunLog)
    tool_calls = _model_list(state, "tool_call_logs", ToolCallLog)
    token_usage = _model_list(state, "token_usage_logs", TokenUsageLog)
    qa_reviews = _model_list(state, "review_tasks", ReviewTask)
    report_quality_checks = _model_list(state, "report_quality_checks", ReportQualityCheck)
    messages = _model_list(state, "agent_messages", AgentMessage)
    revision_messages = [
        message
        for message in messages
        if message.message_type == AgentMessageType.REVISION_REQUEST
    ]
    diffs = _trace_diffs(state)
    prompt_previews = _prompt_previews(agent_runs)
    evidence_chains = _evidence_chains(state)
    quality_records = _quality_records(qa_reviews, report_quality_checks)
    dag_nodes = _dag_nodes(agent_runs, workflow_metadata, workflow_status)
    dag_edges = _dag_edges()

    trace = TraceData(
        trace_view_id=trace_view_id,
        task_id=task.task_id,
        task_status=task_status,
        workflow_status=workflow_status,
        generated_at=datetime.now(UTC),
        dag_nodes=dag_nodes,
        dag_edges=dag_edges,
        agent_runs=agent_runs,
        tool_calls=tool_calls,
        token_usage=token_usage,
        qa_reviews=qa_reviews,
        revision_messages=revision_messages,
        diffs=diffs,
        prompt_previews=prompt_previews,
        evidence_chains=evidence_chains,
        quality_records=quality_records,
        process_view=_process_view(
            dag_node_count=len(dag_nodes),
            agent_run_count=len(agent_runs),
            tool_call_count=len(tool_calls),
            token_usage_count=len(token_usage),
            prompt_preview_count=len(prompt_previews),
        ),
        drilldown_targets=_drilldown_targets(evidence_chains, quality_records, diffs),
        metadata=_trace_metadata(
            state,
            workflow_status,
            evidence_chain_count=len(evidence_chains),
            quality_record_count=len(quality_records),
            diff_count=len(diffs),
        ),
    )
    return _redacted_trace(trace)


def _dag_nodes(
    agent_runs: list[AgentRunLog],
    workflow_metadata: JsonObject,
    workflow_status: str,
) -> list[TraceDagNode]:
    run_ids_by_agent: dict[str, list[str]] = {}
    status_by_agent: dict[str, str] = {}
    for run in agent_runs:
        agent_name = run.agent_name.value
        run_ids_by_agent.setdefault(agent_name, []).append(run.run_id)
        status_by_agent[agent_name] = run.status.value

    current_node = workflow_metadata.get("current_node")
    nodes = [
        _agent_node(
            node_id=COLLECTION_NODE,
            label="Collection Agent",
            agent_name=AgentName.COLLECTION,
            run_ids_by_agent=run_ids_by_agent,
            status_by_agent=status_by_agent,
            current_node=current_node,
        ),
        _agent_node(
            node_id=ANALYSIS_NODE,
            label="Analysis Agent",
            agent_name=AgentName.ANALYSIS,
            run_ids_by_agent=run_ids_by_agent,
            status_by_agent=status_by_agent,
            current_node=current_node,
        ),
        _agent_node(
            node_id=QA_NODE,
            label="QA Agent",
            agent_name=AgentName.QA,
            run_ids_by_agent=run_ids_by_agent,
            status_by_agent=status_by_agent,
            current_node=current_node,
        ),
        _agent_node(
            node_id=WRITER_NODE,
            label="Writer Agent",
            agent_name=AgentName.WRITER,
            run_ids_by_agent=run_ids_by_agent,
            status_by_agent=status_by_agent,
            current_node=current_node,
        ),
    ]
    nodes.append(
        TraceDagNode(
            node_id=FAILED_NODE,
            label="Failed",
            node_type="terminal",
            status="failed" if workflow_status == "failed" else "skipped",
            current=current_node == FAILED_NODE,
            failed=workflow_status == "failed",
            visible=True,
        )
    )
    nodes.append(
        TraceDagNode(
            node_id=END_NODE,
            label="End",
            node_type="terminal",
            status="succeeded" if workflow_status == "completed" else "pending",
            current=False,
            failed=False,
            visible=True,
        )
    )
    return nodes


def _agent_node(
    *,
    node_id: str,
    label: str,
    agent_name: AgentName,
    run_ids_by_agent: dict[str, list[str]],
    status_by_agent: dict[str, str],
    current_node: Any,
) -> TraceDagNode:
    status = status_by_agent.get(agent_name.value, "pending")
    return TraceDagNode(
        node_id=node_id,
        label=label,
        node_type="agent",
        agent_name=agent_name,
        status=status,
        run_ids=run_ids_by_agent.get(agent_name.value, []),
        current=current_node == node_id,
        failed=status == "failed",
        visible=True,
    )


def _dag_edges() -> list[TraceDagEdge]:
    return [
        TraceDagEdge(
            edge_id="edge_collection_analysis",
            source=COLLECTION_NODE,
            target=ANALYSIS_NODE,
            label="collection_complete",
        ),
        TraceDagEdge(
            edge_id="edge_analysis_qa",
            source=ANALYSIS_NODE,
            target=QA_NODE,
            label="analysis_complete",
        ),
        TraceDagEdge(
            edge_id="edge_qa_writer",
            source=QA_NODE,
            target=WRITER_NODE,
            label="qa_passed",
            condition="qa_status == passed",
        ),
        TraceDagEdge(
            edge_id="edge_qa_collection",
            source=QA_NODE,
            target=COLLECTION_NODE,
            label="collection_revision",
            condition="revision_target == collection_agent",
        ),
        TraceDagEdge(
            edge_id="edge_qa_analysis",
            source=QA_NODE,
            target=ANALYSIS_NODE,
            label="analysis_revision",
            condition="revision_target == analysis_agent",
        ),
        TraceDagEdge(
            edge_id="edge_qa_failed",
            source=QA_NODE,
            target=FAILED_NODE,
            label="failed",
            condition="qa_failed",
        ),
        TraceDagEdge(
            edge_id="edge_writer_end",
            source=WRITER_NODE,
            target=END_NODE,
            label="report_ready",
        ),
    ]


def _trace_diffs(state: Mapping[str, Any] | None) -> list[TraceDiff]:
    if state is None:
        return []
    metadata = state.get("metadata", {})
    if not isinstance(metadata, Mapping):
        return []

    diffs: list[TraceDiff] = []
    collection_repair = metadata.get("collection_agent_repair")
    if isinstance(collection_repair, Mapping):
        diffs.extend(_collection_repair_diffs(collection_repair))

    analysis_recompute = metadata.get("analysis_agent_recompute")
    if isinstance(analysis_recompute, Mapping):
        diffs.extend(_analysis_recompute_diffs(analysis_recompute))
    human_feedback_updates = metadata.get("human_feedback_local_updates")
    if isinstance(human_feedback_updates, list | tuple):
        diffs.extend(_human_feedback_diffs(human_feedback_updates))
    return diffs


def _collection_repair_diffs(repair: Mapping[str, Any]) -> list[TraceDiff]:
    result = []
    for index, diff in enumerate(_mapping_items(repair.get("diffs")), start=1):
        target_id = str(diff.get("new_evidence_id") or diff.get("target_evidence_id") or "unknown")
        result.append(
            TraceDiff(
                diff_id=f"collection_repair_diff_{index:03d}",
                source="collection_agent_repair",
                target_type="evidence",
                target_id=target_id,
                status=str(diff.get("status") or "unknown"),
                before=_json_object(diff.get("before")),
                after=_json_object(diff.get("after")),
                business_impact=_collection_repair_business_impact(diff),
                revision_message_ids=_string_items(diff.get("revision_message_ids")),
                metadata={
                    "run_id": repair.get("run_id"),
                    "target_evidence_id": diff.get("target_evidence_id"),
                    "new_evidence_id": diff.get("new_evidence_id"),
                    "navigation": {
                        "trace_tab": "diff_records",
                        "diff_id": f"collection_repair_diff_{index:03d}",
                        "target_id": target_id,
                    },
                },
            )
        )
    return result


def _analysis_recompute_diffs(recompute: Mapping[str, Any]) -> list[TraceDiff]:
    result = []
    for index, diff in enumerate(_mapping_items(recompute.get("diffs")), start=1):
        target_id = str(diff.get("edge_id") or diff.get("target_id") or "unknown")
        result.append(
            TraceDiff(
                diff_id=f"analysis_edge_diff_{index:03d}",
                source="analysis_agent_recompute",
                target_type="competition_edge",
                target_id=target_id,
                status=str(diff.get("status") or "recomputed"),
                before=_json_object(diff.get("before")),
                after=_json_object(diff.get("after")),
                business_impact=_analysis_edge_business_impact(diff),
                revision_message_ids=_string_items(recompute.get("revision_message_ids")),
                metadata={
                    "run_id": recompute.get("run_id"),
                    "target_claim_ids": _string_items(recompute.get("target_claim_ids")),
                    "navigation": {
                        "trace_tab": "diff_records",
                        "diff_id": f"analysis_edge_diff_{index:03d}",
                        "target_id": target_id,
                    },
                },
            )
        )
    for index, diff in enumerate(_mapping_items(recompute.get("claim_diffs")), start=1):
        target_id = str(diff.get("claim_id") or diff.get("target_id") or "unknown")
        result.append(
            TraceDiff(
                diff_id=f"analysis_claim_diff_{index:03d}",
                source="analysis_agent_recompute",
                target_type="claim",
                target_id=target_id,
                status=str(diff.get("status") or "recomputed"),
                before=_json_object(diff.get("before")),
                after=_json_object(diff.get("after")),
                business_impact=_analysis_claim_business_impact(diff),
                revision_message_ids=_string_items(recompute.get("revision_message_ids")),
                metadata={
                    "run_id": recompute.get("run_id"),
                    "target_edge_ids": _string_items(recompute.get("target_edge_ids")),
                    "navigation": {
                        "trace_tab": "diff_records",
                        "diff_id": f"analysis_claim_diff_{index:03d}",
                        "target_id": target_id,
                    },
                },
            )
        )
    return result


def _human_feedback_diffs(updates: Iterable[Any]) -> list[TraceDiff]:
    result = []
    for index, update in enumerate(_mapping_items(updates), start=1):
        target_type = str(update.get("target_type") or "unknown")
        target_id = str(update.get("target_id") or "unknown")
        diff_id = f"human_feedback_diff_{index:03d}"
        result.append(
            TraceDiff(
                diff_id=diff_id,
                source="human_feedback",
                target_type=target_type,
                target_id=target_id,
                status=str(update.get("status") or "applied"),
                before=_json_object(update.get("before")),
                after=_json_object(update.get("after")),
                business_impact=_human_feedback_business_impact(update),
                metadata={
                    "feedback_id": update.get("feedback_id"),
                    "action": update.get("action"),
                    "reason": update.get("reason"),
                    "affected_artifact_ids": _string_items(update.get("affected_artifact_ids")),
                    "navigation": {
                        "trace_tab": "diff_records",
                        "diff_id": diff_id,
                        "target_id": target_id,
                    },
                },
            )
        )
    return result


def _collection_repair_business_impact(diff: Mapping[str, Any]) -> str:
    status = str(diff.get("status") or "unknown")
    repaired_fields = _string_items(diff.get("repaired_fields"))
    unavailable_fields = _string_items(diff.get("unavailable_fields"))
    if status == "repaired":
        return (
            "QA 打回后的证据字段已补齐，相关结论可以从证据缺口状态转为可复核状态，"
            "会影响报告中的证据可信度与风险提示。"
        )
    if status == "partial":
        return (
            "QA 打回后只补齐了部分证据字段，已补齐字段可用于复核，但仍需关注未补齐项："
            f"{'、'.join(unavailable_fields) or '暂无可靠数据'}。"
        )
    if repaired_fields:
        return (
            "证据修复记录包含新增可复核字段，相关 Claim 的证据链会优先引用修复后的证据。"
        )
    return "证据缺口仍未补齐，相关结论需要保持谨慎或继续标记为暂无可靠数据。"


def _analysis_edge_business_impact(diff: Mapping[str, Any]) -> str:
    before = _json_object(diff.get("before"))
    after = _json_object(diff.get("after"))
    before_score = before.get("edge_score")
    after_score = after.get("edge_score")
    if isinstance(before_score, int | float) and isinstance(after_score, int | float):
        if after_score > before_score:
            direction = "上升"
        elif after_score < before_score:
            direction = "下降"
        else:
            direction = "保持不变"
        return (
            f"竞争关系分数由 {before_score:.2f} 调整为 {after_score:.2f}，整体{direction}；"
            "这会影响关键竞品排序、威胁判断和后续行动建议优先级。"
        )
    return "竞争关系已随证据修复重算，可能影响关键竞品排序、威胁判断和行动建议优先级。"


def _analysis_claim_business_impact(diff: Mapping[str, Any]) -> str:
    before = _json_object(diff.get("before"))
    after = _json_object(diff.get("after"))
    before_evidence = set(_string_items(before.get("evidence_ids")))
    after_evidence = set(_string_items(after.get("evidence_ids")))
    if before_evidence != after_evidence:
        return (
            "结论绑定的证据发生变化，报告中的下钻依据会指向更新后的证据链，"
            "同时影响 QA 风险和结论可采纳性。"
        )
    if before.get("status") != after.get("status"):
        return "结论状态发生变化，会影响该判断在报告正文中的采纳程度和风险提示。"
    return "结论经过局部重算后保持结构化可追踪，供复核时确认证据、状态和风险是否仍一致。"


def _human_feedback_business_impact(update: Mapping[str, Any]) -> str:
    target_type = str(update.get("target_type") or "")
    action = str(update.get("action") or "")
    reason = str(update.get("reason") or "").strip()
    reason_text = f"原因：{reason}" if reason else "原因：暂无可靠数据"
    if target_type in {"product", "feature_tree", "pricing_model", "user_persona"}:
        return f"人工修正了画像结构化字段，页面画像和相关缓存已刷新；{reason_text}。"
    if target_type == "claim" and action == "mark_rejected":
        return f"人工将结论标记为不采纳，会影响报告采纳程度与风险提示；{reason_text}。"
    if target_type == "evidence" and action == "add_note":
        return f"人工补充了证据备注，后续复核可结合该备注判断证据是否可用；{reason_text}。"
    return f"人工反馈已保存为受控结构化变更，后续复核可查看变更前后内容；{reason_text}。"


def _prompt_previews(agent_runs: Iterable[AgentRunLog]) -> list[TracePromptPreview]:
    previews = []
    for index, run in enumerate(agent_runs, start=1):
        summary = run.input_summary or "Prompt input is folded; raw prompt is not exposed."
        previews.append(
            TracePromptPreview(
                preview_id=f"prompt_preview_{index:03d}",
                run_id=run.run_id,
                agent_name=run.agent_name,
                title=f"{run.agent_name.value} folded prompt preview",
                content_summary=_shorten(summary),
                folded=True,
                redacted=True,
            )
        )
    return previews


def _evidence_chains(state: Mapping[str, Any] | None) -> list[TraceEvidenceChain]:
    if state is None:
        return []

    claims = _model_list(state, "claims", Claim)
    evidences = _model_list(state, "evidences", Evidence)
    reports = _model_list(state, "reports", ReportData)
    evidences_by_id = {evidence.evidence_id: evidence for evidence in evidences}
    report_section_ids_by_claim = _report_section_ids_by_claim(reports)

    chains: list[TraceEvidenceChain] = []
    for claim in claims:
        evidence_items = [
            _trace_evidence_item(evidences_by_id[evidence_id])
            for evidence_id in claim.evidence_ids
            if evidence_id in evidences_by_id
        ]
        chains.append(
            TraceEvidenceChain(
                chain_id=f"evidence_chain_{claim.claim_id}",
                claim_id=claim.claim_id,
                claim_content=claim.content,
                claim_status=claim.status.value,
                confidence=claim.confidence,
                is_inference=claim.is_inference,
                report_section_ids=report_section_ids_by_claim.get(claim.claim_id, []),
                evidence_items=evidence_items,
                trace_refs=[
                    f"claim:{claim.claim_id}",
                    *[
                        f"evidence:{evidence_item.evidence_id}"
                        for evidence_item in evidence_items
                    ],
                ],
                risk_flags=claim.risk_flags,
                navigation={
                    "trace_tab": "evidence_chain",
                    "claim_id": claim.claim_id,
                },
            )
        )
    return chains


def _trace_evidence_item(evidence: Evidence) -> TraceEvidenceItem:
    risk_flags: list[Any] = []
    if evidence.access_time is None:
        risk_flags.append("missing_access_time")
    if evidence.screenshot_path is None:
        risk_flags.append("missing_screenshot")
    for risk_flag in _string_items(evidence.metadata.get("risk_flags")):
        if risk_flag not in risk_flags:
            risk_flags.append(risk_flag)

    return TraceEvidenceItem(
        evidence_id=evidence.evidence_id,
        product_id=evidence.product_id,
        source_type=evidence.source_type,
        confidence_level=evidence.confidence_level,
        access_time=evidence.access_time,
        access_time_status="available" if evidence.access_time is not None else "missing",
        content_summary=_shorten_to(evidence.content_summary, MAX_EVIDENCE_SUMMARY_CHARS),
        limitations=_shorten_to(evidence.limitations, MAX_EVIDENCE_SUMMARY_CHARS),
        source_url=evidence.source_url,
        risk_flags=risk_flags,
        navigation={
            "trace_tab": "evidence_chain",
            "evidence_id": evidence.evidence_id,
        },
    )


def _report_section_ids_by_claim(reports: list[ReportData]) -> dict[str, list[str]]:
    if not reports:
        return {}

    section_ids_by_claim: dict[str, list[str]] = {}
    report = reports[-1]
    for section_id in report.section_order:
        section = _report_section_by_id(report, section_id)
        if section is None:
            continue
        for claim_id in section.claim_ids:
            section_ids_by_claim.setdefault(claim_id, [])
            if section.section_id not in section_ids_by_claim[claim_id]:
                section_ids_by_claim[claim_id].append(section.section_id)
    return section_ids_by_claim


def _report_section_by_id(report: ReportData, section_id: str) -> Any | None:
    for field_name in type(report).model_fields:
        section = getattr(report, field_name)
        if getattr(section, "section_id", None) == section_id:
            return section
    return None


def _quality_records(
    qa_reviews: Iterable[ReviewTask],
    report_quality_checks: Iterable[ReportQualityCheck],
) -> list[TraceQualityRecord]:
    records: list[TraceQualityRecord] = []
    for review in qa_reviews:
        resolved = review.status in {ReviewStatus.RESOLVED, ReviewStatus.WAIVED}
        records.append(
            TraceQualityRecord(
                quality_record_id=f"quality_{review.review_task_id}",
                review_task_id=review.review_task_id,
                check_item=review.check_name,
                issue_code=review.issue_code,
                severity=review.severity,
                target_type=review.target_type,
                target_id=review.target_id,
                target_agent=review.target_agent,
                status=review.status,
                resolved=resolved,
                needs_attention=not resolved,
                issue_summary=review.message,
                required_action=review.required_action,
                action_result=_quality_action_result(review),
                related_claim_ids=review.related_claim_ids,
                evidence_ids=review.evidence_ids,
                navigation={
                    "trace_tab": "quality_records",
                    "review_task_id": review.review_task_id,
                    "target_id": review.target_id,
                },
            )
        )
    records.extend(_report_quality_records(report_quality_checks))
    return records


def _report_quality_records(
    report_quality_checks: Iterable[ReportQualityCheck],
) -> list[TraceQualityRecord]:
    records: list[TraceQualityRecord] = []
    for quality_check in report_quality_checks:
        if not quality_check.issues:
            records.append(
                _report_quality_record(
                    quality_check,
                    issue_code="report_quality_rules_passed",
                    severity=ReviewSeverity.INFO,
                    status=ReviewStatus.RESOLVED,
                    target_id=quality_check.report_id,
                    issue_summary=quality_check.summary,
                    required_action="规则质检已通过，当前无需额外修正。",
                    action_result="报告正文未发现明显重复、内部编号泄漏或证据越界。",
                    record_index=len(records) + 1,
                )
            )
            continue
        for issue in quality_check.issues:
            records.append(
                _report_quality_record(
                    quality_check,
                    issue_code=issue.issue_type,
                    severity=_report_quality_severity(issue.severity),
                    status=ReviewStatus.OPEN,
                    target_id=issue.item_key or issue.section_id or quality_check.report_id,
                    issue_summary=issue.message,
                    required_action=issue.suggestion,
                    action_result=issue.evidence_boundary,
                    record_index=len(records) + 1,
                )
            )
    return records


def _report_quality_record(
    quality_check: ReportQualityCheck,
    *,
    issue_code: str,
    severity: ReviewSeverity,
    status: ReviewStatus,
    target_id: str,
    issue_summary: str,
    required_action: str,
    action_result: str,
    record_index: int,
) -> TraceQualityRecord:
    resolved = status in {ReviewStatus.RESOLVED, ReviewStatus.WAIVED}
    return TraceQualityRecord(
        quality_record_id=f"quality_{quality_check.quality_check_id}_{record_index}",
        review_task_id=quality_check.quality_check_id,
        check_item="报告质量规则检查",
        issue_code=issue_code,
        severity=severity,
        target_type=ReviewTargetType.REPORT,
        target_id=target_id,
        target_agent=AgentName.WRITER,
        status=status,
        resolved=resolved,
        needs_attention=not resolved,
        issue_summary=issue_summary,
        required_action=required_action,
        action_result=action_result,
        related_claim_ids=[],
        evidence_ids=[],
        navigation={
            "trace_tab": "quality_records",
            "quality_check_id": quality_check.quality_check_id,
            "report_id": quality_check.report_id,
        },
    )


def _report_quality_severity(value: str) -> ReviewSeverity:
    normalized = value.lower()
    if normalized in {"high", "error", "blocker"}:
        return ReviewSeverity.ERROR
    if normalized in {"medium", "warning"}:
        return ReviewSeverity.WARNING
    return ReviewSeverity.INFO


def _quality_action_result(review: ReviewTask) -> str:
    if review.status == ReviewStatus.RESOLVED:
        return "已通过补齐证据或局部重算解决，当前无需继续关注。"
    if review.status == ReviewStatus.WAIVED:
        return "已由人工或规则豁免，后续复核时仍可查看原始问题。"
    return "问题仍处于打开状态，需要继续补齐证据、重算分析或人工复核。"


def _process_view(
    *,
    dag_node_count: int,
    agent_run_count: int,
    tool_call_count: int,
    token_usage_count: int,
    prompt_preview_count: int,
) -> TraceProcessView:
    return TraceProcessView(
        technical_details_folded=True,
        default_tab="evidence_chain",
        dag_node_count=dag_node_count,
        agent_run_count=agent_run_count,
        tool_call_count=tool_call_count,
        token_usage_count=token_usage_count,
        prompt_preview_count=prompt_preview_count,
    )


def _drilldown_targets(
    evidence_chains: Iterable[TraceEvidenceChain],
    quality_records: Iterable[TraceQualityRecord],
    diffs: Iterable[TraceDiff],
) -> list[TraceDrilldownTarget]:
    targets = [
        TraceDrilldownTarget(
            target_id="agent_process",
            tab="agent_process",
            label="智能体过程",
            query={"trace_tab": "agent_process"},
        )
    ]
    for chain in evidence_chains:
        targets.append(
            TraceDrilldownTarget(
                target_id=chain.claim_id,
                tab="evidence_chain",
                label=f"结论 {chain.claim_id}",
                query={"trace_tab": "evidence_chain", "claim_id": chain.claim_id},
            )
        )
    for record in quality_records:
        targets.append(
            TraceDrilldownTarget(
                target_id=record.review_task_id,
                tab="quality_records",
                label=f"质检 {record.issue_code}",
                query={
                    "trace_tab": "quality_records",
                    "review_task_id": record.review_task_id,
                },
            )
        )
    for diff in diffs:
        targets.append(
            TraceDrilldownTarget(
                target_id=diff.diff_id,
                tab="diff_records",
                label=f"差异 {diff.target_type}",
                query={"trace_tab": "diff_records", "diff_id": diff.diff_id},
            )
        )
    return targets


def _trace_metadata(
    state: Mapping[str, Any] | None,
    workflow_status: str,
    *,
    evidence_chain_count: int = 0,
    quality_record_count: int = 0,
    diff_count: int = 0,
) -> JsonObject:
    if state is None:
        return {
            "source": "task_record",
            "workflow_status": workflow_status,
            "counts": {
                "agent_runs": 0,
                "tool_calls": 0,
                "token_usage": 0,
                "qa_reviews": 0,
                "diffs": diff_count,
                "evidence_chains": evidence_chain_count,
                "quality_records": quality_record_count,
            },
        }

    metadata = state.get("metadata", {})
    workflow = metadata.get("workflow", {}) if isinstance(metadata, Mapping) else {}
    return {
        "source": "langgraph_workflow",
        "workflow": dict(workflow) if isinstance(workflow, Mapping) else {},
        "workflow_status": workflow_status,
        "counts": {
            "agent_runs": len(_list_items(state.get("run_logs"))),
            "tool_calls": len(_list_items(state.get("tool_call_logs"))),
            "token_usage": len(_list_items(state.get("token_usage_logs"))),
            "qa_reviews": len(_list_items(state.get("review_tasks"))),
            "diffs": diff_count,
            "evidence_chains": evidence_chain_count,
            "quality_records": quality_record_count,
        },
    }


def _redacted_trace(trace: TraceData) -> TraceData:
    return TraceData.model_validate(
        redact_sensitive_value(trace.model_dump(mode="json"), redact_key_names=True)
    )


def _model_list[T](
    state: Mapping[str, Any] | None,
    field: str,
    model_type: type[T],
) -> list[T]:
    if state is None:
        return []
    return [model_type.model_validate(item) for item in _mapping_items(state.get(field))]


def _workflow_metadata(state: Mapping[str, Any] | None) -> JsonObject:
    if state is None:
        return {}
    metadata = state.get("metadata", {})
    if not isinstance(metadata, Mapping):
        return {}
    workflow = metadata.get("workflow", {})
    return dict(workflow) if isinstance(workflow, Mapping) else {}


def _state_task_status(task: AnalysisTask, state: Mapping[str, Any] | None) -> str:
    if state is None:
        return task.status.value
    task_payload = state.get("task", {})
    if isinstance(task_payload, Mapping) and isinstance(task_payload.get("status"), str):
        return str(task_payload["status"])
    return task.status.value


def _mapping_items(value: Any) -> list[Mapping[str, Any]]:
    return [item for item in _list_items(value) if isinstance(item, Mapping)]


def _list_items(value: Any) -> list[Any]:
    if isinstance(value, list | tuple):
        return list(value)
    return []


def _json_object(value: Any) -> JsonObject:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: Any) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _shorten(value: str) -> str:
    return _shorten_to(value, MAX_PROMPT_SUMMARY_CHARS)


def _shorten_to(value: str, max_chars: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def _trace_artifact_id(task_id: str) -> str:
    return f"trace_{task_id}"
