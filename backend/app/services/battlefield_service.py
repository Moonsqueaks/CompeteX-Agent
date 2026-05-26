from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, datetime
from typing import Any

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AgentMessage,
    AgentMessageType,
    AnalysisTask,
    BattlefieldClaimReference,
    BattlefieldData,
    BattlefieldDecisionChainStage,
    BattlefieldEvidenceCard,
    BattlefieldGraphEdge,
    BattlefieldGraphNode,
    BattlefieldQASummary,
    BattlefieldScoreExplanation,
    BattlefieldSliceOption,
    BattlefieldSliceSelection,
    Claim,
    ClaimStatus,
    CompetitionEdge,
    DecisionStage,
    Evidence,
    Product,
    ProductRole,
    ReviewStatus,
    ReviewTask,
    RiskFlag,
    TaskStatus,
)
from app.storage import ArtifactRepository, TaskRepository

BATTLEFIELD_ARTIFACT_TYPE = "battlefield_data"
MAX_EVIDENCE_CARD_SUMMARY_CHARS = 220

WorkflowFactory = Callable[[], Any]


class BattlefieldServiceError(Exception):
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


class BattlefieldService:
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

    def get_battlefield(
        self,
        task_id: str,
        *,
        price_band: str | None = None,
        persona: str | None = None,
        scenario: str | None = None,
    ) -> BattlefieldData:
        task = self._get_completed_task(task_id)
        selected_slice = BattlefieldSliceSelection(
            price_band=price_band,
            persona=persona,
            scenario=scenario,
        )
        artifact_id = _battlefield_artifact_id(task_id, selected_slice)
        cached = self.artifact_repository.get(
            task_id,
            BATTLEFIELD_ARTIFACT_TYPE,
            artifact_id,
            BattlefieldData,
        )
        if cached is not None:
            return BattlefieldData.model_validate(cached)
        return self._generate_and_cache_battlefield(task, selected_slice, artifact_id)

    def _get_completed_task(self, task_id: str) -> AnalysisTask:
        task = self.task_repository.get(task_id)
        if task is None:
            raise BattlefieldServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task_id},
            )
        if task.status != TaskStatus.COMPLETED:
            raise BattlefieldServiceError(
                "BATTLEFIELD_NOT_READY",
                "Battlefield data is only available after the task is completed.",
                status_code=409,
                details={"task_id": task_id, "status": task.status.value},
            )
        return task

    def _generate_and_cache_battlefield(
        self,
        task: AnalysisTask,
        selected_slice: BattlefieldSliceSelection,
        artifact_id: str,
    ) -> BattlefieldData:
        try:
            workflow = self.workflow_factory()
            state = create_initial_state(task)
            result = workflow.invoke(state)
        except Exception as exc:
            raise BattlefieldServiceError(
                "BATTLEFIELD_GENERATION_FAILED",
                "Battlefield generation failed",
                status_code=500,
                details={"task_id": task.task_id, "reason": exc.__class__.__name__},
            ) from exc

        if result["task"].get("status") != TaskStatus.COMPLETED.value:
            raise BattlefieldServiceError(
                "BATTLEFIELD_GENERATION_FAILED",
                "Battlefield generation did not complete the workflow.",
                status_code=500,
                details={
                    "task_id": task.task_id,
                    "workflow_status": result["task"].get("status"),
                },
            )

        battlefield = _build_battlefield_data(result, selected_slice, artifact_id)
        self.artifact_repository.save(
            BATTLEFIELD_ARTIFACT_TYPE,
            battlefield.battlefield_id,
            battlefield,
        )
        return battlefield


def _build_battlefield_data(
    state: dict[str, Any],
    selected_slice: BattlefieldSliceSelection,
    battlefield_id: str,
) -> BattlefieldData:
    products = [Product.model_validate(item) for item in state["products"]]
    evidences = [Evidence.model_validate(item) for item in state["evidences"]]
    claims = [Claim.model_validate(item) for item in state["claims"]]
    edges = [CompetitionEdge.model_validate(item) for item in state["competition_edges"]]
    review_tasks = [ReviewTask.model_validate(item) for item in state["review_tasks"]]
    agent_messages = [AgentMessage.model_validate(item) for item in state["agent_messages"]]
    task_id = str(state["task"]["task_id"])

    products_by_id = {product.product_id: product for product in products}
    claims_by_id = {claim.claim_id: claim for claim in claims}
    evidences_by_id = {evidence.evidence_id: evidence for evidence in evidences}
    target_product = _target_product(products)
    filtered_edges = _filter_edges(edges, selected_slice)
    filtered_edges = sorted(filtered_edges, key=lambda edge: edge.edge_score, reverse=True)
    graph_edges = [
        _graph_edge(edge, claims_by_id, review_tasks)
        for edge in filtered_edges
        if edge.target_product_id in products_by_id and edge.competitor_product_id in products_by_id
    ]
    product_ids = _dedupe(
        [
            target_product.product_id,
            *[edge.competitor_product_id for edge in filtered_edges],
        ]
    )
    evidence_ids = _dedupe(evidence_id for edge in graph_edges for evidence_id in edge.evidence_ids)

    return BattlefieldData(
        battlefield_id=battlefield_id,
        task_id=task_id,
        generated_at=datetime.now(UTC),
        selected_slice=selected_slice,
        available_slices=_available_slices(edges),
        graph_nodes=[_graph_node(products_by_id[product_id]) for product_id in product_ids],
        graph_edges=graph_edges,
        score_explanations=[
            _score_explanation(edge, claims_by_id) for edge in filtered_edges
        ],
        decision_chain=_decision_chain(filtered_edges, graph_edges),
        evidence_cards=[
            _evidence_card(evidences_by_id[evidence_id])
            for evidence_id in evidence_ids
            if evidence_id in evidences_by_id
        ],
        qa_summary=_qa_summary(graph_edges, claims_by_id, review_tasks, agent_messages),
        metadata={
            "target_product_id": target_product.product_id,
            "edge_count": len(graph_edges),
            "node_count": len(product_ids),
            "source": "langgraph_workflow",
        },
    )


def _target_product(products: Sequence[Product]) -> Product:
    for product in products:
        if product.role == ProductRole.TARGET:
            return product
    raise BattlefieldServiceError(
        "BATTLEFIELD_GENERATION_FAILED",
        "Battlefield generation did not produce a target product.",
        status_code=500,
    )


def _filter_edges(
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


def _available_slices(edges: Sequence[CompetitionEdge]) -> list[BattlefieldSliceOption]:
    grouped: dict[tuple[str, str, str], list[CompetitionEdge]] = {}
    for edge in edges:
        key = (edge.slice.price_band, edge.slice.persona, edge.slice.scenario)
        grouped.setdefault(key, []).append(edge)
    return [
        BattlefieldSliceOption(
            price_band=price_band,
            persona=persona,
            scenario=scenario,
            edge_count=len(slice_edges),
            top_edge_score=max(edge.edge_score for edge in slice_edges),
        )
        for (price_band, persona, scenario), slice_edges in sorted(grouped.items())
    ]


def _graph_node(product: Product) -> BattlefieldGraphNode:
    return BattlefieldGraphNode(
        node_id=product.product_id,
        product_id=product.product_id,
        label=product.name,
        role=product.role,
        brand=product.brand,
        shop_name=product.shop_name,
        product_url=product.product_url,
        evidence_ids=product.evidence_ids,
    )


def _graph_edge(
    edge: CompetitionEdge,
    claims_by_id: dict[str, Claim],
    review_tasks: Sequence[ReviewTask],
) -> BattlefieldGraphEdge:
    claim_refs = [
        _claim_ref(claims_by_id[claim_id])
        for claim_id in edge.claim_ids
        if claim_id in claims_by_id
    ]
    evidence_ids = _dedupe(
        evidence_id for claim_ref in claim_refs for evidence_id in claim_ref.evidence_ids
    )
    risk_flags = _edge_risk_flags(edge, claim_refs, review_tasks)
    return BattlefieldGraphEdge(
        edge_id=edge.edge_id,
        source=edge.target_product_id,
        target=edge.competitor_product_id,
        target_product_id=edge.target_product_id,
        competitor_product_id=edge.competitor_product_id,
        competition_type=edge.competition_type,
        slice=BattlefieldSliceSelection(
            price_band=edge.slice.price_band,
            persona=edge.slice.persona,
            scenario=edge.slice.scenario,
        ),
        decision_stages=edge.decision_stages,
        edge_score=edge.edge_score,
        score_breakdown=edge.score_breakdown,
        score_explanations=_score_explanation_lines(edge),
        claim_ids=edge.claim_ids,
        evidence_ids=evidence_ids,
        claim_refs=claim_refs,
        risk_flags=risk_flags,
        risk_status="at_risk" if risk_flags else "normal",
        human_adjusted=edge.human_adjusted,
    )


def _claim_ref(claim: Claim) -> BattlefieldClaimReference:
    return BattlefieldClaimReference(
        claim_id=claim.claim_id,
        content=claim.content,
        confidence=claim.confidence,
        status=claim.status.value,
        is_inference=claim.is_inference,
        evidence_ids=claim.evidence_ids,
        risk_flags=claim.risk_flags,
    )


def _edge_risk_flags(
    edge: CompetitionEdge,
    claim_refs: Sequence[BattlefieldClaimReference],
    review_tasks: Sequence[ReviewTask],
) -> list[RiskFlag]:
    flags: list[RiskFlag] = [*edge.risk_flags]
    if not claim_refs:
        flags.append(RiskFlag.MISSING_EVIDENCE)
    if not any(claim.evidence_ids for claim in claim_refs):
        flags.append(RiskFlag.MISSING_EVIDENCE)
    for claim in claim_refs:
        flags.extend(claim.risk_flags)
        if claim.status != ClaimStatus.ACCEPTED.value:
            flags.append(RiskFlag.UNRELIABLE_DATA)

    related_claim_ids = {claim.claim_id for claim in claim_refs}
    for review_task in review_tasks:
        if review_task.status != ReviewStatus.OPEN:
            continue
        if review_task.target_id == edge.edge_id or related_claim_ids.intersection(
            review_task.related_claim_ids
        ):
            flags.append(RiskFlag.UNRELIABLE_DATA)
    return _dedupe(flags)


def _score_explanation(
    edge: CompetitionEdge,
    claims_by_id: dict[str, Claim],
) -> BattlefieldScoreExplanation:
    claim_ids = [claim_id for claim_id in edge.claim_ids if claim_id in claims_by_id]
    evidence_ids = _dedupe(
        evidence_id
        for claim_id in claim_ids
        for evidence_id in claims_by_id[claim_id].evidence_ids
    )
    return BattlefieldScoreExplanation(
        edge_id=edge.edge_id,
        edge_score=edge.edge_score,
        score_breakdown=edge.score_breakdown,
        explanations=_score_explanation_lines(edge),
        claim_ids=claim_ids,
        evidence_ids=evidence_ids,
    )


def _score_explanation_lines(edge: CompetitionEdge) -> list[str]:
    breakdown = edge.score_breakdown
    return [
        f"edge_score={edge.edge_score:.4f}; competition_type={edge.competition_type.value}.",
        (
            "demand_substitutability="
            f"{breakdown.demand_substitutability:.2f}, "
            f"context_match={breakdown.context_match:.2f}, "
            f"decision_stage_impact={breakdown.decision_stage_impact:.2f}."
        ),
        (
            "evidence_confidence="
            f"{breakdown.evidence_confidence:.2f}, market_signal_strength="
            f"{breakdown.market_signal_strength:.2f}."
        ),
    ]


def _decision_chain(
    edges: Sequence[CompetitionEdge],
    graph_edges: Sequence[BattlefieldGraphEdge],
) -> list[BattlefieldDecisionChainStage]:
    graph_edges_by_id = {edge.edge_id: edge for edge in graph_edges}
    chain = []
    for stage in DecisionStage:
        stage_edges = [edge for edge in edges if stage in edge.decision_stages]
        if not stage_edges:
            continue
        stage_graph_edges = [
            graph_edges_by_id[edge.edge_id]
            for edge in stage_edges
            if edge.edge_id in graph_edges_by_id
        ]
        scores = [edge.edge_score for edge in stage_edges]
        chain.append(
            BattlefieldDecisionChainStage(
                stage=stage,
                edge_ids=[edge.edge_id for edge in stage_edges],
                claim_ids=_dedupe(
                    claim_id for edge in stage_graph_edges for claim_id in edge.claim_ids
                ),
                evidence_ids=_dedupe(
                    evidence_id for edge in stage_graph_edges for evidence_id in edge.evidence_ids
                ),
                average_edge_score=round(sum(scores) / len(scores), 4),
            )
        )
    return chain


def _evidence_card(evidence: Evidence) -> BattlefieldEvidenceCard:
    risk_flags = []
    if evidence.access_time is None:
        risk_flags.append(RiskFlag.MISSING_ACCESS_TIME)
    if evidence.screenshot_path is None:
        risk_flags.append(RiskFlag.MISSING_SCREENSHOT)
    return BattlefieldEvidenceCard(
        evidence_id=evidence.evidence_id,
        product_id=evidence.product_id,
        source_type=evidence.source_type,
        source_url=evidence.source_url,
        screenshot_path=evidence.screenshot_path,
        access_time=evidence.access_time,
        access_time_status="available" if evidence.access_time is not None else "missing",
        confidence_level=evidence.confidence_level,
        content_summary=_shorten(evidence.content_summary),
        limitations=_shorten(evidence.limitations),
        risk_flags=_dedupe(risk_flags),
    )


def _qa_summary(
    graph_edges: Sequence[BattlefieldGraphEdge],
    claims_by_id: dict[str, Claim],
    review_tasks: Sequence[ReviewTask],
    agent_messages: Sequence[AgentMessage],
) -> BattlefieldQASummary:
    risk_edge_ids = [edge.edge_id for edge in graph_edges if edge.risk_status == "at_risk"]
    risk_claim_ids = _dedupe(
        claim_id
        for edge in graph_edges
        for claim_id in edge.claim_ids
        if claim_id in claims_by_id and claims_by_id[claim_id].status != ClaimStatus.ACCEPTED
    )
    open_count = sum(1 for task in review_tasks if task.status == ReviewStatus.OPEN)
    resolved_count = sum(1 for task in review_tasks if task.status == ReviewStatus.RESOLVED)
    revision_count = sum(
        1 for message in agent_messages if message.message_type == AgentMessageType.REVISION_REQUEST
    )
    return BattlefieldQASummary(
        qa_status="needs_attention" if risk_edge_ids or open_count else "passed",
        review_task_count=len(review_tasks),
        open_review_task_count=open_count,
        resolved_review_task_count=resolved_count,
        revision_message_count=revision_count,
        risk_edge_ids=risk_edge_ids,
        risk_claim_ids=risk_claim_ids,
        review_task_ids=[review_task.review_task_id for review_task in review_tasks],
    )


def _battlefield_artifact_id(task_id: str, selected_slice: BattlefieldSliceSelection) -> str:
    parts = [
        selected_slice.price_band or "all_price_bands",
        selected_slice.persona or "all_personas",
        selected_slice.scenario or "all_scenarios",
    ]
    safe_parts = ["".join(char if char.isalnum() else "_" for char in part) for part in parts]
    return f"battlefield_{task_id}_{'_'.join(safe_parts)}"


def _shorten(value: str) -> str:
    compact = " ".join(value.split())
    if len(compact) <= MAX_EVIDENCE_CARD_SUMMARY_CHARS:
        return compact
    return compact[: MAX_EVIDENCE_CARD_SUMMARY_CHARS - 3].rstrip() + "..."


def _dedupe[T](items: Iterable[T]) -> list[T]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped
