import re
from collections import Counter
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from app.schemas import ReportData, ReportQualityCheck, ReportQualityIssue, ReportSection

BODY_SECTION_IDS = {
    "conclusion_summary",
    "competitive_landscape_judgment",
    "core_competitor_analysis",
    "user_decision_chain_analysis",
    "target_opportunities_and_risks",
    "product_strategy_recommendations",
}
INTERNAL_ID_PATTERN = re.compile(
    r"\b(?:task|trace|run|edge|claim|ev|evidence|prod|product|sku)_[A-Za-z0-9_]+\b"
    r"|\b[A-Za-z]+ Id\b"
)
ABSOLUTE_CLAIM_PATTERN = re.compile(
    r"(一定|必然|绝对|完全|全部|实时|官方认证|排名第一|最高|最低|唯一|直接证明|确定领先)"
)
ACTION_KEYS = {
    "action",
    "recommendation",
    "target_response",
    "response_talk_track",
    "first_action",
}
OWNER_KEYS = {"owner", "responsibility_type", "execution_owner", "responsible_team"}
BUSINESS_KEYS = {
    "action",
    "business_meaning",
    "competition_meaning",
    "expected_impact",
    "impact_on_decision",
    "largest_opportunity",
    "largest_threat",
    "reason",
    "recommendation",
    "target_response",
    "why_now",
    "why_users_compare",
}


class ReportQualityRules:
    def check(
        self,
        *,
        report_data: ReportData,
        task_id: str | None = None,
        report_id: str | None = None,
        checked_at: datetime | None = None,
    ) -> ReportQualityCheck:
        task_id = task_id or report_data.task_id
        report_id = report_id or report_data.report_id
        created_at = checked_at or datetime.now(UTC)
        issues: list[ReportQualityIssue] = []

        body_sections = [
            section
            for section in _ordered_sections(report_data)
            if section.section_id in BODY_SECTION_IDS
        ]
        issues.extend(_duplicate_fact_issues(report_id, body_sections))
        issues.extend(_internal_id_issues(report_id, body_sections))
        issues.extend(
            _recommendation_action_issues(
                report_id,
                report_data.product_strategy_recommendations,
            )
        )
        issues.extend(_business_meaning_issues(report_id, body_sections))
        issues.extend(_overclaim_issues(report_id, body_sections))

        status = "passed" if not issues else "needs_revision"
        summary = (
            "规则质检通过，正文没有发现明显重复、内部编号泄漏或证据越界。"
            if not issues
            else f"规则质检发现 {len(issues)} 个需要关注的问题，建议优先修正文案表达。"
        )
        return ReportQualityCheck(
            quality_check_id=f"report_quality_rules_{_safe_id(report_id)}",
            task_id=task_id,
            report_id=report_id,
            status=status,
            summary=summary,
            issues=issues,
            metrics={
                "rule_version": "report_quality_rules_v1",
                "checked_body_sections": len(body_sections),
                "issue_count": len(issues),
                "issue_types": dict(Counter(issue.issue_type for issue in issues)),
            },
            created_at=created_at,
        )


def apply_report_quality_rules_to_appendix(
    report_data: ReportData,
    quality_check: ReportQualityCheck,
) -> None:
    if not report_data.evidence_quality_appendix.items:
        report_data.evidence_quality_appendix.items.append({})
    report_data.evidence_quality_appendix.items[0]["rule_report_quality"] = {
        "质检状态": "通过" if quality_check.status == "passed" else "需要修正",
        "摘要": quality_check.summary,
        "问题类型": quality_check.metrics.get("issue_types", {}),
        "问题列表": [
            {
                "类型": issue.issue_type,
                "位置": _issue_location_label(issue),
                "问题": issue.message,
                "建议": issue.suggestion,
                "证据边界": issue.evidence_boundary,
            }
            for issue in quality_check.issues
        ],
    }


def _ordered_sections(report_data: ReportData) -> list[ReportSection]:
    sections: list[ReportSection] = []
    seen: set[str] = set()
    for section_id in report_data.section_order:
        section = getattr(report_data, section_id, None)
        if isinstance(section, ReportSection):
            sections.append(section)
            seen.add(section.section_id)
    for section_id in BODY_SECTION_IDS:
        section = getattr(report_data, section_id, None)
        if isinstance(section, ReportSection) and section.section_id not in seen:
            sections.append(section)
    return sections


def _duplicate_fact_issues(
    report_id: str,
    sections: list[ReportSection],
) -> list[ReportQualityIssue]:
    seen: dict[str, tuple[str, str]] = {}
    issues: list[ReportQualityIssue] = []
    for section in sections:
        for key, text in _display_texts(section):
            normalized = _normalize_text(text)
            if len(normalized) < 28:
                continue
            previous = seen.get(normalized)
            if previous is None:
                seen[normalized] = (section.section_id, key)
                continue
            issues.append(
                _issue(
                    report_id,
                    len(issues) + 1,
                    issue_type="duplicated_fact",
                    severity="medium",
                    section_id=section.section_id,
                    item_key=key,
                    message="正文里出现了重复段落或重复事实，读起来像在搬运同一条素材。",
                    suggestion="保留首次出现的事实，后续章节改写成影响、差距或行动建议。",
                    evidence_boundary="重复内容不增加证据强度，只会降低报告可读性。",
                )
            )
    return issues


def _internal_id_issues(
    report_id: str,
    sections: list[ReportSection],
) -> list[ReportQualityIssue]:
    issues: list[ReportQualityIssue] = []
    for section in sections:
        for key, text in _display_texts(section):
            if INTERNAL_ID_PATTERN.search(text):
                issues.append(
                    _issue(
                        report_id,
                        len(issues) + 1,
                        issue_type="internal_id_leak",
                        severity="high",
                        section_id=section.section_id,
                        item_key=key,
                        message="正文里出现了任务、证据、结论或竞争边等内部编号。",
                        suggestion="正文只保留用户能理解的名称和结论，内部编号放到 Trace 或附录。",
                        evidence_boundary="内部编号是审计信息，不应成为用户阅读报告的主体内容。",
                    )
                )
    return issues


def _recommendation_action_issues(
    report_id: str,
    section: ReportSection,
) -> list[ReportQualityIssue]:
    issues: list[ReportQualityIssue] = []
    for index, item in enumerate(section.items):
        key = _item_key(item, index)
        has_action = any(_string_value(item.get(action_key)) for action_key in ACTION_KEYS)
        has_owner = any(_string_value(item.get(owner_key)) for owner_key in OWNER_KEYS)
        if not has_action or not has_owner:
            issues.append(
                _issue(
                    report_id,
                    len(issues) + 1,
                    issue_type="missing_action_owner",
                    severity="high",
                    section_id=section.section_id,
                    item_key=key,
                    message="行动建议缺少清晰动作或责任方向。",
                    suggestion="补齐要做什么、由谁负责、针对哪个卖点/证据/页面执行。",
                    evidence_boundary="没有行动和责任方向的建议不能作为交付结论。",
                )
            )
    return issues


def _business_meaning_issues(
    report_id: str,
    sections: list[ReportSection],
) -> list[ReportQualityIssue]:
    issues: list[ReportQualityIssue] = []
    for section in sections:
        if section.section_id == "evidence_quality_appendix":
            continue
        for index, item in enumerate(section.items):
            key = _item_key(item, index)
            if any(_string_value(item.get(field)) for field in BUSINESS_KEYS):
                continue
            text = " ".join(_text_values(item))
            if any(
                word in text
                for word in ("影响", "建议", "机会", "风险", "回应", "优先", "决策")
            ):
                continue
            issues.append(
                _issue(
                    report_id,
                    len(issues) + 1,
                    issue_type="missing_business_meaning",
                    severity="medium",
                    section_id=section.section_id,
                    item_key=key,
                    message="分析项只像在描述资料，没有回答对业务决策有什么影响。",
                    suggestion="补一句该判断影响谁、影响哪个购买环节、下一步该做什么。",
                    evidence_boundary="信息描述必须转化成业务含义后才适合进入正文。",
                )
            )
    return issues


def _overclaim_issues(
    report_id: str,
    sections: list[ReportSection],
) -> list[ReportQualityIssue]:
    issues: list[ReportQualityIssue] = []
    for section in sections:
        for index, item in enumerate(section.items):
            key = _item_key(item, index)
            text = " ".join(_text_values(item))
            if not ABSOLUTE_CLAIM_PATTERN.search(text):
                continue
            evidence_ids = _string_list(item.get("evidence_ids")) or section.evidence_ids
            has_boundary = any(
                word in text
                for word in ("推断", "暂无可靠数据", "建议复核", "证据不足")
            )
            if evidence_ids and has_boundary:
                continue
            issues.append(
                _issue(
                    report_id,
                    len(issues) + 1,
                    issue_type="evidence_overclaim",
                    severity="high",
                    section_id=section.section_id,
                    item_key=key,
                    message="证据不足或缺少边界时使用了过于确定的表述。",
                    suggestion="改成保守表述，并明确这是推断、暂无可靠数据或需要复核。",
                    evidence_boundary="没有足够证据时不能写成确定事实或实时市场结论。",
                )
            )
    return issues


def _display_texts(section: ReportSection) -> list[tuple[str, str]]:
    texts: list[tuple[str, str]] = [("summary", section.summary)]
    for index, item in enumerate(section.items):
        key = _item_key(item, index)
        texts.extend((key, text) for text in _text_values(item))
    return texts


def _text_values(value: Any, *, parent_key: str | None = None) -> list[str]:
    if isinstance(value, str):
        if parent_key and _is_internal_key(parent_key):
            return []
        return [value.strip()] if value.strip() else []
    if isinstance(value, Mapping):
        texts: list[str] = []
        for key, child in value.items():
            key_text = str(key)
            if _is_internal_key(key_text):
                continue
            texts.extend(_text_values(child, parent_key=key_text))
        return texts
    if isinstance(value, list):
        texts: list[str] = []
        for item in value:
            texts.extend(_text_values(item, parent_key=parent_key))
        return texts
    return []


def _item_key(item: Mapping[str, Any], index: int) -> str:
    for key in ("item_key", "battlecard_id", "gap_id", "opportunity_id", "edge_id"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return f"item_{index + 1}"


def _is_internal_key(key: str) -> bool:
    return key.endswith("_id") or key.endswith("_ids") or key in {
        "id",
        "item_key",
        "task_id",
        "trace_id",
        "edge_id",
        "claim_ids",
        "evidence_ids",
        "product_id",
    }


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text).strip("。；;,.，")


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value)[:80]


def _string_value(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _issue(
    report_id: str,
    index: int,
    *,
    issue_type: str,
    severity: str,
    section_id: str,
    item_key: str | None,
    message: str,
    suggestion: str,
    evidence_boundary: str,
) -> ReportQualityIssue:
    return ReportQualityIssue(
        issue_id=f"rq_{_safe_id(report_id)}_{index:02d}_{issue_type}",
        issue_type=issue_type,
        severity=severity,
        section_id=section_id,
        item_key=item_key,
        message=message,
        suggestion=suggestion,
        evidence_boundary=evidence_boundary,
    )


def _issue_location_label(issue: ReportQualityIssue) -> str:
    if issue.section_id and issue.item_key:
        return f"{issue.section_id} / {issue.item_key}"
    return issue.section_id or "整份报告"
