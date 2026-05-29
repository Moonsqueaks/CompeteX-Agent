import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import AnalysisTask, TaskCreateRequest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = PROJECT_ROOT / "data" / "snapshots" / "demo_sku_snapshot.json"
STABLE_INPUT_PATH = PROJECT_ROOT / "demo" / "stable-demo-input.json"
EXPECTED_SNAPSHOT_SHA256 = (
    "8E8303BEB9E157ACF90929352493DD00330952F09438E94443A4D98E8C01111F"
)
REQUIRED_REPORT_SECTIONS = [
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


def test_demo_freeze_files_lock_snapshot_and_stable_input() -> None:
    snapshot = _load_json(SNAPSHOT_PATH)
    stable_input = _load_json(STABLE_INPUT_PATH)

    assert _sha256(SNAPSHOT_PATH) == EXPECTED_SNAPSHOT_SHA256
    assert snapshot["snapshot_version"] == "2026-05-23.step06.v1"
    assert snapshot["default_target_sku_id"] == "sku_02"
    assert stable_input == {
        "target_product_name": "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
        "target_product_url": "https://v.douyin.com/mv8e4KRLLwc/",
        "category": "smart_pet_hardware",
        "subcategory": "automatic_litter_box",
        "data_source_mode": "demo_snapshot",
        "research_text": "多猫家庭关注除臭稳定性、自动清理可靠性、维护成本和小户型摆放体验。",
    }
    TaskCreateRequest.model_validate(stable_input)


def test_frozen_qa_revision_fixture_remains_reproducible() -> None:
    snapshot = _load_json(SNAPSHOT_PATH)
    fixture = snapshot["qa_revision_fixture"]

    assert fixture["sku_id"] == "sku_01"
    assert fixture["missing_fields"] == ["source.access_time"]
    assert fixture["repair_evidence"]["access_time"] == "2026-05-23T16:00:59+08:00"
    assert fixture["repair_evidence"]["screenshot_path"] == (
        "data/raw/sku_01/QQ图片20260523155546.jpg"
    )

    sku_01 = next(sku for sku in snapshot["skus"] if sku["sku_id"] == "sku_01")
    assert sku_01["source"]["access_time"] is None


def test_same_frozen_demo_input_produces_stable_result_shape_and_report_sections() -> None:
    first = _run_demo_workflow("task_demo_freeze_001")
    second = _run_demo_workflow("task_demo_freeze_002")

    assert first == second
    assert first["task_status"] == "completed"
    assert first["agent_run_counts"] == {
        "analysis_agent": 2,
        "collection_agent": 2,
        "qa_agent": 2,
        "writer_agent": 1,
    }
    assert first["qa_issue_codes"] == ["TIMELY_EVIDENCE_MISSING_ACCESS_TIME"]
    assert first["qa_review_statuses"] == ["resolved"]
    assert first["diff_sources"] == ["analysis_agent_recompute", "collection_agent_repair"]
    assert first["report_sections"] == REQUIRED_REPORT_SECTIONS
    assert first["qa_summary"]["qa_status"] == "passed"
    assert first["qa_summary"]["current_review_task_count"] == 0
    assert first["qa_summary"]["historical_review_task_count"] == 1
    assert first["qa_summary"]["resolved_review_task_count"] == 1
    assert first["qa_summary"]["revision_message_count"] == 2
    assert first["repaired_evidence_used"] is True


def _run_demo_workflow(task_id: str) -> dict:
    workflow = build_analysis_workflow()
    result = workflow.invoke(create_initial_state(_stable_task(task_id)))
    report = result["reports"][-1]
    battlefield = report["dynamic_slice_analysis"]
    qa_item = report["qa_summary"]["items"][0]
    qa_summary = qa_item["qa_agent"]
    repaired_evidence_used = any(
        "ev_sku_01_repair_001" in claim.get("evidence_ids", [])
        for item in report["competitor_findings"]["items"]
        for claim in item.get("claims", [])
    )

    return {
        "agent_run_counts": dict(
            sorted(Counter(run["agent_name"] for run in result["run_logs"]).items())
        ),
        "battlefield_item_count": len(battlefield["items"]),
        "claim_count": len(result["claims"]),
        "diff_sources": _diff_sources(result),
        "edge_count": len(result["competition_edges"]),
        "evidence_count": len(result["evidences"]),
        "product_count": len(result["products"]),
        "qa_issue_codes": sorted({review["issue_code"] for review in result["review_tasks"]}),
        "qa_review_statuses": sorted({review["status"] for review in result["review_tasks"]}),
        "qa_summary": {
            "current_review_task_count": qa_summary["review_task_count"],
            "historical_review_task_count": qa_item["review_task_count"],
            "qa_status": qa_summary["qa_status"],
            "resolved_review_task_count": len(qa_summary["resolved_review_task_ids"]),
            "revision_message_count": qa_item["revision_message_count"],
        },
        "repaired_evidence_used": repaired_evidence_used,
        "report_sections": report["section_order"],
        "task_status": result["task"]["status"],
    }


def _stable_task(task_id: str) -> AnalysisTask:
    payload = _load_json(STABLE_INPUT_PATH)
    now = datetime(2026, 5, 29, 4, 0, tzinfo=UTC)
    return AnalysisTask(
        task_id=task_id,
        target_product_name=payload["target_product_name"],
        target_product_url=payload["target_product_url"],
        category=payload["category"],
        subcategory=payload["subcategory"],
        data_source_mode=payload["data_source_mode"],
        status="created",
        research_text=payload["research_text"],
        created_at=now,
        updated_at=now,
        metadata={"demo_freeze": True},
    )


def _diff_sources(result: dict) -> list[str]:
    sources = []
    if result["metadata"]["collection_agent_repair"]["diffs"]:
        sources.append("collection_agent_repair")
    if (
        result["metadata"]["analysis_agent_recompute"]["diffs"]
        or result["metadata"]["analysis_agent_recompute"]["claim_diffs"]
    ):
        sources.append("analysis_agent_recompute")
    return sorted(sources)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
