from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime

from app.graph import TaskGraphState, append_report_data, append_run_log
from app.schemas import (
    AgentName,
    AgentRunLog,
    Claim,
    CompetitionEdge,
    Evidence,
    FeatureTree,
    PricingModel,
    Product,
    ProductRole,
    ReportData,
    ReportSection,
    ReviewInsight,
    ReviewTask,
    RiskFlag,
    RunStatus,
    TaskStatus,
    UserPersona,
)
from app.schemas.common import JsonObject

REQUIRED_SECTION_ORDER = [
    "executive_summary",
    "product_profile",
    "competitor_findings",
    "dynamic_slice_analysis",
    "decision_chain_analysis",
    "user_research_insights",
    "recommendations",
    "qa_summary",
    "evidence_index",
]


def writer_agent_node(
    state: TaskGraphState,
    *,
    now: datetime | None = None,
) -> TaskGraphState:
    run_started_at = now or datetime.now(UTC)
    task_id = str(state["task"]["task_id"])
    run_id = _next_writer_run_id(state, task_id)
    products = [Product.model_validate(item) for item in state["products"]]
    evidences = [Evidence.model_validate(item) for item in state["evidences"]]
    feature_trees = [FeatureTree.model_validate(item) for item in state["feature_trees"]]
    pricing_models = [PricingModel.model_validate(item) for item in state["pricing_models"]]
    user_personas = [UserPersona.model_validate(item) for item in state["user_personas"]]
    claims = [Claim.model_validate(item) for item in state["claims"]]
    edges = [CompetitionEdge.model_validate(item) for item in state["competition_edges"]]
    review_insights = [
        ReviewInsight.model_validate(item) for item in state["review_insights"]
    ]
    review_tasks = [ReviewTask.model_validate(item) for item in state["review_tasks"]]

    try:
        if not _writer_input_is_allowed(state, claims, edges):
            raise ValueError(
                "Writer Agent requires QA passed metadata or explicitly risk-marked artifacts."
            )

        target_product = _target_product(products)
        report_data = _build_report_data(
            task_id=task_id,
            generated_at=run_started_at,
            products=products,
            evidences=evidences,
            feature_trees=feature_trees,
            pricing_models=pricing_models,
            user_personas=user_personas,
            claims=claims,
            edges=edges,
            review_insights=review_insights,
            review_tasks=review_tasks,
            target_product=target_product,
            state=state,
        )
        append_report_data(state, report_data)
        _set_task_status(state, TaskStatus.COMPLETED, run_started_at)

        state["metadata"]["writer_agent"] = {
            "status": "succeeded",
            "report_id": report_data.report_id,
            "section_order": report_data.section_order,
            "claim_count": len(claims),
            "evidence_count": len(evidences),
            "risk_claim_ids": _risk_claim_ids(claims),
        }
        append_run_log(
            state,
            AgentRunLog(
                run_id=run_id,
                task_id=task_id,
                agent_name=AgentName.WRITER,
                status=RunStatus.SUCCEEDED,
                started_at=run_started_at,
                ended_at=run_started_at,
                input_summary=(
                    f"Generate report data from {len(claims)} claims, "
                    f"{len(edges)} competition edges and {len(evidences)} evidence records."
                ),
                output_summary=(
                    f"Generated report {report_data.report_id} with "
                    f"{len(report_data.section_order)} sections."
                ),
                error_message=None,
            ),
        )
        return state
    except Exception as exc:
        append_run_log(
            state,
            AgentRunLog(
                run_id=run_id,
                task_id=task_id,
                agent_name=AgentName.WRITER,
                status=RunStatus.FAILED,
                started_at=run_started_at,
                ended_at=run_started_at,
                input_summary="Generate web report data from QA-ready artifacts.",
                output_summary=None,
                error_message=str(exc),
            ),
        )
        raise


def _build_report_data(
    *,
    task_id: str,
    generated_at: datetime,
    products: Sequence[Product],
    evidences: Sequence[Evidence],
    feature_trees: Sequence[FeatureTree],
    pricing_models: Sequence[PricingModel],
    user_personas: Sequence[UserPersona],
    claims: Sequence[Claim],
    edges: Sequence[CompetitionEdge],
    review_insights: Sequence[ReviewInsight],
    review_tasks: Sequence[ReviewTask],
    target_product: Product,
    state: TaskGraphState,
) -> ReportData:
    products_by_id = {product.product_id: product for product in products}
    claims_by_id = {claim.claim_id: claim for claim in claims}
    evidences_by_id = {evidence.evidence_id: evidence for evidence in evidences}
    sorted_edges = sorted(edges, key=lambda edge: edge.edge_score, reverse=True)
    top_edges = sorted_edges[:5]

    return ReportData(
        report_id=f"report_{task_id}_{len(state['reports']) + 1:03d}",
        task_id=task_id,
        generated_at=generated_at,
        section_order=REQUIRED_SECTION_ORDER,
        executive_summary=_executive_summary_section(
            target_product=target_product,
            edges=sorted_edges,
            claims_by_id=claims_by_id,
        ),
        product_profile=_product_profile_section(
            target_product=target_product,
            feature_trees=feature_trees,
            pricing_models=pricing_models,
            user_personas=user_personas,
        ),
        competitor_findings=_competitor_findings_section(
            top_edges=top_edges,
            products_by_id=products_by_id,
            claims_by_id=claims_by_id,
            evidences_by_id=evidences_by_id,
        ),
        dynamic_slice_analysis=_dynamic_slice_section(
            edges=sorted_edges,
            claims_by_id=claims_by_id,
        ),
        decision_chain_analysis=_decision_chain_section(
            edges=sorted_edges,
            claims_by_id=claims_by_id,
        ),
        user_research_insights=_user_research_section(review_insights),
        recommendations=_recommendations_section(
            top_edges=top_edges,
            products_by_id=products_by_id,
            claims_by_id=claims_by_id,
        ),
        qa_summary=_qa_summary_section(
            claims=claims,
            review_tasks=review_tasks,
            state=state,
        ),
        evidence_index=_evidence_index_section(evidences),
    )


def _executive_summary_section(
    *,
    target_product: Product,
    edges: Sequence[CompetitionEdge],
    claims_by_id: dict[str, Claim],
) -> ReportSection:
    top_edges = edges[:3]
    claim_ids = _dedupe(
        claim_id for edge in top_edges for claim_id in edge.claim_ids if claim_id in claims_by_id
    )
    evidence_ids = _evidence_ids_for_claims(claim_ids, claims_by_id)
    items = [
        {
            "edge_id": edge.edge_id,
            "competitor_product_id": edge.competitor_product_id,
            "competition_type": edge.competition_type.value,
            "edge_score": edge.edge_score,
            "claim_ids": edge.claim_ids,
            "evidence_ids": _evidence_ids_for_claims(edge.claim_ids, claims_by_id),
            "risk_flags": _risk_values(_edge_and_claim_risks(edge, claims_by_id)),
        }
        for edge in top_edges
    ]
    return _section(
        "executive_summary",
        "执行摘要",
        f"{target_product.name} 的报告基于 {len(edges)} 条竞争关系和可追溯证据生成。",
        items,
        claim_ids=claim_ids,
        evidence_ids=evidence_ids,
    )


def _product_profile_section(
    *,
    target_product: Product,
    feature_trees: Sequence[FeatureTree],
    pricing_models: Sequence[PricingModel],
    user_personas: Sequence[UserPersona],
) -> ReportSection:
    target_feature_tree = _first_for_product(feature_trees, target_product.product_id)
    target_pricing = _first_for_product(pricing_models, target_product.product_id)
    target_persona = _first_for_product(user_personas, target_product.product_id)
    items = [
        {
            "product": target_product.model_dump(mode="json"),
            "feature_tree": _dump_or_none(target_feature_tree),
            "pricing_model": _dump_or_none(target_pricing),
            "user_persona": _dump_or_none(target_persona),
        }
    ]
    evidence_ids = _dedupe(
        [
            *target_product.evidence_ids,
            *_artifact_evidence_ids(target_feature_tree),
            *_artifact_evidence_ids(target_pricing),
            *_artifact_evidence_ids(target_persona),
        ]
    )
    risk_flags = _dedupe(
        [
            *_artifact_risk_flags(target_feature_tree),
            *_artifact_risk_flags(target_pricing),
            *_artifact_risk_flags(target_persona),
        ]
    )
    return _section(
        "product_profile",
        "目标产品画像",
        "整理目标产品的功能、价格、人群和场景结构化画像。",
        items,
        evidence_ids=evidence_ids,
        risk_flags=risk_flags,
    )


def _competitor_findings_section(
    *,
    top_edges: Sequence[CompetitionEdge],
    products_by_id: dict[str, Product],
    claims_by_id: dict[str, Claim],
    evidences_by_id: dict[str, Evidence],
) -> ReportSection:
    items = []
    claim_ids: list[str] = []
    evidence_ids: list[str] = []
    risk_flags: list[RiskFlag] = []
    for edge in top_edges:
        competitor = products_by_id.get(edge.competitor_product_id)
        edge_claims = [
            claims_by_id[claim_id]
            for claim_id in edge.claim_ids
            if claim_id in claims_by_id
        ]
        edge_evidence_ids = _dedupe(
            evidence_id
            for claim in edge_claims
            for evidence_id in claim.evidence_ids
            if evidence_id in evidences_by_id
        )
        claim_ids.extend(claim.claim_id for claim in edge_claims)
        evidence_ids.extend(edge_evidence_ids)
        risk_flags.extend(_edge_and_claim_risks(edge, claims_by_id))
        items.append(
            {
                "edge_id": edge.edge_id,
                "competitor": _product_brief(competitor),
                "competition_type": edge.competition_type.value,
                "slice": edge.slice.model_dump(mode="json"),
                "decision_stages": [stage.value for stage in edge.decision_stages],
                "edge_score": edge.edge_score,
                "score_breakdown": edge.score_breakdown.model_dump(mode="json"),
                "claims": [_claim_reference(claim) for claim in edge_claims],
                "evidence_ids": edge_evidence_ids,
                "risk_flags": _risk_values(_edge_and_claim_risks(edge, claims_by_id)),
            }
        )
    return _section(
        "competitor_findings",
        "竞品发现",
        "按竞争评分排序展示核心竞品关系，结论均保留 Claim 与 Evidence 索引。",
        items,
        claim_ids=_dedupe(claim_ids),
        evidence_ids=_dedupe(evidence_ids),
        risk_flags=_dedupe(risk_flags),
    )


def _dynamic_slice_section(
    *,
    edges: Sequence[CompetitionEdge],
    claims_by_id: dict[str, Claim],
) -> ReportSection:
    slice_groups: dict[tuple[str, str, str], list[CompetitionEdge]] = defaultdict(list)
    for edge in edges:
        slice_groups[
            (edge.slice.price_band, edge.slice.persona, edge.slice.scenario)
        ].append(edge)
    items = []
    claim_ids: list[str] = []
    evidence_ids: list[str] = []
    for (price_band, persona, scenario), grouped_edges in sorted(slice_groups.items()):
        top_edges = grouped_edges[:3]
        grouped_claim_ids = _dedupe(
            claim_id
            for edge in top_edges
            for claim_id in edge.claim_ids
            if claim_id in claims_by_id
        )
        claim_ids.extend(grouped_claim_ids)
        evidence_ids.extend(_evidence_ids_for_claims(grouped_claim_ids, claims_by_id))
        items.append(
            {
                "price_band": price_band,
                "persona": persona,
                "scenario": scenario,
                "edge_ids": [edge.edge_id for edge in top_edges],
                "top_edge_score": top_edges[0].edge_score if top_edges else None,
                "claim_ids": grouped_claim_ids,
                "evidence_ids": _evidence_ids_for_claims(grouped_claim_ids, claims_by_id),
            }
        )
    return _section(
        "dynamic_slice_analysis",
        "动态竞争切片",
        "聚合价格带、人群和使用场景切片下的竞争关系。",
        items,
        claim_ids=_dedupe(claim_ids),
        evidence_ids=_dedupe(evidence_ids),
    )


def _decision_chain_section(
    *,
    edges: Sequence[CompetitionEdge],
    claims_by_id: dict[str, Claim],
) -> ReportSection:
    stage_groups: dict[str, list[CompetitionEdge]] = defaultdict(list)
    for edge in edges:
        for stage in edge.decision_stages:
            stage_groups[stage.value].append(edge)
    items = []
    claim_ids: list[str] = []
    evidence_ids: list[str] = []
    for stage, grouped_edges in sorted(stage_groups.items()):
        top_edges = grouped_edges[:3]
        stage_claim_ids = _dedupe(
            claim_id
            for edge in top_edges
            for claim_id in edge.claim_ids
            if claim_id in claims_by_id
        )
        claim_ids.extend(stage_claim_ids)
        evidence_ids.extend(_evidence_ids_for_claims(stage_claim_ids, claims_by_id))
        items.append(
            {
                "decision_stage": stage,
                "edge_ids": [edge.edge_id for edge in top_edges],
                "claim_ids": stage_claim_ids,
                "evidence_ids": _evidence_ids_for_claims(stage_claim_ids, claims_by_id),
            }
        )
    return _section(
        "decision_chain_analysis",
        "决策链竞争分析",
        "按购买决策阶段组织竞争关系，便于前端展示决策链。",
        items,
        claim_ids=_dedupe(claim_ids),
        evidence_ids=_dedupe(evidence_ids),
    )


def _user_research_section(review_insights: Sequence[ReviewInsight]) -> ReportSection:
    items = [
        {
            "review_insight_id": insight.review_insight_id,
            "product_id": insight.product_id,
            "summary": insight.summary,
            "evidence_ids": insight.evidence_ids,
            "confidence_level": insight.confidence_level.value,
            "limitations": insight.limitations,
            "risk_flags": _risk_values(insight.risk_flags),
        }
        for insight in review_insights[:8]
    ]
    return _section(
        "user_research_insights",
        "用户研究洞察",
        "汇总本地评论快照和研究材料中的用户信号，不展开未脱敏原文。",
        items,
        evidence_ids=_dedupe(
            evidence_id for insight in review_insights for evidence_id in insight.evidence_ids
        ),
        risk_flags=_dedupe(risk for insight in review_insights for risk in insight.risk_flags),
    )


def _recommendations_section(
    *,
    top_edges: Sequence[CompetitionEdge],
    products_by_id: dict[str, Product],
    claims_by_id: dict[str, Claim],
) -> ReportSection:
    items = []
    claim_ids: list[str] = []
    evidence_ids: list[str] = []
    for edge in top_edges[:3]:
        competitor = products_by_id.get(edge.competitor_product_id)
        edge_claim_ids = [claim_id for claim_id in edge.claim_ids if claim_id in claims_by_id]
        edge_evidence_ids = _evidence_ids_for_claims(edge_claim_ids, claims_by_id)
        claim_ids.extend(edge_claim_ids)
        evidence_ids.extend(edge_evidence_ids)
        items.append(
            {
                "recommendation": (
                    f"优先解释 {competitor.name if competitor else edge.competitor_product_id} "
                    f"在 {edge.slice.price_band}/{edge.slice.persona}/{edge.slice.scenario} "
                    "切片下的竞争关系，并展示对应证据。"
                ),
                "basis_edge_id": edge.edge_id,
                "claim_ids": edge_claim_ids,
                "evidence_ids": edge_evidence_ids,
                "is_inference": True,
            }
        )
    if not items:
        items.append(
            {
                "recommendation": "暂无可靠数据",
                "basis_edge_id": None,
                "claim_ids": [],
                "evidence_ids": [],
                "is_inference": True,
            }
        )
    return _section(
        "recommendations",
        "可执行建议",
        "基于已生成竞争关系提出展示和复核建议，不补写新的事实字段。",
        items,
        claim_ids=_dedupe(claim_ids),
        evidence_ids=_dedupe(evidence_ids),
    )


def _qa_summary_section(
    *,
    claims: Sequence[Claim],
    review_tasks: Sequence[ReviewTask],
    state: TaskGraphState,
) -> ReportSection:
    risk_claims = [
        claim for claim in claims if claim.risk_flags or claim.status.value != "accepted"
    ]
    items = [
        {
            "qa_agent": state["metadata"].get("qa_agent", {}),
            "review_task_count": len(review_tasks),
            "revision_message_count": len(state["agent_messages"]),
            "risk_claims": [_claim_reference(claim) for claim in risk_claims],
            "collection_repair": state["metadata"].get("collection_agent_repair"),
            "analysis_recompute": state["metadata"].get("analysis_agent_recompute"),
        }
    ]
    return _section(
        "qa_summary",
        "QA 审查摘要",
        "记录 QA 通过状态、打回处理和仍需标明的风险 Claim。",
        items,
        claim_ids=[claim.claim_id for claim in risk_claims],
        evidence_ids=_dedupe(
            evidence_id for claim in risk_claims for evidence_id in claim.evidence_ids
        ),
        risk_flags=_dedupe(risk for claim in risk_claims for risk in claim.risk_flags),
    )


def _evidence_index_section(evidences: Sequence[Evidence]) -> ReportSection:
    items = [
        {
            "evidence_id": evidence.evidence_id,
            "product_id": evidence.product_id,
            "source_type": evidence.source_type.value,
            "source_url": evidence.source_url,
            "screenshot_path": evidence.screenshot_path,
            "access_time": evidence.access_time.isoformat() if evidence.access_time else None,
            "confidence_level": evidence.confidence_level.value,
            "content_summary": evidence.content_summary,
            "limitations": evidence.limitations,
        }
        for evidence in evidences
    ]
    return _section(
        "evidence_index",
        "Evidence 索引",
        "列出报告中可追溯的证据来源、访问时间、截图和局限性。",
        items,
        evidence_ids=[evidence.evidence_id for evidence in evidences],
    )


def _section(
    section_id: str,
    title: str,
    summary: str,
    items: list[JsonObject],
    *,
    claim_ids: Sequence[str] = (),
    evidence_ids: Sequence[str] = (),
    risk_flags: Sequence[RiskFlag] = (),
) -> ReportSection:
    return ReportSection(
        section_id=section_id,
        title=title,
        summary=summary,
        items=items,
        claim_ids=_dedupe(claim_ids),
        evidence_ids=_dedupe(evidence_ids),
        risk_flags=_dedupe(risk_flags),
    )


def _writer_input_is_allowed(
    state: TaskGraphState,
    claims: Sequence[Claim],
    edges: Sequence[CompetitionEdge],
) -> bool:
    qa_metadata = state["metadata"].get("qa_agent", {})
    if isinstance(qa_metadata, dict) and qa_metadata.get("qa_status") == "passed":
        return True
    return any(claim.risk_flags for claim in claims) or any(edge.risk_flags for edge in edges)


def _target_product(products: Sequence[Product]) -> Product:
    for product in products:
        if product.role == ProductRole.TARGET:
            return product
    raise ValueError("Writer Agent requires one target product in state.products.")


def _first_for_product[T](artifacts: Sequence[T], product_id: str) -> T | None:
    for artifact in artifacts:
        if getattr(artifact, "product_id", None) == product_id:
            return artifact
    return None


def _claim_reference(claim: Claim) -> JsonObject:
    return {
        "claim_id": claim.claim_id,
        "claim_type": claim.claim_type,
        "content": claim.content,
        "confidence": claim.confidence,
        "status": claim.status.value,
        "is_inference": claim.is_inference,
        "risk_flags": _risk_values(claim.risk_flags),
        "evidence_ids": claim.evidence_ids,
    }


def _product_brief(product: Product | None) -> JsonObject:
    if product is None:
        return {}
    return {
        "product_id": product.product_id,
        "name": product.name,
        "brand": product.brand,
        "role": product.role.value,
        "product_url": product.product_url,
        "evidence_ids": product.evidence_ids,
    }


def _edge_and_claim_risks(
    edge: CompetitionEdge,
    claims_by_id: dict[str, Claim],
) -> list[RiskFlag]:
    risks = list(edge.risk_flags)
    for claim_id in edge.claim_ids:
        claim = claims_by_id.get(claim_id)
        if claim is not None:
            risks.extend(claim.risk_flags)
    return _dedupe(risks)


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


def _artifact_evidence_ids(artifact: object | None) -> list[str]:
    evidence_ids = getattr(artifact, "evidence_ids", [])
    return list(evidence_ids) if isinstance(evidence_ids, list) else []


def _artifact_risk_flags(artifact: object | None) -> list[RiskFlag]:
    risk_flags = getattr(artifact, "risk_flags", [])
    return list(risk_flags) if isinstance(risk_flags, list) else []


def _dump_or_none(artifact: object | None) -> JsonObject | None:
    if artifact is None:
        return None
    return artifact.model_dump(mode="json")


def _risk_claim_ids(claims: Sequence[Claim]) -> list[str]:
    return [
        claim.claim_id
        for claim in claims
        if claim.risk_flags or claim.status.value != "accepted"
    ]


def _risk_values(risk_flags: Sequence[RiskFlag]) -> list[str]:
    return [risk_flag.value for risk_flag in _dedupe(risk_flags)]


def _set_task_status(state: TaskGraphState, status: TaskStatus, updated_at: datetime) -> None:
    state["task"]["status"] = status.value
    state["task"]["updated_at"] = updated_at.isoformat()


def _next_writer_run_id(state: TaskGraphState, task_id: str) -> str:
    writer_run_count = sum(
        1 for run_log in state["run_logs"] if run_log.get("agent_name") == AgentName.WRITER.value
    )
    if writer_run_count == 0:
        return f"run_{task_id}_writer"
    return f"run_{task_id}_writer_{writer_run_count + 1:03d}"


def _dedupe[T](items: Iterable[T]) -> list[T]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped
