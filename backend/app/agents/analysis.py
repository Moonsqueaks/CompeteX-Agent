from collections.abc import Iterable, Sequence
from datetime import UTC, datetime

from app.graph import (
    TaskGraphState,
    append_claim,
    append_competition_edge,
    append_competitor_battlecard,
    append_feature_tree,
    append_gap_matrix_item,
    append_opportunity_item,
    append_pricing_model,
    append_review_signal_cluster,
    append_run_log,
    append_strategy_brief,
    append_user_persona,
)
from app.schemas import (
    ActionPriority,
    AgentMessageStatus,
    AgentMessageType,
    AgentName,
    AgentRunLog,
    Claim,
    ClaimStatus,
    CompetitionEdge,
    CompetitionSlice,
    CompetitionType,
    CompetitorBattlecard,
    DecisionStage,
    Evidence,
    FeatureTree,
    GapMatrixItem,
    OpportunityItem,
    PricingModel,
    Product,
    ProductRole,
    ResponsibilityType,
    ReviewInsight,
    ReviewSignalCluster,
    RiskFlag,
    RunStatus,
    StrategyBrief,
    ThreatLevel,
    UserPersona,
)
from app.schemas.common import EvidenceSourceType, JsonObject
from app.services.scoring import calculate_competition_edge_score

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
AI_ASSISTANT_PRODUCT_TYPES = ("general_ai_assistant", "ai_assistant")
AI_CONVERSATION_TERMS = ("对话", "问答", "聊天", "提问", "chat", "conversation", "assistant")
AI_RESEARCH_TERMS = ("搜索", "研究", "深度研究", "长文档", "文档", "网页总结", "research", "search")
AI_CONTENT_TERMS = ("写作", "创作", "PPT", "生图", "视频", "翻译", "内容", "image", "slides")
AI_CODING_TERMS = ("编程", "代码", "推理", "开发者", "API", "code", "reasoning", "developer")
AI_MULTIMODAL_TERMS = ("多模态", "图像", "视频", "识图", "生图", "multimodal", "image", "video")
AI_AGENT_TERMS = ("Agent", "智能体", "工作流", "办公", "协作", "workflow", "office", "claw")
AI_ECOSYSTEM_TERMS = ("生态", "入口", "下载", "App", "开放平台", "小程序", "web", "desktop")
AI_PRIVACY_TRUST_TERMS = ("隐私", "安全", "企业", "登录", "协议", "法务", "privacy", "security")
AI_CAPABILITY_TERMS = (
    AI_CONVERSATION_TERMS
    + AI_RESEARCH_TERMS
    + AI_CONTENT_TERMS
    + AI_CODING_TERMS
    + AI_MULTIMODAL_TERMS
    + AI_AGENT_TERMS
    + AI_ECOSYSTEM_TERMS
)
AI_CONTENT_COOCCURRENCE_TERMS = AI_CAPABILITY_TERMS + AI_PRIVACY_TRUST_TERMS
NO_RELIABLE_DATA = "暂无可靠数据"

AI_FEATURE_MODULE_LABELS = {
    "conversation": "对话问答",
    "search_or_research": "搜索与深度研究",
    "document_processing": "文档处理",
    "content_creation": "内容创作",
    "coding_or_reasoning": "编程与推理",
    "multimodal": "多模态能力",
    "agent_or_workflow": "智能体/工作流",
    "ecosystem_integration": "生态与分发入口",
}


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
        generated_claims: list[Claim] = []
        generated_edges: list[CompetitionEdge] = []

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
            generated_claims.append(claim)

            edge_risk_flags = _edge_risk_flags(score.score_breakdown.evidence_confidence)
            if not competitor_evidences:
                edge_risk_flags.append(RiskFlag.MISSING_EVIDENCE)

            competition_edge = CompetitionEdge(
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
            )
            append_competition_edge(state, competition_edge)
            generated_edges.append(competition_edge)
            edge_explanations[edge_id] = {
                name: explanation.model_dump(mode="json")
                for name, explanation in score.explanations.items()
            }
            recall_reasons[competitor.product_id] = recalled.reasons

        strategy_brief = _build_strategy_brief(
            task_id=task_id,
            target_product=target_product,
            edges=generated_edges,
            claims=generated_claims,
            created_at=run_started_at,
        )
        append_strategy_brief(state, strategy_brief)
        battlecards = _build_competitor_battlecards(
            task_id=task_id,
            target_product=target_product,
            products=products,
            edges=generated_edges,
            claims=generated_claims,
            evidences=evidences,
            created_at=run_started_at,
        )
        for battlecard in battlecards:
            append_competitor_battlecard(state, battlecard)
        gap_items = _build_gap_matrix_items(
            task_id=task_id,
            target_product=target_product,
            edges=generated_edges,
            battlecards=battlecards,
            claims=generated_claims,
            created_at=run_started_at,
        )
        for gap_item in gap_items:
            append_gap_matrix_item(state, gap_item)
        review_signal_clusters = _build_review_signal_clusters(
            task_id=task_id,
            target_product=target_product,
            products=products,
            evidences=evidences,
            review_insights=review_insights,
            research_text=state["task"].get("research_text"),
            created_at=run_started_at,
        )
        opportunity_items = _build_opportunity_items(
            task_id=task_id,
            target_product=target_product,
            strategy_brief=strategy_brief,
            battlecards=battlecards,
            gap_items=gap_items,
            edges=generated_edges,
            review_signal_clusters=review_signal_clusters,
            created_at=run_started_at,
        )
        for opportunity_item in opportunity_items:
            append_opportunity_item(state, opportunity_item)
        for signal_cluster in review_signal_clusters:
            append_review_signal_cluster(state, signal_cluster)

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
            "strategy_brief_count": 1,
            "competitor_battlecard_count": len(battlecards),
            "gap_matrix_item_count": len(gap_items),
            "opportunity_item_count": len(opportunity_items),
            "review_signal_cluster_count": len(review_signal_clusters),
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
    refreshed_artifact_counts = _refresh_formal_analysis_artifacts(
        state=state,
        task_id=task_id,
        target_product=target_product,
        products=products,
        evidences=evidences,
        review_insights=review_insights,
        research_text=state["task"].get("research_text"),
        created_at=started_at,
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
        "refreshed_artifacts": refreshed_artifact_counts,
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
        **refreshed_artifact_counts,
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


def _refresh_formal_analysis_artifacts(
    *,
    state: TaskGraphState,
    task_id: str,
    target_product: Product,
    products: Sequence[Product],
    evidences: Sequence[Evidence],
    review_insights: Sequence[ReviewInsight],
    research_text: object,
    created_at: datetime,
) -> JsonObject:
    claims = [Claim.model_validate(item) for item in state["claims"]]
    edges = [CompetitionEdge.model_validate(item) for item in state["competition_edges"]]
    strategy_brief = _build_strategy_brief(
        task_id=task_id,
        target_product=target_product,
        edges=edges,
        claims=claims,
        created_at=created_at,
    )
    battlecards = _build_competitor_battlecards(
        task_id=task_id,
        target_product=target_product,
        products=products,
        edges=edges,
        claims=claims,
        evidences=evidences,
        created_at=created_at,
    )
    gap_items = _build_gap_matrix_items(
        task_id=task_id,
        target_product=target_product,
        edges=edges,
        battlecards=battlecards,
        claims=claims,
        created_at=created_at,
    )
    review_signal_clusters = _build_review_signal_clusters(
        task_id=task_id,
        target_product=target_product,
        products=products,
        evidences=evidences,
        review_insights=review_insights,
        research_text=research_text,
        created_at=created_at,
    )
    opportunity_items = _build_opportunity_items(
        task_id=task_id,
        target_product=target_product,
        strategy_brief=strategy_brief,
        battlecards=battlecards,
        gap_items=gap_items,
        edges=edges,
        review_signal_clusters=review_signal_clusters,
        created_at=created_at,
    )
    state["strategy_briefs"] = [strategy_brief.model_dump(mode="json")]
    state["competitor_battlecards"] = [
        battlecard.model_dump(mode="json") for battlecard in battlecards
    ]
    state["gap_matrix_items"] = [gap_item.model_dump(mode="json") for gap_item in gap_items]
    state["opportunity_items"] = [
        opportunity_item.model_dump(mode="json") for opportunity_item in opportunity_items
    ]
    state["review_signal_clusters"] = [
        signal_cluster.model_dump(mode="json")
        for signal_cluster in review_signal_clusters
    ]
    return {
        "strategy_brief_count": 1,
        "competitor_battlecard_count": len(battlecards),
        "gap_matrix_item_count": len(gap_items),
        "opportunity_item_count": len(opportunity_items),
        "review_signal_cluster_count": len(review_signal_clusters),
    }


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
    if _is_internet_ai_product(target_product, evidences):
        return FeatureTree(
            feature_tree_id=f"ft_{target_product.product_id}",
            task_id=task_id,
            product_id=target_product.product_id,
            cleaning_capability=_ai_feature_items(
                evidences,
                target_text,
                ("conversation",),
                AI_CONVERSATION_TERMS,
                "暂无可靠对话问答证据",
            ),
            odor_control=_ai_feature_items(
                evidences,
                target_text,
                ("search_or_research", "document_processing"),
                AI_RESEARCH_TERMS,
                "暂无可靠搜索/文档研究证据",
            ),
            safety_features=_ai_feature_items(
                evidences,
                target_text,
                ("multimodal", "agent_or_workflow", "ecosystem_integration"),
                AI_MULTIMODAL_TERMS + AI_AGENT_TERMS + AI_ECOSYSTEM_TERMS,
                "暂无可靠多模态/智能体/生态入口证据",
            ),
            smart_features=_ai_feature_items(
                evidences,
                target_text,
                ("content_creation", "coding_or_reasoning"),
                AI_CONTENT_TERMS + AI_CODING_TERMS,
                "暂无可靠内容创作/编程推理证据",
            ),
            maintenance_cost=price_notes or ["商业模式/付费层：暂无可靠数据"],
            evidence_ids=evidence_ids,
            risk_flags=risk_flags,
        )
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

    if _is_internet_ai_product(target_product, evidences):
        pricing_note = str(price.get("price_note") or "暂无可靠定价数据")
        return PricingModel(
            pricing_model_id=f"pm_{target_product.product_id}",
            task_id=task_id,
            product_id=target_product.product_id,
            price_band=_ai_business_model_band(price, target_product),
            currency=str(price.get("currency") or "CNY"),
            list_price=_coerce_float(price.get("max_price_yuan")),
            final_price=_coerce_float(
                price.get("display_price_yuan") or price.get("min_price_yuan")
            ),
            promotions=[pricing_note],
            bundle_description=pricing_note,
            evidence_ids=evidence_ids,
            access_time=access_time,
            risk_flags=_dedupe(risk_flags),
        )

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

    if _is_internet_ai_product(target_product, evidences):
        return UserPersona(
            persona_id=f"persona_{target_product.product_id}",
            task_id=task_id,
            product_id=target_product.product_id,
            personas=_ai_persona_items(target_product, combined_text),
            pain_points=_extract_persona_items(
                combined_text,
                {
                    "长文档/深度研究效率": AI_RESEARCH_TERMS,
                    "内容创作与多格式输出": AI_CONTENT_TERMS,
                    "开发者编程与推理": AI_CODING_TERMS,
                    "办公协作与智能体工作流": AI_AGENT_TERMS,
                },
            ),
            scenarios=_ai_scenario_items(target_product, combined_text),
            decision_factors=_extract_persona_items(
                combined_text,
                {
                    "核心能力覆盖": AI_CAPABILITY_TERMS,
                    "商业模式/付费层证据": ("定价", "价格", "付费", "会员", "订阅", "API"),
                    "平台入口与生态": AI_ECOSYSTEM_TERMS,
                    "隐私安全与企业能力": AI_PRIVACY_TRUST_TERMS,
                },
            ),
            evidence_ids=evidence_ids,
            is_inference=True,
            risk_flags=_missing_evidence_risk(evidence_ids),
        )

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
    is_ai_domain = _is_internet_ai_product(
        target_product,
        _evidences_for_product(target_product, evidences),
    )
    cooccurrence_terms = (
        AI_CONTENT_COOCCURRENCE_TERMS if is_ai_domain else CONTENT_COOCCURRENCE_TERMS
    )
    target_terms = _term_hits(
        _product_text(target_product, _evidences_for_product(target_product, evidences), ()),
        cooccurrence_terms,
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
        if is_ai_domain and _is_internet_ai_product(
            product,
            _evidences_for_product(product, evidences),
        ):
            reasons.append("same_ai_assistant_domain")
        if product.role in {ProductRole.ALTERNATIVE, ProductRole.CHANNEL_ALTERNATIVE} or any(
            term in product_type for term in ALTERNATIVE_TYPE_TERMS
        ):
            reasons.append("demand_alternative")
        if target_terms and set(target_terms).intersection(
            _term_hits(product_text, cooccurrence_terms),
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


def _build_strategy_brief(
    *,
    task_id: str,
    target_product: Product,
    edges: Sequence[CompetitionEdge],
    claims: Sequence[Claim],
    created_at: datetime,
) -> StrategyBrief:
    top_edge = _top_edge(edges)
    claim_ids = _dedupe(claim_id for edge in edges[:3] for claim_id in edge.claim_ids)
    claims_by_id = {claim.claim_id: claim for claim in claims}
    evidence_ids = _evidence_ids_for_claims(claim_ids, claims_by_id)
    risk_flags = _dedupe(
        [
            *[risk for edge in edges[:3] for risk in edge.risk_flags],
            *[
                risk
                for claim_id in claim_ids
                if claim_id in claims_by_id
                for risk in claims_by_id[claim_id].risk_flags
            ],
        ]
    )
    if not evidence_ids:
        risk_flags.append(RiskFlag.MISSING_EVIDENCE)

    if top_edge is None:
        business_question = f"{target_product.name} 当前应优先补齐哪些竞品证据？"
        target_segment = "暂无可靠数据"
        primary_axis = "暂无可靠数据"
        owner_view = "面向产品和运营的初步证据补齐视角"
        confidence = 0.3
    else:
        target_segment = (
            f"{top_edge.slice.price_band}/{top_edge.slice.persona}/"
            f"{top_edge.slice.scenario}"
        )
        primary_axis = _primary_axis_for_edge(top_edge)
        business_question = (
            f"{target_product.name} 在 {target_segment} 下如何回应最强竞争压力？"
        )
        owner_view = "面向产品、运营和内容表达的竞争应对视角"
        confidence = top_edge.edge_score
    analysis_scope = _analysis_scope_for_product(target_product)

    return StrategyBrief(
        strategy_brief_id=f"strategy_{task_id}",
        task_id=task_id,
        business_question=business_question,
        research_question=business_question,
        analysis_scope=analysis_scope,
        category_tensions=_category_tensions(target_product),
        competitor_selection_rationale=(
            "优先选择与目标产品在商业模式/付费层、人群、使用场景和核心能力诉求上重叠，"
            "且已有 Claim/Evidence 可追溯的 AI 助手竞品。"
            if _is_internet_ai_domain_product(target_product)
            else (
                "优先选择与目标产品在价格带、人群、使用场景、自动清理/除臭/维护成本诉求上重叠，"
                "且已有 Claim/Evidence 可追溯的直接竞品、替代方案和低价威胁对象。"
            )
        ),
        target_segment=target_segment,
        primary_competition_axis=primary_axis,
        decision_owner_view=owner_view,
        evidence_boundary=_evidence_boundary_for_product(
            target_product,
            evidence_ids,
            risk_flags,
        ),
        claim_ids=claim_ids,
        evidence_ids=evidence_ids,
        is_inference=True,
        confidence=confidence,
        risk_flags=_dedupe(risk_flags),
        created_at=created_at,
    )


def _build_competitor_battlecards(
    *,
    task_id: str,
    target_product: Product,
    products: Sequence[Product],
    edges: Sequence[CompetitionEdge],
    claims: Sequence[Claim],
    evidences: Sequence[Evidence],
    created_at: datetime,
) -> list[CompetitorBattlecard]:
    products_by_id = {product.product_id: product for product in products}
    claims_by_id = {claim.claim_id: claim for claim in claims}
    sorted_edges = sorted(edges, key=lambda edge: edge.edge_score, reverse=True)
    battlecards: list[CompetitorBattlecard] = []
    seen_competitors: set[str] = set()

    for edge in sorted_edges:
        if edge.competitor_product_id in seen_competitors:
            continue
        competitor = products_by_id.get(edge.competitor_product_id)
        if competitor is None:
            continue
        claim_ids = [claim_id for claim_id in edge.claim_ids if claim_id in claims_by_id]
        evidence_ids = _evidence_ids_for_claims(claim_ids, claims_by_id)
        competitor_evidences = _evidences_for_product(competitor, evidences)
        risk_flags = _dedupe(
            [
                *edge.risk_flags,
                *[
                    risk
                    for claim_id in claim_ids
                    for risk in claims_by_id[claim_id].risk_flags
                ],
            ]
        )
        if not evidence_ids:
            risk_flags.append(RiskFlag.MISSING_EVIDENCE)
        priority = _battlecard_priority(edge)
        evidence_status = _evidence_status(
            evidence_ids=evidence_ids,
            risk_flags=risk_flags,
            confidence=edge.score_breakdown.evidence_confidence,
        )
        battlecards.append(
            CompetitorBattlecard(
                battlecard_id=f"battlecard_{edge.edge_id}",
                task_id=task_id,
                competitor_id=competitor.product_id,
                competitor_name=competitor.name,
                competitor_tier=_competitor_tier(edge),
                threat_level=_battlecard_threat_level(edge),
                target_slice=_edge_slice_label(edge),
                evidence_status=evidence_status,
                do_not_overclaim=_do_not_overclaim(
                    target_product,
                    evidence_status,
                    risk_flags,
                ),
                why_users_compare=_why_users_compare(
                    target_product=target_product,
                    competitor=competitor,
                    edge=edge,
                ),
                competitor_strengths=_competitor_strengths(
                    competitor=competitor,
                    edge=edge,
                    evidences=competitor_evidences,
                ),
                competitor_weaknesses=_competitor_weaknesses(
                    edge=edge,
                    evidence_ids=evidence_ids,
                ),
                target_response=_target_response_for_edge(edge, competitor),
                sales_objection=_sales_objection_for_edge(edge, competitor),
                response_talk_track=_response_talk_track_for_edge(edge, competitor),
                priority=priority,
                claim_ids=claim_ids,
                evidence_ids=evidence_ids,
                is_inference=True,
                confidence=edge.edge_score,
                risk_flags=_dedupe(risk_flags),
                created_at=created_at,
            )
        )
        seen_competitors.add(edge.competitor_product_id)
        if len(battlecards) >= 5:
            break
    return battlecards


def _build_gap_matrix_items(
    *,
    task_id: str,
    target_product: Product,
    edges: Sequence[CompetitionEdge],
    battlecards: Sequence[CompetitorBattlecard],
    claims: Sequence[Claim],
    created_at: datetime,
) -> list[GapMatrixItem]:
    top_edge = _top_edge(edges)
    if top_edge is None:
        return []
    claims_by_id = {claim.claim_id: claim for claim in claims}
    top_battlecard = battlecards[0] if battlecards else None
    base_claim_ids = list(top_edge.claim_ids)
    base_evidence_ids = _evidence_ids_for_claims(base_claim_ids, claims_by_id)
    base_risks = _dedupe(
        [
            *top_edge.risk_flags,
            *[
                risk
                for claim_id in base_claim_ids
                if claim_id in claims_by_id
                for risk in claims_by_id[claim_id].risk_flags
            ],
        ]
    )
    competitor_name = top_battlecard.competitor_name if top_battlecard else "核心竞品"
    if _is_internet_ai_domain_product(target_product):
        gap_specs = [
            (
                "capability_coverage",
                "能力覆盖差距",
                "feature",
                f"{target_product.name} 需要把对话、创作、研究、编程和多模态能力拆成可验证场景。",
                f"{competitor_name} 已进入同一 AI 助手候选集。",
                "如果能力场景表达不清，用户会把目标产品视为泛化同质助手。",
                "把已由官方公开页支持的能力模块写成场景化证据，缺证据处标记建议复核。",
                ResponsibilityType.PRODUCT_FEATURE,
            ),
            (
                "evidence_quality",
                "证据差距",
                "evidence",
                _evidence_boundary_for_product(
                    target_product,
                    base_evidence_ids,
                    base_risks,
                ),
                f"{competitor_name} 的竞争关系同样依赖现有 Claim/Evidence。",
                "证据不足会降低定价、API、应用商店、模型能力或用户规模判断的可采纳度。",
                "优先补齐官方定价页、应用商店页、访问时间或关键页面截图；不足处写暂无可靠数据。",
                ResponsibilityType.EVIDENCE_RESEARCH,
            ),
            (
                "message_expression",
                "表达差距",
                "message",
                "目标产品需要把能力名改写为用户任务收益。",
                f"{competitor_name} 会拦截同一类 AI 助手使用场景。",
                "表达不清会让用户转向场景解释更直接的助手。",
                "围绕长文档研究、内容创作、编程推理或办公协作重写对比话术。",
                ResponsibilityType.CONTENT_EXPRESSION,
            ),
            (
                "conversion_stage",
                "决策链差距",
                "conversion",
                f"当前竞争影响集中在{_stage_label(top_edge.decision_stages)}。",
                f"{competitor_name} 会在该阶段影响用户是否继续试用或迁移目标产品。",
                "如果这一阶段缺少证据或回应，用户可能转向已有生态或场景心智更强的竞品。",
                "把 Battlecard 的 target_response 转成官网、产品入口或运营内容的可执行动作。",
                ResponsibilityType.CONTENT_EXPRESSION,
            ),
            (
                "commercial_model",
                "商业模式/付费层差距",
                "pricing",
                "目标产品的免费、订阅、API 或企业版信息需要直接证据支持。",
                f"{competitor_name} 若有更清晰的付费层或开放平台说明，会影响试用和迁移判断。",
                "商业模式证据不足时，不能写免费优势、价格优势或 API 成本优势。",
                "补齐官方定价、会员、API 或企业页证据；补齐前维持暂无可靠数据。",
                ResponsibilityType.EVIDENCE_RESEARCH,
            ),
            (
                "privacy_and_enterprise",
                "隐私安全与企业能力差距",
                "trust",
                "隐私、安全、企业能力和登录后能力只能基于已有证据保守表达。",
                f"{competitor_name} 若在协议、企业能力或生态入口上更清晰，会影响信任建立。",
                "安全或企业能力表达过满会带来合规和复核风险。",
                "把已有隐私、安全、协议和企业入口证据分开展示，避免绝对化承诺。",
                ResponsibilityType.CONTENT_EXPRESSION,
            ),
        ]
    else:
        gap_specs = [
            (
                "function_capability",
                "功能能力差距",
                "feature",
                f"{target_product.name} 需要把自动清理、除臭和容量能力讲成连续使用收益。",
                f"{competitor_name} 已进入同一任务候选集。",
                "如果功能收益表达不清，用户会把目标产品视为同质替代。",
                "把省心清理、除臭可信和容量适配写成可验证的购买理由。",
                ResponsibilityType.PRODUCT_FEATURE,
            ),
            (
                "evidence_quality",
                "证据差距",
                "evidence",
                _evidence_boundary(base_evidence_ids, base_risks),
                f"{competitor_name} 的竞争关系同样依赖现有 Claim/Evidence。",
                "证据不足会降低价格、认证、安全或销量判断的可采纳度。",
                "优先补齐访问时间、截图、评论聚类或售后材料；不足处写建议复核。",
                ResponsibilityType.EVIDENCE_RESEARCH,
            ),
            (
                "message_expression",
                "表达差距",
                "message",
                "目标产品需要把卖点从功能名改写为用户收益。",
                f"{competitor_name} 会拦截同一类省心清理诉求。",
                "表达不清会让用户转向价格或场景解释更直接的方案。",
                "围绕用户异议重写对比话术，避免内部评分和字段口径进入正文。",
                ResponsibilityType.CONTENT_EXPRESSION,
            ),
            (
                "conversion_stage",
                "转化差距",
                "conversion",
                f"当前竞争影响集中在{_stage_label(top_edge.decision_stages)}。",
                f"{competitor_name} 会在该阶段影响用户是否继续比较目标产品。",
                "如果这一阶段缺少证据或回应，用户可能在下单前改变选择。",
                "把 Battlecard 的 target_response 转成页面、客服或投放可执行动作。",
                ResponsibilityType.CONTENT_EXPRESSION,
            ),
            (
                "maintenance_cost",
                "维护成本差距",
                "cost",
                "目标产品需要解释耗材、清洗、故障处理等长期使用成本边界。",
                f"{competitor_name} 可能通过低进入门槛或省心表达降低用户顾虑。",
                "维护成本不透明会削弱高价或智能功能的说服力。",
                "补齐耗材/清洗/售后说明；缺少证据时只写建议复核，不写长期成本确定结论。",
                ResponsibilityType.EVIDENCE_RESEARCH,
            ),
            (
                "trust_and_safety",
                "信任与安全表达差距",
                "trust",
                "宠物安全、电器安全和稳定性只能基于已有证据保守表达。",
                f"{competitor_name} 若在安全或售后信息上更清晰，会影响信任建立。",
                "安全或认证表达过满会带来合规和复核风险。",
                "把已有安全机制证据、售后边界和复核事项分开展示，避免绝对化承诺。",
                ResponsibilityType.CONTENT_EXPRESSION,
            ),
        ]
    return [
        GapMatrixItem(
            gap_id=f"gap_{task_id}_{index:02d}_{gap_key}",
            task_id=task_id,
            gap_type=gap_type,
            dimension=dimension,
            target_status=target_status,
            competitor_reference=competitor_reference,
            impact_on_decision=impact_on_decision,
            recommendation=recommendation,
            evidence_status=_evidence_status(
                evidence_ids=base_evidence_ids,
                risk_flags=base_risks,
                confidence=_gap_confidence(top_edge, base_evidence_ids),
            ),
            next_step_owner=next_step_owner,
            claim_ids=base_claim_ids,
            evidence_ids=base_evidence_ids,
            confidence=_gap_confidence(top_edge, base_evidence_ids),
            is_inference=True,
            risk_flags=_dedupe(base_risks),
            created_at=created_at,
        )
        for index, (
            gap_key,
            dimension,
            gap_type,
            target_status,
            competitor_reference,
            impact_on_decision,
            recommendation,
            next_step_owner,
        ) in enumerate(gap_specs, start=1)
    ]


def _build_opportunity_items(
    *,
    task_id: str,
    target_product: Product,
    strategy_brief: StrategyBrief,
    battlecards: Sequence[CompetitorBattlecard],
    gap_items: Sequence[GapMatrixItem],
    edges: Sequence[CompetitionEdge],
    review_signal_clusters: Sequence[ReviewSignalCluster],
    created_at: datetime,
) -> list[OpportunityItem]:
    top_edge = _top_edge(edges)
    top_battlecard = battlecards[0] if battlecards else None
    opportunity_specs = _opportunity_specs_for_target(target_product)
    opportunities: list[OpportunityItem] = []
    for index, (
        opportunity_type,
        title,
        action_type,
        owner,
        effort,
        expected_impact,
        acceptance_signal,
    ) in enumerate(
        opportunity_specs,
        start=1,
    ):
        linked_gaps = _linked_gap_ids_for_opportunity(opportunity_type, gap_items)
        linked_battlecards = [top_battlecard.battlecard_id] if top_battlecard is not None else []
        linked_evidence_ids = _dedupe(
            evidence_id
            for gap in gap_items
            if gap.gap_id in linked_gaps
            for evidence_id in gap.evidence_ids
        )
        priority_score = _opportunity_priority_score(
            top_edge=top_edge,
            linked_evidence_ids=linked_evidence_ids,
            effort_level=effort,
            expected_impact=0.8 if index == 1 else 0.65,
        )
        priority = _opportunity_priority(priority_score, linked_evidence_ids)
        risk_flags: list[RiskFlag] = []
        if not linked_evidence_ids:
            risk_flags.append(RiskFlag.MISSING_EVIDENCE)
        opportunities.append(
            OpportunityItem(
                opportunity_id=f"opp_{task_id}_{index:02d}_{opportunity_type}",
                task_id=task_id,
                title=title,
                opportunity_type=opportunity_type,
                action_type=action_type,
                target_segment=strategy_brief.target_segment,
                why_now=_opportunity_why_now(strategy_brief, top_battlecard),
                expected_impact=expected_impact,
                acceptance_signal=acceptance_signal,
                must_not_claim=_must_not_claim_for_opportunity(
                    target_product=target_product,
                    action_type=action_type,
                    linked_evidence_ids=linked_evidence_ids,
                ),
                effort_level=effort,
                priority_score=priority_score,
                priority=priority,
                confidence=min(strategy_brief.confidence, priority_score),
                owner=owner,
                linked_gaps=linked_gaps,
                linked_battlecards=linked_battlecards,
                linked_evidence_ids=linked_evidence_ids,
                evidence_boundary=_evidence_boundary_for_product(
                    target_product,
                    linked_evidence_ids,
                    risk_flags,
                ),
                is_inference=True,
                risk_flags=risk_flags,
                created_at=created_at,
            )
        )
    research_opportunity = _user_research_opportunity_item(
        task_id=task_id,
        target_product=target_product,
        strategy_brief=strategy_brief,
        battlecards=battlecards,
        gap_items=gap_items,
        review_signal_clusters=review_signal_clusters,
        created_at=created_at,
    )
    if research_opportunity is not None:
        opportunities.append(research_opportunity)
    return sorted(opportunities, key=lambda item: item.priority_score, reverse=True)


def _user_research_opportunity_item(
    *,
    task_id: str,
    target_product: Product,
    strategy_brief: StrategyBrief,
    battlecards: Sequence[CompetitorBattlecard],
    gap_items: Sequence[GapMatrixItem],
    review_signal_clusters: Sequence[ReviewSignalCluster],
    created_at: datetime,
) -> OpportunityItem | None:
    research_clusters = [
        cluster
        for cluster in review_signal_clusters
        if any("user_research" in evidence_id for evidence_id in cluster.evidence_ids)
    ]
    if not research_clusters:
        return None

    evidence_ids = _dedupe(
        evidence_id
        for cluster in research_clusters
        for evidence_id in cluster.evidence_ids
    )
    user_research_evidence_ids = [
        evidence_id for evidence_id in evidence_ids if "user_research" in evidence_id
    ]
    if not user_research_evidence_ids:
        return None

    signal_labels = _join_readable(
        _review_signal_label(cluster.signal_type) for cluster in research_clusters
    )
    stage_labels = _join_readable(
        _single_decision_stage_label(cluster.related_decision_stage.value)
        for cluster in research_clusters
    )
    risk_flags = _dedupe(
        risk_flag
        for cluster in research_clusters
        for risk_flag in cluster.risk_flags
    )
    priority_score = min(0.9, max(0.74, 0.62 + len(research_clusters) * 0.04))
    if _is_internet_ai_domain_product(target_product):
        title = "把用户任务痛点转成产品入口理由"
        expected_impact = (
            "让报告优先回答用户为什么会尝试、迁移或继续比较该 AI 助手，"
            "并把复杂任务、创作效率、隐私顾虑和付费判断分开说明。"
        )
    else:
        title = "把问卷痛点转成购买理由"
        expected_impact = (
            "让报告优先回答用户真正会问的问题，例如清理是否省心、除臭是否可信、"
            "长期维护是否麻烦、安全与售后是否足够放心。"
        )
    return OpportunityItem(
        opportunity_id=f"opp_{task_id}_00_user_research",
        task_id=task_id,
        title=title,
        opportunity_type="user_research",
        action_type="content",
        target_segment=strategy_brief.target_segment,
        why_now=(
            f"任务输入和评论信号集中指向{signal_labels or '用户真实顾虑'}，"
            f"主要影响{stage_labels or '购买决策'}。这些内容不会改写价格、销量、下载量、"
            "模型能力或竞品事实，但应改变报告和页面最先解释的问题。"
        ),
        expected_impact=expected_impact,
        acceptance_signal=(
            "报告正文能看到用户研究痛点对应的原因分析和行动建议，且相关判断绑定用户研究或评论证据。"
        ),
        must_not_claim=[
            "不得把单次问卷或任务输入当作全市场结论",
            "不得凭用户研究补写价格、销量、下载量、认证、安全或模型能力事实",
            "不得把用户顾虑写成已经被证明的产品缺陷",
        ],
        effort_level=0.3,
        priority_score=priority_score,
        priority=_opportunity_priority(priority_score, user_research_evidence_ids),
        confidence=min(strategy_brief.confidence, 0.68),
        owner=ResponsibilityType.CONTENT_EXPRESSION,
        linked_gaps=[gap.gap_id for gap in gap_items[:2]],
        linked_battlecards=[battlecard.battlecard_id for battlecard in battlecards[:2]],
        linked_evidence_ids=evidence_ids,
        evidence_boundary=_evidence_boundary(user_research_evidence_ids, risk_flags),
        is_inference=True,
        risk_flags=risk_flags,
        created_at=created_at,
    )


def _review_signal_label(signal_type: str) -> str:
    return {
        "pain": "痛点",
        "buying_reason": "购买理由",
        "objection": "下单异议",
        "trust_factor": "信任顾虑",
        "maintenance_cost": "维护成本",
        "safety_concern": "安全顾虑",
    }.get(signal_type, "用户信号")


def _single_decision_stage_label(stage: str) -> str:
    return {
        "information_reach": "信息触达",
        "interest_formation": "兴趣形成",
        "capability_understanding": "能力理解",
        "trust_building": "信任建立",
        "decision_completion": "决策完成",
    }.get(stage, "购买决策")


def _join_readable(values: Iterable[str]) -> str:
    unique_values = _dedupe(value for value in values if value)
    if len(unique_values) <= 2:
        return "和".join(unique_values)
    return "、".join(unique_values[:-1]) + f"和{unique_values[-1]}"


def _competition_slice_for(
    competitor: Product,
    competitor_evidences: Sequence[Evidence],
) -> CompetitionSlice:
    competitor_text = _product_text(competitor, competitor_evidences, ())
    price_band = _price_band(competitor, competitor_evidences)

    if _is_internet_ai_product(competitor, competitor_evidences):
        return CompetitionSlice(
            price_band=_ai_business_model_band(_first_price(competitor_evidences), competitor),
            persona=_ai_slice_persona(competitor, competitor_text),
            scenario=_ai_slice_scenario(competitor, competitor_text),
        )

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


def _top_edge(edges: Sequence[CompetitionEdge]) -> CompetitionEdge | None:
    if not edges:
        return None
    return max(edges, key=lambda edge: edge.edge_score)


def _primary_axis_for_edge(edge: CompetitionEdge) -> str:
    scenario = edge.slice.scenario
    if any(
        marker in scenario
        for marker in ("研究", "文档", "创作", "编程", "推理", "办公", "智能体", "多模态", "问答")
    ):
        if "研究" in scenario or "文档" in scenario:
            return "长文档研究与信息获取效率"
        if "编程" in scenario or "推理" in scenario:
            return "编程推理与开发者心智"
        if "办公" in scenario or "智能体" in scenario:
            return "办公协作与智能体工作流"
        if "创作" in scenario or "多模态" in scenario:
            return "内容创作与多模态输出"
        return "AI 助手核心任务覆盖"
    if "除臭" in scenario:
        return "除臭可信度与维护成本"
    if "自动" in scenario or "清理" in scenario:
        return "自动清理省心程度"
    if "基础" in scenario:
        return "价格接受度与基础替代"
    return "清理负担、价格和信任建立"


def _category_tensions(target_product: Product) -> list[str]:
    if _is_internet_ai_domain_product(target_product):
        return [
            "能力覆盖与证据边界：对话、搜索、文档、创作、编程和多模态能力必须回到官方公开页证据。",
            "免费体验与付费层：没有官方定价页或会员/API 证据时，只能写暂无可靠数据。",
            "场景心智与生态入口：AI 助手会在长文档研究、内容创作、"
            "编程推理和办公协作间形成不同比较关系。",
            "隐私安全与企业能力：协议、登录后能力和企业能力需要保守表达，不能凭印象补写。",
            "模型能力与市场规模：不得无证据补写排名、用户规模、模型能力高低或市场份额。",
        ]
    return [
        "便利性与维护成本：自动清理若带来更复杂清洗或耗材成本，需要在报告中分开说明。",
        "除臭能力与小户型环境：除臭卖点必须回到场景和证据，不能写成绝对效果。",
        "智能功能与可靠性：App、称重、提醒等功能要说明稳定性边界和复核证据。",
        "宠物安全与信任建立：安全机制只能保守引用已有证据，缺证据时写建议复核。",
        "价格带与转化阻力：高价产品需要更强的长期价值证据，低价方案会形成替代压力。",
    ]


def _analysis_scope_for_product(target_product: Product) -> str:
    if _is_internet_ai_domain_product(target_product):
        return (
            "本轮仅覆盖用户提供的本地 AI 助手公开页快照、官方页面 Evidence、"
            "QA 打回与人工修正记录；不代表实时下载量、用户规模、市场份额、"
            "模型能力排名或未核验定价。"
        )
    return (
        "本轮仅覆盖用户提供的本地脱敏 SKU 快照、评论摘要、研究文本、QA 打回与人工修正记录；"
        "不代表实时全网销量、市场份额、认证或排名。"
    )


def _evidence_boundary_for_product(
    target_product: Product,
    evidence_ids: Sequence[str],
    risk_flags: Sequence[RiskFlag],
) -> str:
    if _is_internet_ai_domain_product(target_product):
        if not evidence_ids:
            return "当前缺少可直接采纳证据，相关 AI 助手判断只能作为推断，建议复核。"
        if any(
            risk in risk_flags
            for risk in (RiskFlag.MISSING_ACCESS_TIME, RiskFlag.MISSING_SCREENSHOT)
        ):
            return (
                "当前有本地公开页快照证据，但定价、截图或访问时间等字段仍建议复核。"
            )
        if risk_flags:
            return "当前 AI 助手判断有证据支撑，但存在缺失或可靠性风险，正文需保守表达。"
        return "当前判断由本地 AI 助手公开页快照和结构化 Claim 支撑，可用于初步决策。"
    return _evidence_boundary(evidence_ids, risk_flags)


def _evidence_boundary(evidence_ids: Sequence[str], risk_flags: Sequence[RiskFlag]) -> str:
    if not evidence_ids:
        return "当前缺少可直接采纳证据，相关判断只能作为推断，建议复核。"
    if any(
        risk in risk_flags
        for risk in (RiskFlag.MISSING_ACCESS_TIME, RiskFlag.MISSING_SCREENSHOT)
    ):
        return "当前有本地脱敏快照证据，但价格、截图或访问时间等字段仍建议复核。"
    if risk_flags:
        return "当前判断有证据支撑，但存在缺失或可靠性风险，正文需保守表达。"
    return "当前判断由本地脱敏 SKU 快照和结构化 Claim 支撑，可用于初步决策。"


def _evidence_status(
    *,
    evidence_ids: Sequence[str],
    risk_flags: Sequence[RiskFlag],
    confidence: float,
) -> str:
    if not evidence_ids:
        return "missing"
    if risk_flags or confidence < 0.55:
        return "low"
    if confidence < 0.75:
        return "medium"
    return "high"


def _battlecard_priority(edge: CompetitionEdge) -> ActionPriority:
    if edge.edge_score >= 0.8:
        return ActionPriority.P0
    if edge.edge_score >= 0.6:
        return ActionPriority.P1
    return ActionPriority.P2


def _battlecard_threat_level(edge: CompetitionEdge) -> ThreatLevel:
    if edge.edge_score >= 0.8 and edge.risk_flags:
        return ThreatLevel.HIGH_SCORE_NEEDS_REVIEW
    if edge.edge_score >= 0.75:
        return ThreatLevel.HIGH
    if edge.edge_score >= 0.55:
        return ThreatLevel.MEDIUM
    return ThreatLevel.LOW


def _competitor_tier(edge: CompetitionEdge) -> str:
    if edge.competition_type == CompetitionType.DIRECT and edge.edge_score >= 0.65:
        return "direct_core"
    if edge.competition_type == CompetitionType.ALTERNATIVE:
        return "alternative_solution"
    if edge.competition_type == CompetitionType.CHANNEL:
        return "low_price_or_channel_threat"
    if edge.edge_score >= 0.75:
        return "high_threat_reference"
    return "watchlist"


def _edge_slice_label(edge: CompetitionEdge) -> str:
    return f"{edge.slice.price_band}/{edge.slice.persona}/{edge.slice.scenario}"


def _do_not_overclaim(
    target_product: Product,
    evidence_status: str,
    risk_flags: Sequence[RiskFlag],
) -> list[str]:
    if _is_internet_ai_domain_product(target_product):
        blocked_claims = [
            "不得写成实时下载量、全网排名、用户规模、市场份额或模型能力第一。",
            "不得补写未经证据核验的定价、会员/API、企业能力或隐私绝对安全承诺。",
        ]
        if evidence_status in {"missing", "low"} or risk_flags:
            blocked_claims.append(
                "不得把模型能力、付费边界、用户规模或隐私安全写成确定事实。"
            )
        return blocked_claims

    blocked_claims = [
        "不得写成实时销量、全网排名、市场份额或平台第一。",
        "不得补写未经证据核验的认证、尺寸、电器安全或宠物安全承诺。",
    ]
    if evidence_status in {"missing", "low"} or risk_flags:
        blocked_claims.append("不得把价格、除臭效果、长期维护成本或售后体验写成确定事实。")
    return blocked_claims


def _stage_label(stages: Sequence[DecisionStage]) -> str:
    if not stages:
        return "购买决策阶段"
    return "、".join(stage.value for stage in stages)


def _gap_confidence(edge: CompetitionEdge, evidence_ids: Sequence[str]) -> float:
    if not evidence_ids:
        return min(edge.edge_score, 0.45)
    return min(edge.edge_score, edge.score_breakdown.evidence_confidence)


def _linked_gap_ids_for_opportunity(
    opportunity_type: str,
    gap_items: Sequence[GapMatrixItem],
) -> list[str]:
    preferred_dimensions = {
        "content": {"表达差距", "转化差距", "决策链差距"},
        "evidence": {"证据差距", "商业模式/付费层差距"},
        "positioning": {"功能能力差距", "能力覆盖差距", "表达差距"},
    }
    dimensions = preferred_dimensions.get(opportunity_type, set())
    linked = [gap.gap_id for gap in gap_items if gap.dimension in dimensions]
    return linked or [gap.gap_id for gap in gap_items[:1]]


def _opportunity_priority_score(
    *,
    top_edge: CompetitionEdge | None,
    linked_evidence_ids: Sequence[str],
    effort_level: float,
    expected_impact: float,
) -> float:
    if top_edge is None:
        return 0.25
    evidence_confidence = (
        top_edge.score_breakdown.evidence_confidence if linked_evidence_ids else 0.0
    )
    score = (
        0.35 * top_edge.score_breakdown.decision_stage_impact
        + 0.25 * top_edge.edge_score
        + 0.20 * evidence_confidence
        + 0.10 * expected_impact
        - 0.10 * effort_level
    )
    return max(0.0, min(1.0, score))


def _opportunity_priority(
    priority_score: float,
    linked_evidence_ids: Sequence[str],
) -> ActionPriority:
    if not linked_evidence_ids:
        return ActionPriority.P2
    if priority_score >= 0.75:
        return ActionPriority.P0
    if priority_score >= 0.55:
        return ActionPriority.P1
    return ActionPriority.P2


def _must_not_claim_for_opportunity(
    *,
    target_product: Product,
    action_type: str,
    linked_evidence_ids: Sequence[str],
) -> list[str]:
    if _is_internet_ai_domain_product(target_product):
        common = [
            "不能声称用户规模、下载量、排名、市场份额或模型能力高低，除非后续补齐直接证据。",
            "不能声称免费优势、价格优势、API 成本优势或企业能力，除非有官方定价/协议/企业页证据。",
        ]
    else:
        common = [
            "不能声称销量、排名、市场份额、认证或尺寸事实，除非后续补齐直接证据。",
            "不能用绝对安全、完全除臭、长期零维护等不可证实表述。",
        ]
    if not linked_evidence_ids:
        common.append("当前缺少直接证据，不得把该机会写成已验证优势。")
    if action_type == "content":
        common.append("不能把页面话术写成贬低竞品或无法复核的效果承诺。")
    if action_type == "evidence":
        common.append("证据补齐前只能写建议复核，不能替代 QA 结论。")
    return common


def _opportunity_why_now(
    strategy_brief: StrategyBrief,
    top_battlecard: CompetitorBattlecard | None,
) -> str:
    competitor_phrase = (
        f"当前最大比较对象是 {top_battlecard.competitor_name}，"
        if top_battlecard is not None
        else ""
    )
    return (
        f"{competitor_phrase}{strategy_brief.business_question}"
        " 这类问题会直接影响用户是否继续把目标产品留在候选集中。"
    )


def _research_evidence_ids(evidences: Sequence[Evidence]) -> list[str]:
    return [
        evidence.evidence_id
        for evidence in evidences
        if evidence.source_type == EvidenceSourceType.USER_RESEARCH
        or evidence.metadata.get("source") == "task.research_text"
    ]


def _build_review_signal_clusters(
    *,
    task_id: str,
    target_product: Product,
    products: Sequence[Product],
    evidences: Sequence[Evidence],
    review_insights: Sequence[ReviewInsight],
    research_text: object,
    created_at: datetime,
) -> list[ReviewSignalCluster]:
    is_ai_domain = _is_internet_ai_domain_product(target_product)
    product_ids = {product.product_id for product in products}
    text_by_type: dict[str, list[str]] = {
        "pain": [],
        "buying_reason": [],
        "objection": [],
        "trust_factor": [],
        "maintenance_cost": [],
        "safety_concern": [],
    }
    evidence_by_type: dict[str, list[str]] = {key: [] for key in text_by_type}
    affected_by_type: dict[str, list[str]] = {key: [] for key in text_by_type}
    research_evidence_ids = _research_evidence_ids(evidences)

    evidence_by_id = {evidence.evidence_id: evidence for evidence in evidences}
    for insight in review_insights:
        source_text = " ".join(
            [
                insight.summary,
                jsonable_text(insight.market_signals),
                insight.limitations,
                *[
                    evidence_by_id[evidence_id].content_summary
                    for evidence_id in insight.evidence_ids
                    if evidence_id in evidence_by_id
                ],
            ]
        )
        signal_types = _signal_types_for_text(source_text, is_ai_domain=is_ai_domain)
        for signal_type in signal_types:
            text_by_type[signal_type].append(insight.summary)
            evidence_by_type[signal_type].extend(insight.evidence_ids)
            affected_by_type[signal_type].append(insight.product_id)

    if isinstance(research_text, str) and research_text.strip():
        research_signal_types = _signal_types_for_text(
            research_text,
            is_ai_domain=is_ai_domain,
        )
        for signal_type in research_signal_types:
            text_by_type[signal_type].append(research_text.strip()[:180])
            evidence_by_type[signal_type].extend(research_evidence_ids)
            affected_by_type[signal_type].extend(sorted(product_ids)[:3])

    clusters: list[ReviewSignalCluster] = []
    for signal_type in (
        "pain",
        "buying_reason",
        "objection",
        "trust_factor",
        "maintenance_cost",
        "safety_concern",
    ):
        snippets = _dedupe(text_by_type[signal_type])
        evidence_ids = _dedupe(evidence_by_type[signal_type])
        affected_products = _dedupe(affected_by_type[signal_type])
        if not snippets and signal_type not in {"pain", "buying_reason", "trust_factor"}:
            continue
        if not snippets:
            snippets = [
                _fallback_signal_summary(signal_type, is_ai_domain=is_ai_domain)
            ]
        risk_flags: list[RiskFlag] = []
        if not evidence_ids:
            risk_flags.append(RiskFlag.MISSING_EVIDENCE)
        clusters.append(
            ReviewSignalCluster(
                signal_cluster_id=f"signal_{task_id}_{len(clusters) + 1:02d}_{signal_type}",
                task_id=task_id,
                signal_type=signal_type,  # type: ignore[arg-type]
                signal_summary=_signal_summary(
                    signal_type,
                    snippets,
                    is_ai_domain=is_ai_domain,
                ),
                affected_products=affected_products,
                related_decision_stage=_decision_stage_for_signal(signal_type),
                evidence_ids=evidence_ids,
                action_hint=_action_hint_for_signal(
                    signal_type,
                    is_ai_domain=is_ai_domain,
                ),
                evidence_status=_evidence_status(
                    evidence_ids=evidence_ids,
                    risk_flags=risk_flags,
                    confidence=0.7 if evidence_ids else 0.2,
                ),
                is_inference=True,
                risk_flags=risk_flags,
                created_at=created_at,
            )
        )
    return clusters


def _signal_types_for_text(text: str, *, is_ai_domain: bool = False) -> list[str]:
    lowered = text.lower()
    signal_types: list[str] = []
    if is_ai_domain:
        if any(
            term.lower() in lowered
            for term in ("效率", "复杂", "信息", "任务", "研究", "创作", "代码", "文档")
        ):
            signal_types.append("pain")
        if any(
            term.lower() in lowered
            for term in (
                "对话",
                "问答",
                "搜索",
                "研究",
                "创作",
                "编程",
                "办公",
                "智能体",
            )
        ):
            signal_types.append("buying_reason")
        if any(
            term.lower() in lowered
            for term in (
                "担心",
                "顾虑",
                "付费",
                "会员",
                "api",
                "隐私",
                "稳定",
                "迁移",
            )
        ):
            signal_types.append("objection")
        if any(
            term.lower() in lowered
            for term in ("隐私", "安全", "企业", "协议", "访问时间", "截图", "可靠")
        ):
            signal_types.append("trust_factor")
        if any(
            term.lower() in lowered
            for term in ("定价", "价格", "付费", "会员", "订阅", "api", "企业版")
        ):
            signal_types.append("maintenance_cost")
        if any(
            term.lower() in lowered
            for term in ("隐私", "安全", "协议", "企业")
        ):
            signal_types.append("safety_concern")
        return _dedupe(signal_types) or ["pain", "buying_reason"]
    if any(term in lowered for term in ("麻烦", "负担", "痛点", "清理", "铲屎", "异味", "odor")):
        signal_types.append("pain")
    if any(term in lowered for term in ("省心", "自动", "免铲", "多猫", "大空间", "购买", "理由")):
        signal_types.append("buying_reason")
    if any(term in lowered for term in ("担心", "顾虑", "异议", "贵", "噪音", "故障", "卡", "堵")):
        signal_types.append("objection")
    if any(term in lowered for term in ("售后", "信任", "稳定", "可靠", "评价", "评论", "保障")):
        signal_types.append("trust_factor")
    if any(term in lowered for term in ("耗材", "清洗", "维护", "成本", "省钱", "长期")):
        signal_types.append("maintenance_cost")
    if any(term in lowered for term in ("安全", "防夹", "感应", "电器", "认证", "宠物")):
        signal_types.append("safety_concern")
    return _dedupe(signal_types) or ["pain", "buying_reason"]


def _signal_summary(
    signal_type: str,
    snippets: Sequence[str],
    *,
    is_ai_domain: bool = False,
) -> str:
    first = snippets[0] if snippets else _fallback_signal_summary(
        signal_type,
        is_ai_domain=is_ai_domain,
    )
    if is_ai_domain:
        prefix = {
            "pain": "用户任务痛点信号",
            "buying_reason": "使用理由信号",
            "objection": "试用与迁移顾虑信号",
            "trust_factor": "信任建立信号",
            "maintenance_cost": "商业模式与成本信号",
            "safety_concern": "隐私安全关注信号",
        }[signal_type]
    else:
        prefix = {
            "pain": "用户痛点信号",
            "buying_reason": "购买理由信号",
            "objection": "用户异议信号",
            "trust_factor": "信任建立信号",
            "maintenance_cost": "维护成本信号",
            "safety_concern": "安全关注信号",
        }[signal_type]
    return f"{prefix}：{first[:160]}"


def _fallback_signal_summary(signal_type: str, *, is_ai_domain: bool = False) -> str:
    if is_ai_domain:
        return {
            "pain": "现有公开页快照不足以独立聚类用户痛点，建议补充任务场景或用户研究证据。",
            "buying_reason": "任务完成、入口便利、能力覆盖和可信使用边界是可先验证的使用理由。",
            "trust_factor": "信任建立需要更多隐私说明、企业能力、访问时间和关键页面证据。",
        }.get(signal_type, "暂无可靠数据，建议补充证据后复核。")
    return {
        "pain": "现有快照不足以独立聚类评论痛点，建议补充评论摘要。",
        "buying_reason": "自动清理、除臭和省心维护是可先验证的购买理由。",
        "trust_factor": "信任建立需要更多售后、稳定性和安全机制证据。",
    }.get(signal_type, "暂无可靠数据，建议补充证据后复核。")


def _decision_stage_for_signal(signal_type: str) -> DecisionStage:
    return {
        "pain": DecisionStage.INFORMATION_REACH,
        "buying_reason": DecisionStage.INTEREST_FORMATION,
        "objection": DecisionStage.CAPABILITY_UNDERSTANDING,
        "trust_factor": DecisionStage.TRUST_BUILDING,
        "maintenance_cost": DecisionStage.DECISION_COMPLETION,
        "safety_concern": DecisionStage.TRUST_BUILDING,
    }[signal_type]


def _action_hint_for_signal(signal_type: str, *, is_ai_domain: bool = False) -> str:
    if is_ai_domain:
        return {
            "pain": "把信息获取、复杂内容处理和创作效率改写成首屏可读的用户任务痛点。",
            "buying_reason": "将对话问答、长文档研究、内容创作或编程推理转成可验证使用理由。",
            "objection": "补充定价/会员、API、平台入口、稳定性或隐私说明证据，回应试用和迁移顾虑。",
            "trust_factor": "把隐私说明、企业能力、访问时间和证据边界前置到信任建立环节。",
            "maintenance_cost": "补齐定价、会员、API 或企业页说明，避免只讲免费或低成本。",
            "safety_concern": "隐私和安全相关表述保持保守，未核验证据时只写建议复核。",
        }[signal_type]
    return {
        "pain": "把清理负担、异味和维护麻烦改写成页面首屏可读的用户痛点。",
        "buying_reason": "将自动清理、除臭可信和多猫适配转成可验证购买理由。",
        "objection": "补充价格、维护成本、稳定性或售后证据，回应用户下单前异议。",
        "trust_factor": "把售后、稳定性、安全机制和证据边界前置到信任建立环节。",
        "maintenance_cost": "补齐耗材、清洗频率和长期维护说明，避免只讲购买价。",
        "safety_concern": "安全相关表述保持保守，未核验证据时只写建议复核。",
    }[signal_type]


def jsonable_text(value: object) -> str:
    if isinstance(value, dict):
        return " ".join(str(item) for item in value.values() if item is not None)
    if isinstance(value, list):
        return " ".join(str(item) for item in value if item is not None)
    return str(value) if value is not None else ""


def _is_internet_ai_domain_product(product: Product) -> bool:
    domain_text = " ".join(
        [
            product.category,
            product.subcategory,
            product.product_url or "",
            " ".join(product.tags),
        ]
    ).lower()
    return any(marker in domain_text for marker in ("internet_ai_assistant", "ai 助手")) or any(
        product_type in domain_text for product_type in AI_ASSISTANT_PRODUCT_TYPES
    )


def _is_internet_ai_product(product: Product, evidences: Sequence[Evidence]) -> bool:
    if _is_internet_ai_domain_product(product):
        return True
    for evidence in evidences:
        product_type = evidence.metadata.get("product_type")
        if isinstance(product_type, str) and product_type in AI_ASSISTANT_PRODUCT_TYPES:
            return True
        if str(evidence.source_type) in {
            "official_product_page",
            "official_help_doc",
            "app_store_page",
            "official_release_note",
        } and any(
            marker in (evidence.source_url or "")
            for marker in (
                "doubao.com",
                "kimi.com",
                "deepseek.com",
                "qianwen.com",
                "yuanbao.tencent.com",
            )
        ):
            return True
    return False


def _ai_feature_items(
    evidences: Sequence[Evidence],
    text: str,
    module_keys: Sequence[str],
    terms: Sequence[str],
    fallback: str,
) -> list[str]:
    labels = []
    for evidence in evidences:
        feature_modules = evidence.metadata.get("feature_modules")
        if not isinstance(feature_modules, dict):
            continue
        for module_key in module_keys:
            module_values = feature_modules.get(module_key)
            if isinstance(module_values, list) and module_values:
                labels.append(AI_FEATURE_MODULE_LABELS.get(module_key, module_key))
    labels.extend(_term_hits(text, terms))
    return _dedupe(labels) or [fallback]


def _ai_business_model_band(price: JsonObject, product: Product) -> str:
    band = str(price.get("price_band") or "").strip()
    if band and band.lower() not in {"unknown", "none", "null"}:
        return band
    tag_text = " ".join(product.tags).lower()
    if any(term in tag_text for term in ("api", "开放平台")):
        return "API/开发者"
    if any(term in tag_text for term in ("企业", "enterprise")):
        return "企业版"
    if any(term in tag_text for term in ("订阅", "会员", "subscription", "paid")):
        return "订阅/会员"
    if any(term in tag_text for term in ("免费", "free")):
        return "免费/公开入口"
    return NO_RELIABLE_DATA


def _ai_persona_items(product: Product, text: str) -> list[str]:
    personas = [
        tag
        for tag in product.tags
        if tag in {"学生", "知识工作者", "内容创作者", "开发者", "企业团队"}
    ]
    if any(term.lower() in text for term in AI_RESEARCH_TERMS):
        personas.append("知识工作者")
    if any(term.lower() in text for term in AI_CONTENT_TERMS):
        personas.append("内容创作者")
    if any(term.lower() in text for term in AI_CODING_TERMS):
        personas.append("开发者")
    if any(term.lower() in text for term in AI_AGENT_TERMS):
        personas.append("企业团队")
    if not personas:
        personas.append("AI 助手潜在使用者（推断）")
    return _dedupe(personas)


def _ai_scenario_items(product: Product, text: str) -> list[str]:
    scenarios = [
        tag
        for tag in product.tags
        if tag in {"日常问答", "长文档研究", "内容创作", "办公协作", "编程推理", "多模态创作"}
    ]
    if any(term.lower() in text for term in AI_RESEARCH_TERMS):
        scenarios.append("长文档研究")
    if any(term.lower() in text for term in AI_CONTENT_TERMS):
        scenarios.append("内容创作")
    if any(term.lower() in text for term in AI_CODING_TERMS):
        scenarios.append("编程推理")
    if any(term.lower() in text for term in AI_AGENT_TERMS):
        scenarios.append("办公协作")
    if any(term.lower() in text for term in AI_MULTIMODAL_TERMS):
        scenarios.append("多模态创作")
    if any(term.lower() in text for term in AI_CONVERSATION_TERMS):
        scenarios.append("日常问答")
    return _dedupe(scenarios) or ["日常问答"]


def _ai_slice_persona(competitor: Product, text: str) -> str:
    personas = _ai_persona_items(competitor, text)
    preferred = ("知识工作者", "内容创作者", "开发者", "企业团队", "学生")
    for persona in preferred:
        if persona in personas:
            return persona
    return personas[0]


def _ai_slice_scenario(competitor: Product, text: str) -> str:
    scenarios = _ai_scenario_items(competitor, text)
    preferred = ("长文档研究", "编程推理", "办公协作", "内容创作", "多模态创作", "日常问答")
    for scenario in preferred:
        if scenario in scenarios:
            return scenario
    return scenarios[0]


def _opportunity_specs_for_target(
    target_product: Product,
) -> list[tuple[str, str, str, ResponsibilityType, float, str, str]]:
    if _is_internet_ai_domain_product(target_product):
        return [
            (
                "content",
                "重写 AI 助手场景化对比话术",
                "content",
                ResponsibilityType.CONTENT_EXPRESSION,
                0.35,
                "把最大威胁竞品的比较逻辑改成用户能读懂的任务场景回应。",
                "官网、产品入口或运营内容中能明确回答用户为什么比较该 AI 助手。",
            ),
            (
                "evidence",
                "补齐定价与关键页面证据",
                "evidence",
                ResponsibilityType.EVIDENCE_RESEARCH,
                0.55,
                "优先补齐影响采纳的官方定价/API/应用商店/截图/访问时间证据。",
                "关键结论能绑定官方公开页、访问时间或截图，并在报告中不再触发证据缺口。",
            ),
            (
                "positioning",
                "明确豆包主竞争场景",
                "positioning",
                ResponsibilityType.PRODUCT_FEATURE,
                0.45,
                "围绕内容创作、办公协作、编程推理或长文档研究建立更清楚的定位表达。",
                "报告摘要能稳定说明主竞争轴，且不依赖无证据的用户规模、排名或模型能力表述。",
            ),
        ]
    return [
        (
            "content",
            "重写核心竞品对比话术",
            "content",
            ResponsibilityType.CONTENT_EXPRESSION,
            0.35,
            "把最大威胁竞品的比较逻辑改成用户能读懂的回应话术。",
            "页面首屏、对比表或客服话术中能明确回答用户为什么比较该竞品。",
        ),
        (
            "evidence",
            "补齐高风险证据材料",
            "evidence",
            ResponsibilityType.EVIDENCE_RESEARCH,
            0.55,
            "优先补齐影响采纳的价格、截图、访问时间、评论或售后证据。",
            "关键结论能绑定访问时间、截图、评论摘要或售后说明，并在报告中不再触发证据缺口。",
        ),
        (
            "positioning",
            "明确目标产品主竞争轴",
            "positioning",
            ResponsibilityType.PRODUCT_FEATURE,
            0.45,
            "围绕清理省心、除臭可信和维护成本建立更清楚的定位表达。",
            "目标产品详情页和报告摘要能稳定说明主竞争轴，且不依赖无证据的销量、排名或认证表述。",
        ),
    ]


def _why_users_compare(
    *,
    target_product: Product,
    competitor: Product,
    edge: CompetitionEdge,
) -> str:
    if _is_internet_ai_domain_product(target_product):
        return (
            f"用户会在 {edge.slice.price_band}/{edge.slice.persona}/{edge.slice.scenario} "
            f"场景下把 {competitor.name} 与 {target_product.name} 放进同一 AI 助手候选集，"
            "核心是在任务覆盖、入口生态、证据完整性和迁移成本之间做取舍。"
        )
    return (
        f"用户会在 {edge.slice.price_band}/{edge.slice.persona}/{edge.slice.scenario} "
        f"场景下把 {competitor.name} 与 {target_product.name} 放进同一候选集，"
        "核心是在清理负担、除臭可信度、容量和长期维护成本之间做取舍。"
    )


def _competitor_strengths(
    *,
    competitor: Product,
    edge: CompetitionEdge,
    evidences: Sequence[Evidence],
) -> list[str]:
    if _is_internet_ai_domain_product(competitor):
        strengths = []
        if edge.competition_type == CompetitionType.DIRECT:
            strengths.append("与目标产品同属通用 AI 助手，容易进入同一组任务场景比较。")
        if edge.edge_score >= 0.75:
            strengths.append("当前规则评分显示其竞争压力较高，需优先解释任务场景差异。")
        evidence_text = " ".join(evidence.content_summary for evidence in evidences).lower()
        if any(term.lower() in evidence_text for term in AI_RESEARCH_TERMS):
            strengths.append("已有官方公开页证据提到搜索、研究或文档相关能力。")
        if any(term.lower() in evidence_text for term in AI_CONTENT_TERMS):
            strengths.append("已有官方公开页证据提到内容创作相关能力。")
        if any(term.lower() in evidence_text for term in AI_CODING_TERMS):
            strengths.append("已有官方公开页证据提到编程、推理或 API 相关线索。")
        if any(term.lower() in evidence_text for term in AI_AGENT_TERMS):
            strengths.append("已有官方公开页证据提到智能体、工作流或办公协作线索。")
        return strengths or [f"{competitor.name} 当前具备可被用户比较的 AI 助手定位。"]

    strengths = []
    if edge.competition_type == CompetitionType.DIRECT:
        strengths.append("与目标产品解决相近的自动清理任务，容易进入同一组横向比较。")
    if edge.edge_score >= 0.75:
        strengths.append("当前规则评分显示其竞争压力较高，需优先解释差异。")
    evidence_text = " ".join(evidence.content_summary for evidence in evidences)
    if any(term in evidence_text for term in ODOR_TERMS):
        strengths.append("已有快照文本提到除臭或控味相关卖点。")
    if any(term in evidence_text for term in SIZE_TERMS):
        strengths.append("已有快照文本提到大空间或多猫适配相关卖点。")
    return strengths or [f"{competitor.name} 当前具备可被用户比较的同类商品定位。"]


def _competitor_weaknesses(
    *,
    edge: CompetitionEdge,
    evidence_ids: Sequence[str],
) -> list[str]:
    weaknesses = []
    if not evidence_ids:
        weaknesses.append("暂无可靠数据支撑更细的强弱项拆解，建议补充证据后复核。")
    if edge.risk_flags:
        weaknesses.append("当前关系存在证据或可靠性风险，报告正文应保守表达。")
    if edge.score_breakdown.evidence_confidence < 0.7:
        weaknesses.append(
            "证据置信度仍不高，定价、用户规模、下载量、模型能力或隐私安全信息不宜写成确定结论。"
        )
    return weaknesses or ["暂无可靠数据显示其明确短板，建议继续补充评论和售后材料。"]


def _target_response_for_edge(edge: CompetitionEdge, competitor: Product) -> str:
    axis = _primary_axis_for_edge(edge)
    if _is_internet_ai_domain_product(competitor):
        return (
            f"围绕“{axis}”解释目标产品差异，不直接贬低 {competitor.name}；"
            "优先用已有官方公开页证据说明适用任务、入口和能力边界，"
            "对定价、用户规模、排名或模型能力等证据不足处保留“暂无可靠数据/建议复核”。"
        )
    return (
        f"围绕“{axis}”解释目标产品差异，不直接贬低 {competitor.name}；"
        "优先用已有证据说明为什么更省心、为什么可信、哪些信息仍建议复核。"
    )


def _sales_objection_for_edge(edge: CompetitionEdge, competitor: Product) -> str:
    if _is_internet_ai_domain_product(competitor):
        return (
            f"用户可能会问：既然 {competitor.name} 也覆盖 {edge.slice.scenario} 场景，"
            "为什么还要继续试用或迁移到目标产品？定价、API、平台入口和关键能力是否有可靠证据？"
        )
    return (
        f"用户可能会问：既然 {competitor.name} 也覆盖 {edge.slice.scenario} 场景，"
        "为什么还要选择目标产品？价格、维护成本和除臭效果是否有可靠证据？"
    )


def _response_talk_track_for_edge(edge: CompetitionEdge, competitor: Product) -> str:
    if _is_internet_ai_domain_product(competitor):
        return (
            f"可以回应为：{competitor.name} 是当前 AI 助手切片下值得比较的方案；"
            "目标产品应把已有证据能支持的任务场景、入口和能力边界讲清楚，"
            "对定价、模型能力、用户规模、排名等证据不足处保留“暂无可靠数据/建议复核”。"
        )
    return (
        f"可以回应为：{competitor.name} 是当前切片下值得比较的方案；"
        "目标产品应把已有证据能支持的省心清理、容量和除臭表达讲清楚，"
        "对价格、认证、销量等证据不足处保留“建议复核”。"
    )


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


def _evidence_ids_for_claims(
    claim_ids: Sequence[str],
    claims_by_id: dict[str, Claim],
) -> list[str]:
    return _dedupe(
        evidence_id
        for claim_id in claim_ids
        if claim_id in claims_by_id
        for evidence_id in claims_by_id[claim_id].evidence_ids
    )


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
