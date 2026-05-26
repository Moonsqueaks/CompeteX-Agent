from collections.abc import Iterable, Sequence
from datetime import UTC, datetime

from app.graph import (
    TaskGraphState,
    append_claim,
    append_competition_edge,
    append_feature_tree,
    append_pricing_model,
    append_run_log,
    append_user_persona,
)
from app.schemas import (
    AgentMessageStatus,
    AgentMessageType,
    AgentName,
    AgentRunLog,
    Claim,
    ClaimStatus,
    CompetitionEdge,
    CompetitionSlice,
    CompetitionType,
    DecisionStage,
    Evidence,
    FeatureTree,
    PricingModel,
    Product,
    ProductRole,
    ReviewInsight,
    RiskFlag,
    RunStatus,
    UserPersona,
)
from app.schemas.common import JsonObject
from app.services import calculate_competition_edge_score

AUTO_CLEANING_TERMS = ("自动", "免铲", "铲屎", "self-clean", "automatic")
ODOR_TERMS = ("除臭", "控臭", "吸臭", "藏味", "odor", "deodor")
SAFETY_TERMS = ("防外溅", "防带砂", "防粘", "安全", "感应", "safe", "sensor")
SMART_TERMS = ("智能", "电动", "可视", "新风", "app", "smart", "sensor")
SIZE_TERMS = ("多猫", "大空间", "超大", "大号", "大体型", "multi cat", "large")
LOW_BUDGET_TERMS = ("低预算", "低价", "入门", "0-100", "0-500", "low budget", "entry")
ALTERNATIVE_TYPE_TERMS = ("semi_enclosed", "litter_box", "cat_litter", "deodorizer", "toilet")
CONTENT_COOCCURRENCE_TERMS = (
    AUTO_CLEANING_TERMS + ODOR_TERMS + SAFETY_TERMS + SMART_TERMS + SIZE_TERMS
)


def analysis_agent_node(
    state: TaskGraphState,
    *,
    now: datetime | None = None,
) -> TaskGraphState:
    run_started_at = now or datetime.now(UTC)
    task_id = str(state["task"]["task_id"])
    products = [Product.model_validate(item) for item in state["products"]]
    evidences = [Evidence.model_validate(item) for item in state["evidences"]]
    review_insights = [ReviewInsight.model_validate(item) for item in state["review_insights"]]
    revision_messages = _pending_analysis_revision_messages(state)
    run_id = _next_analysis_run_id(
        state,
        task_id,
        is_revision=bool(revision_messages and state["claims"]),
    )

    try:
        if revision_messages and state["claims"]:
            return _recompute_analysis_from_revision_requests(
                state=state,
                task_id=task_id,
                run_id=run_id,
                products=products,
                evidences=evidences,
                review_insights=review_insights,
                revision_messages=revision_messages,
                started_at=run_started_at,
                now=now,
            )

        target_product = _find_target_product(products)
        target_evidences = _evidences_for_product(target_product, evidences)
        target_text = _product_text(target_product, target_evidences, review_insights)

        append_feature_tree(
            state,
            _build_feature_tree(task_id, target_product, target_evidences, target_text),
        )
        append_pricing_model(
            state,
            _build_pricing_model(task_id, target_product, target_evidences),
        )
        append_user_persona(
            state,
            _build_user_persona(
                task_id,
                target_product,
                target_evidences,
                target_text,
                review_insights,
            ),
        )

        recalled_competitors = _recall_competitors(target_product, products, evidences)
        edge_explanations: dict[str, JsonObject] = {}
        recall_reasons: dict[str, list[str]] = {}

        for index, recalled in enumerate(recalled_competitors, start=1):
            competitor = recalled.product
            competitor_evidences = _evidences_for_product(competitor, evidences)
            competition_slice = _competition_slice_for(competitor, competitor_evidences)
            score = calculate_competition_edge_score(
                target_product=target_product,
                competitor_product=competitor,
                competition_slice=competition_slice,
                evidences=evidences,
                review_insights=review_insights,
            )
            competition_type = _competition_type_for(competitor, recalled.reasons)
            edge_id = f"edge_{target_product.product_id}_{competitor.product_id}_{index}"
            claim = _build_competition_claim(
                task_id=task_id,
                edge_id=edge_id,
                target_product=target_product,
                target_evidences=target_evidences,
                competitor=competitor,
                competitor_evidences=competitor_evidences,
                competition_type=competition_type,
                competition_slice=competition_slice,
                confidence=score.edge_score,
                created_at=run_started_at,
            )
            append_claim(state, claim)

            edge_risk_flags = _edge_risk_flags(score.score_breakdown.evidence_confidence)
            if not competitor_evidences:
                edge_risk_flags.append(RiskFlag.MISSING_EVIDENCE)

            append_competition_edge(
                state,
                CompetitionEdge(
                    edge_id=edge_id,
                    task_id=task_id,
                    target_product_id=target_product.product_id,
                    competitor_product_id=competitor.product_id,
                    competition_type=competition_type,
                    slice=competition_slice,
                    decision_stages=_decision_stages_for(score.score_breakdown),
                    edge_score=score.edge_score,
                    score_breakdown=score.score_breakdown,
                    claim_ids=[claim.claim_id],
                    risk_flags=_dedupe(edge_risk_flags),
                    created_at=run_started_at,
                ),
            )
            edge_explanations[edge_id] = {
                name: explanation.model_dump(mode="json")
                for name, explanation in score.explanations.items()
            }
            recall_reasons[competitor.product_id] = recalled.reasons

        _record_success_run(
            state=state,
            task_id=task_id,
            run_id=run_id,
            started_at=run_started_at,
            edge_count=len(recalled_competitors),
        )
        state["metadata"]["analysis_agent"] = {
            "target_product_id": target_product.product_id,
            "feature_tree_count": 1,
            "pricing_model_count": 1,
            "user_persona_count": 1,
            "claim_count": len(recalled_competitors),
            "competition_edge_count": len(recalled_competitors),
            "recall_reasons": recall_reasons,
            "edge_explanations": edge_explanations,
        }
        return state
    except Exception as exc:
        append_run_log(
            state,
            AgentRunLog(
                run_id=run_id,
                task_id=task_id,
                agent_name=AgentName.ANALYSIS,
                status=RunStatus.FAILED,
                started_at=run_started_at,
                ended_at=run_started_at,
                input_summary=(
                    f"Analyze {len(products)} products and {len(evidences)} evidence records."
                ),
                output_summary=None,
                error_message=str(exc),
            ),
        )
        raise


class RecalledCompetitor:
    def __init__(self, product: Product, reasons: list[str]) -> None:
        self.product = product
        self.reasons = reasons


def _recompute_analysis_from_revision_requests(
    *,
    state: TaskGraphState,
    task_id: str,
    run_id: str,
    products: Sequence[Product],
    evidences: Sequence[Evidence],
    review_insights: Sequence[ReviewInsight],
    revision_messages: list[JsonObject],
    started_at: datetime,
    now: datetime | None,
) -> TaskGraphState:
    target_product = _find_target_product(products)
    target_evidences = _evidences_for_product(target_product, evidences)
    products_by_id = {product.product_id: product for product in products}
    claims = [Claim.model_validate(item) for item in state["claims"]]
    edges = [CompetitionEdge.model_validate(item) for item in state["competition_edges"]]
    claims_by_id = {claim.claim_id: claim for claim in claims}
    edges_by_id = {edge.edge_id: edge for edge in edges}
    target_claim_ids = _revision_target_claim_ids(revision_messages)
    target_edge_ids = _revision_target_edge_ids(revision_messages)

    for edge in edges:
        if set(edge.claim_ids).intersection(target_claim_ids):
            target_edge_ids.append(edge.edge_id)

    target_claim_ids = _dedupe(target_claim_ids)
    target_edge_ids = _dedupe(target_edge_ids)
    edge_explanations = _existing_edge_explanations(state)
    claim_diffs: list[JsonObject] = []
    edge_diffs: list[JsonObject] = []
    recomputed_claim_ids: list[str] = []
    recomputed_edge_ids: list[str] = []

    for edge_id in target_edge_ids:
        edge = edges_by_id.get(edge_id)
        if edge is None:
            continue
        competitor = products_by_id.get(edge.competitor_product_id)
        if competitor is None:
            continue

        competitor_evidences = _evidences_for_product(competitor, evidences)
        score = calculate_competition_edge_score(
            target_product=target_product,
            competitor_product=competitor,
            competition_slice=edge.slice,
            evidences=evidences,
            review_insights=review_insights,
        )
        claim_id = edge.claim_ids[0] if edge.claim_ids else f"claim_{edge.edge_id}"
        old_claim = claims_by_id.get(claim_id)
        new_claim = _build_competition_claim(
            task_id=task_id,
            edge_id=edge.edge_id,
            claim_id=claim_id,
            target_product=target_product,
            target_evidences=target_evidences,
            competitor=competitor,
            competitor_evidences=competitor_evidences,
            competition_type=edge.competition_type,
            competition_slice=edge.slice,
            confidence=score.edge_score,
            created_at=started_at,
        )
        new_edge = _recomputed_edge(
            task_id=task_id,
            edge=edge,
            score=score,
            claim_id=new_claim.claim_id,
            created_at=started_at,
            competitor_has_evidence=bool(competitor_evidences),
        )

        _replace_claim(state, new_claim)
        _replace_competition_edge(state, new_edge)
        claims_by_id[new_claim.claim_id] = new_claim
        edges_by_id[new_edge.edge_id] = new_edge
        recomputed_claim_ids.append(new_claim.claim_id)
        recomputed_edge_ids.append(new_edge.edge_id)
        edge_explanations[new_edge.edge_id] = {
            name: explanation.model_dump(mode="json")
            for name, explanation in score.explanations.items()
        }
        if old_claim is not None:
            claim_diffs.append(
                {
                    "claim_id": new_claim.claim_id,
                    "before": _claim_diff_snapshot(old_claim),
                    "after": _claim_diff_snapshot(new_claim),
                }
            )
        edge_diffs.append(
            {
                "edge_id": new_edge.edge_id,
                "before": _edge_diff_snapshot(edge),
                "after": _edge_diff_snapshot(new_edge),
            }
        )

    claim_only_ids = [
        claim_id
        for claim_id in target_claim_ids
        if claim_id not in recomputed_claim_ids and claim_id in claims_by_id
    ]
    for claim_id in claim_only_ids:
        old_claim = claims_by_id[claim_id]
        new_claim = _recomputed_claim_without_edge(
            old_claim,
            evidences=evidences,
            created_at=started_at,
        )
        _replace_claim(state, new_claim)
        claims_by_id[new_claim.claim_id] = new_claim
        recomputed_claim_ids.append(new_claim.claim_id)
        claim_diffs.append(
            {
                "claim_id": new_claim.claim_id,
                "before": _claim_diff_snapshot(old_claim),
                "after": _claim_diff_snapshot(new_claim),
            }
        )

    _mark_analysis_revision_messages_processed(
        revision_messages=revision_messages,
        run_id=run_id,
        recomputed_claim_ids=recomputed_claim_ids,
        recomputed_edge_ids=recomputed_edge_ids,
    )

    ended_at = now or datetime.now(UTC)
    unaffected_edge_ids = [
        edge["edge_id"]
        for edge in state["competition_edges"]
        if edge["edge_id"] not in recomputed_edge_ids
    ]
    recompute_summary: JsonObject = {
        "run_id": run_id,
        "status": "succeeded",
        "operation": "qa_analysis_recompute",
        "revision_message_ids": [
            message["message_id"] for message in revision_messages
        ],
        "target_claim_ids": target_claim_ids,
        "target_edge_ids": target_edge_ids,
        "recomputed_claim_ids": _dedupe(recomputed_claim_ids),
        "recomputed_edge_ids": _dedupe(recomputed_edge_ids),
        "unaffected_edge_ids": unaffected_edge_ids,
        "diffs": edge_diffs,
        "claim_diffs": claim_diffs,
    }
    analysis_metadata = state["metadata"].get("analysis_agent", {})
    if not isinstance(analysis_metadata, dict):
        analysis_metadata = {}
    recompute_runs = list(analysis_metadata.get("recompute_runs", []))
    recompute_runs.append(recompute_summary)
    state["metadata"]["analysis_agent"] = {
        **analysis_metadata,
        "status": "succeeded",
        "last_operation": "qa_analysis_recompute",
        "edge_explanations": edge_explanations,
        "recompute_runs": recompute_runs,
    }
    state["metadata"]["analysis_agent_recompute"] = recompute_summary

    append_run_log(
        state,
        AgentRunLog(
            run_id=run_id,
            task_id=task_id,
            agent_name=AgentName.ANALYSIS,
            status=RunStatus.SUCCEEDED,
            started_at=started_at,
            ended_at=ended_at,
            input_summary="Recompute targeted Analysis artifacts from QA revision messages.",
            output_summary=(
                f"Recomputed {len(recomputed_claim_ids)} claims and "
                f"{len(recomputed_edge_ids)} competition edges; "
                f"unaffected_edges={len(unaffected_edge_ids)}."
            ),
            error_message=None,
        ),
    )
    return state


def _find_target_product(products: Sequence[Product]) -> Product:
    for product in products:
        if product.role == ProductRole.TARGET:
            return product
    raise ValueError("Analysis Agent requires one target product in state.products.")


def _build_feature_tree(
    task_id: str,
    target_product: Product,
    evidences: Sequence[Evidence],
    target_text: str,
) -> FeatureTree:
    evidence_ids = [evidence.evidence_id for evidence in evidences]
    risk_flags = _missing_evidence_risk(evidence_ids)
    price_notes = _price_notes(evidences)
    return FeatureTree(
        feature_tree_id=f"ft_{target_product.product_id}",
        task_id=task_id,
        product_id=target_product.product_id,
        cleaning_capability=_extract_feature_items(target_text, AUTO_CLEANING_TERMS),
        odor_control=_extract_feature_items(target_text, ODOR_TERMS),
        safety_features=_extract_feature_items(target_text, SAFETY_TERMS),
        smart_features=_extract_feature_items(target_text, SMART_TERMS),
        maintenance_cost=price_notes or ["暂无可靠数据"],
        evidence_ids=evidence_ids,
        risk_flags=risk_flags,
    )


def _build_pricing_model(
    task_id: str,
    target_product: Product,
    evidences: Sequence[Evidence],
) -> PricingModel:
    evidence_ids = [evidence.evidence_id for evidence in evidences]
    price = _first_price(evidences)
    access_time = _first_access_time(evidences)
    risk_flags = _missing_evidence_risk(evidence_ids)
    if access_time is None:
        risk_flags.append(RiskFlag.MISSING_ACCESS_TIME)

    return PricingModel(
        pricing_model_id=f"pm_{target_product.product_id}",
        task_id=task_id,
        product_id=target_product.product_id,
        price_band=str(price.get("price_band") or _price_band_from_tags(target_product)),
        currency=str(price.get("currency") or "CNY"),
        list_price=_coerce_float(price.get("max_price_yuan")),
        final_price=_coerce_float(price.get("display_price_yuan") or price.get("min_price_yuan")),
        promotions=_compact_strings(str(price.get("price_note") or "")),
        bundle_description=str(price.get("price_note")) if price.get("price_note") else None,
        evidence_ids=evidence_ids,
        access_time=access_time,
        risk_flags=_dedupe(risk_flags),
    )


def _build_user_persona(
    task_id: str,
    target_product: Product,
    evidences: Sequence[Evidence],
    target_text: str,
    review_insights: Sequence[ReviewInsight],
) -> UserPersona:
    evidence_ids = _dedupe(
        [
            evidence.evidence_id
            for evidence in evidences
            if evidence.evidence_id in target_product.evidence_ids
            or evidence.product_id == target_product.product_id
        ]
    )
    personas = _persona_items(target_text)
    review_text = " ".join(
        insight.summary
        for insight in review_insights
        if insight.product_id == target_product.product_id
    ).lower()
    combined_text = f"{target_text} {review_text}"

    return UserPersona(
        persona_id=f"persona_{target_product.product_id}",
        task_id=task_id,
        product_id=target_product.product_id,
        personas=personas,
        pain_points=_extract_persona_items(
            combined_text,
            {
                "除臭/控臭敏感": ODOR_TERMS,
                "希望减少铲屎频次": AUTO_CLEANING_TERMS,
                "担心带砂外溅或清洁维护": SAFETY_TERMS,
            },
        ),
        scenarios=_extract_persona_items(
            combined_text,
            {
                "自动清理场景": AUTO_CLEANING_TERMS,
                "除臭控味场景": ODOR_TERMS,
                "智能可视/电动体验场景": SMART_TERMS,
            },
        ),
        decision_factors=_extract_persona_items(
            combined_text,
            {
                "自动清理能力": AUTO_CLEANING_TERMS,
                "价格带与套餐": ("价格", "价位", "到手价", "price", "CNY"),
                "智能/电动/可视能力": SMART_TERMS,
            },
        ),
        evidence_ids=evidence_ids,
        is_inference=True,
        risk_flags=_missing_evidence_risk(evidence_ids),
    )


def _recall_competitors(
    target_product: Product,
    products: Sequence[Product],
    evidences: Sequence[Evidence],
) -> list[RecalledCompetitor]:
    recalled = []
    target_terms = _term_hits(
        _product_text(target_product, _evidences_for_product(target_product, evidences), ()),
        CONTENT_COOCCURRENCE_TERMS,
    )

    for product in products:
        if product.product_id == target_product.product_id:
            continue

        reasons: list[str] = []
        product_type = _product_type(product, evidences)
        product_text = _product_text(product, _evidences_for_product(product, evidences), ())

        if product.role == ProductRole.DIRECT_COMPETITOR or product_type == _product_type(
            target_product,
            evidences,
        ):
            reasons.append("direct_competitor")
        if product.role in {ProductRole.ALTERNATIVE, ProductRole.CHANNEL_ALTERNATIVE} or any(
            term in product_type for term in ALTERNATIVE_TYPE_TERMS
        ):
            reasons.append("demand_alternative")
        if target_terms and set(target_terms).intersection(
            _term_hits(product_text, CONTENT_COOCCURRENCE_TERMS),
        ):
            reasons.append("content_cooccurrence")

        if reasons:
            recalled.append(RecalledCompetitor(product=product, reasons=_dedupe(reasons)))

    return recalled


def _build_competition_claim(
    *,
    task_id: str,
    edge_id: str,
    claim_id: str | None = None,
    target_product: Product,
    target_evidences: Sequence[Evidence],
    competitor: Product,
    competitor_evidences: Sequence[Evidence],
    competition_type: CompetitionType,
    competition_slice: CompetitionSlice,
    confidence: float,
    created_at: datetime,
) -> Claim:
    target_evidence_ids = _preferred_claim_evidence_ids(target_evidences)
    competitor_evidence_ids = _preferred_claim_evidence_ids(competitor_evidences)
    risk_flags: list[RiskFlag] = []
    status = ClaimStatus.ACCEPTED
    if not target_evidence_ids or not competitor_evidence_ids:
        risk_flags.append(RiskFlag.MISSING_EVIDENCE)
        status = ClaimStatus.NEEDS_REVIEW
    if confidence < 0.45:
        risk_flags.append(RiskFlag.UNRELIABLE_DATA)

    content = (
        f"基于本地快照规则评分，{competitor.name} 在 "
        f"{competition_slice.price_band}/{competition_slice.persona}/"
        f"{competition_slice.scenario} 切片下与 {target_product.name} "
        f"存在 {competition_type.value} 竞争关系；该判断为推断，评分 {confidence:.2f}。"
    )
    return Claim(
        claim_id=claim_id or f"claim_{edge_id}",
        task_id=task_id,
        claim_type="competition_edge",
        content=content,
        evidence_ids=_dedupe(target_evidence_ids + competitor_evidence_ids),
        confidence=confidence,
        is_inference=True,
        risk_flags=_dedupe(risk_flags),
        status=status,
        created_at=created_at,
    )


def _competition_slice_for(
    competitor: Product,
    competitor_evidences: Sequence[Evidence],
) -> CompetitionSlice:
    competitor_text = _product_text(competitor, competitor_evidences, ())
    price_band = _price_band(competitor, competitor_evidences)

    if competitor.role == ProductRole.DIRECT_COMPETITOR:
        persona = "多猫或大空间自动清理用户"
        scenario = "自动清理"
    elif any(term in competitor_text for term in ODOR_TERMS):
        persona = "低预算除臭敏感用户"
        scenario = "除臭控味"
    else:
        persona = "低预算基础如厕需求用户"
        scenario = "基础如厕替代"

    return CompetitionSlice(
        price_band=price_band,
        persona=persona,
        scenario=scenario,
    )


def _competition_type_for(product: Product, reasons: Sequence[str]) -> CompetitionType:
    if product.role == ProductRole.DIRECT_COMPETITOR:
        return CompetitionType.DIRECT
    if product.role == ProductRole.CHANNEL_ALTERNATIVE:
        return CompetitionType.CHANNEL
    if product.role == ProductRole.ALTERNATIVE or "demand_alternative" in reasons:
        return CompetitionType.ALTERNATIVE
    return CompetitionType.CONTENT_COOCCURRENCE


def _decision_stages_for(score_breakdown: object) -> list[DecisionStage]:
    stages = [
        DecisionStage.INFORMATION_REACH,
        DecisionStage.CAPABILITY_UNDERSTANDING,
    ]
    if score_breakdown.decision_stage_impact >= 0.55:
        stages.append(DecisionStage.TRUST_BUILDING)
    if score_breakdown.context_match >= 0.55:
        stages.append(DecisionStage.DECISION_COMPLETION)
    return _dedupe(stages)


def _edge_risk_flags(evidence_confidence: float) -> list[RiskFlag]:
    return [RiskFlag.UNRELIABLE_DATA] if evidence_confidence < 0.45 else []


def _recomputed_edge(
    *,
    task_id: str,
    edge: CompetitionEdge,
    score: object,
    claim_id: str,
    created_at: datetime,
    competitor_has_evidence: bool,
) -> CompetitionEdge:
    edge_risk_flags = _edge_risk_flags(score.score_breakdown.evidence_confidence)
    if not competitor_has_evidence:
        edge_risk_flags.append(RiskFlag.MISSING_EVIDENCE)
    return CompetitionEdge(
        edge_id=edge.edge_id,
        task_id=task_id,
        target_product_id=edge.target_product_id,
        competitor_product_id=edge.competitor_product_id,
        competition_type=edge.competition_type,
        slice=edge.slice,
        decision_stages=_decision_stages_for(score.score_breakdown),
        edge_score=score.edge_score,
        score_breakdown=score.score_breakdown,
        claim_ids=[claim_id],
        human_adjusted=edge.human_adjusted,
        risk_flags=_dedupe(edge_risk_flags),
        created_at=created_at,
    )


def _recomputed_claim_without_edge(
    claim: Claim,
    *,
    evidences: Sequence[Evidence],
    created_at: datetime,
) -> Claim:
    evidence_ids = [
        evidence_id
        for evidence_id in claim.evidence_ids
        if any(evidence.evidence_id == evidence_id for evidence in evidences)
    ]
    risk_flags = [
        risk_flag
        for risk_flag in claim.risk_flags
        if risk_flag
        not in {
            RiskFlag.CONFLICTING_ANALYSIS,
            RiskFlag.UNSUPPORTED_INFERENCE,
        }
    ]
    status = ClaimStatus.ACCEPTED
    if not evidence_ids:
        risk_flags.append(RiskFlag.MISSING_EVIDENCE)
        status = ClaimStatus.NEEDS_REVIEW
    return Claim(
        claim_id=claim.claim_id,
        task_id=claim.task_id,
        claim_type=claim.claim_type,
        content=claim.content,
        evidence_ids=evidence_ids,
        confidence=claim.confidence,
        is_inference=True if _claim_revision_should_mark_inference(claim) else claim.is_inference,
        risk_flags=_dedupe(risk_flags),
        status=status,
        created_at=created_at,
    )


def _record_success_run(
    *,
    state: TaskGraphState,
    task_id: str,
    run_id: str,
    started_at: datetime,
    edge_count: int,
) -> None:
    append_run_log(
        state,
        AgentRunLog(
            run_id=run_id,
            task_id=task_id,
            agent_name=AgentName.ANALYSIS,
            status=RunStatus.SUCCEEDED,
            started_at=started_at,
            ended_at=started_at,
            input_summary=(
                f"Analyze {len(state['products'])} products and {len(state['evidences'])} "
                "evidence records."
            ),
            output_summary=(
                "Generated target profile artifacts and "
                f"{edge_count} competition edges."
            ),
            error_message=None,
        ),
    )


def _next_analysis_run_id(
    state: TaskGraphState,
    task_id: str,
    *,
    is_revision: bool,
) -> str:
    analysis_run_count = sum(
        1 for run_log in state["run_logs"] if run_log.get("agent_name") == AgentName.ANALYSIS.value
    )
    if not is_revision and analysis_run_count == 0:
        return f"run_{task_id}_analysis"
    operation = "analysis_revision" if is_revision else "analysis"
    return f"run_{task_id}_{operation}_{analysis_run_count + 1:03d}"


def _pending_analysis_revision_messages(state: TaskGraphState) -> list[JsonObject]:
    return [
        message
        for message in state["agent_messages"]
        if message.get("from_agent") == AgentName.QA.value
        and message.get("to_agent") == AgentName.ANALYSIS.value
        and message.get("message_type") == AgentMessageType.REVISION_REQUEST.value
        and message.get("status") == AgentMessageStatus.REQUIRES_REVISION.value
    ]


def _revision_target_claim_ids(revision_messages: Sequence[JsonObject]) -> list[str]:
    claim_ids: list[str] = []
    for message in revision_messages:
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            continue
        for target in payload.get("targets", []):
            if not isinstance(target, dict):
                continue
            claim_ids.extend(_string_items(target.get("related_claim_ids")))
            if target.get("target_type") == "claim":
                target_id = target.get("target_id")
                if isinstance(target_id, str):
                    claim_ids.append(target_id)
        claim_ids.extend(_string_items(payload.get("claim_ids")))
    return _dedupe(claim_ids)


def _revision_target_edge_ids(revision_messages: Sequence[JsonObject]) -> list[str]:
    edge_ids: list[str] = []
    for message in revision_messages:
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            continue
        for target in payload.get("targets", []):
            if not isinstance(target, dict):
                continue
            if target.get("target_type") == "competition_edge":
                target_id = target.get("target_id")
                if isinstance(target_id, str):
                    edge_ids.append(target_id)
        edge_ids.extend(_string_items(payload.get("competition_edge_ids")))
    return _dedupe(edge_ids)


def _replace_claim(state: TaskGraphState, claim: Claim) -> None:
    _replace_state_artifact(
        state=state,
        field="claims",
        id_field="claim_id",
        artifact_id=claim.claim_id,
        artifact=claim,
    )


def _replace_competition_edge(state: TaskGraphState, edge: CompetitionEdge) -> None:
    _replace_state_artifact(
        state=state,
        field="competition_edges",
        id_field="edge_id",
        artifact_id=edge.edge_id,
        artifact=edge,
    )


def _replace_state_artifact(
    *,
    state: TaskGraphState,
    field: str,
    id_field: str,
    artifact_id: str,
    artifact: Claim | CompetitionEdge,
) -> None:
    artifact_payload = artifact.model_dump(mode="json")
    for index, item in enumerate(state[field]):
        if item.get(id_field) == artifact_id:
            state[field][index] = artifact_payload
            return
    state[field].append(artifact_payload)


def _mark_analysis_revision_messages_processed(
    *,
    revision_messages: Sequence[JsonObject],
    run_id: str,
    recomputed_claim_ids: Sequence[str],
    recomputed_edge_ids: Sequence[str],
) -> None:
    for message in revision_messages:
        message["status"] = AgentMessageStatus.PROCESSED.value
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        payload["analysis_recompute"] = {
            "status": "processed",
            "run_id": run_id,
            "recomputed_claim_ids": _dedupe(recomputed_claim_ids),
            "recomputed_edge_ids": _dedupe(recomputed_edge_ids),
        }
        message["payload"] = payload


def _existing_edge_explanations(state: TaskGraphState) -> dict[str, JsonObject]:
    metadata = state["metadata"].get("analysis_agent", {})
    if not isinstance(metadata, dict):
        return {}
    explanations = metadata.get("edge_explanations", {})
    return dict(explanations) if isinstance(explanations, dict) else {}


def _claim_diff_snapshot(claim: Claim) -> JsonObject:
    return {
        "claim_id": claim.claim_id,
        "status": claim.status.value,
        "confidence": claim.confidence,
        "is_inference": claim.is_inference,
        "risk_flags": [risk_flag.value for risk_flag in claim.risk_flags],
        "evidence_ids": claim.evidence_ids,
    }


def _edge_diff_snapshot(edge: CompetitionEdge) -> JsonObject:
    return {
        "edge_id": edge.edge_id,
        "edge_score": edge.edge_score,
        "score_breakdown": edge.score_breakdown.model_dump(mode="json"),
        "risk_flags": [risk_flag.value for risk_flag in edge.risk_flags],
        "claim_ids": edge.claim_ids,
    }


def _claim_revision_should_mark_inference(claim: Claim) -> bool:
    return any(
        term in claim.content
        for term in ("推断", "判断", "规则评分", "竞争关系", "优势", "替代")
    )


def _evidences_for_product(product: Product, evidences: Sequence[Evidence]) -> list[Evidence]:
    return [
        evidence
        for evidence in evidences
        if evidence.product_id == product.product_id or evidence.evidence_id in product.evidence_ids
    ]


def _preferred_claim_evidence_ids(evidences: Sequence[Evidence]) -> list[str]:
    repaired_original_ids = {
        repaired_from
        for evidence in evidences
        if isinstance(
            repaired_from := evidence.metadata.get("repaired_from_evidence_id"),
            str,
        )
    }
    return [
        evidence.evidence_id
        for evidence in evidences
        if evidence.evidence_id not in repaired_original_ids
    ]


def _product_text(
    product: Product,
    evidences: Sequence[Evidence],
    review_insights: Sequence[ReviewInsight],
) -> str:
    parts = [product.name, product.brand or "", " ".join(product.tags)]
    parts.extend(evidence.content_summary for evidence in evidences)
    parts.extend(
        insight.summary
        for insight in review_insights
        if insight.product_id == product.product_id
    )
    return " ".join(part for part in parts if part).lower()


def _product_type(product: Product, evidences: Sequence[Evidence]) -> str:
    for evidence in _evidences_for_product(product, evidences):
        product_type = evidence.metadata.get("product_type")
        if isinstance(product_type, str) and product_type.strip():
            return product_type
    for tag in product.tags:
        if tag != product.role.value and "-" not in tag:
            return tag
    return ""


def _price_band(product: Product, evidences: Sequence[Evidence]) -> str:
    price = _first_price(evidences)
    price_band = price.get("price_band")
    if isinstance(price_band, str) and price_band.strip():
        return price_band
    return _price_band_from_tags(product)


def _price_band_from_tags(product: Product) -> str:
    for tag in product.tags:
        if "-" in tag:
            return tag
    return "暂无可靠数据"


def _first_price(evidences: Sequence[Evidence]) -> JsonObject:
    for evidence in evidences:
        price = evidence.metadata.get("price")
        if isinstance(price, dict):
            return price
    return {}


def _first_access_time(evidences: Sequence[Evidence]) -> datetime | None:
    for evidence in evidences:
        if evidence.access_time is not None:
            return evidence.access_time
    return None


def _price_notes(evidences: Sequence[Evidence]) -> list[str]:
    notes = []
    for evidence in evidences:
        price = evidence.metadata.get("price")
        if isinstance(price, dict) and isinstance(price.get("price_note"), str):
            notes.append(price["price_note"])
    return _dedupe(notes)


def _extract_feature_items(text: str, terms: Iterable[str]) -> list[str]:
    hits = _term_hits(text, terms)
    return hits or ["暂无可靠数据"]


def _persona_items(text: str) -> list[str]:
    personas = []
    if any(term in text for term in SIZE_TERMS):
        personas.append("多猫或大空间需求家庭")
    if any(term in text for term in ODOR_TERMS):
        personas.append("除臭控味敏感家庭")
    if any(term in text for term in SMART_TERMS + AUTO_CLEANING_TERMS):
        personas.append("希望减少铲屎负担的智能设备用户")
    return personas or ["自动猫砂盆潜在购买用户（推断）"]


def _extract_persona_items(text: str, mapping: dict[str, Sequence[str]]) -> list[str]:
    items = [label for label, terms in mapping.items() if any(term in text for term in terms)]
    return items or ["暂无可靠数据"]


def _term_hits(text: str, terms: Iterable[str]) -> list[str]:
    return sorted({term for term in terms if term.lower() in text})


def _coerce_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _compact_strings(*values: str) -> list[str]:
    return [value for value in values if value.strip()]


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _missing_evidence_risk(evidence_ids: Sequence[str]) -> list[RiskFlag]:
    return [] if evidence_ids else [RiskFlag.MISSING_EVIDENCE]


def _dedupe[T](items: Iterable[T]) -> list[T]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped
