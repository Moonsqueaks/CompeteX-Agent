import json
import re
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from docx import Document

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AnalysisTask,
    BattlefieldData,
    BattlefieldSliceSelection,
    OverviewData,
    TraceData,
)
from app.services.battlefield_service import _build_battlefield_data
from app.services.overview_service import _build_overview_data
from app.services.trace_service import _build_trace_data
from app.services.word_report_service import render_word_report

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = PROJECT_ROOT / "data" / "snapshots" / "demo_sku_snapshot.json"
STABLE_INPUT_PATH = PROJECT_ROOT / "demo" / "stable-demo-input.json"
CREATED_AT = datetime(2026, 5, 29, 4, 0, tzinfo=UTC)


def test_backend_v2_fixture_contract_covers_overview_key_relations_and_evidence_chain() -> None:
    state = _completed_demo_state("task_v2_fixture_contract")
    overview = _build_overview_data(
        state,
        BattlefieldSliceSelection(),
        "overview_task_v2_fixture_contract_all",
    )
    battlefield = _build_battlefield_data(
        state,
        BattlefieldSliceSelection(),
        "battlefield_task_v2_fixture_contract_all",
    )
    trace = _build_trace_data(
        task=AnalysisTask.model_validate(state["task"]),
        state=state,
        trace_view_id="trace_task_v2_fixture_contract",
    )

    assert isinstance(overview, OverviewData)
    assert overview.analysis_scope.data_source_mode == "demo_snapshot"
    assert overview.analysis_scope.sku_count >= 8
    assert overview.one_sentence_judgment.evidence_ids
    assert overview.key_competitors
    assert overview.key_competitors[0].drilldown_refs[0].reference_type == "battlefield"

    assert isinstance(battlefield, BattlefieldData)
    assert battlefield.graph_nodes
    assert battlefield.graph_edges
    assert battlefield.key_relations
    assert battlefield.evidence_cards
    assert battlefield.available_slices
    relation = battlefield.key_relations[0]
    assert relation.inclusion_reason
    assert relation.relationship_label_explanation
    assert relation.four_part_explanation.response_suggestion.is_analysis_suggestion
    assert relation.evidence_credibility.evidence_ids
    assert relation.competitor_primary_image_path is None or not Path(
        relation.competitor_primary_image_path,
    ).is_absolute()

    assert isinstance(trace, TraceData)
    assert trace.evidence_chains
    assert trace.evidence_chains[0].claim_id
    assert trace.evidence_chains[0].evidence_items
    assert trace.evidence_chains[0].navigation["trace_tab"] == "evidence_chain"
    assert trace.quality_records
    assert trace.diffs
    assert all(diff.business_impact and "JSON" not in diff.business_impact for diff in trace.diffs)


def test_backend_v2_fixture_contract_docx_handles_missing_images(tmp_path: Path) -> None:
    state = _completed_demo_state("task_v2_fixture_docx_missing_images")
    state = deepcopy(state)
    for product in state["products"]:
        product["primary_image_path"] = None
        product["primary_image_url"] = None
        product["primary_image_source_path"] = None
        product["primary_image_status"] = "missing"

    report = state["reports"][-1]
    battlefield = _build_battlefield_data(
        state,
        BattlefieldSliceSelection(),
        "battlefield_task_v2_fixture_docx_missing_images",
    )

    word_report = render_word_report(
        report,
        products=state["products"],
        battlefield=battlefield,
        relationship_graph_path=None,
        output_dir=tmp_path,
    )
    text = _docx_text(Path(word_report.file_path))

    assert "暂无可靠图片" not in text
    assert "产品图片摘要" not in text
    assert word_report.metadata["target_image_status"] == "omitted"
    assert word_report.metadata["core_competitor_image_count"] == 0
    assert word_report.metadata["relationship_graph_included"] is False


def test_backend_v2_fixture_contract_fixture_safety_scan() -> None:
    serialized = "\n".join(
        [
            SNAPSHOT_PATH.read_text(encoding="utf-8"),
            STABLE_INPUT_PATH.read_text(encoding="utf-8"),
            json.dumps(_completed_demo_shape(), ensure_ascii=False),
        ]
    )
    lower = serialized.lower()

    forbidden_literals = [
        "api_key",
        "apikey",
        "authorization",
        "bearer ",
        "password",
        "secret",
        "token",
        "手机号",
        "身份证",
        "地址",
        "account_id",
        "user_id",
        "openid",
    ]
    for literal in forbidden_literals:
        assert literal not in lower

    assert re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)", serialized) is None
    assert re.search(r"sk-[a-zA-Z0-9]{20,}", serialized) is None


def _completed_demo_state(task_id: str) -> dict:
    workflow = build_analysis_workflow()
    return workflow.invoke(create_initial_state(_stable_task(task_id)))


def _completed_demo_shape() -> dict:
    state = _completed_demo_state("task_v2_fixture_safety_scan")
    return {
        "task_status": state["task"]["status"],
        "product_count": len(state["products"]),
        "evidence_count": len(state["evidences"]),
        "claim_count": len(state["claims"]),
        "edge_count": len(state["competition_edges"]),
        "report_sections": state["reports"][-1]["section_order"],
        "qa_issue_codes": sorted({review["issue_code"] for review in state["review_tasks"]}),
    }


def _stable_task(task_id: str) -> AnalysisTask:
    payload = json.loads(STABLE_INPUT_PATH.read_text(encoding="utf-8"))
    return AnalysisTask(
        task_id=task_id,
        target_product_name=payload["target_product_name"],
        target_product_url=payload["target_product_url"],
        category=payload["category"],
        subcategory=payload["subcategory"],
        data_source_mode=payload["data_source_mode"],
        status="created",
        research_text=payload["research_text"],
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        metadata={"fixture_contract": True},
    )


def _docx_text(path: Path) -> str:
    document = Document(path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs)
