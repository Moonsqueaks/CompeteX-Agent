import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.graph.state import TaskGraphState, append_markdown_report
from app.schemas import MarkdownReport, ReportData, ReportSection
from app.schemas.common import JsonObject

NO_RELIABLE_DATA = "暂无可靠数据"
DEFAULT_REPORTS_DIR = Path(__file__).resolve().parents[3] / "data" / "reports"

REPORT_TEMPLATE = """# 竞品分析报告

- Report ID: {report_id}
- Task ID: {task_id}
- Report Generated At: {report_generated_at}
- Markdown Exported At: {markdown_generated_at}

{sections}
"""

SECTION_TEMPLATE = """## {title}

{summary}

{body}

- Claim 索引: {claim_ids}
- Evidence 索引: {evidence_ids}
"""

SENSITIVE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{12,}"),
)
SAFE_FILE_STEM_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


class MarkdownRenderError(ValueError):
    pass


def render_markdown_report(
    report_data: ReportData | Mapping[str, Any],
    *,
    output_dir: Path | str | None = None,
    generated_at: datetime | None = None,
) -> MarkdownReport:
    report = ReportData.model_validate(report_data)
    markdown_generated_at = generated_at or datetime.now(UTC)
    markdown = _render_report(report, markdown_generated_at)
    _assert_markdown_is_safe(markdown)

    report_dir = Path(output_dir) if output_dir is not None else DEFAULT_REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    output_path = report_dir / _report_file_name(report)
    output_path.write_text(markdown, encoding="utf-8")

    return MarkdownReport(
        markdown_report_id=f"markdown_{report.report_id}",
        task_id=report.task_id,
        report_id=report.report_id,
        generated_at=markdown_generated_at,
        markdown=markdown,
        file_path=str(output_path),
        metadata={
            "section_count": len(report.section_order),
            "claim_count": _unique_count(
                claim_id for section in _ordered_sections(report) for claim_id in section.claim_ids
            ),
            "evidence_count": _unique_count(
                evidence_id
                for section in _ordered_sections(report)
                for evidence_id in section.evidence_ids
            ),
            "file_name": output_path.name,
            "byte_size": len(markdown.encode("utf-8")),
            "security_scan": "passed",
        },
    )


def export_markdown_report_for_state(
    state: TaskGraphState,
    *,
    output_dir: Path | str | None = None,
    generated_at: datetime | None = None,
) -> MarkdownReport:
    if not state["reports"]:
        raise MarkdownRenderError("Markdown export requires at least one ReportData artifact.")

    markdown_report = render_markdown_report(
        state["reports"][-1],
        output_dir=output_dir,
        generated_at=generated_at,
    )
    append_markdown_report(state, markdown_report)
    state["metadata"]["markdown_report"] = {
        "markdown_report_id": markdown_report.markdown_report_id,
        "report_id": markdown_report.report_id,
        "file_path": markdown_report.file_path,
        "generated_at": markdown_report.generated_at.isoformat(),
        "metadata": markdown_report.metadata,
    }
    return markdown_report


def _render_report(report: ReportData, markdown_generated_at: datetime) -> str:
    sections = "\n\n".join(
        _render_section(section) for section in _ordered_sections(report)
    )
    return REPORT_TEMPLATE.format(
        report_id=report.report_id,
        task_id=report.task_id,
        report_generated_at=report.generated_at.isoformat(),
        markdown_generated_at=markdown_generated_at.isoformat(),
        sections=sections,
    ).strip() + "\n"


def _render_section(section: ReportSection) -> str:
    body = _render_section_body(section)
    return SECTION_TEMPLATE.format(
        title=section.title,
        summary=section.summary,
        body=body,
        claim_ids=_format_id_list(section.claim_ids),
        evidence_ids=_format_id_list(section.evidence_ids),
    ).strip()


def _render_section_body(section: ReportSection) -> str:
    if not section.items:
        return NO_RELIABLE_DATA
    if section.section_id == "competitor_findings":
        return _render_competitor_findings(section.items)
    if section.section_id == "evidence_index":
        return _render_evidence_index(section.items)
    if section.section_id == "recommendations":
        return _render_recommendations(section.items)
    return _render_generic_items(section.items)


def _render_competitor_findings(items: Sequence[JsonObject]) -> str:
    blocks = []
    for item in items:
        competitor = _as_mapping(item.get("competitor"))
        competitor_name = competitor.get("name") or competitor.get("product_id") or NO_RELIABLE_DATA
        claim_lines = _render_claims(item.get("claims"))
        blocks.append(
            "\n".join(
                [
                    f"### {competitor_name}",
                    f"- Edge: {_format_value(item.get('edge_id'))}",
                    f"- Competition Type: {_format_value(item.get('competition_type'))}",
                    f"- Edge Score: {_format_value(item.get('edge_score'))}",
                    f"- Decision Stages: {_format_id_list(item.get('decision_stages'))}",
                    f"- Evidence: {_format_id_list(item.get('evidence_ids'))}",
                    f"- Risk Flags: {_format_id_list(item.get('risk_flags'))}",
                    claim_lines,
                ]
            )
        )
    return "\n\n".join(blocks)


def _render_claims(value: Any) -> str:
    claims = value if isinstance(value, list) else []
    if not claims:
        return f"- Claim: {NO_RELIABLE_DATA}"

    rendered_claims = []
    for claim in claims:
        claim_ref = _as_mapping(claim)
        rendered_claims.append(
            "\n".join(
                [
                    (
                        f"- Claim {claim_ref.get('claim_id', NO_RELIABLE_DATA)}: "
                        f"{_format_value(claim_ref.get('content'))}"
                    ),
                    f"  - 置信度: {_format_value(claim_ref.get('confidence'))}",
                    f"  - 推断标识: {_format_bool(claim_ref.get('is_inference'))}",
                    f"  - 状态: {_format_value(claim_ref.get('status'))}",
                    f"  - Evidence: {_format_id_list(claim_ref.get('evidence_ids'))}",
                    f"  - Risk Flags: {_format_id_list(claim_ref.get('risk_flags'))}",
                ]
            )
        )
    return "\n".join(rendered_claims)


def _render_evidence_index(items: Sequence[JsonObject]) -> str:
    evidence_blocks = []
    for item in items:
        evidence = _as_mapping(item)
        evidence_blocks.append(
            "\n".join(
                [
                    f"- Evidence {evidence.get('evidence_id', NO_RELIABLE_DATA)}",
                    f"  - Product ID: {_format_value(evidence.get('product_id'))}",
                    f"  - Source Type: {_format_value(evidence.get('source_type'))}",
                    f"  - Source URL: {_format_value(evidence.get('source_url'))}",
                    f"  - Screenshot Path: {_format_value(evidence.get('screenshot_path'))}",
                    f"  - 访问时间: {_format_value(evidence.get('access_time'))}",
                    f"  - 置信度: {_format_value(evidence.get('confidence_level'))}",
                    f"  - Content Summary: {_format_value(evidence.get('content_summary'))}",
                    f"  - Limitations: {_format_value(evidence.get('limitations'))}",
                ]
            )
        )
    return "\n".join(evidence_blocks) if evidence_blocks else NO_RELIABLE_DATA


def _render_recommendations(items: Sequence[JsonObject]) -> str:
    rendered = []
    for item in items:
        recommendation = _as_mapping(item)
        rendered.append(
            "\n".join(
                [
                    f"- Recommendation: {_format_value(recommendation.get('recommendation'))}",
                    f"  - Basis Edge: {_format_value(recommendation.get('basis_edge_id'))}",
                    f"  - Claim: {_format_id_list(recommendation.get('claim_ids'))}",
                    f"  - Evidence: {_format_id_list(recommendation.get('evidence_ids'))}",
                    f"  - 推断标识: {_format_bool(recommendation.get('is_inference'))}",
                ]
            )
        )
    return "\n".join(rendered) if rendered else NO_RELIABLE_DATA


def _render_generic_items(items: Sequence[JsonObject]) -> str:
    rendered_items = []
    for index, item in enumerate(items, start=1):
        lines = [f"### Item {index}"]
        for key, value in _as_mapping(item).items():
            if key in {"metadata"}:
                continue
            lines.append(f"- {_humanize_key(key)}: {_format_value(value)}")
        rendered_items.append("\n".join(lines))
    return "\n\n".join(rendered_items) if rendered_items else NO_RELIABLE_DATA


def _ordered_sections(report: ReportData) -> list[ReportSection]:
    return [getattr(report, section_id) for section_id in report.section_order]


def _assert_markdown_is_safe(markdown: str) -> None:
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(markdown):
            raise MarkdownRenderError("Markdown export blocked by sensitive content scan.")


def _report_file_name(report: ReportData) -> str:
    task_id = _safe_file_stem(report.task_id)
    report_id = _safe_file_stem(report.report_id)
    return f"{task_id}_{report_id}.md"


def _safe_file_stem(value: str) -> str:
    safe_value = SAFE_FILE_STEM_PATTERN.sub("_", value).strip("._")
    return safe_value or "report"


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _format_id_list(value: Any) -> str:
    if isinstance(value, list | tuple):
        items = [str(item) for item in value if str(item)]
        return ", ".join(items) if items else NO_RELIABLE_DATA
    if value is None:
        return NO_RELIABLE_DATA
    return str(value)


def _format_value(value: Any) -> str:
    if value is None or value == "" or value == [] or value == {}:
        return NO_RELIABLE_DATA
    if isinstance(value, bool):
        return _format_bool(value)
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, list | tuple):
        return _format_id_list(value)
    if isinstance(value, Mapping):
        return "; ".join(
            f"{_humanize_key(str(key))}={_format_value(item)}" for key, item in value.items()
        )
    return str(value)


def _format_bool(value: Any) -> str:
    if value is True:
        return "是"
    if value is False:
        return "否"
    return NO_RELIABLE_DATA


def _humanize_key(key: str) -> str:
    return key.replace("_", " ").title()


def _unique_count(items: Iterable[str]) -> int:
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return len(seen)
