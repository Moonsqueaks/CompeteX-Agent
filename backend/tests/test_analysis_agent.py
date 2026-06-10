from datetime import UTC, datetime

from app.agents import analysis_agent_node, collection_agent_node, qa_agent_node
from app.graph import append_evidence, append_product, create_initial_state
from app.schemas import AnalysisTask, Evidence, Product

NOW = datetime(2026, 5, 24, 2, 0, tzinfo=UTC)


def _task(task_id: str = "task_analysis_agent") -> AnalysisTask:
    return AnalysisTask(
        task_id=task_id,
        target_product_name="Demo automatic litter box",
        target_product_url="https://example.com/products/target",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        data_source_mode="demo_snapshot",
        status="created",
        research_text=None,
        created_at=NOW,
        updated_at=NOW,
        metadata={"demo": True},
    )


def _internet_task(task_id: str = "task_analysis_internet") -> AnalysisTask:
    return AnalysisTask(
        task_id=task_id,
        target_product_name="豆包",
        target_product_url="https://www.doubao.com/chat/",
        category="互联网产品",
        subcategory="AI 助手",
        data_source_mode="builtin_candidates",
        status="created",
        research_text=None,
        created_at=NOW,
        updated_at=NOW,
        metadata={
            "domain_key": "internet_ai_assistant",
            "selected_target_product_id": "doubao",
            "selected_target_sku_id": "ip_doubao",
            "target_selection": "matched_candidate_pool",
            "candidate_discovery_mode": "builtin_candidates",
            "candidate_pool_id": "internet_ai_assistant_v1",
            "candidate_pool_path": "data/snapshots/internet_ai_assistant_snapshot.json",
            "candidate_pool_loaded": True,
            "candidate_source_type": "builtin_candidate_pool",
            "candidate_count": 4,
            "selected_for_analysis_count": 4,
        },
    )


def _state_after_collection() -> dict:
    state = create_initial_state(_task())
    collection_agent_node(state, now=NOW)
    return state


def _internet_state_after_collection() -> dict:
    state = create_initial_state(_internet_task())
    collection_agent_node(state, now=NOW)
    return state


def test_analysis_agent_generates_target_profile_artifacts() -> None:
    state = _state_after_collection()

    analysis_agent_node(state, now=NOW)

    target = next(product for product in state["products"] if product["role"] == "target")
    assert len(state["feature_trees"]) == 1
    assert len(state["pricing_models"]) == 1
    assert len(state["user_personas"]) == 1
    assert state["feature_trees"][0]["product_id"] == target["product_id"]
    assert state["pricing_models"][0]["price_band"] == "1500-2000"
    assert state["pricing_models"][0]["final_price"] == 1599
    assert state["user_personas"][0]["is_inference"] is True
    assert state["user_personas"][0]["evidence_ids"] == target["evidence_ids"]


def test_analysis_agent_recalls_direct_and_alternative_competitors() -> None:
    state = _state_after_collection()

    analysis_agent_node(state, now=NOW)

    edge_types = {edge["competition_type"] for edge in state["competition_edges"]}
    competitor_ids = {edge["competitor_product_id"] for edge in state["competition_edges"]}
    assert "direct" in edge_types
    assert "alternative" in edge_types
    assert "channel" in edge_types
    assert len(state["competition_edges"]) == 13
    assert "prod_sku_01" in competitor_ids
    assert "prod_sku_11" in competitor_ids


def test_analysis_agent_generates_internet_ai_assistant_competition_edges() -> None:
    state = _internet_state_after_collection()

    analysis_agent_node(state, now=NOW)

    competitor_ids = {edge["competitor_product_id"] for edge in state["competition_edges"]}
    slice_scenarios = {edge["slice"]["scenario"] for edge in state["competition_edges"]}
    slice_personas = {edge["slice"]["persona"] for edge in state["competition_edges"]}
    explanations = state["metadata"]["analysis_agent"]["edge_explanations"]
    claim_by_id = {claim["claim_id"]: claim for claim in state["claims"]}

    assert competitor_ids == {"kimi", "deepseek", "qianwen", "yuanbao"}
    assert len(state["competition_edges"]) == 4
    assert len(state["claims"]) == 4
    assert state["pricing_models"][0]["price_band"] == "暂无可靠数据"
    assert any(
        scenario in slice_scenarios
        for scenario in {"长文档研究", "编程推理", "内容创作", "办公协作"}
    )
    assert any(
        persona in slice_personas
        for persona in {"知识工作者", "内容创作者", "开发者", "企业团队"}
    )
    for edge in state["competition_edges"]:
        assert edge["competition_type"] == "direct"
        assert edge["claim_ids"]
        assert edge["slice"]["price_band"]
        assert "自动清理" not in edge["slice"]["scenario"]
        assert edge["edge_id"] in explanations
        assert (
            explanations[edge["edge_id"]]["context_match"]["signals"]["scenario"]
            == edge["slice"]["scenario"]
        )
        for claim_id in edge["claim_ids"]:
            claim = claim_by_id[claim_id]
            assert claim["is_inference"] is True
            assert claim["evidence_ids"] or claim["risk_flags"]

    assert state["strategy_briefs"][0]["category_tensions"][0].startswith("能力覆盖与证据边界")
    assert len(state["competitor_battlecards"]) == 4
    assert all("AI 助手" in item["why_users_compare"] for item in state["competitor_battlecards"])
    assert {"能力覆盖差距", "商业模式/付费层差距"}.issubset(
        {item["dimension"] for item in state["gap_matrix_items"]}
    )


def test_analysis_edges_include_slice_decision_stages_and_scoring_explanations() -> None:
    state = _state_after_collection()

    analysis_agent_node(state, now=NOW)

    explanations = state["metadata"]["analysis_agent"]["edge_explanations"]
    for edge in state["competition_edges"]:
        assert edge["slice"]["price_band"]
        assert edge["slice"]["persona"]
        assert edge["slice"]["scenario"]
        assert edge["decision_stages"]
        assert edge["score_breakdown"]["demand_substitutability"] >= 0
        assert edge["edge_id"] in explanations
        assert "demand_substitutability" in explanations[edge["edge_id"]]


def test_analysis_agent_generates_strategy_brief_and_battlecards() -> None:
    state = _state_after_collection()

    analysis_agent_node(state, now=NOW)

    assert len(state["strategy_briefs"]) == 1
    strategy_brief = state["strategy_briefs"][0]
    assert strategy_brief["business_question"]
    assert strategy_brief["target_segment"]
    assert strategy_brief["primary_competition_axis"]
    assert strategy_brief["decision_owner_view"]
    assert strategy_brief["evidence_boundary"]
    assert strategy_brief["is_inference"] is True
    assert strategy_brief["claim_ids"]
    assert strategy_brief["evidence_ids"]

    assert 1 <= len(state["competitor_battlecards"]) <= 5
    for battlecard in state["competitor_battlecards"]:
        assert battlecard["competitor_id"]
        assert battlecard["why_users_compare"]
        assert battlecard["competitor_strengths"]
        assert battlecard["target_response"]
        assert battlecard["sales_objection"]
        assert battlecard["response_talk_track"]
        assert battlecard["priority"]
        assert battlecard["claim_ids"]
        assert battlecard["evidence_ids"]
        assert battlecard["is_inference"] is True


def test_analysis_agent_generates_gap_matrix_and_opportunity_map() -> None:
    state = _state_after_collection()

    analysis_agent_node(state, now=NOW)

    dimensions = {item["dimension"] for item in state["gap_matrix_items"]}
    assert len(state["gap_matrix_items"]) >= 2
    assert {"功能能力差距", "证据差距"}.issubset(dimensions)
    for gap in state["gap_matrix_items"]:
        assert gap["target_status"]
        assert gap["competitor_reference"]
        assert gap["impact_on_decision"]
        assert gap["recommendation"]
        assert gap["claim_ids"]
        assert gap["evidence_ids"]
        assert gap["is_inference"] is True

    assert len(state["opportunity_items"]) >= 3
    for opportunity in state["opportunity_items"]:
        assert opportunity["title"]
        assert opportunity["owner"]
        assert opportunity["expected_impact"]
        assert opportunity["evidence_boundary"]
        assert opportunity["linked_gaps"] or opportunity["linked_battlecards"]
        if opportunity["priority"] == "p0_immediate":
            assert opportunity["linked_evidence_ids"]


def test_analysis_agent_flags_claim_when_competitor_evidence_is_missing() -> None:
    state = create_initial_state(_task("task_analysis_missing_evidence"))
    target = Product(
        product_id="prod_target",
        task_id="task_analysis_missing_evidence",
        sku_id="sku_target",
        role="target",
        name="Target automatic litter box",
        brand="Demo Brand",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        product_url="https://example.com/target",
        evidence_ids=["ev_target"],
        tags=["automatic_litter_box", "1500-2000", "target"],
        created_at=NOW,
    )
    competitor = Product(
        product_id="prod_competitor",
        task_id="task_analysis_missing_evidence",
        sku_id="sku_competitor",
        role="direct_competitor",
        name="Competitor automatic litter box",
        brand="Demo Brand",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        product_url="https://example.com/competitor",
        evidence_ids=[],
        tags=["automatic_litter_box", "1500-2000", "direct_competitor"],
        created_at=NOW,
    )
    evidence = Evidence(
        evidence_id="ev_target",
        task_id="task_analysis_missing_evidence",
        product_id="prod_target",
        source_type="douyin_sku_snapshot",
        source_url="https://example.com/target",
        screenshot_path="data/raw/target.png",
        access_time=NOW,
        content_summary="Target automatic cleaning and smart visible design.",
        confidence_level="medium",
        limitations="Local snapshot.",
        metadata={
            "product_type": "automatic_litter_box",
            "price": {
                "currency": "CNY",
                "display_price_yuan": 1599,
                "price_band": "1500-2000",
            },
        },
    )

    append_product(state, target)
    append_product(state, competitor)
    append_evidence(state, evidence)

    analysis_agent_node(state, now=NOW)

    assert len(state["competition_edges"]) == 1
    assert state["claims"][0]["status"] == "needs_review"
    assert "missing_evidence" in state["claims"][0]["risk_flags"]
    assert "missing_evidence" in state["competition_edges"][0]["risk_flags"]
    assert state["competitor_battlecards"][0]["target_response"]
    assert "missing_evidence" in state["competitor_battlecards"][0]["risk_flags"]
    assert "建议复核" in state["competitor_battlecards"][0]["response_talk_track"]


def test_analysis_agent_records_trace_run_without_starting_qa_step() -> None:
    state = _state_after_collection()

    analysis_agent_node(state, now=NOW)

    run_log = state["run_logs"][-1]
    assert run_log["agent_name"] == "analysis_agent"
    assert run_log["status"] == "succeeded"
    assert "competition edges" in run_log["output_summary"]
    assert state["review_tasks"] == []


def test_analysis_agent_recomputes_targeted_revision_after_collection_repair() -> None:
    state = create_initial_state(_task("task_analysis_revision_recompute"))
    collection_agent_node(state, now=NOW)
    analysis_agent_node(state, now=NOW)

    target_edge = next(
        edge
        for edge in state["competition_edges"]
        if edge["competitor_product_id"] == "prod_sku_01"
    )
    target_claim_id = target_edge["claim_ids"][0]
    target_claim = next(claim for claim in state["claims"] if claim["claim_id"] == target_claim_id)
    target_claim["status"] = "needs_review"
    target_claim["risk_flags"] = ["conflicting_analysis"]

    before_edge_score = target_edge["edge_score"]
    before_evidence_confidence = target_edge["score_breakdown"]["evidence_confidence"]
    before_unrelated_edges = {
        edge["edge_id"]: dict(edge)
        for edge in state["competition_edges"]
        if edge["edge_id"] != target_edge["edge_id"]
    }

    qa_agent_node(state, now=NOW)
    assert any(message["to_agent"] == "analysis_agent" for message in state["agent_messages"])

    collection_agent_node(state, now=NOW)
    repaired_evidence_id = state["metadata"]["collection_agent_repair"]["new_evidence_ids"][0]

    analysis_agent_node(state, now=NOW)

    after_edge = next(
        edge
        for edge in state["competition_edges"]
        if edge["edge_id"] == target_edge["edge_id"]
    )
    after_claim = next(
        claim for claim in state["claims"] if claim["claim_id"] == target_claim_id
    )
    after_unrelated_edges = {
        edge["edge_id"]: edge
        for edge in state["competition_edges"]
        if edge["edge_id"] != target_edge["edge_id"]
    }
    analysis_messages = [
        message for message in state["agent_messages"] if message["to_agent"] == "analysis_agent"
    ]
    analysis_run_logs = [
        run_log for run_log in state["run_logs"] if run_log["agent_name"] == "analysis_agent"
    ]

    assert len(state["competition_edges"]) == 13
    assert len(state["claims"]) == 13
    assert len(analysis_run_logs) == 2
    assert analysis_run_logs[-1]["status"] == "succeeded"
    assert after_claim["status"] == "accepted"
    assert "conflicting_analysis" not in after_claim["risk_flags"]
    assert repaired_evidence_id in after_claim["evidence_ids"]
    assert after_edge["edge_score"] > before_edge_score
    assert (
        after_edge["score_breakdown"]["evidence_confidence"]
        > before_evidence_confidence
    )
    assert after_unrelated_edges == before_unrelated_edges
    assert analysis_messages[0]["status"] == "processed"
    assert (
        analysis_messages[0]["payload"]["analysis_recompute"]["recomputed_edge_ids"]
        == [target_edge["edge_id"]]
    )
    recompute_summary = state["metadata"]["analysis_agent_recompute"]
    assert recompute_summary["target_claim_ids"] == [target_claim_id]
    assert recompute_summary["target_edge_ids"] == [target_edge["edge_id"]]
    assert recompute_summary["unaffected_edge_ids"] == list(before_unrelated_edges)
    assert recompute_summary["diffs"][0]["before"]["edge_score"] == before_edge_score
    assert recompute_summary["diffs"][0]["after"]["edge_score"] == after_edge["edge_score"]
