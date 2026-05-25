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


def _state_after_collection() -> dict:
    state = create_initial_state(_task())
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
