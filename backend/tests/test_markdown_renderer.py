from datetime import UTC, datetime
from pathlib import Path

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import AnalysisTask
from app.services.markdown_renderer import (
    export_markdown_report_for_state,
    render_markdown_report,
)

NOW = datetime(2026, 5, 24, 2, 0, tzinfo=UTC)
REQUIRED_SECTION_TITLES = [
    "结论摘要",
    "竞争格局判断",
    "核心竞品拆解",
    "用户决策链分析",
    "目标产品机会与风险",
    "产品策略建议",
    "证据与质检附录",
    "分析流程与系统能力附录",
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


def test_markdown_report_exports_v2_sections_and_file_metadata(tmp_path: Path) -> None:
    state = _workflow_result("task_markdown_sections")

    markdown_report = export_markdown_report_for_state(
        state,
        output_dir=tmp_path,
        generated_at=NOW,
    )
    markdown = markdown_report.markdown

    for title in REQUIRED_SECTION_TITLES:
        assert f"## {title}" in markdown
    assert sum(line.startswith("## ") for line in markdown.splitlines()) == 8
    assert Path(markdown_report.file_path).read_text(encoding="utf-8") == markdown
    assert state["markdown_reports"][0]["markdown_report_id"] == markdown_report.markdown_report_id
    assert state["metadata"]["markdown_report"]["file_path"] == markdown_report.file_path
    assert markdown_report.metadata["section_count"] == 8
    assert markdown_report.metadata["security_scan"] == "passed"


def test_markdown_report_displays_claim_evidence_confidence_and_access_time(
    tmp_path: Path,
) -> None:
    state = _workflow_result("task_markdown_claims")
    report = state["reports"][0]

    markdown_report = render_markdown_report(report, output_dir=tmp_path, generated_at=NOW)
    markdown = markdown_report.markdown

    for item in report["core_competitor_analysis"]["items"]:
        for claim in item["claims"]:
            assert f"Claim {claim['claim_id']}:" in markdown
            assert f"{claim['confidence']:.2f}" in markdown
            assert "推断标识" in markdown
            for evidence_id in claim["evidence_ids"]:
                assert f"Evidence {evidence_id}" in markdown

    evidence_index = next(
        item
        for item in report["evidence_quality_appendix"]["items"]
        if item.get("appendix_type") == "evidence_index"
    )
    for evidence in evidence_index["items"]:
        if evidence["access_time"] is None:
            assert "访问时间: 暂无可靠数据" in markdown
        else:
            assert evidence["access_time"] in markdown
        assert evidence["confidence_level"] in markdown


def test_markdown_report_marks_missing_evidence_as_no_reliable_data(tmp_path: Path) -> None:
    state = _workflow_result("task_markdown_missing_evidence")
    report = state["reports"][0]
    finding = report["core_competitor_analysis"]["items"][0]
    finding["evidence_ids"] = []
    finding["claims"][0]["evidence_ids"] = []

    markdown_report = render_markdown_report(report, output_dir=tmp_path, generated_at=NOW)

    assert "Evidence: 暂无可靠数据" in markdown_report.markdown


def test_markdown_report_redacts_sensitive_patterns_before_export(tmp_path: Path) -> None:
    state = _workflow_result("task_markdown_security")
    report = state["reports"][0]
    evidence_index = next(
        item
        for item in report["evidence_quality_appendix"]["items"]
        if item.get("appendix_type") == "evidence_index"
    )
    evidence_index["items"][0]["content_summary"] = (
        "DOUBAO_API_KEY=sk-testsecret000 手机 13800138000 "
        "account_id=acct-private-001 地址: 北京市朝阳区幸福路88号3单元501室"
    )

    markdown_report = render_markdown_report(report, output_dir=tmp_path, generated_at=NOW)
    markdown = markdown_report.markdown

    assert "DOUBAO_API_KEY" not in markdown
    assert "sk-testsecret000" not in markdown
    assert "13800138000" not in markdown
    assert "acct-private-001" not in markdown
    assert "北京市朝阳区幸福路88号3单元501室" not in markdown
    assert "[REDACTED]" in markdown
    assert Path(markdown_report.file_path).read_text(encoding="utf-8") == markdown
