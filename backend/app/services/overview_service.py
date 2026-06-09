from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AgentMessage,
    AnalysisScopeSummary,
    AnalysisTask,
    BattlefieldData,
    BattlefieldEvidenceCard,
    BattlefieldGraphEdge,
    BattlefieldGraphNode,
    BattlefieldSliceSelection,
    Claim,
    CompetitionEdge,
    CompetitionType,
    DecisionUsabilityStatus,
    DisplayStatus,
    Evidence,
    EvidenceCredibilityStatus,
    JudgmentStrength,
    OverviewActionRecommendation,
    OverviewConclusion,
    OverviewData,
    OverviewDrilldownReference,
    OverviewDrilldownType,
    OverviewFinding,
    OverviewFindingType,
    OverviewKeyCompetitor,
    OverviewKeyCompetitorType,
    PMRelationshipLabel,
    Product,
    ReviewSeverity,
    ReviewStatus,
    ReviewTask,
    RiskFlag,
    TaskStatus,
    ThreatLevel,
)
from app.services.analysis_scope_service import (
    SNAPSHOT_SCOPE_NOTICE,
    UNKNOWN_DATA_LABEL,
    build_analysis_scope_summary,
)
from app.services.battlefield_service import BATTLEFIELD_ARTIFACT_TYPE, _battlefield_artifact_id
from app.services.product_image_metadata import product_main_image_url
from app.storage import ArtifactRepository, TaskRepository

OVERVIEW_ARTIFACT_TYPE = "overview_data"
_OVERVIEW_READABLE_STATUSES = {TaskStatus.COMPLETED, TaskStatus.HUMAN_REVIEWING}
WorkflowFactory = Callable[[], Any]


class OverviewServiceError(Exception):
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


class OverviewService:
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

    def get_overview(
        self,
        task_id: str,
        *,
        price_band: str | None = None,
        persona: str | None = None,
        scenario: str | None = None,
    ) -> OverviewData:
        task = self._get_completed_task(task_id)
        selected_slice = BattlefieldSliceSelection(
            price_band=price_band,
            persona=persona,
            scenario=scenario,
        )
        artifact_id = _overview_artifact_id(task_id, selected_slice)
        cached = self.artifact_repository.get(
            task_id,
            OVERVIEW_ARTIFACT_TYPE,
            artifact_id,
            OverviewData,
        )
        if cached is not None:
            cached_overview = OverviewData.model_validate(cached)
            overview = _hydrate_overview_product_images(cached_overview)
            if overview != cached_overview:
                self.artifact_repository.save(
                    OVERVIEW_ARTIFACT_TYPE,
                    overview.overview_id,
                    overview,
                )
            return overview
        cached_battlefield_overview = self._build_from_cached_battlefield(
            task,
            selected_slice,
            artifact_id,
        )
        if cached_battlefield_overview is not None:
            self.artifact_repository.save(
                OVERVIEW_ARTIFACT_TYPE,
                cached_battlefield_overview.overview_id,
                cached_battlefield_overview,
            )
            return _hydrate_overview_product_images(cached_battlefield_overview)
        return self._generate_and_cache_overview(task, selected_slice, artifact_id)

    def _get_completed_task(self, task_id: str) -> AnalysisTask:
        task = self.task_repository.get(task_id)
        if task is None:
            raise OverviewServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task_id},
            )
        if task.status not in _OVERVIEW_READABLE_STATUSES:
            raise OverviewServiceError(
                "OVERVIEW_NOT_READY",
                "Overview data is only available after completion or human review.",
                status_code=409,
                details=_overview_not_ready_details(task),
            )
        return task

    def _generate_and_cache_overview(
        self,
        task: AnalysisTask,
        selected_slice: BattlefieldSliceSelection,
        artifact_id: str,
    ) -> OverviewData:
        try:
            workflow = self.workflow_factory()
            result = workflow.invoke(create_initial_state(task))
        except Exception as exc:
            raise OverviewServiceError(
                "OVERVIEW_GENERATION_FAILED",
                "Overview generation failed",
                status_code=500,
                details={"task_id": task.task_id, "reason": exc.__class__.__name__},
            ) from exc

        if result["task"].get("status") != TaskStatus.COMPLETED.value:
            raise OverviewServiceError(
                "OVERVIEW_GENERATION_FAILED",
                "Overview generation did not complete the workflow.",
                status_code=500,
                details={
                    "task_id": task.task_id,
                    "workflow_status": result["task"].get("status"),
                },
            )

        overview = _build_overview_data(result, selected_slice, artifact_id)
        overview = _hydrate_overview_product_images(overview)
        self.artifact_repository.save(OVERVIEW_ARTIFACT_TYPE, overview.overview_id, overview)
        return overview

    def _build_from_cached_battlefield(
        self,
        task: AnalysisTask,
        selected_slice: BattlefieldSliceSelection,
        artifact_id: str,
    ) -> OverviewData | None:
        battlefield = self._cached_battlefield(task.task_id, selected_slice)
        if battlefield is None:
            return None
        overview = _build_overview_from_battlefield(
            task=task,
            battlefield=battlefield,
            selected_slice=selected_slice,
            overview_id=artifact_id,
        )
        return _hydrate_overview_product_images(overview)

    def _cached_battlefield(
        self,
        task_id: str,
        selected_slice: BattlefieldSliceSelection,
    ) -> BattlefieldData | None:
        exact_id = _battlefield_artifact_id(task_id, selected_slice)
        cached = self.artifact_repository.get(
            task_id,
            BATTLEFIELD_ARTIFACT_TYPE,
            exact_id,
            BattlefieldData,
        )
        if cached is not None:
            return BattlefieldData.model_validate(cached)

        default_slice = BattlefieldSliceSelection()
        default_id = _battlefield_artifact_id(task_id, default_slice)
        cached = self.artifact_repository.get(
            task_id,
            BATTLEFIELD_ARTIFACT_TYPE,
            default_id,
            BattlefieldData,
        )
        if cached is None:
            return None
        return BattlefieldData.model_validate(cached)


def _overview_not_ready_details(task: AnalysisTask) -> dict[str, str]:
    details = {"task_id": task.task_id, "status": task.status.value}
    if task.status != TaskStatus.FAILED:
        return details

    execution_metadata = task.metadata.get("task_execution")
    if not isinstance(execution_metadata, Mapping):
        return details

    failure_reason = execution_metadata.get("failure_reason")
    failure_message = execution_metadata.get("failure_message")
    if isinstance(failure_reason, str) and failure_reason.strip():
        details["failure_reason"] = failure_reason.strip()
    if isinstance(failure_message, str) and failure_message.strip():
        details["failure_message"] = _safe_failure_message(failure_message)
    return details


def _hydrate_overview_product_images(overview: OverviewData) -> OverviewData:
    key_competitors = [
        _hydrate_overview_key_competitor_image(competitor)
        for competitor in overview.key_competitors
    ]
    if all(
        before.primary_image_path == after.primary_image_path
        for before, after in zip(overview.key_competitors, key_competitors, strict=True)
    ):
        return overview
    return overview.model_copy(update={"key_competitors": key_competitors})


def _hydrate_overview_key_competitor_image(
    competitor: OverviewKeyCompetitor,
) -> OverviewKeyCompetitor:
    image_url = product_main_image_url(
        sku_id=competitor.sku_id,
        product_id=competitor.product_id,
    )
    if image_url is None or image_url == competitor.primary_image_path:
        return competitor
    return competitor.model_copy(update={"primary_image_path": image_url})


def _safe_failure_message(message: str) -> str:
    safe_message = message.strip()
    if not safe_message:
        return ""
    sensitive_markers = ("api_key", "apikey", "token", "secret", "password", "authorization")
    lowered = safe_message.lower()
    if any(marker in lowered for marker in sensitive_markers):
        return "任务执行时发生内部异常，详细信息已脱敏。"
    return safe_message[:300]


def _build_overview_data(
    state: Mapping[str, Any],
    selected_slice: BattlefieldSliceSelection,
    overview_id: str,
) -> OverviewData:
    task = AnalysisTask.model_validate(state["task"])
    products = _model_list(state, "products", Product)
    evidences = _model_list(state, "evidences", Evidence)
    claims = _model_list(state, "claims", Claim)
    edges = _model_list(state, "competition_edges", CompetitionEdge)
    review_tasks = _model_list(state, "review_tasks", ReviewTask)
    agent_messages = _model_list(state, "agent_messages", AgentMessage)

    metadata = _safe_mapping(state.get("metadata"))
    snapshot_version = _safe_mapping(metadata.get("collection_agent")).get("snapshot_version")
    analysis_scope = build_analysis_scope_summary(
        task=task,
        products=products,
        evidences=evidences,
        snapshot_version=snapshot_version if isinstance(snapshot_version, str) else None,
    )

    products_by_id = {product.product_id: product for product in products}
    claims_by_id = {claim.claim_id: claim for claim in claims}
    evidences_by_id = {evidence.evidence_id: evidence for evidence in evidences}
    filtered_edges = _filtered_edges(edges, selected_slice)
    ranked_edges = sorted(filtered_edges, key=lambda edge: edge.edge_score, reverse=True)
    edge_contexts = [
        _edge_context(edge, products_by_id, claims_by_id, evidences_by_id, review_tasks)
        for edge in ranked_edges
        if edge.competitor_product_id in products_by_id
    ]
    key_competitors = _key_competitors(task.task_id, edge_contexts)
    judgment_strength = _judgment_strength(edge_contexts, claims_by_id, review_tasks)
    decision_usability = _decision_usability(judgment_strength, key_competitors, review_tasks)
    one_sentence = _one_sentence_judgment(
        task=task,
        key_competitors=key_competitors,
        decision_usability=decision_usability,
        selected_slice=selected_slice,
    )

    opportunities = _opportunities(task.task_id, key_competitors, selected_slice)
    risk_points = _risk_points(task.task_id, key_competitors, analysis_scope, review_tasks)
    actions = _actions(task.task_id, key_competitors, risk_points, decision_usability)

    return OverviewData(
        overview_id=overview_id,
        task_id=task.task_id,
        generated_at=datetime.now(UTC),
        one_sentence_judgment=one_sentence,
        judgment_strength=judgment_strength,
        decision_usability=decision_usability,
        status_reasons=[
            judgment_strength.reason,
            decision_usability.reason,
            f"当前切片覆盖 {len(filtered_edges)} 条竞争关系。",
        ],
        analysis_scope=analysis_scope,
        key_competitors=key_competitors,
        opportunities=opportunities,
        risk_points=risk_points,
        action_recommendations=actions,
        current_slice=selected_slice,
        drilldown_refs=[
            _drilldown(
                OverviewDrilldownType.TRACE,
                "查看证据与过程",
                f"trace_{task.task_id}",
                f"/tasks/{task.task_id}/trace",
            )
        ],
        metadata={
            "source": "langgraph_workflow",
            "edge_count": len(edges),
            "filtered_edge_count": len(filtered_edges),
            "agent_message_count": len(agent_messages),
        },
    )


def _build_overview_from_battlefield(
    *,
    task: AnalysisTask,
    battlefield: BattlefieldData,
    selected_slice: BattlefieldSliceSelection,
    overview_id: str,
) -> OverviewData:
    filtered_edges = sorted(
        [
            edge
            for edge in battlefield.graph_edges
            if _battlefield_edge_matches(edge, selected_slice)
        ],
        key=lambda edge: edge.edge_score,
        reverse=True,
    )
    nodes_by_id = {node.product_id: node for node in battlefield.graph_nodes}
    evidence_cards_by_id = {card.evidence_id: card for card in battlefield.evidence_cards}
    key_competitors = _key_competitors_from_battlefield(
        task.task_id,
        filtered_edges,
        nodes_by_id,
        evidence_cards_by_id,
    )
    judgment_strength = _judgment_strength_from_battlefield(filtered_edges)
    decision_usability = _decision_usability_from_battlefield(
        judgment_strength,
        key_competitors,
        filtered_edges,
    )
    analysis_scope = _analysis_scope_from_battlefield(task, battlefield)
    one_sentence = _one_sentence_judgment(
        task=task,
        key_competitors=key_competitors,
        decision_usability=decision_usability,
        selected_slice=selected_slice,
    )
    opportunities = _opportunities(task.task_id, key_competitors, selected_slice)
    risk_points = _risk_points(task.task_id, key_competitors, analysis_scope, [])
    actions = _actions(task.task_id, key_competitors, risk_points, decision_usability)

    return OverviewData(
        overview_id=overview_id,
        task_id=task.task_id,
        generated_at=datetime.now(UTC),
        one_sentence_judgment=one_sentence,
        judgment_strength=judgment_strength,
        decision_usability=decision_usability,
        status_reasons=[
            judgment_strength.reason,
            decision_usability.reason,
            f"当前切片覆盖 {len(filtered_edges)} 条竞争关系。",
        ],
        analysis_scope=analysis_scope,
        key_competitors=key_competitors,
        opportunities=opportunities,
        risk_points=risk_points,
        action_recommendations=actions,
        current_slice=selected_slice,
        drilldown_refs=[
            _drilldown(
                OverviewDrilldownType.BATTLEFIELD,
                "查看竞争图谱",
                task.task_id,
                f"/tasks/{task.task_id}/battlefield",
            )
        ],
        metadata={
            "source": "cached_battlefield_artifact",
            "battlefield_id": battlefield.battlefield_id,
            "edge_count": len(battlefield.graph_edges),
            "filtered_edge_count": len(filtered_edges),
        },
    )


def _key_competitors_from_battlefield(
    task_id: str,
    edges: Sequence[BattlefieldGraphEdge],
    nodes_by_id: Mapping[str, BattlefieldGraphNode],
    evidence_cards_by_id: Mapping[str, BattlefieldEvidenceCard],
) -> list[OverviewKeyCompetitor]:
    contexts = [
        _battlefield_edge_context(edge, nodes_by_id, evidence_cards_by_id)
        for edge in edges
        if edge.competitor_product_id in nodes_by_id
    ]
    selected_contexts = []
    direct_context = _first_context(
        contexts,
        lambda context: (
            context["edge"].competition_type == CompetitionType.DIRECT
            and context["threat_level"] != ThreatLevel.HIGH_SCORE_NEEDS_REVIEW
        ),
    )
    alternative_context = _first_context(
        contexts,
        lambda context: (
            context["edge"].competition_type
            in {CompetitionType.ALTERNATIVE, CompetitionType.CHANNEL}
            and context["threat_level"] != ThreatLevel.HIGH_SCORE_NEEDS_REVIEW
        ),
    )
    review_context = _first_context(
        contexts,
        lambda context: context["threat_level"] == ThreatLevel.HIGH_SCORE_NEEDS_REVIEW,
    )
    for competitor_type, context in (
        (OverviewKeyCompetitorType.HIGHEST_THREAT_DIRECT, direct_context),
        (OverviewKeyCompetitorType.HIGHEST_THREAT_ALTERNATIVE, alternative_context),
        (OverviewKeyCompetitorType.HIGH_SCORE_NEEDS_REVIEW, review_context),
    ):
        if context is None:
            continue
        edge_id = context["edge"].edge_id
        if edge_id in {selected["edge"].edge_id for selected in selected_contexts}:
            continue
        selected_contexts.append({"competitor_type": competitor_type, **context})
    return [_key_competitor_from_battlefield(task_id, context) for context in selected_contexts]


def _battlefield_edge_context(
    edge: BattlefieldGraphEdge,
    nodes_by_id: Mapping[str, BattlefieldGraphNode],
    evidence_cards_by_id: Mapping[str, BattlefieldEvidenceCard],
) -> dict[str, Any]:
    credibility = _battlefield_evidence_credibility(edge, evidence_cards_by_id)
    threat_level = _threat_level(edge.edge_score, credibility.value)
    return {
        "edge": edge,
        "node": nodes_by_id[edge.competitor_product_id],
        "credibility": credibility,
        "threat_level": threat_level,
    }


def _key_competitor_from_battlefield(
    task_id: str,
    context: Mapping[str, Any],
) -> OverviewKeyCompetitor:
    edge: BattlefieldGraphEdge = context["edge"]
    node: BattlefieldGraphNode = context["node"]
    trace_ref = f"analysis_agent:{edge.edge_id}"
    return OverviewKeyCompetitor(
        competitor_type=context["competitor_type"],
        product_id=node.product_id,
        sku_id=None,
        product_name=node.label,
        brand=node.brand,
        primary_image_path=node.primary_image_path,
        relationship_label=_relationship_label_from_competition_type(edge.competition_type),
        threat_level=context["threat_level"],
        evidence_credibility=context["credibility"],
        inclusion_reason=_battlefield_competitor_reason(edge, node, context["threat_level"]),
        evidence_ids=edge.evidence_ids,
        trace_refs=[trace_ref],
        drilldown_refs=[
            _drilldown(
                OverviewDrilldownType.BATTLEFIELD,
                "查看竞争关系",
                edge.edge_id,
                f"/tasks/{task_id}/battlefield?edge_id={edge.edge_id}",
            )
        ],
        risk_flags=_dedupe([*edge.risk_flags, *context["credibility"].risk_flags]),
    )


def _battlefield_evidence_credibility(
    edge: BattlefieldGraphEdge,
    evidence_cards_by_id: Mapping[str, BattlefieldEvidenceCard],
) -> DisplayStatus:
    if not edge.evidence_ids or any(
        evidence_id not in evidence_cards_by_id for evidence_id in edge.evidence_ids
    ):
        return _display_status(
            EvidenceCredibilityStatus.INSUFFICIENT,
            "证据不足",
            "缺少关键证据或证据记录不可追溯。",
            evidence_ids=edge.evidence_ids,
            trace_refs=[],
            risk_flags=[RiskFlag.MISSING_EVIDENCE],
        )

    edge_evidences = [evidence_cards_by_id[evidence_id] for evidence_id in edge.evidence_ids]
    if edge.risk_flags or any(
        evidence.access_time is None or evidence.source_url is None
        for evidence in edge_evidences
    ):
        return _display_status(
            EvidenceCredibilityStatus.CAUTIOUS_REFERENCE,
            "谨慎参考",
            "证据可用于方向判断，但仍存在来源、时间或局限性约束。",
            evidence_ids=edge.evidence_ids,
            trace_refs=[],
            risk_flags=[RiskFlag.UNRELIABLE_DATA],
        )

    return _display_status(
        EvidenceCredibilityStatus.DIRECTLY_ADOPTABLE,
        "可直接采纳",
        "关键证据具备来源、访问时间、内容摘要和局限性说明。",
        evidence_ids=edge.evidence_ids,
        trace_refs=[],
        risk_flags=[],
    )


def _judgment_strength_from_battlefield(edges: Sequence[BattlefieldGraphEdge]) -> DisplayStatus:
    claim_confidences = [
        claim_ref.confidence
        for edge in edges
        for claim_ref in edge.claim_refs
        if isinstance(claim_ref.confidence, int | float)
    ]
    average_confidence = (
        sum(claim_confidences) / len(claim_confidences) if claim_confidences else 0
    )
    if average_confidence >= 0.75:
        return _display_status(
            JudgmentStrength.CLEAR,
            "明确判断",
            f"平均置信度 {average_confidence:.2f}，关键证据可追溯。",
            evidence_ids=[],
            trace_refs=[],
            risk_flags=[],
        )
    if average_confidence >= 0.55:
        return _display_status(
            JudgmentStrength.DIRECTIONAL,
            "倾向判断",
            f"平均置信度 {average_confidence:.2f}，适合作为方向性讨论输入。",
            evidence_ids=[],
            trace_refs=[],
            risk_flags=[],
        )
    return _display_status(
        JudgmentStrength.HYPOTHESIS,
        "仅作假设",
        "当前切片缺少足够高置信度证据，建议先补充复核。",
        evidence_ids=[],
        trace_refs=[],
        risk_flags=[RiskFlag.UNRELIABLE_DATA],
    )


def _decision_usability_from_battlefield(
    judgment_strength: DisplayStatus,
    key_competitors: Sequence[OverviewKeyCompetitor],
    edges: Sequence[BattlefieldGraphEdge],
) -> DisplayStatus:
    if not edges or not key_competitors:
        return _display_status(
            DecisionUsabilityStatus.DIRECTIONAL_ONLY,
            "仅供方向参考",
            "当前切片缺少可排序的关键竞争关系。",
            evidence_ids=[],
            trace_refs=[],
            risk_flags=[RiskFlag.MISSING_EVIDENCE],
        )
    risky_evidence_ids = _dedupe(
        evidence_id
        for competitor in key_competitors
        if competitor.evidence_credibility.value != EvidenceCredibilityStatus.DIRECTLY_ADOPTABLE
        for evidence_id in competitor.evidence_ids
    )
    if risky_evidence_ids or judgment_strength.value == JudgmentStrength.HYPOTHESIS:
        return _display_status(
            DecisionUsabilityStatus.CAUTION,
            "建议谨慎决策",
            "存在局部证据限制，可作为产品讨论输入，但不宜直接当成最终判断。",
            evidence_ids=risky_evidence_ids,
            trace_refs=_dedupe(
                trace_ref
                for competitor in key_competitors
                for trace_ref in competitor.trace_refs
            ),
            risk_flags=[RiskFlag.UNRELIABLE_DATA],
        )
    return _display_status(
        DecisionUsabilityStatus.READY,
        "可用于初步决策",
        "关键竞品和主要结论已经有可追溯证据支撑。",
        evidence_ids=_dedupe(
            evidence_id for competitor in key_competitors for evidence_id in competitor.evidence_ids
        ),
        trace_refs=_dedupe(
            trace_ref for competitor in key_competitors for trace_ref in competitor.trace_refs
        ),
        risk_flags=[],
    )


def _analysis_scope_from_battlefield(
    task: AnalysisTask,
    battlefield: BattlefieldData,
) -> AnalysisScopeSummary:
    access_times = [
        card.access_time for card in battlefield.evidence_cards if card.access_time is not None
    ]
    if not battlefield.evidence_cards or len(access_times) != len(battlefield.evidence_cards):
        access_time_range = UNKNOWN_DATA_LABEL
        missing_fields = ["Evidence.access_time"]
    else:
        start = min(access_times)
        end = max(access_times)
        access_time_range = (
            start.isoformat() if start == end else f"{start.isoformat()} 至 {end.isoformat()}"
        )
        missing_fields = []

    platforms = _dedupe(
        _platform_label_from_source(card.source_type.value) for card in battlefield.evidence_cards
    )
    return AnalysisScopeSummary(
        task_id=task.task_id,
        category=task.category,
        subcategory=task.subcategory,
        data_source_mode=task.data_source_mode,
        data_source_label="用户提供的脱敏 SKU 快照",
        scope_notice=SNAPSHOT_SCOPE_NOTICE,
        sku_count=len([node for node in battlefield.graph_nodes if node.role.value != "target"]),
        product_count=len(battlefield.graph_nodes),
        evidence_count=len(battlefield.evidence_cards),
        platform_label="、".join(platforms) if platforms else UNKNOWN_DATA_LABEL,
        platforms=platforms,
        source_description="由已缓存的竞争图谱结果快速生成总览，不重新调用完整分析流程。",
        snapshot_version=None,
        snapshot_date=UNKNOWN_DATA_LABEL,
        access_time_range=access_time_range,
        missing_fields=missing_fields,
        evidence_ids=[card.evidence_id for card in battlefield.evidence_cards],
    )


def _battlefield_competitor_reason(
    edge: BattlefieldGraphEdge,
    node: BattlefieldGraphNode,
    threat_level: ThreatLevel,
) -> str:
    return (
        f"{node.label} 与目标产品处在同一购买比较场景，当前关系强度约"
        f"{edge.edge_score:.0%}，可优先作为{_threat_label(threat_level)}竞品查看。"
    )


def _relationship_label_from_competition_type(
    competition_type: CompetitionType,
) -> PMRelationshipLabel:
    if competition_type == CompetitionType.DIRECT:
        return PMRelationshipLabel.HEAD_TO_HEAD
    if competition_type == CompetitionType.CHANNEL:
        return PMRelationshipLabel.LOW_PRICE_INTERCEPTION
    if competition_type == CompetitionType.CONTENT_COOCCURRENCE:
        return PMRelationshipLabel.CONTENT_SEEDING_COMPETITION
    return PMRelationshipLabel.SCENARIO_SUBSTITUTE


def _battlefield_edge_matches(
    edge: BattlefieldGraphEdge,
    selected_slice: BattlefieldSliceSelection,
) -> bool:
    return (
        (selected_slice.price_band is None or edge.slice.price_band == selected_slice.price_band)
        and (selected_slice.persona is None or edge.slice.persona == selected_slice.persona)
        and (selected_slice.scenario is None or edge.slice.scenario == selected_slice.scenario)
    )


def _platform_label_from_source(source_type: str) -> str:
    if source_type.startswith("douyin_"):
        return "抖音电商"
    if source_type == "user_research":
        return "用户研究"
    if source_type == "manual_review":
        return "人工复核"
    return "派生分析"


def _edge_context(
    edge: CompetitionEdge,
    products_by_id: Mapping[str, Product],
    claims_by_id: Mapping[str, Claim],
    evidences_by_id: Mapping[str, Evidence],
    review_tasks: Sequence[ReviewTask],
) -> dict[str, Any]:
    claim_ids = [claim_id for claim_id in edge.claim_ids if claim_id in claims_by_id]
    evidence_ids = _dedupe(
        evidence_id
        for claim_id in claim_ids
        for evidence_id in claims_by_id[claim_id].evidence_ids
    )
    related_open_reviews = _related_open_reviews(edge, claim_ids, evidence_ids, review_tasks)
    credibility = _evidence_credibility(evidence_ids, evidences_by_id, related_open_reviews)
    threat_level = _threat_level(edge.edge_score, credibility.value)
    return {
        "edge": edge,
        "product": products_by_id[edge.competitor_product_id],
        "claim_ids": claim_ids,
        "evidence_ids": evidence_ids,
        "credibility": credibility,
        "threat_level": threat_level,
        "related_open_reviews": related_open_reviews,
    }


def _key_competitors(
    task_id: str,
    contexts: Sequence[dict[str, Any]],
) -> list[OverviewKeyCompetitor]:
    selected_contexts = []
    direct_context = _first_context(
        contexts,
        lambda context: (
            context["edge"].competition_type == CompetitionType.DIRECT
            and context["threat_level"] != ThreatLevel.HIGH_SCORE_NEEDS_REVIEW
        ),
    )
    alternative_context = _first_context(
        contexts,
        lambda context: (
            context["edge"].competition_type
            in {CompetitionType.ALTERNATIVE, CompetitionType.CHANNEL}
            and context["threat_level"] != ThreatLevel.HIGH_SCORE_NEEDS_REVIEW
        ),
    )
    review_context = _first_context(
        contexts,
        lambda context: context["threat_level"] == ThreatLevel.HIGH_SCORE_NEEDS_REVIEW,
    )

    for competitor_type, context in (
        (OverviewKeyCompetitorType.HIGHEST_THREAT_DIRECT, direct_context),
        (OverviewKeyCompetitorType.HIGHEST_THREAT_ALTERNATIVE, alternative_context),
        (OverviewKeyCompetitorType.HIGH_SCORE_NEEDS_REVIEW, review_context),
    ):
        if context is None:
            continue
        edge_id = context["edge"].edge_id
        if edge_id in {selected["edge"].edge_id for selected in selected_contexts}:
            continue
        selected_contexts.append({"competitor_type": competitor_type, **context})

    return [_key_competitor(task_id, context) for context in selected_contexts]


def _key_competitor(task_id: str, context: Mapping[str, Any]) -> OverviewKeyCompetitor:
    edge: CompetitionEdge = context["edge"]
    product: Product = context["product"]
    evidence_ids = list(context["evidence_ids"])
    trace_ref = f"analysis_agent:{edge.edge_id}"
    return OverviewKeyCompetitor(
        competitor_type=context["competitor_type"],
        product_id=product.product_id,
        sku_id=product.sku_id,
        product_name=product.name,
        brand=product.brand,
        primary_image_path=product.primary_image_path,
        relationship_label=_relationship_label(edge),
        threat_level=context["threat_level"],
        evidence_credibility=context["credibility"],
        inclusion_reason=_competitor_reason(edge, product, context["threat_level"]),
        evidence_ids=evidence_ids,
        trace_refs=[trace_ref],
        drilldown_refs=[
            _drilldown(
                OverviewDrilldownType.BATTLEFIELD,
                "查看竞争关系",
                edge.edge_id,
                f"/tasks/{task_id}/battlefield?edge_id={edge.edge_id}",
            )
        ],
        risk_flags=_key_competitor_risks(context),
    )


def _one_sentence_judgment(
    *,
    task: AnalysisTask,
    key_competitors: Sequence[OverviewKeyCompetitor],
    decision_usability: DisplayStatus,
    selected_slice: BattlefieldSliceSelection,
) -> OverviewConclusion:
    top_competitor = key_competitors[0] if key_competitors else None
    slice_label = _slice_label(selected_slice)
    if top_competitor is None:
        content = (
            f"{task.target_product_name} 在{slice_label}暂无可排序的关键竞争对象；"
            f"当前结论仅能作为后续补证方向，{decision_usability.reason}"
        )
        evidence_ids: list[str] = []
        trace_refs = [f"overview:{task.task_id}"]
    else:
        content = (
            f"{task.target_product_name} 在{slice_label}主要面对"
            f"{top_competitor.product_name} 的{_threat_label(top_competitor.threat_level)}；"
            f"证据状态为{top_competitor.evidence_credibility.label}，"
            f"{decision_usability.reason}"
        )
        evidence_ids = top_competitor.evidence_ids
        trace_refs = top_competitor.trace_refs

    return OverviewConclusion(
        content=content,
        evidence_ids=evidence_ids,
        trace_refs=trace_refs,
        drilldown_refs=[
            _drilldown(
                OverviewDrilldownType.BATTLEFIELD,
                "查看竞争图谱",
                task.task_id,
                f"/tasks/{task.task_id}/battlefield",
            )
        ],
        risk_flags=[],
    )


def _opportunities(
    task_id: str,
    key_competitors: Sequence[OverviewKeyCompetitor],
    selected_slice: BattlefieldSliceSelection,
) -> list[OverviewFinding]:
    findings = []
    top_competitor = key_competitors[0] if key_competitors else None
    if top_competitor is not None:
        findings.append(
            OverviewFinding(
                finding_id=f"opp_{task_id}_content_001",
                finding_type=OverviewFindingType.EXPRESSION_OPPORTUNITY,
                title="强化关键卖点证据表达",
                description=(
                    f"围绕{_slice_plain_text(selected_slice)}补充对比证据，"
                    f"优先回应{top_competitor.product_name} 的拦截点。"
                ),
                evidence_ids=top_competitor.evidence_ids,
                trace_refs=top_competitor.trace_refs,
                drilldown_refs=top_competitor.drilldown_refs,
                risk_flags=[],
            )
        )

    findings.append(
        OverviewFinding(
            finding_id=f"opp_{task_id}_product_001",
            finding_type=OverviewFindingType.PRODUCT_OPPORTUNITY,
            title="聚焦当前切片体验差异",
            description=f"将{_slice_plain_text(selected_slice)}下的使用场景转化为功能与体验对比点。",
            evidence_ids=top_competitor.evidence_ids if top_competitor is not None else [],
            trace_refs=(
                top_competitor.trace_refs
                if top_competitor is not None
                else [f"overview:{task_id}"]
            ),
            drilldown_refs=top_competitor.drilldown_refs if top_competitor is not None else [],
            risk_flags=[],
        )
    )
    return findings[:3]


def _risk_points(
    task_id: str,
    key_competitors: Sequence[OverviewKeyCompetitor],
    analysis_scope,
    review_tasks: Sequence[ReviewTask],
) -> list[OverviewFinding]:
    findings = []
    top_competitor = key_competitors[0] if key_competitors else None
    open_reviews = _open_review_tasks(review_tasks)
    if open_reviews:
        findings.append(
            OverviewFinding(
                finding_id=f"risk_{task_id}_qa_001",
                finding_type=OverviewFindingType.EVIDENCE_RISK,
                title="仍有证据风险待处理",
                description="当前仍存在未解决的审查问题，结论不应直接进入产品决策。",
                evidence_ids=_dedupe(
                    evidence_id for task in open_reviews for evidence_id in task.evidence_ids
                ),
                trace_refs=[f"qa_agent:{task.review_task_id}" for task in open_reviews],
                drilldown_refs=[
                    _drilldown(
                        OverviewDrilldownType.TRACE,
                        "查看审查问题",
                        open_reviews[0].review_task_id,
                        f"/tasks/{task_id}/trace",
                    )
                ],
                risk_flags=[RiskFlag.UNRELIABLE_DATA],
            )
        )

    if analysis_scope.missing_fields:
        findings.append(
            OverviewFinding(
                finding_id=f"risk_{task_id}_scope_001",
                finding_type=OverviewFindingType.EVIDENCE_RISK,
                title="分析范围存在字段缺口",
                description="部分时效字段不完整，价格与竞争判断需要结合快照限制阅读。",
                evidence_ids=analysis_scope.evidence_ids,
                trace_refs=[f"collection_agent:{task_id}"],
                drilldown_refs=[
                    _drilldown(
                        OverviewDrilldownType.TRACE,
                        "查看采集过程",
                        f"trace_{task_id}",
                        f"/tasks/{task_id}/trace",
                    )
                ],
                risk_flags=[RiskFlag.MISSING_ACCESS_TIME],
            )
        )

    if top_competitor is not None and top_competitor.threat_level in {
        ThreatLevel.HIGH,
        ThreatLevel.HIGH_SCORE_NEEDS_REVIEW,
    }:
        findings.append(
            OverviewFinding(
                finding_id=f"risk_{task_id}_competition_001",
                finding_type=OverviewFindingType.COMPETITION_RISK,
                title="关键竞品拦截风险较高",
                description=(
                    f"{top_competitor.product_name} 在当前切片中形成明显拦截，"
                    "需要优先拆解。"
                ),
                evidence_ids=top_competitor.evidence_ids,
                trace_refs=top_competitor.trace_refs,
                drilldown_refs=top_competitor.drilldown_refs,
                risk_flags=top_competitor.risk_flags,
            )
        )
    return findings[:3]


def _actions(
    task_id: str,
    key_competitors: Sequence[OverviewKeyCompetitor],
    risk_points: Sequence[OverviewFinding],
    decision_usability: DisplayStatus,
) -> list[OverviewActionRecommendation]:
    actions = []
    top_competitor = key_competitors[0] if key_competitors else None
    if top_competitor is not None:
        priority = (
            "p0_immediate"
            if top_competitor.threat_level
            in {ThreatLevel.HIGH, ThreatLevel.HIGH_SCORE_NEEDS_REVIEW}
            else "p1_current_iteration"
        )
        actions.append(
            OverviewActionRecommendation(
                action_id=f"action_{task_id}_content_001",
                title="优先补强关键竞品对比表达",
                description=(
                    f"针对{top_competitor.product_name} 的关系标签补充卖点、"
                    "价格和场景证据。"
                ),
                priority=priority,
                responsibility_type="content_expression",
                expected_impact="提升当前切片下的转化解释力。",
                evidence_ids=top_competitor.evidence_ids,
                trace_refs=top_competitor.trace_refs,
                drilldown_refs=top_competitor.drilldown_refs,
                risk_flags=top_competitor.risk_flags,
            )
        )

    if risk_points and decision_usability.value != DecisionUsabilityStatus.READY:
        risk = risk_points[0]
        actions.append(
            OverviewActionRecommendation(
                action_id=f"action_{task_id}_evidence_001",
                title="先补齐阻断性证据",
                description="优先处理未解决或限制决策可信度的证据问题，再推进策略结论。",
                priority="p0_immediate",
                responsibility_type="evidence_research",
                expected_impact="降低误判和复盘成本。",
                evidence_ids=risk.evidence_ids,
                trace_refs=risk.trace_refs,
                drilldown_refs=risk.drilldown_refs,
                risk_flags=risk.risk_flags,
            )
        )

    if not actions:
        actions.append(
            OverviewActionRecommendation(
                action_id=f"action_{task_id}_validation_001",
                title="保留后续验证清单",
                description="当前没有阻断项，可将弱证据结论纳入后续调研验证。",
                priority="p2_follow_up_validation",
                responsibility_type="evidence_research",
                expected_impact="保持结论可追溯并减少过度推断。",
                evidence_ids=[],
                trace_refs=[f"overview:{task_id}"],
                drilldown_refs=[],
                risk_flags=[],
            )
        )
    return actions[:5]


def _judgment_strength(
    edge_contexts: Sequence[dict[str, Any]],
    claims_by_id: Mapping[str, Claim],
    review_tasks: Sequence[ReviewTask],
) -> DisplayStatus:
    open_high_risk = _has_open_high_severity_review(review_tasks)
    claim_ids = _dedupe(
        claim_id for context in edge_contexts for claim_id in context["claim_ids"]
    )
    confidences = [
        claims_by_id[claim_id].confidence for claim_id in claim_ids if claim_id in claims_by_id
    ]
    average_confidence = sum(confidences) / len(confidences) if confidences else 0
    if open_high_risk or average_confidence < 0.55:
        return _display_status(
            JudgmentStrength.HYPOTHESIS,
            "仅作假设",
            "核心证据不足或仍有未解决的高严重度审查风险。",
            evidence_ids=[],
            trace_refs=_review_trace_refs(review_tasks),
            risk_flags=[RiskFlag.UNRELIABLE_DATA] if open_high_risk else [],
        )
    if average_confidence >= 0.75:
        return _display_status(
            JudgmentStrength.CLEAR,
            "明确判断",
            f"平均置信度 {average_confidence:.2f}，关键证据可追溯且无未解决高严重度风险。",
            evidence_ids=[],
            trace_refs=[],
            risk_flags=[],
        )
    return _display_status(
        JudgmentStrength.DIRECTIONAL,
        "倾向判断",
        f"平均置信度 {average_confidence:.2f}，适合作为方向性讨论输入。",
        evidence_ids=[],
        trace_refs=[],
        risk_flags=[],
    )


def _decision_usability(
    judgment_strength: DisplayStatus,
    key_competitors: Sequence[OverviewKeyCompetitor],
    review_tasks: Sequence[ReviewTask],
) -> DisplayStatus:
    open_reviews = _open_review_tasks(review_tasks)
    has_insufficient_evidence = any(
        competitor.evidence_credibility.value == EvidenceCredibilityStatus.INSUFFICIENT
        for competitor in key_competitors
    )
    if _has_open_high_severity_review(review_tasks) or has_insufficient_evidence:
        return _display_status(
            DecisionUsabilityStatus.DIRECTIONAL_ONLY,
            "仅供方向参考",
            "存在未解决高严重度风险或关键证据不足，不建议直接用于产品决策。",
            evidence_ids=_dedupe(
                evidence_id for task in open_reviews for evidence_id in task.evidence_ids
            ),
            trace_refs=_review_trace_refs(open_reviews),
            risk_flags=[RiskFlag.UNRELIABLE_DATA],
        )
    if open_reviews or judgment_strength.value == JudgmentStrength.HYPOTHESIS:
        return _display_status(
            DecisionUsabilityStatus.CAUTION,
            "建议谨慎决策",
            "存在局部证据限制或中低风险，可作为产品讨论输入。",
            evidence_ids=_dedupe(
                evidence_id for task in open_reviews for evidence_id in task.evidence_ids
            ),
            trace_refs=_review_trace_refs(open_reviews),
            risk_flags=[RiskFlag.UNRELIABLE_DATA] if open_reviews else [],
        )
    return _display_status(
        DecisionUsabilityStatus.READY,
        "可用于初步决策",
        "关键结论有证据支持，QA 风险已解决或可接受。",
        evidence_ids=_dedupe(
            evidence_id for competitor in key_competitors for evidence_id in competitor.evidence_ids
        ),
        trace_refs=_dedupe(
            trace_ref for competitor in key_competitors for trace_ref in competitor.trace_refs
        ),
        risk_flags=[],
    )


def _evidence_credibility(
    evidence_ids: Sequence[str],
    evidences_by_id: Mapping[str, Evidence],
    related_open_reviews: Sequence[ReviewTask],
) -> DisplayStatus:
    if related_open_reviews:
        return _display_status(
            EvidenceCredibilityStatus.INSUFFICIENT,
            "证据不足",
            "存在未解决的相关审查问题。",
            evidence_ids=evidence_ids,
            trace_refs=_review_trace_refs(related_open_reviews),
            risk_flags=[RiskFlag.UNRELIABLE_DATA],
        )
    if not evidence_ids or any(evidence_id not in evidences_by_id for evidence_id in evidence_ids):
        return _display_status(
            EvidenceCredibilityStatus.INSUFFICIENT,
            "证据不足",
            "缺少关键证据或证据记录不可追溯。",
            evidence_ids=evidence_ids,
            trace_refs=[],
            risk_flags=[RiskFlag.MISSING_EVIDENCE],
        )

    edge_evidences = [evidences_by_id[evidence_id] for evidence_id in evidence_ids]
    if any(_evidence_is_incomplete(evidence) for evidence in edge_evidences):
        return _display_status(
            EvidenceCredibilityStatus.CAUTIOUS_REFERENCE,
            "谨慎参考",
            "证据基本可追溯，但存在时间或来源局限。",
            evidence_ids=evidence_ids,
            trace_refs=[],
            risk_flags=[RiskFlag.UNRELIABLE_DATA],
        )
    return _display_status(
        EvidenceCredibilityStatus.DIRECTLY_ADOPTABLE,
        "可直接采纳",
        "关键证据具备来源、访问时间、内容摘要和局限性说明。",
        evidence_ids=evidence_ids,
        trace_refs=[],
        risk_flags=[],
    )


def _threat_level(edge_score: float, credibility: EvidenceCredibilityStatus) -> ThreatLevel:
    if credibility == EvidenceCredibilityStatus.INSUFFICIENT and edge_score >= 0.60:
        return ThreatLevel.HIGH_SCORE_NEEDS_REVIEW
    if edge_score >= 0.80:
        return ThreatLevel.HIGH
    if edge_score >= 0.60 and credibility != EvidenceCredibilityStatus.INSUFFICIENT:
        return ThreatLevel.MEDIUM
    return ThreatLevel.LOW


def _relationship_label(edge: CompetitionEdge) -> PMRelationshipLabel:
    if edge.competition_type == CompetitionType.DIRECT:
        return PMRelationshipLabel.HEAD_TO_HEAD
    if edge.competition_type == CompetitionType.CHANNEL:
        return PMRelationshipLabel.LOW_PRICE_INTERCEPTION
    if edge.competition_type == CompetitionType.CONTENT_COOCCURRENCE:
        return PMRelationshipLabel.CONTENT_SEEDING_COMPETITION
    return PMRelationshipLabel.SCENARIO_SUBSTITUTE


def _competitor_reason(edge: CompetitionEdge, product: Product, threat_level: ThreatLevel) -> str:
    return (
        f"{product.name} 在 {edge.slice.price_band}/{edge.slice.persona}/"
        f"{edge.slice.scenario} 切片下关系分为 {edge.edge_score:.2f}，"
        f"按 2.0 标准标记为{_threat_label(threat_level)}。"
    )


def _key_competitor_risks(context: Mapping[str, Any]) -> list[RiskFlag]:
    risks = []
    risks.extend(context["edge"].risk_flags)
    risks.extend(context["credibility"].risk_flags)
    if context["threat_level"] == ThreatLevel.HIGH_SCORE_NEEDS_REVIEW:
        risks.append(RiskFlag.UNRELIABLE_DATA)
    return _dedupe(risks)


def _related_open_reviews(
    edge: CompetitionEdge,
    claim_ids: Sequence[str],
    evidence_ids: Sequence[str],
    review_tasks: Sequence[ReviewTask],
) -> list[ReviewTask]:
    claim_id_set = set(claim_ids)
    evidence_id_set = set(evidence_ids)
    related_reviews = []
    for task in _open_review_tasks(review_tasks):
        if task.target_id == edge.edge_id:
            related_reviews.append(task)
            continue
        if task.target_id in claim_id_set or task.target_id in evidence_id_set:
            related_reviews.append(task)
            continue
        if claim_id_set.intersection(task.related_claim_ids) or evidence_id_set.intersection(
            task.evidence_ids
        ):
            related_reviews.append(task)
    return related_reviews


def _open_review_tasks(review_tasks: Sequence[ReviewTask]) -> list[ReviewTask]:
    return [task for task in review_tasks if task.status == ReviewStatus.OPEN]


def _has_open_high_severity_review(review_tasks: Sequence[ReviewTask]) -> bool:
    return any(
        task.status == ReviewStatus.OPEN
        and task.severity in {ReviewSeverity.ERROR, ReviewSeverity.BLOCKER}
        for task in review_tasks
    )


def _review_trace_refs(review_tasks: Sequence[ReviewTask]) -> list[str]:
    return [f"qa_agent:{task.review_task_id}" for task in review_tasks]


def _evidence_is_incomplete(evidence: Evidence) -> bool:
    return (
        evidence.source_url is None
        or evidence.access_time is None
        or not evidence.content_summary.strip()
        or not evidence.limitations.strip()
    )


def _filtered_edges(
    edges: Sequence[CompetitionEdge],
    selected_slice: BattlefieldSliceSelection,
) -> list[CompetitionEdge]:
    return [
        edge
        for edge in edges
        if (selected_slice.price_band is None or edge.slice.price_band == selected_slice.price_band)
        and (selected_slice.persona is None or edge.slice.persona == selected_slice.persona)
        and (selected_slice.scenario is None or edge.slice.scenario == selected_slice.scenario)
    ]


def _first_context(
    contexts: Sequence[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> dict[str, Any] | None:
    for context in contexts:
        if predicate(context):
            return context
    return None


def _display_status(
    value,
    label: str,
    reason: str,
    *,
    evidence_ids: Sequence[str],
    trace_refs: Sequence[str],
    risk_flags: Sequence[RiskFlag],
) -> DisplayStatus:
    return DisplayStatus(
        value=value,
        label=label,
        reason=reason,
        evidence_ids=list(evidence_ids),
        trace_refs=list(trace_refs),
        risk_flags=list(risk_flags),
    )


def _drilldown(
    reference_type: OverviewDrilldownType,
    label: str,
    target_id: str,
    route: str,
) -> OverviewDrilldownReference:
    return OverviewDrilldownReference(
        reference_type=reference_type,
        label=label,
        target_id=target_id,
        route=route,
    )


def _overview_artifact_id(task_id: str, selected_slice: BattlefieldSliceSelection) -> str:
    parts = [
        selected_slice.price_band or "all_price_bands",
        selected_slice.persona or "all_personas",
        selected_slice.scenario or "all_scenarios",
    ]
    safe_parts = ["".join(char if char.isalnum() else "_" for char in part) for part in parts]
    return f"overview_{task_id}_{'_'.join(safe_parts)}"


def _slice_label(selected_slice: BattlefieldSliceSelection) -> str:
    if not any([selected_slice.price_band, selected_slice.persona, selected_slice.scenario]):
        return "整体竞争视角下"
    return f"{_slice_plain_text(selected_slice)}中"


def _slice_plain_text(selected_slice: BattlefieldSliceSelection) -> str:
    parts = [
        selected_slice.price_band or "全部价格带",
        selected_slice.persona or "全部人群",
        selected_slice.scenario or "全部场景",
    ]
    return "/".join(parts)


def _threat_label(threat_level: ThreatLevel) -> str:
    labels = {
        ThreatLevel.HIGH: "高威胁",
        ThreatLevel.MEDIUM: "中威胁",
        ThreatLevel.LOW: "低威胁",
        ThreatLevel.HIGH_SCORE_NEEDS_REVIEW: "高分需复核",
    }
    return labels[threat_level]


def _model_list[T](
    state: Mapping[str, Any],
    key: str,
    model_type: type[T],
) -> list[T]:
    values = state.get(key, [])
    if not isinstance(values, list):
        return []
    return [model_type.model_validate(item) for item in values]


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _dedupe[T](items: Iterable[T]) -> list[T]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped
