import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from app.graph import (
    TaskGraphState,
    append_knowledge_artifact,
    append_report_data,
    append_run_log,
    append_token_usage_log,
)
from app.schemas import (
    ActionPriority,
    AgentName,
    AgentRunLog,
    Claim,
    CompetitionEdge,
    Evidence,
    FeatureTree,
    JudgmentStrength,
    PricingModel,
    Product,
    ProductRole,
    ReportData,
    ReportSection,
    ResponsibilityType,
    ReviewInsight,
    ReviewTask,
    RiskFlag,
    RunStatus,
    TaskStatus,
    UserPersona,
)
from app.schemas.common import JsonObject
from app.services.knowledge_retrieval import (
    KnowledgeRetrievalService,
    compact_knowledge_for_llm,
)
from app.services.llm_client import LLMCallResult, LLMClient

REQUIRED_SECTION_ORDER = [
    "conclusion_summary",
    "competitive_landscape_judgment",
    "core_competitor_analysis",
    "user_decision_chain_analysis",
    "target_opportunities_and_risks",
    "product_strategy_recommendations",
    "evidence_quality_appendix",
    "analysis_process_appendix",
]
MIN_PLANNED_REPORT_EDGES = 3
MAX_PLANNED_REPORT_EDGES = 5
MAX_LLM_INSIGHT_PRODUCTS = 8
MAX_LLM_QUALITY_ISSUES = 6
MAX_LLM_EXPANDED_PARAGRAPHS = 4
MAX_LLM_REPAIR_TARGETS = 4


@dataclass(frozen=True)
class ReportPlan:
    priority_edges: list[CompetitionEdge]
    total_edge_count: int

    @property
    def priority_edge_ids(self) -> list[str]:
        return [edge.edge_id for edge in self.priority_edges]


@dataclass(frozen=True)
class SectionLLMConfig:
    label: str
    schema_name: str
    section_ids: tuple[str, ...]
    objective: str
    rules: tuple[str, ...]
    max_items: int


def writer_agent_node(
    state: TaskGraphState,
    *,
    now: datetime | None = None,
    llm_client: LLMClient | None = None,
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
        knowledge_artifact = KnowledgeRetrievalService().retrieve_for_writer(
            state=state,
            report_items=_report_focus_items(report_data),
            now=run_started_at,
        )
        append_knowledge_artifact(state, knowledge_artifact)
        llm_client_instance = llm_client or LLMClient()
        insight_result = _extract_report_insights_with_llm(
            report_data=report_data,
            state=state,
            llm_client=llm_client_instance,
        )
        paragraph_results = _rewrite_report_summaries_with_llm(
            report_data=report_data,
            state=state,
            llm_client=llm_client_instance,
        )
        expansion_result = _expand_report_analysis_with_llm(
            report_data=report_data,
            state=state,
            llm_client=llm_client_instance,
        )
        quality_result = _review_report_quality_with_llm(
            report_data=report_data,
            state=state,
            llm_client=llm_client_instance,
        )
        quality_repair_result = _repair_report_quality_issues_with_llm(
            report_data=report_data,
            state=state,
            quality_result=quality_result,
            llm_client=llm_client_instance,
        )
        usage_results: list[tuple[str, LLMCallResult | None]] = [("insight", insight_result)]
        usage_results.extend(
            (f"paragraph_{label}", result) for label, result in paragraph_results
        )
        usage_results.extend(
            [
                ("expansion", expansion_result),
                ("quality", quality_result),
                ("quality_repair", quality_repair_result),
            ]
        )
        for usage_label, result in usage_results:
            if result is not None and result.token_usage.total_tokens > 0:
                append_token_usage_log(
                    state,
                    result.token_usage.to_log(
                        task_id=task_id,
                        run_id=run_id,
                        agent_name=AgentName.WRITER,
                        usage_id=f"usage_{run_id}_llm_{usage_label}",
                    ),
                )
        append_report_data(state, report_data)
        _set_task_status(state, TaskStatus.COMPLETED, run_started_at)

        llm_metadata = _llm_rewrite_batch_metadata(paragraph_results)
        state["metadata"]["writer_agent"] = {
            "status": "succeeded",
            "report_id": report_data.report_id,
            "section_order": report_data.section_order,
            "claim_count": len(claims),
            "evidence_count": len(evidences),
            "risk_claim_ids": _risk_claim_ids(claims),
            "report_plan": {
                "total_edge_count": len(edges),
                "planned_edge_ids": _planned_edge_ids_from_report(report_data),
            },
            "knowledge_retrieval": {
                "status": "succeeded",
                "knowledge_id": knowledge_artifact.knowledge_id,
                "retrieval_mode": knowledge_artifact.retrieval_mode,
                "external_search_performed": knowledge_artifact.external_search_performed,
                "item_count": len(knowledge_artifact.items),
                "source_count": len(knowledge_artifact.sources),
            },
            "llm_insight_extraction": (
                _llm_rewrite_metadata(insight_result) if insight_result else {"status": "not_run"}
            ),
            "llm_rewrite": llm_metadata,
            "llm_analysis_expansion": (
                _llm_rewrite_metadata(expansion_result)
                if expansion_result
                else {"status": "not_run"}
            ),
            "llm_quality_review": (
                _llm_rewrite_metadata(quality_result) if quality_result else {"status": "not_run"}
            ),
            "llm_quality_repair": (
                _llm_rewrite_metadata(quality_repair_result)
                if quality_repair_result
                else {"status": "not_run"}
            ),
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
    report_plan = _build_report_plan(sorted_edges)
    planned_edges = report_plan.priority_edges

    return ReportData(
        report_id=f"report_{task_id}_{len(state['reports']) + 1:03d}",
        task_id=task_id,
        generated_at=generated_at,
        section_order=REQUIRED_SECTION_ORDER,
        conclusion_summary=_executive_summary_section(
            target_product=target_product,
            edges=planned_edges,
            total_edge_count=report_plan.total_edge_count,
            claims_by_id=claims_by_id,
        ),
        target_opportunities_and_risks=_product_profile_section(
            target_product=target_product,
            feature_trees=feature_trees,
            pricing_models=pricing_models,
            user_personas=user_personas,
        ),
        core_competitor_analysis=_competitor_findings_section(
            top_edges=planned_edges,
            products_by_id=products_by_id,
            claims_by_id=claims_by_id,
            evidences_by_id=evidences_by_id,
        ),
        competitive_landscape_judgment=_dynamic_slice_section(
            edges=planned_edges,
            claims_by_id=claims_by_id,
        ),
        user_decision_chain_analysis=_decision_chain_section(
            edges=planned_edges,
            claims_by_id=claims_by_id,
        ),
        product_strategy_recommendations=_recommendations_section(
            top_edges=planned_edges,
            products_by_id=products_by_id,
            claims_by_id=claims_by_id,
        ),
        evidence_quality_appendix=_evidence_quality_appendix_section(
            claims=claims,
            evidences=evidences,
            review_tasks=review_tasks,
            state=state,
        ),
        analysis_process_appendix=_analysis_process_appendix_section(
            state=state,
            review_insights=review_insights,
        ),
    )


def _build_report_plan(sorted_edges: Sequence[CompetitionEdge]) -> ReportPlan:
    if not sorted_edges:
        return ReportPlan(priority_edges=[], total_edge_count=0)

    target_count = min(MAX_PLANNED_REPORT_EDGES, len(sorted_edges))
    min_count = min(MIN_PLANNED_REPORT_EDGES, target_count)
    selected: list[CompetitionEdge] = []
    selected_ids: set[str] = set()
    seen_competitors: set[str] = set()
    seen_slices: set[tuple[str, str, str]] = set()

    for edge in sorted_edges:
        if len(selected) >= target_count:
            break
        slice_key = _edge_slice_key(edge)
        is_new_competitor = edge.competitor_product_id not in seen_competitors
        is_new_slice = slice_key not in seen_slices
        if selected and not (is_new_competitor or is_new_slice):
            continue
        _append_planned_edge(
            edge,
            selected=selected,
            selected_ids=selected_ids,
            seen_competitors=seen_competitors,
            seen_slices=seen_slices,
        )

    for edge in sorted_edges:
        if len(selected) >= target_count:
            break
        _append_planned_edge(
            edge,
            selected=selected,
            selected_ids=selected_ids,
            seen_competitors=seen_competitors,
            seen_slices=seen_slices,
        )

    if len(selected) < min_count:
        for edge in sorted_edges:
            if len(selected) >= min_count:
                break
            _append_planned_edge(
                edge,
                selected=selected,
                selected_ids=selected_ids,
                seen_competitors=seen_competitors,
                seen_slices=seen_slices,
            )

    return ReportPlan(priority_edges=selected, total_edge_count=len(sorted_edges))


def _append_planned_edge(
    edge: CompetitionEdge,
    *,
    selected: list[CompetitionEdge],
    selected_ids: set[str],
    seen_competitors: set[str],
    seen_slices: set[tuple[str, str, str]],
) -> None:
    if edge.edge_id in selected_ids:
        return

    selected.append(edge)
    selected_ids.add(edge.edge_id)
    seen_competitors.add(edge.competitor_product_id)
    seen_slices.add(_edge_slice_key(edge))


def _edge_slice_key(edge: CompetitionEdge) -> tuple[str, str, str]:
    return (edge.slice.price_band, edge.slice.persona, edge.slice.scenario)


def _extract_report_insights_with_llm(
    *,
    report_data: ReportData,
    state: TaskGraphState,
    llm_client: LLMClient | None,
) -> LLMCallResult | None:
    client = llm_client or LLMClient()
    fallback = {"insights": []}
    result = client.complete_json(
        system_prompt=_insight_extraction_system_prompt(),
        user_prompt=_insight_extraction_user_prompt(report_data=report_data, state=state),
        fallback=fallback,
        schema_name="writer_review_selling_point_insight_extraction",
        temperature=0.1,
    )
    if not result.used_fallback:
        _apply_llm_extracted_insights(report_data=report_data, state=state, payload=result.data)
    return result


def _insight_extraction_system_prompt() -> str:
    return (
        "你是电商评论与卖点洞察分析师，只从输入的 SKU 快照、评论摘要和用户研究文本中抽取信息。"
        "必须只返回 JSON object，顶层字段只能是 insights。"
        "每条 insight 必须包含 product_id、summary、pain_points、buying_reasons、objections。"
        "pain_points、buying_reasons、objections 都是中文短句数组，每类最多 4 条。"
        "不得编造价格、销量、认证、尺寸、排名、真实评论原文或输入中不存在的事实；"
        "证据不足时用“暂无可靠数据”或“需要复核”，不要写成确定事实。"
    )


def _insight_extraction_user_prompt(*, report_data: ReportData, state: TaskGraphState) -> str:
    planned_edge_ids = set(_planned_edge_ids_from_report(report_data))
    product_ids = _product_ids_for_edges(state, planned_edge_ids)
    review_insights = _compact_review_insights_from_state(state, product_ids)
    review_evidence_ids = {
        evidence_id
        for insight in review_insights
        for evidence_id in insight.get("evidence_ids", [])
        if isinstance(evidence_id, str)
    }
    payload = {
        "task": {
            "category": state["task"].get("category"),
            "subcategory": state["task"].get("subcategory"),
        },
        "target_product_name": _target_product_name_from_report(report_data),
        "products": _compact_products_from_state(state, product_ids),
        "review_insights": review_insights,
        "evidence": _compact_evidences_from_state(state, review_evidence_ids),
        "user_research_text": _compact_research_text(state["task"].get("research_text")),
        "output_contract": {
            "top_level": "只返回 JSON object，且只包含 insights 字段。",
            "insights": (
                "数组；每条必须包含 product_id、summary、pain_points、"
                "buying_reasons、objections。"
            ),
            "rules": [
                "product_id 必须来自输入 products。",
                "summary 只写一句中文洞察。",
                "pain_points 是用户担心、抱怨或使用阻碍。",
                "buying_reasons 是用户愿意比较或购买的理由。",
                "objections 是可能导致放弃或转向竞品的顾虑。",
                "不要输出 task_id、edge_id、claim_id、evidence_id。",
            ],
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def _compact_review_insights_from_state(
    state: TaskGraphState,
    product_ids: set[str],
) -> list[JsonObject]:
    insights = [ReviewInsight.model_validate(item) for item in state["review_insights"]]
    compact: list[JsonObject] = []
    for insight in insights:
        if insight.product_id not in product_ids:
            continue
        compact.append(
            {
                "review_insight_id": insight.review_insight_id,
                "product_id": insight.product_id,
                "summary": insight.summary,
                "confidence_level": insight.confidence_level.value,
                "market_signals": insight.market_signals,
                "limitations": insight.limitations,
                "risk_flags": [risk.value for risk in insight.risk_flags],
                "evidence_ids": insight.evidence_ids,
            }
        )
        if len(compact) >= MAX_LLM_INSIGHT_PRODUCTS:
            break
    return compact


def _compact_research_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())
    if not text:
        return None
    return _clean_llm_report_text(text, max_chars=1200)


def _apply_llm_extracted_insights(
    *,
    report_data: ReportData,
    state: TaskGraphState,
    payload: JsonObject,
) -> None:
    raw_insights = payload.get("insights")
    if not isinstance(raw_insights, list):
        return

    products_by_id = {
        product.product_id: product
        for product in [Product.model_validate(item) for item in state["products"]]
    }
    extracted: list[JsonObject] = []
    for raw in raw_insights:
        if not isinstance(raw, dict):
            continue
        product_id = raw.get("product_id")
        product = products_by_id.get(product_id) if isinstance(product_id, str) else None
        if product is None:
            continue
        item: JsonObject = {
            "product_name": product.name,
            "summary": _clean_optional_text(raw.get("summary"), max_chars=120),
            "pain_points": _clean_text_list(raw.get("pain_points"), max_items=4, max_chars=80),
            "buying_reasons": _clean_text_list(
                raw.get("buying_reasons"),
                max_items=4,
                max_chars=80,
            ),
            "objections": _clean_text_list(raw.get("objections"), max_items=4, max_chars=80),
        }
        if item["summary"] or item["pain_points"] or item["buying_reasons"] or item["objections"]:
            extracted.append(item)
    if not extracted or not report_data.target_opportunities_and_risks.items:
        return

    report_data.target_opportunities_and_risks.items[0]["llm_extracted_insights"] = extracted


def _compact_extracted_insights_from_report(report_data: ReportData) -> list[JsonObject]:
    compact: list[JsonObject] = []
    for item in report_data.target_opportunities_and_risks.items:
        insights = item.get("llm_extracted_insights")
        if isinstance(insights, list):
            compact.extend(insight for insight in insights if isinstance(insight, dict))
    return compact[:MAX_LLM_INSIGHT_PRODUCTS]


def _rewrite_report_summaries_with_llm(
    *,
    report_data: ReportData,
    state: TaskGraphState,
    llm_client: LLMClient | None,
) -> list[tuple[str, LLMCallResult]]:
    client = llm_client or LLMClient()
    results: list[tuple[str, LLMCallResult]] = []
    for config in _section_llm_configs():
        sections = _sections_for_config(report_data, config)
        if not sections:
            continue
        fallback = _llm_rewrite_fallback(sections, config)
        result = client.complete_json(
            system_prompt=_writer_llm_system_prompt(config),
            user_prompt=_writer_llm_user_prompt(
                report_data=report_data,
                state=state,
                config=config,
                sections=sections,
            ),
            fallback=fallback,
            schema_name=config.schema_name,
            temperature=0.2,
        )
        if not result.used_fallback:
            _apply_llm_report_sections(report_data, result.data)
        results.append((config.label, result))
    return results


def _review_report_quality_with_llm(
    *,
    report_data: ReportData,
    state: TaskGraphState,
    llm_client: LLMClient | None,
) -> LLMCallResult | None:
    client = llm_client or LLMClient()
    fallback = {
        "overall_status": "not_checked",
        "summary": "模型质检未运行，保留本地规则报告。",
        "issues": [],
    }
    result = client.complete_json(
        system_prompt=_report_quality_system_prompt(),
        user_prompt=_report_quality_user_prompt(report_data=report_data, state=state),
        fallback=fallback,
        schema_name="writer_report_quality_review",
        temperature=0.0,
    )
    if not result.used_fallback:
        _apply_llm_report_quality(report_data=report_data, payload=result.data)
    return result


def _repair_report_quality_issues_with_llm(
    *,
    report_data: ReportData,
    state: TaskGraphState,
    quality_result: LLMCallResult | None,
    llm_client: LLMClient | None,
) -> LLMCallResult | None:
    if quality_result is None or quality_result.used_fallback:
        return None
    if not _quality_requires_revision(quality_result.data):
        return None

    repair_targets = _quality_repair_targets(report_data, quality_result.data)
    if not repair_targets:
        _mark_quality_repair_not_applied(
            report_data,
            reason="质检要求修改，但没有定位到可修复的报告段落。",
        )
        return None

    client = llm_client or LLMClient()
    fallback = {"sections": []}
    result = client.complete_json(
        system_prompt=_quality_repair_system_prompt(),
        user_prompt=_quality_repair_user_prompt(
            report_data=report_data,
            state=state,
            repair_targets=repair_targets,
        ),
        fallback=fallback,
        schema_name="writer_report_quality_repair",
        temperature=0.15,
    )
    if not result.used_fallback:
        applied_count = _apply_llm_quality_repair(report_data, result.data, repair_targets)
        _mark_quality_repair_applied(
            report_data,
            applied_count=applied_count,
            target_count=_repair_target_count(repair_targets),
        )
    else:
        _mark_quality_repair_not_applied(
            report_data,
            reason=result.fallback_reason or "质检修复调用降级，保留原报告段落。",
        )
    return result


def _expand_report_analysis_with_llm(
    *,
    report_data: ReportData,
    state: TaskGraphState,
    llm_client: LLMClient | None,
) -> LLMCallResult | None:
    client = llm_client or LLMClient()
    fallback = {"sections": []}
    result = client.complete_json(
        system_prompt=_analysis_expansion_system_prompt(),
        user_prompt=_analysis_expansion_user_prompt(report_data=report_data, state=state),
        fallback=fallback,
        schema_name="writer_report_analysis_expansion",
        temperature=0.25,
    )
    if not result.used_fallback:
        _apply_llm_expanded_analysis(report_data, result.data)
    return result


def _analysis_expansion_system_prompt() -> str:
    return (
        "你是竞品分析报告主笔，负责把短结论扩写成可阅读的分析正文。"
        "只能基于输入的商品、证据、竞争关系、评论洞察和通用知识框架推理。"
        "通用知识只能作为分析维度，不能写成某个产品的事实。"
        "不得编造价格、销量、认证、尺寸、真实评论、排名或平台趋势。"
        "每个 item 输出 2 到 4 段中文自然段，每段 80 到 180 字，像正式咨询报告正文。"
        "必须避免内部字段、ID、token、trace、几条证据/几条判断等审计口径。"
        "顶层 JSON 必须且只能包含 sections 数组，格式为 "
        '{"sections":[{"section_id":"...","items":[{"item_key":"...","paragraphs":["..."]}]}]}。'
    )


def _analysis_expansion_user_prompt(*, report_data: ReportData, state: TaskGraphState) -> str:
    llm_sections = _llm_report_sections(report_data)
    planned_edge_ids = set(_planned_edge_ids_from_report(report_data))
    used_evidence_ids = {
        evidence_id
        for section in llm_sections
        for item in section.items[:MAX_PLANNED_REPORT_EDGES]
        for evidence_id in item.get("evidence_ids", [])
        if isinstance(evidence_id, str)
    }
    used_product_ids = _product_ids_for_edges(state, planned_edge_ids)
    payload = {
        "target_product_name": _target_product_name_from_report(report_data),
        "knowledge_artifact": _compact_knowledge_context_from_state(state),
        "extracted_user_insights": _compact_extracted_insights_from_report(report_data),
        "products": _compact_products_from_state(state, used_product_ids),
        "competition_edges": _compact_edges_from_state(state, planned_edge_ids),
        "evidence": _compact_evidences_from_state(state, used_evidence_ids),
        "sections": [_section_expansion_context(section) for section in llm_sections],
        "output_contract": {
            "allowed_section_ids": [section.section_id for section in llm_sections],
            "allowed_item_keys_by_section": {
                section.section_id: [
                    _report_item_key(item, index)
                    for index, item in enumerate(section.items[:MAX_PLANNED_REPORT_EDGES])
                ]
                for section in llm_sections
            },
            "paragraph_rules": [
                "每个 item 写 2 到 4 段。",
                "先写判断，再写原因，再写用户决策影响，最后写行动建议。",
                "证据不足处必须写成需要复核或暂无可靠数据。",
                "不要输出任何内部 ID 或字段名。",
            ],
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def _section_expansion_context(section: ReportSection) -> JsonObject:
    return {
        "section_id": section.section_id,
        "title": section.title,
        "summary": section.summary,
        "items": [
            {
                "item_key": _report_item_key(item, index),
                **_compact_report_item(item),
                "llm_paragraphs": item.get("llm_paragraphs"),
            }
            for index, item in enumerate(section.items[:MAX_PLANNED_REPORT_EDGES])
        ],
    }


def _apply_llm_expanded_analysis(report_data: ReportData, payload: JsonObject) -> None:
    sections = payload.get("sections")
    if not isinstance(sections, list):
        return

    section_by_id = {
        section.section_id: section
        for section in _ordered_report_sections(report_data)
    }
    for section_update in sections:
        if not isinstance(section_update, dict):
            continue
        section_id = section_update.get("section_id")
        if not isinstance(section_id, str) or section_id not in section_by_id:
            continue
        item_updates = section_update.get("items")
        if isinstance(item_updates, list):
            _apply_llm_expanded_items(section_by_id[section_id], item_updates)


def _apply_llm_expanded_items(section: ReportSection, item_updates: list[object]) -> None:
    item_by_key = {
        _report_item_key(report_item, index): report_item
        for index, report_item in enumerate(section.items)
    }
    for update in item_updates:
        if not isinstance(update, dict):
            continue
        item_key = update.get("item_key")
        if not isinstance(item_key, str) or item_key not in item_by_key:
            continue
        paragraphs = _clean_text_list(
            update.get("paragraphs"),
            max_items=MAX_LLM_EXPANDED_PARAGRAPHS,
            max_chars=260,
        )
        if paragraphs:
            item_by_key[item_key]["llm_expanded_analysis"] = paragraphs


def _report_quality_system_prompt() -> str:
    return (
        "你是竞品分析报告质检员，不改写报告，只检查问题并返回 JSON。"
        "重点检查四类问题：是否冗余、是否不像人话、是否出现内部字段或 ID、"
        "是否在证据不足时写得过满。"
        "只返回 JSON object，顶层字段必须是 overall_status、summary、issues。"
        "overall_status 只能是 pass 或 needs_revision；issues 最多 6 条。"
        "每条 issue 包含 issue_type、severity、section_id、item_key、location、"
        "message、suggestion；"
        "section_id 和 item_key 必须优先使用输入中的原值，无法定位 item 时 item_key 可为空。"
        "不要输出 API Key、完整 prompt、task_id、trace_id、edge_id、claim_id、evidence_id。"
    )


def _report_quality_user_prompt(*, report_data: ReportData, state: TaskGraphState) -> str:
    payload = {
        "task": {
            "category": state["task"].get("category"),
            "subcategory": state["task"].get("subcategory"),
        },
        "target_product_name": _target_product_name_from_report(report_data),
        "quality_rules": [
            "结论应短，不能长篇铺垫。",
            "段落应像产品经理能直接读懂的话。",
            "不得出现 task_id、trace、token、edge_id、claim_id、evidence_id、字段名解释。",
            "证据不足时必须保守，不能把推断写成确定事实。",
            "不要反复写“几条证据/几条判断”这类审计口径。",
        ],
        "report": [
            {
                "section_id": section.section_id,
                "title": section.title,
                "summary": section.summary,
                "risk_flags": [risk.value for risk in section.risk_flags],
                "items": [
                    {
                        "item_key": _report_item_key(item, index),
                        "llm_expanded_analysis": item.get("llm_expanded_analysis"),
                        "llm_paragraphs": item.get("llm_paragraphs"),
                        "risk_flags": item.get("risk_flags"),
                        "is_inference": item.get("is_inference"),
                    }
                    for index, item in enumerate(section.items[:MAX_PLANNED_REPORT_EDGES])
                ],
            }
            for section in _llm_report_sections(report_data)
        ],
        "output_contract": {
            "overall_status": "pass 或 needs_revision",
            "summary": "一句中文质检结论",
            "issues": (
                "最多 6 条；每条包含 issue_type、severity、section_id、item_key、"
                "location、message、suggestion"
            ),
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def _apply_llm_report_quality(*, report_data: ReportData, payload: JsonObject) -> None:
    if not report_data.evidence_quality_appendix.items:
        return

    issues = payload.get("issues")
    if not isinstance(issues, list):
        issues = []

    readable_issues: list[JsonObject] = []
    for issue in issues[:MAX_LLM_QUALITY_ISSUES]:
        if not isinstance(issue, dict):
            continue
        readable_issues.append(
            {
                "问题类型": _clean_optional_text(issue.get("issue_type"), max_chars=40),
                "严重程度": _clean_optional_text(issue.get("severity"), max_chars=20),
                "位置": _clean_optional_text(issue.get("location"), max_chars=80),
                "说明": _clean_optional_text(issue.get("message"), max_chars=160),
                "建议": _clean_optional_text(issue.get("suggestion"), max_chars=160),
            }
        )

    status = payload.get("overall_status")
    if status not in {"pass", "needs_revision"}:
        status = "needs_revision" if readable_issues else "pass"
    report_data.evidence_quality_appendix.items[0]["llm_report_quality"] = {
        "质检状态": "通过" if status == "pass" else "需要修改",
        "质检摘要": _clean_optional_text(payload.get("summary"), max_chars=160),
        "问题清单": readable_issues,
    }


def _quality_requires_revision(payload: JsonObject) -> bool:
    issues = payload.get("issues")
    return payload.get("overall_status") == "needs_revision" and isinstance(issues, list) and bool(
        issues
    )


def _quality_repair_targets(
    report_data: ReportData,
    quality_payload: JsonObject,
) -> list[JsonObject]:
    issues = quality_payload.get("issues")
    if not isinstance(issues, list):
        return []

    section_by_id = {
        section.section_id: section
        for section in _llm_report_sections(report_data)
    }
    item_keys_by_section = {
        section.section_id: {
            _report_item_key(item, index): item
            for index, item in enumerate(section.items)
        }
        for section in section_by_id.values()
    }
    targets_by_section: dict[str, JsonObject] = {}

    for issue in issues[:MAX_LLM_QUALITY_ISSUES]:
        if not isinstance(issue, dict):
            continue
        section_id, item_key = _quality_issue_location(
            issue,
            section_by_id=section_by_id,
            item_keys_by_section=item_keys_by_section,
        )
        if section_id is None:
            continue
        section = section_by_id[section_id]
        section_target = targets_by_section.setdefault(
            section_id,
            {
                "section": section,
                "section_issues": [],
                "item_keys": [],
                "item_issues": defaultdict(list),
            },
        )
        if item_key is None:
            section_target["section_issues"].append(issue)
        elif item_key not in section_target["item_keys"]:
            section_target["item_keys"].append(item_key)
        if item_key is not None:
            section_target["item_issues"][item_key].append(issue)

        if _repair_target_count(list(targets_by_section.values())) >= MAX_LLM_REPAIR_TARGETS:
            break

    return list(targets_by_section.values())


def _quality_issue_location(
    issue: JsonObject,
    *,
    section_by_id: Mapping[str, ReportSection],
    item_keys_by_section: Mapping[str, Mapping[str, JsonObject]],
) -> tuple[str | None, str | None]:
    raw_section_id = issue.get("section_id")
    section_id = raw_section_id if isinstance(raw_section_id, str) else None
    raw_item_key = issue.get("item_key")
    item_key = raw_item_key if isinstance(raw_item_key, str) else None
    location = issue.get("location")
    location_text = location if isinstance(location, str) else ""

    if section_id not in section_by_id:
        section_id = _section_id_from_location(location_text, section_by_id)
    if section_id is None:
        return None, None

    if item_key not in item_keys_by_section[section_id]:
        item_key = _item_key_from_location(location_text, item_keys_by_section[section_id])
    return section_id, item_key


def _section_id_from_location(
    location: str,
    section_by_id: Mapping[str, ReportSection],
) -> str | None:
    for section_id, section in section_by_id.items():
        if section_id in location or section.title in location:
            return section_id
    return None


def _item_key_from_location(
    location: str,
    item_by_key: Mapping[str, JsonObject],
) -> str | None:
    for item_key in item_by_key:
        if item_key in location:
            return item_key
    return None


def _quality_repair_system_prompt() -> str:
    return (
        "你是竞品分析报告二修编辑，只修复质检指出的问题段落。"
        "只能改写输入 targets 中列出的 section/item，不得新增 section、item、产品、价格、销量、"
        "认证、排名、尺寸或真实评论。证据不足必须保守表达为暂无可靠数据、建议复核或仅作方向参考。"
        "必须删除内部字段、ID、trace、token、几条证据/几条判断等审计口径。"
        "输出应更短、更像产品经理能直接读懂的话。"
        "顶层 JSON 必须且只能包含 sections 数组，格式为 "
        '{"sections":[{"section_id":"...","summary":"...","items":[{"item_key":"...",'
        '"conclusion":"...","reason":"...","action":"...","paragraphs":["..."]}]}]}。'
        "summary、conclusion、reason、action、paragraphs 都是可选字段，但只允许返回目标位置。"
    )


def _quality_repair_user_prompt(
    *,
    report_data: ReportData,
    state: TaskGraphState,
    repair_targets: Sequence[JsonObject],
) -> str:
    target_edge_ids = _edge_ids_from_repair_targets(repair_targets)
    target_evidence_ids = _evidence_ids_from_repair_targets(repair_targets)
    used_product_ids = _product_ids_for_edges(state, set(target_edge_ids))
    payload = {
        "target_product_name": _target_product_name_from_report(report_data),
        "knowledge_artifact": _compact_knowledge_context_from_state(state),
        "products": _compact_products_from_state(state, used_product_ids),
        "competition_edges": _compact_edges_from_state(state, set(target_edge_ids)),
        "evidence": _compact_evidences_from_state(state, set(target_evidence_ids)),
        "targets": [_quality_repair_target_payload(target) for target in repair_targets],
        "rules": [
            "只返回 targets 中允许的 section_id 和 item_key。",
            "如果修 summary，只写一句短结论。",
            "如果修 item，优先返回 paragraphs；也可以返回 conclusion、reason、action 三个短句。",
            "paragraphs 最多 3 段，每段 60 到 160 字。",
            "不要出现 task_id、trace、token、edge_id、claim_id、evidence_id、字段名解释。",
            "不要写“几条证据/几条判断”，不要把证据不足写成确定事实。",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _quality_repair_target_payload(target: JsonObject) -> JsonObject:
    section = target["section"]
    item_keys = set(target["item_keys"])
    item_issues = target["item_issues"]
    return {
        "section_id": section.section_id,
        "title": section.title,
        "current_summary": section.summary,
        "section_issues": [
            _compact_quality_issue(issue) for issue in target["section_issues"]
        ],
        "allowed_item_keys": list(item_keys),
        "items": [
            {
                "item_key": _report_item_key(item, index),
                **_compact_report_item(item),
                "llm_paragraphs": item.get("llm_paragraphs"),
                "llm_expanded_analysis": item.get("llm_expanded_analysis"),
                "quality_issues": [
                    _compact_quality_issue(issue)
                    for issue in item_issues.get(_report_item_key(item, index), [])
                ],
            }
            for index, item in enumerate(section.items)
            if _report_item_key(item, index) in item_keys
        ],
    }


def _compact_quality_issue(issue: JsonObject) -> JsonObject:
    return {
        "issue_type": _clean_optional_text(issue.get("issue_type"), max_chars=40),
        "severity": _clean_optional_text(issue.get("severity"), max_chars=20),
        "location": _clean_optional_text(issue.get("location"), max_chars=100),
        "message": _clean_optional_text(issue.get("message"), max_chars=160),
        "suggestion": _clean_optional_text(issue.get("suggestion"), max_chars=160),
    }


def _apply_llm_quality_repair(
    report_data: ReportData,
    payload: JsonObject,
    repair_targets: Sequence[JsonObject],
) -> int:
    sections = payload.get("sections")
    if not isinstance(sections, list):
        return 0

    target_item_keys_by_section = {
        target["section"].section_id: set(target["item_keys"])
        for target in repair_targets
    }
    target_section_ids = set(target_item_keys_by_section)
    section_by_id = {
        section.section_id: section
        for section in _llm_report_sections(report_data)
        if section.section_id in target_section_ids
    }
    applied_count = 0
    for section_update in sections:
        if not isinstance(section_update, dict):
            continue
        section_id = section_update.get("section_id")
        if not isinstance(section_id, str) or section_id not in section_by_id:
            continue
        section = section_by_id[section_id]
        summary = section_update.get("summary")
        if isinstance(summary, str) and summary.strip():
            section.summary = _clean_llm_report_text(summary, max_chars=140)
            applied_count += 1

        item_updates = section_update.get("items")
        if isinstance(item_updates, list):
            applied_count += _apply_llm_quality_repair_items(
                section,
                item_updates,
                target_item_keys_by_section[section_id],
            )
    return applied_count


def _apply_llm_quality_repair_items(
    section: ReportSection,
    item_updates: Sequence[object],
    allowed_item_keys: set[str],
) -> int:
    item_by_key = {
        _report_item_key(report_item, index): report_item
        for index, report_item in enumerate(section.items)
        if _report_item_key(report_item, index) in allowed_item_keys
    }
    applied_count = 0
    for update in item_updates:
        if not isinstance(update, dict):
            continue
        item_key = update.get("item_key")
        if not isinstance(item_key, str) or item_key not in item_by_key:
            continue
        target_item = item_by_key[item_key]

        paragraphs = _clean_text_list(
            update.get("paragraphs"),
            max_items=MAX_LLM_EXPANDED_PARAGRAPHS,
            max_chars=240,
        )
        if paragraphs:
            target_item["llm_expanded_analysis"] = paragraphs
            applied_count += 1

        short_paragraphs: JsonObject = {}
        for field in ("conclusion", "reason", "action"):
            value = update.get(field)
            if isinstance(value, str) and value.strip():
                short_paragraphs[field] = _clean_llm_report_text(value, max_chars=110)
        if short_paragraphs:
            target_item["llm_paragraphs"] = short_paragraphs
            applied_count += 1
    return applied_count


def _mark_quality_repair_applied(
    report_data: ReportData,
    *,
    applied_count: int,
    target_count: int,
) -> None:
    if not report_data.evidence_quality_appendix.items:
        return
    quality = report_data.evidence_quality_appendix.items[0].setdefault(
        "llm_report_quality",
        {},
    )
    if isinstance(quality, dict):
        if applied_count:
            quality["质检状态"] = "已自动修正"
        quality["自动修正"] = {
            "状态": "已修正" if applied_count else "未应用",
            "目标段落数": target_count,
            "应用修改数": applied_count,
            "说明": "质检发现问题后，Writer 已对定位到的问题段落执行一次自动修正。",
        }


def _mark_quality_repair_not_applied(report_data: ReportData, *, reason: str) -> None:
    if not report_data.evidence_quality_appendix.items:
        return
    quality = report_data.evidence_quality_appendix.items[0].setdefault(
        "llm_report_quality",
        {},
    )
    if isinstance(quality, dict):
        quality["自动修正"] = {
            "状态": "未触发",
            "目标段落数": 0,
            "应用修改数": 0,
            "说明": reason,
        }


def _repair_target_count(repair_targets: Sequence[JsonObject]) -> int:
    return sum(len(target.get("item_keys", [])) or 1 for target in repair_targets)


def _edge_ids_from_repair_targets(repair_targets: Sequence[JsonObject]) -> list[str]:
    edge_ids: list[str] = []
    for target in repair_targets:
        section = target["section"]
        item_keys = set(target.get("item_keys", []))
        for index, item in enumerate(section.items):
            if _report_item_key(item, index) not in item_keys:
                continue
            edge_id = item.get("edge_id") or item.get("basis_edge_id")
            if isinstance(edge_id, str):
                edge_ids.append(edge_id)
            item_edge_ids = item.get("edge_ids")
            if isinstance(item_edge_ids, list):
                edge_ids.extend(value for value in item_edge_ids if isinstance(value, str))
    return _dedupe(edge_ids)


def _evidence_ids_from_repair_targets(repair_targets: Sequence[JsonObject]) -> list[str]:
    evidence_ids: list[str] = []
    for target in repair_targets:
        section = target["section"]
        item_keys = set(target.get("item_keys", []))
        evidence_ids.extend(section.evidence_ids)
        for index, item in enumerate(section.items):
            if _report_item_key(item, index) not in item_keys:
                continue
            item_evidence_ids = item.get("evidence_ids")
            if isinstance(item_evidence_ids, list):
                evidence_ids.extend(value for value in item_evidence_ids if isinstance(value, str))
            claims = item.get("claims")
            if isinstance(claims, list):
                for claim in claims:
                    if isinstance(claim, dict) and isinstance(claim.get("evidence_ids"), list):
                        evidence_ids.extend(
                            value for value in claim["evidence_ids"] if isinstance(value, str)
                        )
    return _dedupe(evidence_ids)


def _section_llm_configs() -> list[SectionLLMConfig]:
    return [
        SectionLLMConfig(
            label="conclusion",
            schema_name="writer_report_conclusion_generation",
            section_ids=("conclusion_summary",),
            objective="总体判断只输出 3 条核心结论，让用户先知道最重要的竞争压力和优先动作。",
            rules=(
                "summary 只写一句总判断。",
                "items 最多输出 3 个核心结论。",
                "每个 item 的 conclusion 必须是明确判断，reason 只解释为什么重要。",
                "action 必须告诉用户下一步先看什么或先补什么。",
            ),
            max_items=3,
        ),
        SectionLLMConfig(
            label="core_competitor",
            schema_name="writer_report_core_competitor_generation",
            section_ids=("core_competitor_analysis",),
            objective="核心竞品章节重点讲为什么它会被用户拿来比较，而不是罗列字段。",
            rules=(
                "summary 只概括核心竞品压力。",
                "conclusion 说明它为什么是竞品。",
                "reason 围绕同一需求、同一价格心智、同一使用场景解释。",
                "action 说明目标产品该如何回应这个竞品。",
            ),
            max_items=MAX_PLANNED_REPORT_EDGES,
        ),
        SectionLLMConfig(
            label="competitive_slice",
            schema_name="writer_report_competitive_slice_generation",
            section_ids=("competitive_landscape_judgment", "user_decision_chain_analysis"),
            objective="竞争切片章节重点讲用户在什么价格、人群、场景或决策阶段会比较。",
            rules=(
                "summary 说明当前切片或决策阶段的比较逻辑。",
                "conclusion 说明用户在哪个场景会把这些产品放在一起看。",
                "reason 解释场景、人群、价格带或决策阶段如何影响选择。",
                "action 给出该切片下应该强化的信息表达或证据动作。",
            ),
            max_items=MAX_PLANNED_REPORT_EDGES,
        ),
        SectionLLMConfig(
            label="action",
            schema_name="writer_report_action_recommendation_generation",
            section_ids=("product_strategy_recommendations",),
            objective="行动建议章节必须输出可执行动作，避免空泛策略词。",
            rules=(
                "summary 只写最优先的行动方向。",
                "conclusion 必须是一个可以落地的动作。",
                "reason 说明这个动作解决哪个竞争或转化问题。",
                "action 必须包含负责方向、执行对象或复核对象。",
            ),
            max_items=3,
        ),
    ]


def _sections_for_config(
    report_data: ReportData,
    config: SectionLLMConfig,
) -> list[ReportSection]:
    section_id_set = set(config.section_ids)
    return [
        section
        for section in _ordered_report_sections(report_data)
        if section.section_id in section_id_set
    ]


def _writer_llm_system_prompt(config: SectionLLMConfig) -> str:
    return (
        f"你是竞品分析报告编辑，当前只负责“{config.label}”章节组。"
        f"写作目标：{config.objective}"
        "必须遵守：只能使用输入材料；不得编造价格、销量、认证、尺寸、排名；"
        "证据不足时写“暂无可靠数据”或“建议复核”；推断必须明确保守；"
        "每个章节摘要只写 1 句；每个分析项只写 conclusion、reason、action 三个短句；"
        "顶层 JSON 必须且只能包含 sections 数组，格式为 "
        '{"sections":[{"section_id":"...","summary":"...","items":[{"item_key":"...",'
        '"conclusion":"...","reason":"...","action":"..."}]}]}；'
        "不要输出内部 ID、字段名、token、trace、QA 字段名或“几条证据/几条判断”的审计口径；"
        "不要逐条罗列切片、关系或证据编号；不要重复“证据说明”“本报告基于”等套话；"
        "优先写用户能直接理解的结论、原因和下一步动作。不得输出 Markdown；只输出 JSON object。"
    )


def _writer_llm_user_prompt(
    *,
    report_data: ReportData,
    state: TaskGraphState,
    config: SectionLLMConfig,
    sections: Sequence[ReportSection],
) -> str:
    planned_edge_ids = set(_planned_edge_ids_from_sections(sections))
    used_evidence_ids = {
        evidence_id
        for section in sections
        for item in section.items[: config.max_items]
        for evidence_id in item.get("evidence_ids", [])
        if isinstance(evidence_id, str)
    }
    used_product_ids = _product_ids_for_edges(state, planned_edge_ids)
    payload = {
        "task": {
            "category": state["task"].get("category"),
            "subcategory": state["task"].get("subcategory"),
            "data_source_mode": state["task"].get("data_source_mode"),
        },
        "target_product_name": _target_product_name_from_report(report_data),
        "chapter_group": {
            "label": config.label,
            "objective": config.objective,
            "section_ids": list(config.section_ids),
        },
        "report_plan": {
            "planned_edge_ids": list(planned_edge_ids),
            "max_focus_items": config.max_items,
            "planning_rule": "只围绕当前章节组的重点关系和切片写，不展开全部关系。",
        },
        "output_contract": {
            "top_level": "只返回一个 JSON object，且只包含 sections 字段。",
            "sections": "数组；每个元素必须包含 section_id、summary、items。",
            "items": "数组；每个元素必须包含 item_key、conclusion、reason、action。",
            "allowed_section_ids": [section.section_id for section in sections],
            "allowed_item_keys_by_section": {
                section.section_id: [
                    _report_item_key(item, index)
                    for index, item in enumerate(section.items[: config.max_items])
                ]
                for section in sections
            },
        },
        "rules": [
            *config.rules,
            "section_id 必须来自 allowed_section_ids。",
            "item_key 必须来自对应 section 的输入 items。",
            "summary 必须是中文短结论，1 句，不要列内部 ID。",
            "conclusion、reason、action 都必须是中文短句，每句尽量不超过 60 字。",
            "不要写“依据几条判断/几条证据”，不要暴露 edge_id、claim_id、evidence_id、task_id。",
            "不要把所有 item 逐项复述，只写当前 item 最重要判断。",
            "不要新增输入中不存在的事实。",
            "保留证据不足、暂无可靠数据、建议复核等保守表达。",
        ],
        "products": _compact_products_from_state(state, used_product_ids),
        "competition_edges": _compact_edges_from_state(state, planned_edge_ids),
        "evidence": _compact_evidences_from_state(state, used_evidence_ids),
        "extracted_user_insights": _compact_extracted_insights_from_report(report_data),
        "knowledge_artifact": _compact_knowledge_context_from_state(state),
        "sections": [
            _section_llm_context(section, max_items=config.max_items)
            for section in sections
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _section_llm_context(section: ReportSection, *, max_items: int) -> JsonObject:
    return {
        "section_id": section.section_id,
        "title": section.title,
        "current_summary": section.summary,
        "claim_count": len(section.claim_ids),
        "evidence_count": len(section.evidence_ids),
        "risk_flags": [risk.value for risk in section.risk_flags],
        "items": [
            {
                "item_key": _report_item_key(item, index),
                **_compact_report_item(item),
            }
            for index, item in enumerate(section.items[:max_items])
        ],
    }


def _compact_report_item(item: JsonObject) -> JsonObject:
    compact: JsonObject = {}
    for key in (
        "competition_type",
        "judgment_strength",
        "decision_stage",
        "decision_stages",
        "price_band",
        "persona",
        "scenario",
        "top_edge_score",
        "recommendation",
        "priority",
        "responsibility_type",
        "is_inference",
        "risk_flags",
        "review_task_count",
        "revision_message_count",
        "appendix_type",
    ):
        if key in item:
            compact[key] = item[key]
    if isinstance(item.get("competitor"), dict):
        competitor = item["competitor"]
        compact["competitor"] = {
            "name": competitor.get("name"),
            "brand": competitor.get("brand"),
            "role": competitor.get("role"),
        }
    if isinstance(item.get("product"), dict):
        product = item["product"]
        compact["product"] = {
            "name": product.get("name"),
            "brand": product.get("brand"),
            "role": product.get("role"),
        }
    if isinstance(item.get("claims"), list):
        compact["claims"] = [
            {
                "content": claim.get("content"),
                "confidence": claim.get("confidence"),
                "status": claim.get("status"),
                "is_inference": claim.get("is_inference"),
                "risk_flags": claim.get("risk_flags"),
            }
            for claim in item["claims"][:2]
            if isinstance(claim, dict)
        ]
    return compact


def _apply_llm_report_sections(report_data: ReportData, payload: JsonObject) -> None:
    sections = payload.get("sections")
    if not isinstance(sections, list):
        return

    section_by_id = {
        section.section_id: section
        for section in _ordered_report_sections(report_data)
    }
    for item in sections:
        if not isinstance(item, dict):
            continue
        section_id = item.get("section_id")
        summary = item.get("summary")
        if not isinstance(section_id, str) or section_id not in section_by_id:
            continue
        if not isinstance(summary, str) or not summary.strip():
            summary = None
        if summary:
            section_by_id[section_id].summary = _clean_llm_report_text(summary, max_chars=160)

        item_updates = item.get("items")
        if isinstance(item_updates, list):
            _apply_llm_item_paragraphs(section_by_id[section_id], item_updates)


def _apply_llm_item_paragraphs(section: ReportSection, item_updates: list[object]) -> None:
    item_by_key = {
        _report_item_key(report_item, index): report_item
        for index, report_item in enumerate(section.items)
    }
    for update in item_updates:
        if not isinstance(update, dict):
            continue
        item_key = update.get("item_key")
        if not isinstance(item_key, str) or item_key not in item_by_key:
            continue
        paragraphs: JsonObject = {}
        for field in ("conclusion", "reason", "action"):
            value = update.get(field)
            if isinstance(value, str) and value.strip():
                paragraphs[field] = _clean_llm_report_text(value, max_chars=120)
        if paragraphs:
            item_by_key[item_key]["llm_paragraphs"] = paragraphs


def _clean_llm_report_text(value: str, *, max_chars: int) -> str:
    text = " ".join(value.strip().split())
    text = text.replace("```json", "").replace("```", "").strip()
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 1].rstrip()}…"


def _clean_optional_text(value: object, *, max_chars: int) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    return _clean_llm_report_text(value, max_chars=max_chars)


def _clean_text_list(value: object, *, max_items: int, max_chars: int) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    for item in value:
        text = _clean_optional_text(item, max_chars=max_chars)
        if text:
            cleaned.append(text)
        if len(cleaned) >= max_items:
            break
    return cleaned


def _llm_rewrite_fallback(
    sections: Sequence[ReportSection],
    config: SectionLLMConfig,
) -> JsonObject:
    return {
        "sections": [
            {
                "section_id": section.section_id,
                "summary": section.summary,
                "items": [
                    {
                        "item_key": _report_item_key(item, index),
                        "conclusion": "",
                        "reason": "",
                        "action": "",
                    }
                    for index, item in enumerate(section.items[: config.max_items])
                ],
            }
            for section in sections
        ]
    }


def _llm_rewrite_batch_metadata(results: Sequence[tuple[str, LLMCallResult]]) -> JsonObject:
    if not results:
        return {"status": "not_run", "stages": []}

    stages = [
        {
            "label": label,
            "schema_name": _schema_name_for_stage(label),
            **_llm_rewrite_metadata(result),
        }
        for label, result in results
    ]
    applied_count = sum(1 for _, result in results if not result.used_fallback)
    fallback_count = len(results) - applied_count
    token_usage = {
        "model_name": results[-1][1].token_usage.model_name,
        "prompt_tokens": sum(result.token_usage.prompt_tokens for _, result in results),
        "completion_tokens": sum(result.token_usage.completion_tokens for _, result in results),
        "total_tokens": sum(result.token_usage.total_tokens for _, result in results),
    }
    return {
        "status": "applied" if applied_count else "fallback",
        "attempts": sum(result.attempts for _, result in results),
        "fallback_reason": (
            results[-1][1].fallback_reason if applied_count == 0 else None
        ),
        "error_count": sum(len(result.errors) for _, result in results),
        "token_usage": token_usage,
        "stage_count": len(results),
        "applied_stage_count": applied_count,
        "fallback_stage_count": fallback_count,
        "stages": stages,
    }


def _schema_name_for_stage(label: str) -> str:
    for config in _section_llm_configs():
        if config.label == label:
            return config.schema_name
    return label


def _llm_rewrite_metadata(result: LLMCallResult) -> JsonObject:
    return {
        "status": "fallback" if result.used_fallback else "applied",
        "attempts": result.attempts,
        "fallback_reason": result.fallback_reason,
        "error_count": len(result.errors),
        "token_usage": result.token_metadata,
    }


def _ordered_report_sections(report_data: ReportData) -> list[ReportSection]:
    sections: list[ReportSection] = []
    for section_id in report_data.section_order:
        section = getattr(report_data, section_id, None)
        if isinstance(section, ReportSection):
            sections.append(section)
    return sections


def _llm_report_sections(report_data: ReportData) -> list[ReportSection]:
    llm_section_ids = {
        "conclusion_summary",
        "competitive_landscape_judgment",
        "core_competitor_analysis",
        "user_decision_chain_analysis",
        "product_strategy_recommendations",
    }
    return [
        section
        for section in _ordered_report_sections(report_data)
        if section.section_id in llm_section_ids
    ]


def _report_focus_items(report_data: ReportData) -> list[JsonObject]:
    items: list[JsonObject] = []
    for section in _llm_report_sections(report_data):
        items.extend(
            item
            for item in section.items[:MAX_PLANNED_REPORT_EDGES]
            if isinstance(item, dict)
        )
    return items


def _compact_knowledge_context_from_state(state: TaskGraphState) -> JsonObject:
    return compact_knowledge_for_llm(state.get("knowledge_artifacts", []), max_items=8)


def _target_product_name_from_report(report_data: ReportData) -> str:
    profile_items = report_data.target_opportunities_and_risks.items
    for item in profile_items:
        product = item.get("product")
        if isinstance(product, dict) and isinstance(product.get("name"), str):
            return product["name"]
    return "目标产品"


def _planned_edge_ids_from_report(report_data: ReportData) -> list[str]:
    edge_ids: list[str] = []
    for section in _ordered_report_sections(report_data):
        edge_ids.extend(_planned_edge_ids_from_section(section))
    return _dedupe(edge_ids)


def _planned_edge_ids_from_sections(sections: Sequence[ReportSection]) -> list[str]:
    edge_ids: list[str] = []
    for section in sections:
        edge_ids.extend(_planned_edge_ids_from_section(section))
    return _dedupe(edge_ids)


def _planned_edge_ids_from_section(section: ReportSection) -> list[str]:
    edge_ids: list[str] = []
    for item in section.items:
        edge_id = item.get("edge_id") or item.get("basis_edge_id")
        if isinstance(edge_id, str):
            edge_ids.append(edge_id)
        item_edge_ids = item.get("edge_ids")
        if isinstance(item_edge_ids, list):
            edge_ids.extend(value for value in item_edge_ids if isinstance(value, str))
    return _dedupe(edge_ids)


def _report_item_key(item: JsonObject, index: int) -> str:
    for key in ("edge_id", "basis_edge_id", "recommendation_id"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return value

    edge_ids = item.get("edge_ids")
    if isinstance(edge_ids, list) and edge_ids:
        joined_edge_ids = "_".join(str(edge_id) for edge_id in edge_ids if isinstance(edge_id, str))
        if joined_edge_ids:
            return f"edges_{joined_edge_ids}"

    if all(isinstance(item.get(key), str) for key in ("price_band", "persona", "scenario")):
        return f"slice_{item['price_band']}_{item['persona']}_{item['scenario']}"

    decision_stage = item.get("decision_stage")
    if isinstance(decision_stage, str) and decision_stage:
        return f"decision_stage_{decision_stage}"

    appendix_type = item.get("appendix_type")
    if isinstance(appendix_type, str) and appendix_type:
        return f"appendix_{appendix_type}"

    return f"item_{index + 1}"


def _product_ids_for_edges(state: TaskGraphState, edge_ids: set[str]) -> set[str]:
    products = [Product.model_validate(item) for item in state["products"]]
    target_product_ids = {
        product.product_id
        for product in products
        if product.role == ProductRole.TARGET
    }
    edge_product_ids = {
        edge.competitor_product_id
        for edge in [CompetitionEdge.model_validate(item) for item in state["competition_edges"]]
        if edge.edge_id in edge_ids
    }
    return target_product_ids | edge_product_ids


def _compact_products_from_state(state: TaskGraphState, product_ids: set[str]) -> list[JsonObject]:
    products = [Product.model_validate(item) for item in state["products"]]
    return [
        {
            "product_id": product.product_id,
            "name": product.name,
            "brand": product.brand,
            "role": product.role.value,
        }
        for product in products
        if product.product_id in product_ids
    ]


def _compact_edges_from_state(state: TaskGraphState, edge_ids: set[str]) -> list[JsonObject]:
    edges = [CompetitionEdge.model_validate(item) for item in state["competition_edges"]]
    return [
        {
            "edge_id": edge.edge_id,
            "competitor_product_id": edge.competitor_product_id,
            "competition_type": edge.competition_type.value,
            "edge_score": edge.edge_score,
            "slice": edge.slice.model_dump(mode="json"),
            "decision_stages": [stage.value for stage in edge.decision_stages],
            "claim_ids": edge.claim_ids,
        }
        for edge in edges
        if edge.edge_id in edge_ids
    ]


def _compact_evidences_from_state(
    state: TaskGraphState,
    evidence_ids: set[str],
) -> list[JsonObject]:
    evidences = [Evidence.model_validate(item) for item in state["evidences"]]
    return [
        {
            "evidence_id": evidence.evidence_id,
            "product_id": evidence.product_id,
            "source_type": evidence.source_type.value,
            "confidence_level": evidence.confidence_level.value,
            "content_summary": evidence.content_summary,
            "limitations": evidence.limitations,
            "access_time": evidence.access_time.isoformat() if evidence.access_time else None,
            "risk_flags": _string_items(evidence.metadata.get("risk_flags")),
            "missing_fields": _string_items(evidence.metadata.get("missing_fields")),
        }
        for evidence in evidences
        if evidence.evidence_id in evidence_ids
    ]


def _executive_summary_section(
    *,
    target_product: Product,
    edges: Sequence[CompetitionEdge],
    total_edge_count: int,
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
            "judgment_strength": _judgment_strength_for_edge(edge, claims_by_id).value,
            "claim_ids": edge.claim_ids,
            "evidence_ids": _evidence_ids_for_claims(edge.claim_ids, claims_by_id),
            "risk_flags": _risk_values(_edge_and_claim_risks(edge, claims_by_id)),
        }
        for edge in top_edges
    ]
    return _section(
        "conclusion_summary",
        "结论摘要",
        (
            f"{target_product.name} 的报告从 {total_edge_count} 条竞争关系中"
            f"筛出 {len(edges)} 条重点关系，结论先点出 {len(top_edges)} 条最高优先级关系。"
        ),
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
        "target_opportunities_and_risks",
        "目标产品机会与风险",
        "整理目标产品的机会、限制和需要优先复核的风险。",
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
                "judgment_strength": _judgment_strength_for_edge(edge, claims_by_id).value,
                "claims": [_claim_reference(claim) for claim in edge_claims],
                "evidence_ids": edge_evidence_ids,
                "risk_flags": _risk_values(_edge_and_claim_risks(edge, claims_by_id)),
            }
        )
    return _section(
        "core_competitor_analysis",
        "核心竞品拆解",
        "拆解核心竞品关系，关键判断均保留证据和判断强度。",
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
        "competitive_landscape_judgment",
        "竞争格局判断",
        "聚合价格带、人群和使用场景切片下的竞争格局。",
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
        "user_decision_chain_analysis",
        "用户决策链分析",
        "按购买决策阶段组织竞争关系和用户信号。",
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
                "priority": _recommendation_priority(edge).value,
                "responsibility_type": ResponsibilityType.CONTENT_EXPRESSION.value,
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
                "priority": ActionPriority.P2.value,
                "responsibility_type": ResponsibilityType.EVIDENCE_RESEARCH.value,
                "basis_edge_id": None,
                "claim_ids": [],
                "evidence_ids": [],
                "is_inference": True,
            }
        )
    return _section(
        "product_strategy_recommendations",
        "产品策略建议",
        "基于已生成竞争关系提出策略建议，不补写新的事实字段。",
        items,
        claim_ids=_dedupe(claim_ids),
        evidence_ids=_dedupe(evidence_ids),
    )


def _evidence_quality_appendix_section(
    *,
    claims: Sequence[Claim],
    evidences: Sequence[Evidence],
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
        },
        {
            "appendix_type": "evidence_index",
            "items": _evidence_index_items(evidences),
        },
    ]
    return _section(
        "evidence_quality_appendix",
        "证据与质检附录",
        "记录证据索引、QA 通过状态、打回处理和仍需标明的风险。",
        items,
        claim_ids=[claim.claim_id for claim in risk_claims],
        evidence_ids=_dedupe(
            [
                *[evidence_id for claim in risk_claims for evidence_id in claim.evidence_ids],
                *[evidence.evidence_id for evidence in evidences],
            ]
        ),
        risk_flags=_dedupe(risk for claim in risk_claims for risk in claim.risk_flags),
    )


def _evidence_index_section(evidences: Sequence[Evidence]) -> ReportSection:
    items = _evidence_index_items(evidences)
    return _section(
        "evidence_index",
        "Evidence 索引",
        "列出报告中可追溯的证据来源、访问时间、截图和局限性。",
        items,
        evidence_ids=[evidence.evidence_id for evidence in evidences],
    )


def _evidence_index_items(evidences: Sequence[Evidence]) -> list[JsonObject]:
    return [
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


def _analysis_process_appendix_section(
    *,
    state: TaskGraphState,
    review_insights: Sequence[ReviewInsight],
) -> ReportSection:
    items = [
        {
            "appendix_type": "workflow",
            "workflow": state["metadata"].get("workflow", {}),
            "agent_count": len(state["run_logs"]),
            "revision_message_count": len(state["agent_messages"]),
        },
        {
            "appendix_type": "user_research",
            "items": _user_research_section(review_insights).items,
        },
    ]
    return _section(
        "analysis_process_appendix",
        "分析流程与系统能力附录",
        "记录本次分析流程、Agent 运行概况和用户研究信号来源。",
        items,
        evidence_ids=_dedupe(
            evidence_id for insight in review_insights for evidence_id in insight.evidence_ids
        ),
        risk_flags=_dedupe(risk for insight in review_insights for risk in insight.risk_flags),
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


def _judgment_strength_for_edge(
    edge: CompetitionEdge,
    claims_by_id: dict[str, Claim],
) -> JudgmentStrength:
    edge_claims = [
        claims_by_id[claim_id] for claim_id in edge.claim_ids if claim_id in claims_by_id
    ]
    if not edge_claims:
        return JudgmentStrength.HYPOTHESIS
    if edge.risk_flags or any(claim.risk_flags for claim in edge_claims):
        return JudgmentStrength.HYPOTHESIS
    average_confidence = sum(claim.confidence for claim in edge_claims) / len(edge_claims)
    if average_confidence >= 0.75:
        return JudgmentStrength.CLEAR
    if average_confidence >= 0.55:
        return JudgmentStrength.DIRECTIONAL
    return JudgmentStrength.HYPOTHESIS


def _recommendation_priority(edge: CompetitionEdge) -> ActionPriority:
    if edge.edge_score >= 0.80:
        return ActionPriority.P0
    if edge.edge_score >= 0.60:
        return ActionPriority.P1
    return ActionPriority.P2


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


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


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
