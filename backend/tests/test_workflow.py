from datetime import UTC, datetime

from app.graph import (
    ANALYSIS_NODE,
    COLLECTION_NODE,
    WRITER_NODE,
    build_analysis_workflow,
    create_initial_state,
    route_after_qa,
)
from app.schemas import AnalysisTask

NOW = datetime(2026, 5, 24, 2, 0, tzinfo=UTC)


def _task(task_id: str = "task_workflow") -> AnalysisTask:
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


def test_workflow_completes_after_real_collection_revision() -> None:
    workflow = build_analysis_workflow()
    state = create_initial_state(_task("task_workflow_completion"))

    result = workflow.invoke(state)

    workflow_metadata = result["metadata"]["workflow"]
    collection_repair = result["metadata"]["collection_agent_repair"]
    analysis_recompute = result["metadata"]["analysis_agent_recompute"]
    writer_run = next(
        run_log for run_log in result["run_logs"] if run_log["agent_name"] == "writer_agent"
    )

    assert result["task"]["status"] == "completed"
    assert workflow_metadata["status"] == "completed"
    assert workflow_metadata["writer_status"] == "succeeded"
    assert workflow_metadata["revision_rounds"] == 1
    assert collection_repair["repaired_count"] == 1
    assert analysis_recompute["recomputed_edge_ids"]
    assert writer_run["status"] == "succeeded"
    assert result["reports"]
    assert result["metadata"]["writer_agent"]["status"] == "succeeded"
    assert result["metadata"]["qa_agent"]["qa_status"] == "passed"


def test_workflow_records_qa_collection_revision_and_analysis_recompute_message() -> None:
    workflow = build_analysis_workflow()
    state = create_initial_state(_task("task_workflow_revision"))

    result = workflow.invoke(state)

    collection_messages = [
        message
        for message in result["agent_messages"]
        if message["to_agent"] == COLLECTION_NODE
    ]
    analysis_messages = [
        message for message in result["agent_messages"] if message["to_agent"] == ANALYSIS_NODE
    ]

    assert collection_messages
    assert analysis_messages
    assert collection_messages[0]["status"] == "processed"
    assert analysis_messages[-1]["status"] == "processed"
    assert (
        "COLLECTION_REPAIR_REQUIRES_ANALYSIS_RECOMPUTE"
        in analysis_messages[-1]["payload"]["issue_codes"]
    )


def test_route_after_qa_uses_pass_and_revision_targets() -> None:
    state = create_initial_state(_task("task_workflow_route"))
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}
    assert route_after_qa(state) == WRITER_NODE

    state["metadata"]["qa_agent"] = {
        "qa_status": "requires_revision",
        "revision_target": COLLECTION_NODE,
    }
    assert route_after_qa(state) == COLLECTION_NODE

    state["metadata"]["qa_agent"] = {
        "qa_status": "requires_revision",
        "revision_target": ANALYSIS_NODE,
    }
    assert route_after_qa(state) == ANALYSIS_NODE


def test_workflow_fails_when_max_revision_rounds_are_exceeded() -> None:
    workflow = build_analysis_workflow(max_revision_rounds=0)
    state = create_initial_state(_task("task_workflow_max_revision"))

    result = workflow.invoke(state)

    workflow_metadata = result["metadata"]["workflow"]

    assert result["task"]["status"] == "failed"
    assert workflow_metadata["status"] == "failed"
    assert workflow_metadata["revision_rounds"] == 1
    assert workflow_metadata["failure_reason"] == "Maximum QA revision rounds exceeded."
    assert result["metadata"]["qa_agent"]["qa_status"] == "requires_revision"
