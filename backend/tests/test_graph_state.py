import json
from datetime import UTC, datetime

import pytest

from app.graph import (
    STATE_LIST_FIELDS,
    append_agent_message,
    append_claim,
    append_evidence,
    append_human_feedback,
    append_knowledge_artifact,
    append_product,
    append_review_task,
    append_run_log,
    append_token_usage_log,
    append_tool_call_log,
    create_initial_state,
    serialize_state_for_trace,
)
from app.schemas import (
    AgentMessage,
    AgentRunLog,
    AnalysisTask,
    Claim,
    Evidence,
    HumanFeedback,
    KnowledgeArtifact,
    Product,
    ReviewTask,
    TokenUsageLog,
    ToolCallLog,
)

NOW = datetime(2026, 5, 22, 2, 0, tzinfo=UTC)


def _task(task_id: str = "task_001") -> AnalysisTask:
    return AnalysisTask(
        task_id=task_id,
        target_product_name="Demo automatic litter box",
        target_product_url="https://example.com/products/target",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        data_source_mode="demo_snapshot",
        status="created",
        research_text="Interview summary",
        created_at=NOW,
        updated_at=NOW,
        metadata={"demo": True},
    )


def _product() -> Product:
    return Product(
        product_id="prod_target",
        task_id="task_001",
        sku_id="sku_02",
        role="target",
        name="Demo automatic litter box",
        brand="Demo Brand",
        shop_name="Demo Shop",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        product_url="https://example.com/products/target",
        evidence_ids=["ev_001"],
        tags=["odor_control"],
        created_at=NOW,
    )


def _evidence() -> Evidence:
    return Evidence(
        evidence_id="ev_001",
        task_id="task_001",
        product_id="prod_target",
        source_type="douyin_sku_snapshot",
        source_url="https://example.com/products/target",
        screenshot_path="data/raw/sku_02/price.png",
        access_time=NOW,
        content_summary="Snapshot includes price and selling points.",
        confidence_level="medium",
        limitations="Local snapshot, not a live page.",
        metadata={"sku_id": "sku_02"},
    )


def _claim() -> Claim:
    return Claim(
        claim_id="claim_001",
        task_id="task_001",
        claim_type="pricing_advantage",
        content="Competitor A is more price-attractive in this slice.",
        evidence_ids=["ev_001"],
        confidence=0.78,
        is_inference=False,
        risk_flags=[],
        status="accepted",
        created_at=NOW,
    )


def _review_task() -> ReviewTask:
    return ReviewTask(
        review_task_id="review_001",
        task_id="task_001",
        check_name="price_access_time",
        issue_code="MISSING_ACCESS_TIME",
        severity="error",
        status="open",
        target_agent="collection_agent",
        target_type="evidence",
        target_id="ev_001",
        message="Price evidence is missing access time.",
        required_action="Add access time or mark unavailable.",
        related_claim_ids=["claim_001"],
        evidence_ids=["ev_001"],
        created_at=NOW,
        resolved_at=None,
    )


def _human_feedback() -> HumanFeedback:
    return HumanFeedback(
        feedback_id="hf_001",
        task_id="task_001",
        target_type="claim",
        target_id="claim_001",
        action="mark_needs_review",
        before_value={"status": "accepted"},
        after_value={"status": "needs_review"},
        reason="Evidence needs manual review.",
        created_at=NOW,
    )


def _agent_message() -> AgentMessage:
    return AgentMessage(
        message_id="msg_001",
        task_id="task_001",
        from_agent="qa_agent",
        to_agent="collection_agent",
        message_type="revision_request",
        artifact_type="claim_evidence_check",
        payload={"claim_id": "claim_001", "missing_fields": ["access_time"]},
        evidence_ids=["ev_001"],
        status="requires_revision",
        created_at=NOW,
    )


def _run_log() -> AgentRunLog:
    return AgentRunLog(
        run_id="run_001",
        task_id="task_001",
        agent_name="collection_agent",
        status="succeeded",
        started_at=NOW,
        ended_at=NOW,
        input_summary="Load local SKU snapshots.",
        output_summary="Loaded products and evidence.",
        error_message=None,
    )


def _tool_call_log() -> ToolCallLog:
    return ToolCallLog(
        tool_call_id="tool_001",
        task_id="task_001",
        run_id="run_001",
        tool_name="snapshot_loader",
        arguments_summary={"path": "data/snapshots/demo_sku_snapshot.json"},
        status="succeeded",
        started_at=NOW,
        ended_at=NOW,
        duration_ms=35,
        error_message=None,
    )


def _token_usage_log() -> TokenUsageLog:
    return TokenUsageLog(
        usage_id="usage_001",
        task_id="task_001",
        run_id="run_001",
        agent_name="analysis_agent",
        model_name="rules",
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        created_at=NOW,
    )


def _knowledge_artifact() -> KnowledgeArtifact:
    return KnowledgeArtifact(
        knowledge_id="knowledge_task_001_writer_v1",
        task_id="task_001",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        generated_at=NOW,
        retrieval_mode="local_static_category_framework",
        external_search_performed=False,
        query_context={"target_product_name": "Demo automatic litter box"},
        sources=[],
        items=[],
        limitations=["Local framework only."],
    )


def test_initial_state_can_be_created_from_task() -> None:
    state = create_initial_state(_task())

    assert state["task"]["task_id"] == "task_001"
    assert state["task"]["created_at"] == "2026-05-22T02:00:00Z"
    assert state["metadata"] == {}
    for field in STATE_LIST_FIELDS:
        assert state[field] == []


def test_state_can_append_core_artifacts() -> None:
    state = create_initial_state(_task())

    append_product(state, _product())
    append_evidence(state, _evidence())
    append_claim(state, _claim())
    append_review_task(state, _review_task())

    assert state["products"][0]["product_id"] == "prod_target"
    assert state["evidences"][0]["evidence_id"] == "ev_001"
    assert state["claims"][0]["claim_id"] == "claim_001"
    assert state["review_tasks"][0]["review_task_id"] == "review_001"


def test_state_serialization_can_power_trace_display() -> None:
    state = create_initial_state(_task())
    append_product(state, _product())
    append_evidence(state, _evidence())
    append_claim(state, _claim())
    append_review_task(state, _review_task())
    append_human_feedback(state, _human_feedback())
    append_agent_message(state, _agent_message())
    append_run_log(state, _run_log())
    append_tool_call_log(state, _tool_call_log())
    append_token_usage_log(state, _token_usage_log())
    append_knowledge_artifact(state, _knowledge_artifact())

    trace_payload = serialize_state_for_trace(state)
    encoded = json.dumps(trace_payload, ensure_ascii=False)

    assert "task_001" in encoded
    assert trace_payload["counts"]["products"] == 1
    assert trace_payload["counts"]["review_tasks"] == 1
    assert trace_payload["agent_messages"][0]["message_type"] == "revision_request"
    assert trace_payload["run_logs"][0]["agent_name"] == "collection_agent"
    assert trace_payload["tool_call_logs"][0]["tool_name"] == "snapshot_loader"
    assert trace_payload["token_usage_logs"][0]["total_tokens"] == 0
    assert trace_payload["knowledge_artifacts"][0]["retrieval_mode"] == (
        "local_static_category_framework"
    )


@pytest.mark.parametrize("task_payload", [{}, {"task_id": ""}, {"task_id": None}])
def test_initial_state_requires_task_id(task_payload: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="task_id"):
        create_initial_state(task_payload)
