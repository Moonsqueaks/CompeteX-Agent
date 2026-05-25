from datetime import UTC, datetime

from app.agents import qa_agent_node
from app.graph import append_claim, append_competition_edge, append_evidence, create_initial_state
from app.schemas import (
    AnalysisTask,
    Claim,
    CompetitionEdge,
    CompetitionSlice,
    Evidence,
    ScoreBreakdown,
)

NOW = datetime(2026, 5, 24, 2, 0, tzinfo=UTC)
TASK_ID = "task_qa_agent"


def _task() -> AnalysisTask:
    return AnalysisTask(
        task_id=TASK_ID,
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


def _evidence(
    *,
    access_time: datetime | None = NOW,
    screenshot_path: str | None = "data/raw/sku_01/price.png",
    content_summary: str = "商品页显示自动清理功能。",
    metadata: dict | None = None,
) -> Evidence:
    return Evidence(
        evidence_id="ev_qa_001",
        task_id=TASK_ID,
        product_id="prod_qa_001",
        source_type="douyin_sku_snapshot",
        source_url="https://example.com/product",
        screenshot_path=screenshot_path,
        access_time=access_time,
        content_summary=content_summary,
        confidence_level="medium",
        limitations="Local snapshot.",
        metadata=metadata or {},
    )


def _claim(
    *,
    content: str = "商品页证据显示该产品具备自动清理能力。",
    is_inference: bool = False,
    risk_flags: list[str] | None = None,
) -> Claim:
    return Claim(
        claim_id="claim_qa_001",
        task_id=TASK_ID,
        claim_type="feature_fact",
        content=content,
        evidence_ids=["ev_qa_001"],
        confidence=0.82,
        is_inference=is_inference,
        risk_flags=risk_flags or [],
        status="accepted",
        created_at=NOW,
    )


def _edge() -> CompetitionEdge:
    return CompetitionEdge(
        edge_id="edge_qa_001",
        task_id=TASK_ID,
        target_product_id="prod_target",
        competitor_product_id="prod_qa_001",
        competition_type="direct",
        slice=CompetitionSlice(
            price_band="1000-1500",
            persona="多猫家庭",
            scenario="自动清理",
        ),
        decision_stages=["capability_understanding"],
        edge_score=0.76,
        score_breakdown=ScoreBreakdown(
            demand_substitutability=0.8,
            context_match=0.7,
            decision_stage_impact=0.8,
            evidence_confidence=0.8,
            market_signal_strength=0.6,
        ),
        claim_ids=["claim_qa_001"],
        risk_flags=[],
        created_at=NOW,
    )


def _state_with_artifacts(
    evidence: Evidence | None = None,
    claim: Claim | None = None,
    edge: CompetitionEdge | None = None,
) -> dict:
    state = create_initial_state(_task())
    append_evidence(state, evidence or _evidence())
    append_claim(state, claim or _claim())
    append_competition_edge(state, edge or _edge())
    return state


def test_qa_agent_marks_qualified_state_as_passed() -> None:
    state = _state_with_artifacts()

    result = qa_agent_node(state, now=NOW)

    assert result is state
    assert state["review_tasks"] == []
    assert state["agent_messages"] == []
    assert state["metadata"]["qa_agent"]["qa_status"] == "passed"
    assert state["metadata"]["qa_agent"]["passed"] is True
    assert state["run_logs"][-1]["agent_name"] == "qa_agent"
    assert state["run_logs"][-1]["status"] == "succeeded"


def test_qa_agent_generates_collection_revision_for_missing_price_access_time() -> None:
    state = _state_with_artifacts(
        evidence=_evidence(
            access_time=None,
            content_summary="商品页显示到手价和价格带。",
            metadata={"price": {"display_price_yuan": 999, "price_band": "500-1000"}},
        ),
        claim=_claim(
            content="该竞品在 500-1000 价格带存在价格优势，该判断为推断。",
            is_inference=True,
        ),
    )

    qa_agent_node(state, now=NOW)

    assert state["review_tasks"][0]["issue_code"] == "TIMELY_EVIDENCE_MISSING_ACCESS_TIME"
    assert state["review_tasks"][0]["target_agent"] == "collection_agent"
    assert len(state["agent_messages"]) == 1
    message = state["agent_messages"][0]
    assert message["message_type"] == "revision_request"
    assert message["to_agent"] == "collection_agent"
    assert message["status"] == "requires_revision"
    assert message["evidence_ids"] == ["ev_qa_001"]
    assert message["payload"]["issue_codes"] == ["TIMELY_EVIDENCE_MISSING_ACCESS_TIME"]
    assert state["metadata"]["qa_agent"]["revision_target"] == "collection_agent"
    assert state["run_logs"][-1]["status"] == "requires_revision"


def test_qa_agent_generates_analysis_revision_for_conflicting_analysis() -> None:
    state = _state_with_artifacts(
        claim=_claim(risk_flags=["conflicting_analysis"]),
    )

    qa_agent_node(state, now=NOW)

    assert state["review_tasks"][0]["issue_code"] == "CLAIM_CONFLICTING_ANALYSIS"
    assert state["review_tasks"][0]["target_agent"] == "analysis_agent"
    assert state["agent_messages"][0]["to_agent"] == "analysis_agent"
    assert state["metadata"]["qa_agent"]["revision_targets"] == ["analysis_agent"]


def test_qa_agent_trace_contains_check_severity_and_revision_target() -> None:
    state = _state_with_artifacts(
        evidence=_evidence(
            access_time=None,
            content_summary="商品页显示到手价和价格带。",
            metadata={"price": {"display_price_yuan": 999, "price_band": "500-1000"}},
        ),
        claim=_claim(
            content="该竞品在 500-1000 价格带存在价格优势，该判断为推断。",
            is_inference=True,
        ),
    )

    qa_agent_node(state, now=NOW)

    review_task = state["review_tasks"][0]
    message_target = state["agent_messages"][0]["payload"]["targets"][0]
    assert review_task["check_name"] == "time_sensitive_evidence_access_time"
    assert review_task["severity"] == "error"
    assert review_task["target_agent"] == "collection_agent"
    assert message_target["check_name"] == review_task["check_name"]
    assert message_target["severity"] == "error"
    assert state["metadata"]["qa_agent"]["severity_counts"] == {"error": 1}
    assert "QA found 1 review tasks" in state["run_logs"][-1]["output_summary"]
