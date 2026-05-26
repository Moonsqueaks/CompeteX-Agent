from datetime import UTC, datetime

from app.agents import analysis_agent_node, collection_agent_node, writer_agent_node
from app.graph import create_initial_state
from app.schemas import AnalysisTask

NOW = datetime(2026, 5, 24, 2, 0, tzinfo=UTC)
REQUIRED_SECTIONS = [
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


def _task(task_id: str = "task_writer_agent") -> AnalysisTask:
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


def _analysis_ready_state(task_id: str = "task_writer_agent") -> dict:
    state = create_initial_state(_task(task_id))
    collection_agent_node(state, now=NOW)
    analysis_agent_node(state, now=NOW)
    return state


def test_writer_agent_generates_all_required_report_sections() -> None:
    state = _analysis_ready_state("task_writer_sections")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}

    writer_agent_node(state, now=NOW)

    report = state["reports"][0]
    assert report["section_order"] == REQUIRED_SECTIONS
    for section_id in REQUIRED_SECTIONS:
        assert report[section_id]["section_id"] == section_id
        assert report[section_id]["summary"]
    assert report["executive_summary"]["items"]
    assert report["product_profile"]["items"]
    assert report["evidence_index"]["items"]


def test_writer_report_core_findings_trace_back_to_evidence() -> None:
    state = _analysis_ready_state("task_writer_evidence")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}

    writer_agent_node(state, now=NOW)

    findings = state["reports"][0]["competitor_findings"]
    assert findings["items"]
    for item in findings["items"]:
        assert item["claims"]
        assert item["evidence_ids"]
        for claim in item["claims"]:
            assert claim["evidence_ids"]


def test_writer_report_marks_risk_claims_without_new_facts() -> None:
    state = _analysis_ready_state("task_writer_risk")
    top_edge = max(state["competition_edges"], key=lambda edge: edge["edge_score"])
    claim_id = top_edge["claim_ids"][0]
    risk_claim = next(claim for claim in state["claims"] if claim["claim_id"] == claim_id)
    risk_claim["status"] = "needs_review"
    risk_claim["risk_flags"] = ["missing_evidence"]

    writer_agent_node(state, now=NOW)

    report = state["reports"][0]
    finding = next(
        item
        for item in report["competitor_findings"]["items"]
        if item["edge_id"] == top_edge["edge_id"]
    )
    risk_claim_summary = report["qa_summary"]["items"][0]["risk_claims"][0]

    assert "missing_evidence" in finding["risk_flags"]
    assert risk_claim_summary["claim_id"] == claim_id
    assert risk_claim_summary["status"] == "needs_review"
    assert report["recommendations"]["items"][0]["is_inference"] is True


def test_writer_agent_records_trace_run_log() -> None:
    state = _analysis_ready_state("task_writer_trace")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}

    writer_agent_node(state, now=NOW)

    writer_run_logs = [
        run_log for run_log in state["run_logs"] if run_log["agent_name"] == "writer_agent"
    ]
    assert writer_run_logs
    assert writer_run_logs[-1]["status"] == "succeeded"
    assert state["metadata"]["writer_agent"]["report_id"] == state["reports"][0]["report_id"]
