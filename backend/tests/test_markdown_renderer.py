from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import AnalysisTask
from app.services.markdown_renderer import (
    MarkdownRenderError,
    export_markdown_report_for_state,
    render_markdown_report,
)

NOW = datetime(2026, 5, 24, 2, 0, tzinfo=UTC)
REQUIRED_SECTION_TITLES = [
    "执行摘要",
    "目标产品画像",
    "竞品发现",
    "动态竞争切片",
    "决策链竞争分析",
    "用户研究洞察",
    "可执行建议",
    "QA 审查摘要",
    "Evidence 索引",
]


def _task(task_id: str = "task_markdown") -> AnalysisTask:
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


def _workflow_result(task_id: str = "task_markdown") -> dict:
    workflow = build_analysis_workflow()
    state = create_initial_state(_task(task_id))
    return workflow.invoke(state)


def test_markdown_report_exports_nine_sections_and_file_metadata(tmp_path: Path) -> None:
    state = _workflow_result("task_markdown_sections")

    markdown_report = export_markdown_report_for_state(
        state,
        output_dir=tmp_path,
        generated_at=NOW,
    )
    markdown = markdown_report.markdown

    for title in REQUIRED_SECTION_TITLES:
        assert f"## {title}" in markdown
    assert sum(line.startswith("## ") for line in markdown.splitlines()) == 9
    assert Path(markdown_report.file_path).read_text(encoding="utf-8") == markdown
    assert state["markdown_reports"][0]["markdown_report_id"] == markdown_report.markdown_report_id
    assert state["metadata"]["markdown_report"]["file_path"] == markdown_report.file_path
    assert markdown_report.metadata["section_count"] == 9
    assert markdown_report.metadata["security_scan"] == "passed"


def test_markdown_report_displays_claim_evidence_confidence_and_access_time(
    tmp_path: Path,
) -> None:
    state = _workflow_result("task_markdown_claims")
    report = state["reports"][0]

    markdown_report = render_markdown_report(report, output_dir=tmp_path, generated_at=NOW)
    markdown = markdown_report.markdown

    for item in report["competitor_findings"]["items"]:
        for claim in item["claims"]:
            assert f"Claim {claim['claim_id']}:" in markdown
            assert f"{claim['confidence']:.2f}" in markdown
            assert "推断标识" in markdown
            for evidence_id in claim["evidence_ids"]:
                assert f"Evidence {evidence_id}" in markdown

    for evidence in report["evidence_index"]["items"]:
        if evidence["access_time"] is None:
            assert "访问时间: 暂无可靠数据" in markdown
        else:
            assert evidence["access_time"] in markdown
        assert evidence["confidence_level"] in markdown


def test_markdown_report_marks_missing_evidence_as_no_reliable_data(tmp_path: Path) -> None:
    state = _workflow_result("task_markdown_missing_evidence")
    report = state["reports"][0]
    finding = report["competitor_findings"]["items"][0]
    finding["evidence_ids"] = []
    finding["claims"][0]["evidence_ids"] = []

    markdown_report = render_markdown_report(report, output_dir=tmp_path, generated_at=NOW)

    assert "Evidence: 暂无可靠数据" in markdown_report.markdown


def test_markdown_report_blocks_sensitive_key_patterns(tmp_path: Path) -> None:
    state = _workflow_result("task_markdown_security")
    report = state["reports"][0]
    report["evidence_index"]["items"][0]["content_summary"] = "DOUBAO_API_KEY=sk-testsecret000"

    with pytest.raises(MarkdownRenderError, match="sensitive content"):
        render_markdown_report(report, output_dir=tmp_path, generated_at=NOW)
