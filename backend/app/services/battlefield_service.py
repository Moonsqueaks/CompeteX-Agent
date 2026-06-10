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
    BattlefieldExplanationSegment,
    BattlefieldFourPartExplanation,
    BattlefieldGraphEdge,
    BattlefieldGraphNode,
    BattlefieldKeyRelation,
    BattlefieldQASummary,
    BattlefieldRelationFilter,
    BattlefieldScoreExplanation,
    BattlefieldSliceOption,
    BattlefieldSliceSelection,
    Claim,
    ClaimStatus,
    CompetitionEdge,
    CompetitionType,
    DecisionStage,
    DisplayStatus,
    Evidence,
    EvidenceCredibilityStatus,
    PMRelationshipLabel,
    Product,
    ProductRole,
    ReviewStatus,
    ReviewTask,
    RiskFlag,
    TaskStatus,
    ThreatLevel,
)
from app.services.display_copy import sanitize_internal_standard_copy
from app.services.product_image_metadata import product_main_image_url
from app.storage import ArtifactRepository, TaskRepository

BATTLEFIELD_ARTIFACT_TYPE = "battlefield_data"
MAX_EVIDENCE_CARD_SUMMARY_CHARS = 220
DEFAULT_KEY_RELATION_LIMIT = 5
DEFAULT_KEY_RELATION_MIN_COUNT = 3
_BATTLEFIELD_READABLE_STATUSES = {TaskStatus.COMPLETED, TaskStatus.HUMAN_REVIEWING}

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
        include_all_relations: bool = False,
    ) -> BattlefieldData:
        task = self._get_completed_task(task_id)
        selected_slice = BattlefieldSliceSelection(
            price_band=price_band,
            persona=persona,
            scenario=scenario,
        )
        artifact_id = _battlefield_artifact_id(
            task_id,
            selected_slice,
            include_all_relations=include_all_relations,
        )
        cached = self.artifact_repository.get(
            task_id,
            BATTLEFIELD_ARTIFACT_TYPE,
            artifact_id,
            BattlefieldData,
        )
        if cached is not None:
            cached_battlefield = BattlefieldData.model_validate(cached)
            battlefield = _sanitize_battlefield_display_copy(cached_battlefield)
            battlefield = _hydrate_battlefield_product_images(battlefield)
            if battlefield != cached_battlefield:
                self.artifact_repository.save(
                    BATTLEFIELD_ARTIFACT_TYPE,
                    battlefield.battlefield_id,
                    battlefield,
                )
            return battlefield
        return self._generate_and_cache_battlefield(
            task,
            selected_slice,
            artifact_id,
            include_all_relations,
        )

    def _get_completed_task(self, task_id: str) -> AnalysisTask:
        task = self.task_repository.get(task_id)
        if task is None:
            raise BattlefieldServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task_id},
            )
        if task.status not in _BATTLEFIELD_READABLE_STATUSES:
            raise BattlefieldServiceError(
                "BATTLEFIELD_NOT_READY",
                "Battlefield data is only available after completion or human review.",
                status_code=409,
                details={"task_id": task_id, "status": task.status.value},
            )
        return task

    def _generate_and_cache_battlefield(
        self,
        task: AnalysisTask,
        selected_slice: BattlefieldSliceSelection,
        artifact_id: str,
        include_all_relations: bool,
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

        battlefield = _build_battlefield_data(
            result,
            selected_slice,
            artifact_id,
            include_all_relations=include_all_relations,
        )
        battlefield = _hydrate_battlefield_product_images(battlefield)
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
    *,
    include_all_relations: bool = False,
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
    all_key_relations = [
        _key_relation(edge, products_by_id, claims_by_id, evidences_by_id, review_tasks)
        for edge in filtered_edges
        if edge.target_product_id in products_by_id and edge.competitor_product_id in products_by_id
    ]
    key_relations, relation_filter = _visible_key_relations(
        all_key_relations,
        filtered_edges,
        include_all_relations=include_all_relations,
    )
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
        key_relations=key_relations,
        relation_filter=relation_filter,
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


def _hydrate_battlefield_product_images(battlefield: BattlefieldData) -> BattlefieldData:
    graph_nodes = [_hydrate_battlefield_graph_node_image(node) for node in battlefield.graph_nodes]
    key_relations = [
        _hydrate_battlefield_key_relation_image(relation)
        for relation in battlefield.key_relations
    ]
    if graph_nodes == battlefield.graph_nodes and key_relations == battlefield.key_relations:
        return battlefield
    return battlefield.model_copy(
        update={
            "graph_nodes": graph_nodes,
            "key_relations": key_relations,
        },
    )


def _hydrate_battlefield_graph_node_image(
    node: BattlefieldGraphNode,
) -> BattlefieldGraphNode:
    image_url = product_main_image_url(product_id=node.product_id)
    if image_url is None or image_url == node.primary_image_path:
        return node
    return node.model_copy(update={"primary_image_path": image_url})


def _hydrate_battlefield_key_relation_image(
    relation: BattlefieldKeyRelation,
) -> BattlefieldKeyRelation:
    image_url = product_main_image_url(product_id=relation.competitor_product_id)
    if image_url is None or image_url == relation.competitor_primary_image_path:
        return relation
    return relation.model_copy(update={"competitor_primary_image_path": image_url})


def _sanitize_battlefield_display_copy(battlefield: BattlefieldData) -> BattlefieldData:
    payload = sanitize_internal_standard_copy(battlefield.model_dump(mode="json"))
    return BattlefieldData.model_validate(payload)


def _target_product(products: Sequence[Product]) -> Product:
    for product in products:
        if product.role == ProductRole.TARGET:
            return product
    raise BattlefieldServiceError(
        "BATTLEFIELD_GENERATION_FAILED",
        "Battlefield generation did not produce a target product.",
        status_code=500,
    )


def _visible_key_relations(
    all_relations: Sequence[BattlefieldKeyRelation],
    filtered_edges: Sequence[CompetitionEdge],
    *,
    include_all_relations: bool,
) -> tuple[list[BattlefieldKeyRelation], BattlefieldRelationFilter]:
    edges_by_id = {edge.edge_id: edge for edge in filtered_edges}
    default_relations = _default_key_relations(all_relations, edges_by_id)
    default_ids = {relation.edge_id for relation in default_relations}

    if include_all_relations:
        visible_relations = [
            relation.model_copy(update={"is_default_visible": relation.edge_id in default_ids})
            for relation in all_relations
        ]
    else:
        visible_relations = [
            relation.model_copy(update={"is_default_visible": True})
            for relation in default_relations
        ]

    relation_filter = BattlefieldRelationFilter(
        include_all_relations=include_all_relations,
        default_limit=DEFAULT_KEY_RELATION_LIMIT,
        total_relation_count=len(all_relations),
        visible_relation_count=len(visible_relations),
        can_expand_all=not include_all_relations and len(visible_relations) < len(all_relations),
    )
    return visible_relations, relation_filter


def _default_key_relations(
    all_relations: Sequence[BattlefieldKeyRelation],
    edges_by_id: dict[str, CompetitionEdge],
) -> list[BattlefieldKeyRelation]:
    if len(all_relations) <= DEFAULT_KEY_RELATION_MIN_COUNT:
        return list(all_relations)

    selected: list[BattlefieldKeyRelation] = []
    _append_first_relation(
        selected,
        all_relations,
        lambda relation: (
            edges_by_id[relation.edge_id].competition_type == CompetitionType.DIRECT
            and relation.threat_level != ThreatLevel.HIGH_SCORE_NEEDS_REVIEW
        ),
    )
    _append_first_relation(
        selected,
        all_relations,
        lambda relation: (
            edges_by_id[relation.edge_id].competition_type
            in {CompetitionType.ALTERNATIVE, CompetitionType.CHANNEL}
            and relation.threat_level != ThreatLevel.HIGH_SCORE_NEEDS_REVIEW
        ),
    )
    _append_first_relation(
        selected,
        all_relations,
        lambda relation: relation.threat_level == ThreatLevel.HIGH_SCORE_NEEDS_REVIEW,
    )
    _append_first_relation(selected, all_relations, _is_actionable_relation)

    target_count = min(DEFAULT_KEY_RELATION_LIMIT, len(all_relations))
    minimum_count = min(DEFAULT_KEY_RELATION_MIN_COUNT, len(all_relations))
    for relation in all_relations:
        if len(selected) >= target_count and len(selected) >= minimum_count:
            break
        _append_relation(selected, relation)

    return selected[:target_count]


def _append_first_relation(
    selected: list[BattlefieldKeyRelation],
    relations: Sequence[BattlefieldKeyRelation],
    predicate: Callable[[BattlefieldKeyRelation], bool],
) -> None:
    for relation in relations:
        if predicate(relation):
            _append_relation(selected, relation)
            return


def _append_relation(
    selected: list[BattlefieldKeyRelation],
    relation: BattlefieldKeyRelation,
) -> None:
    if relation.edge_id not in {item.edge_id for item in selected}:
        selected.append(relation)


def _is_actionable_relation(relation: BattlefieldKeyRelation) -> bool:
    return (
        relation.evidence_credibility.value != EvidenceCredibilityStatus.INSUFFICIENT
        and relation.threat_level in {ThreatLevel.HIGH, ThreatLevel.MEDIUM}
        and bool(relation.action_suggestion.strip())
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
        primary_image_path=_product_primary_image(product),
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


def _key_relation(
    edge: CompetitionEdge,
    products_by_id: dict[str, Product],
    claims_by_id: dict[str, Claim],
    evidences_by_id: dict[str, Evidence],
    review_tasks: Sequence[ReviewTask],
) -> BattlefieldKeyRelation:
    target = products_by_id[edge.target_product_id]
    competitor = products_by_id[edge.competitor_product_id]
    claim_ids = [claim_id for claim_id in edge.claim_ids if claim_id in claims_by_id]
    evidence_ids = _dedupe(
        evidence_id
        for claim_id in claim_ids
        for evidence_id in claims_by_id[claim_id].evidence_ids
    )
    evidence_credibility = _evidence_credibility(edge, evidence_ids, evidences_by_id, review_tasks)
    relationship_label = _relationship_label(
        edge=edge,
        target=target,
        competitor=competitor,
        evidence_ids=evidence_ids,
        evidences_by_id=evidences_by_id,
    )
    threat_level = _threat_level(edge.edge_score, evidence_credibility)
    risk_flags = _dedupe(
        [
            *edge.risk_flags,
            *evidence_credibility.risk_flags,
            *(
                [RiskFlag.UNRELIABLE_DATA]
                if threat_level == ThreatLevel.HIGH_SCORE_NEEDS_REVIEW
                else []
            ),
        ]
    )
    return BattlefieldKeyRelation(
        edge_id=edge.edge_id,
        target_product_id=edge.target_product_id,
        competitor_product_id=edge.competitor_product_id,
        competitor_product_name=competitor.name,
        competitor_brand=competitor.brand,
        competitor_primary_image_path=_product_primary_image(competitor),
        relationship_label=relationship_label,
        relationship_label_explanation=_relationship_label_explanation(relationship_label),
        threat_level=threat_level,
        evidence_credibility=evidence_credibility,
        inclusion_reason=_inclusion_reason(edge, competitor, threat_level),
        four_part_explanation=_four_part_explanation(
            edge=edge,
            competitor=competitor,
            evidence_credibility=evidence_credibility,
            threat_level=threat_level,
            claim_ids=claim_ids,
            evidence_ids=evidence_ids,
        ),
        action_suggestion=_action_suggestion(competitor, threat_level),
        claim_ids=claim_ids,
        evidence_ids=evidence_ids,
        trace_refs=[f"analysis_agent:{edge.edge_id}"],
        risk_flags=risk_flags,
    )


def _product_primary_image(product: Product) -> str | None:
    return (
        product_main_image_url(sku_id=product.sku_id, product_id=product.product_id)
        or product.primary_image_path
    )


def _evidence_credibility(
    edge: CompetitionEdge,
    evidence_ids: Sequence[str],
    evidences_by_id: dict[str, Evidence],
    review_tasks: Sequence[ReviewTask],
) -> DisplayStatus:
    related_open_reviews = _related_open_reviews(edge, evidence_ids, review_tasks)
    if related_open_reviews:
        return DisplayStatus(
            value=EvidenceCredibilityStatus.INSUFFICIENT,
            label="证据不足",
            reason="存在未解决的相关审查问题。",
            evidence_ids=list(evidence_ids),
            trace_refs=[f"qa_agent:{task.review_task_id}" for task in related_open_reviews],
            risk_flags=[RiskFlag.UNRELIABLE_DATA],
        )
    if not evidence_ids or any(evidence_id not in evidences_by_id for evidence_id in evidence_ids):
        return DisplayStatus(
            value=EvidenceCredibilityStatus.INSUFFICIENT,
            label="证据不足",
            reason="缺少关键证据或证据记录不可追溯。",
            evidence_ids=list(evidence_ids),
            trace_refs=[],
            risk_flags=[RiskFlag.MISSING_EVIDENCE],
    )
    edge_evidences = [evidences_by_id[evidence_id] for evidence_id in evidence_ids]
    if any(
        evidence.access_time is None or evidence.source_url is None
        for evidence in edge_evidences
    ):
        return DisplayStatus(
            value=EvidenceCredibilityStatus.CAUTIOUS_REFERENCE,
            label="谨慎参考",
            reason="证据基本可追溯，但存在时间或来源局限。",
            evidence_ids=list(evidence_ids),
            trace_refs=[],
            risk_flags=[RiskFlag.UNRELIABLE_DATA],
        )
    return DisplayStatus(
        value=EvidenceCredibilityStatus.DIRECTLY_ADOPTABLE,
        label="可直接采纳",
        reason="关键证据具备来源、访问时间、内容摘要和局限性说明。",
        evidence_ids=list(evidence_ids),
        trace_refs=[],
        risk_flags=[],
    )


def _related_open_reviews(
    edge: CompetitionEdge,
    evidence_ids: Sequence[str],
    review_tasks: Sequence[ReviewTask],
) -> list[ReviewTask]:
    evidence_id_set = set(evidence_ids)
    claim_id_set = set(edge.claim_ids)
    related_reviews = []
    for review_task in review_tasks:
        if review_task.status != ReviewStatus.OPEN:
            continue
        if review_task.target_id == edge.edge_id:
            related_reviews.append(review_task)
            continue
        if review_task.target_id in claim_id_set or review_task.target_id in evidence_id_set:
            related_reviews.append(review_task)
            continue
        if claim_id_set.intersection(review_task.related_claim_ids) or evidence_id_set.intersection(
            review_task.evidence_ids
        ):
            related_reviews.append(review_task)
    return related_reviews


def _threat_level(edge_score: float, evidence_credibility: DisplayStatus) -> ThreatLevel:
    if evidence_credibility.value == EvidenceCredibilityStatus.INSUFFICIENT and edge_score >= 0.60:
        return ThreatLevel.HIGH_SCORE_NEEDS_REVIEW
    if edge_score >= 0.80:
        return ThreatLevel.HIGH
    if edge_score >= 0.60:
        return ThreatLevel.MEDIUM
    return ThreatLevel.LOW


def _relationship_label(
    *,
    edge: CompetitionEdge,
    target: Product,
    competitor: Product,
    evidence_ids: Sequence[str],
    evidences_by_id: dict[str, Evidence],
) -> PMRelationshipLabel:
    if _has_trust_advantage_signal(competitor, evidence_ids, evidences_by_id):
        return PMRelationshipLabel.TRUST_SUPPRESSION
    if edge.competition_type == CompetitionType.CONTENT_COOCCURRENCE:
        return PMRelationshipLabel.CONTENT_SEEDING_COMPETITION
    if _is_low_price_interception(edge, target, competitor, evidence_ids, evidences_by_id):
        return PMRelationshipLabel.LOW_PRICE_INTERCEPTION
    if edge.competition_type == CompetitionType.DIRECT:
        return PMRelationshipLabel.HEAD_TO_HEAD
    if edge.competition_type == CompetitionType.CHANNEL:
        return PMRelationshipLabel.LOW_PRICE_INTERCEPTION
    return PMRelationshipLabel.SCENARIO_SUBSTITUTE


def _is_low_price_interception(
    edge: CompetitionEdge,
    target: Product,
    competitor: Product,
    evidence_ids: Sequence[str],
    evidences_by_id: dict[str, Evidence],
) -> bool:
    if edge.competition_type == CompetitionType.CHANNEL:
        return True
    target_price = _product_price(target.product_id, evidence_ids, evidences_by_id)
    competitor_price = _product_price(competitor.product_id, evidence_ids, evidences_by_id)
    if target_price is None or competitor_price is None:
        return False
    return competitor_price <= target_price * 0.8


def _product_price(
    product_id: str,
    evidence_ids: Sequence[str],
    evidences_by_id: dict[str, Evidence],
) -> float | None:
    for evidence_id in evidence_ids:
        evidence = evidences_by_id.get(evidence_id)
        if evidence is None or evidence.product_id != product_id:
            continue
        price = evidence.metadata.get("price")
        if not isinstance(price, dict):
            continue
        for field_name in ("display_price_yuan", "min_price_yuan", "max_price_yuan"):
            value = price.get(field_name)
            if isinstance(value, int | float):
                return float(value)
    return None


def _has_trust_advantage_signal(
    competitor: Product,
    evidence_ids: Sequence[str],
    evidences_by_id: dict[str, Evidence],
) -> bool:
    text_parts = [competitor.name, competitor.brand or "", *competitor.tags]
    for evidence_id in evidence_ids:
        evidence = evidences_by_id.get(evidence_id)
        if evidence is None or evidence.product_id != competitor.product_id:
            continue
        text_parts.append(evidence.content_summary)
        selling_points = evidence.metadata.get("selling_points")
        if isinstance(selling_points, list):
            text_parts.extend(item for item in selling_points if isinstance(item, str))
    text = " ".join(text_parts)
    trust_terms = ("安全", "认证", "防夹", "口碑", "评价", "售后", "信任", "质保")
    return any(term in text for term in trust_terms)


def _relationship_label_explanation(label: PMRelationshipLabel) -> str:
    explanations = {
        PMRelationshipLabel.HEAD_TO_HEAD: "同一核心需求与相近决策场景下直接比较。",
        PMRelationshipLabel.LOW_PRICE_INTERCEPTION: "通过更低价格或渠道可得性拦截预算敏感用户。",
        PMRelationshipLabel.SCENARIO_SUBSTITUTE: "在特定使用场景中替代目标产品完成相近任务。",
        PMRelationshipLabel.TRUST_SUPPRESSION: "通过信任、认证或口碑表达压制目标产品。",
        PMRelationshipLabel.CONTENT_SEEDING_COMPETITION: "在内容触达阶段争夺同类用户注意力。",
    }
    return explanations[label]


def _inclusion_reason(
    edge: CompetitionEdge,
    competitor: Product,
    threat_level: ThreatLevel,
) -> str:
    return (
        f"{competitor.name} 在当前切片关系分为 {edge.edge_score:.2f}，"
        f"当前标记为{_threat_label(threat_level)}候选关系。"
    )


def _four_part_explanation(
    *,
    edge: CompetitionEdge,
    competitor: Product,
    evidence_credibility: DisplayStatus,
    threat_level: ThreatLevel,
    claim_ids: Sequence[str],
    evidence_ids: Sequence[str],
) -> BattlefieldFourPartExplanation:
    slice_text = f"{edge.slice.price_band}/{edge.slice.persona}/{edge.slice.scenario}"
    trace_refs = [f"analysis_agent:{edge.edge_id}"]
    return BattlefieldFourPartExplanation(
        why_competitor=_explanation_segment(
            text=(
                f"{competitor.name} 覆盖 {slice_text}，与目标产品进入同一决策比较集合，"
                f"因此构成{_threat_label(threat_level)}关系。"
            ),
            claim_ids=claim_ids,
            evidence_ids=evidence_ids,
            trace_refs=trace_refs,
        ),
        strength=_explanation_segment(
            text=(
                f"它强在{_strongest_dimension(edge)}；当前证据可信状态为"
                f"{evidence_credibility.label}。"
            ),
            claim_ids=claim_ids,
            evidence_ids=evidence_ids,
            trace_refs=trace_refs,
        ),
        decision_stage_impact=_explanation_segment(
            text=(
                f"它可能在{_decision_stage_text(edge)}阶段抢走用户注意力或决策信心。"
            ),
            claim_ids=claim_ids,
            evidence_ids=evidence_ids,
            trace_refs=trace_refs,
        ),
        response_suggestion=_explanation_segment(
            text=(
                f"分析建议：围绕{competitor.name} 的关系标签补充可追溯对比证据，"
                "优先回应价格、卖点和场景表达。"
            ),
            claim_ids=claim_ids,
            evidence_ids=evidence_ids,
            trace_refs=trace_refs,
            is_analysis_suggestion=True,
        ),
    )


def _explanation_segment(
    *,
    text: str,
    claim_ids: Sequence[str],
    evidence_ids: Sequence[str],
    trace_refs: Sequence[str],
    is_analysis_suggestion: bool = False,
) -> BattlefieldExplanationSegment:
    return BattlefieldExplanationSegment(
        text=text,
        claim_ids=list(claim_ids),
        evidence_ids=list(evidence_ids),
        trace_refs=list(trace_refs),
        risk_flags=[],
        is_analysis_suggestion=is_analysis_suggestion,
    )


def _strongest_dimension(edge: CompetitionEdge) -> str:
    breakdown = edge.score_breakdown
    dimensions = {
        "需求替代性": breakdown.demand_substitutability,
        "切片匹配度": breakdown.context_match,
        "决策阶段影响": breakdown.decision_stage_impact,
        "证据支撑": breakdown.evidence_confidence,
        "市场信号": breakdown.market_signal_strength,
    }
    return max(dimensions.items(), key=lambda item: item[1])[0]


def _decision_stage_text(edge: CompetitionEdge) -> str:
    labels = {
        DecisionStage.INFORMATION_REACH: "信息触达",
        DecisionStage.INTEREST_FORMATION: "兴趣形成",
        DecisionStage.CAPABILITY_UNDERSTANDING: "能力理解",
        DecisionStage.TRUST_BUILDING: "信任建立",
        DecisionStage.DECISION_COMPLETION: "决策完成",
    }
    return "、".join(labels[stage] for stage in edge.decision_stages)


def _action_suggestion(competitor: Product, threat_level: ThreatLevel) -> str:
    if threat_level in {ThreatLevel.HIGH, ThreatLevel.HIGH_SCORE_NEEDS_REVIEW}:
        return f"优先拆解{competitor.name} 的卖点、价格和证据表达，形成对比回应。"
    if threat_level == ThreatLevel.MEDIUM:
        return f"将{competitor.name} 纳入本轮详情页和价格策略对照。"
    return f"保留{competitor.name} 作为弱关系观察对象，后续补证后再判断。"


def _threat_label(threat_level: ThreatLevel) -> str:
    labels = {
        ThreatLevel.HIGH: "高威胁",
        ThreatLevel.MEDIUM: "中威胁",
        ThreatLevel.LOW: "低威胁",
        ThreatLevel.HIGH_SCORE_NEEDS_REVIEW: "高分需复核",
    }
    return labels[threat_level]


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


def _battlefield_artifact_id(
    task_id: str,
    selected_slice: BattlefieldSliceSelection,
    *,
    include_all_relations: bool = False,
) -> str:
    parts = [
        selected_slice.price_band or "all_price_bands",
        selected_slice.persona or "all_personas",
        selected_slice.scenario or "all_scenarios",
        "all_relations" if include_all_relations else "default_relations",
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
