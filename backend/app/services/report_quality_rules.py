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
FORMAL_NARRATIVE_SECTION_ORDER = [
    "report_info",
    "executive_summary",
    "research_question_and_scope",
    "category_context",
    "competitor_selection",
    "competitive_landscape",
    "core_competitor_battlecards",
    "decision_chain",
    "gap_matrix",
    "opportunity_map",
    "risk_and_evidence_boundary",
    "appendix_traceability",
]
FORMAL_DECISION_STAGES = {
    "information_reach",
    "interest_formation",
    "capability_understanding",
    "trust_building",
    "decision_completion",
}
INTERNAL_ID_PATTERN = re.compile(
    r"\b(?:task|trace|run|edge|claim|ev|evidence|prod|product|sku)_[A-Za-z0-9_]+\b"
    r"|\b[A-Za-z]+ Id\b"
)
ABSOLUTE_CLAIM_PATTERN = re.compile(
    r"(一定|必然|绝对|完全|全部|实时|官方认证|排名第一|最高|最低|唯一|直接证明|确定领先)"
)
UNSUPPORTED_MARKET_CLAIM_PATTERN = re.compile(
    r"(市场份额|市场规模|全网排名|排名第一|销量最高|销量第一|行业第一|增长率|渗透率|认证齐全|官方认证)"
)
SAFETY_OVERCLAIM_PATTERN = re.compile(
    r"(绝对安全|完全安全|零风险|不会夹|一定不会|100%安全|彻底除臭|完全除臭|认证齐全)"
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
        issues.extend(_formal_section_coverage_issues(report_id, report_data))
        issues.extend(_battlecard_count_issues(report_id, report_data))
        issues.extend(_gap_matrix_count_issues(report_id, report_data))
        issues.extend(_opportunity_count_issues(report_id, report_data))
        issues.extend(_decision_chain_coverage_issues(report_id, report_data))
        issues.extend(_research_scope_issues(report_id, report_data))
        issues.extend(_unsupported_market_claim_issues(report_id, report_data))
        issues.extend(_safety_language_issues(report_id, report_data))
        issues.extend(_action_owner_required_issues(report_id, report_data))

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
                "formal_section_count": len(_narrative_sections(report_data)),
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


def _formal_section_coverage_issues(
    report_id: str,
    report_data: ReportData,
) -> list[ReportQualityIssue]:
    sections = _narrative_sections(report_data)
    section_ids = [section.get("section_id") for section in sections]
    missing = [
        section_id for section_id in FORMAL_NARRATIVE_SECTION_ORDER
        if section_id not in section_ids
    ]
    if not missing:
        return []
    return [
        _issue(
            report_id,
            1,
            issue_type="section_coverage",
            severity="high",
            section_id="narrative_report",
            item_key=None,
            message=f"正式报告缺少章节：{', '.join(missing)}。",
            suggestion=(
                "补齐封面、执行摘要、研究范围、类目背景、竞品分层、格局、"
                "Battlecard、决策链、差距、机会、风险和附录 12 个章节。"
            ),
            evidence_boundary="章节不完整会使报告仍像素材整理，不能作为正式竞品分析交付。",
        )
    ]


def _battlecard_count_issues(
    report_id: str,
    report_data: ReportData,
) -> list[ReportQualityIssue]:
    battlecard_section = _narrative_section(report_data, "core_competitor_battlecards")
    items = _section_items(battlecard_section) or report_data.core_competitor_analysis.items
    sample_note = _section_text(battlecard_section)
    if len(items) >= 3 or "样本不足" in sample_note or "暂无可靠数据" in sample_note:
        return []
    return [
        _issue(
            report_id,
            1,
            issue_type="battlecard_min_count",
            severity="high",
            section_id="core_competitor_battlecards",
            item_key=None,
            message="核心竞品 Battlecard 少于 3 个，且没有解释样本不足。",
            suggestion="至少输出 3 个核心 Battlecard；若样本确实不足，明确写明原因和补采建议。",
            evidence_boundary="核心竞品不足会削弱竞品选择与分层的正式性。",
        )
    ]


def _gap_matrix_count_issues(
    report_id: str,
    report_data: ReportData,
) -> list[ReportQualityIssue]:
    gap_section = _narrative_section(report_data, "gap_matrix")
    items = _section_items(gap_section) or report_data.target_opportunities_and_risks.items
    gap_types = {
        _string_value(item.get("gap_type")) or _string_value(item.get("dimension"))
        for item in items
        if isinstance(item, Mapping)
    }
    if len(items) >= 6 and len(gap_types) >= 3:
        return []
    return [
        _issue(
            report_id,
            1,
            issue_type="gap_matrix_min_count",
            severity="medium",
            section_id="gap_matrix",
            item_key=None,
            message="差距矩阵未达到 6 条或未覆盖至少 3 类差距。",
            suggestion="补齐功能、证据、表达、转化、维护成本、信任/安全等差距维度。",
            evidence_boundary="差距矩阵过薄会让报告停留在少量 SKU 字段整理。",
        )
    ]


def _opportunity_count_issues(
    report_id: str,
    report_data: ReportData,
) -> list[ReportQualityIssue]:
    opportunity_section = _narrative_section(report_data, "opportunity_map")
    items = (
        _section_items(opportunity_section)
        or report_data.product_strategy_recommendations.items
    )
    priorities = {
        _string_value(item.get("priority"))
        for item in items
        if isinstance(item, Mapping)
    }
    required_priorities = {"p0_immediate", "p1_current_iteration", "p2_follow_up_validation"}
    if len(items) >= 3 and required_priorities.issubset(priorities):
        return []
    return [
        _issue(
            report_id,
            1,
            issue_type="opportunity_min_count",
            severity="high",
            section_id="opportunity_map",
            item_key=None,
            message="机会地图少于 3 条，或没有明确 P0/P1/P2 优先级。",
            suggestion="至少输出 3 条机会，包含优先级、动作类型、责任方向、验收信号和证据边界。",
            evidence_boundary="没有优先级和执行口径的建议不能作为产品/运营动作清单。",
        )
    ]


def _decision_chain_coverage_issues(
    report_id: str,
    report_data: ReportData,
) -> list[ReportQualityIssue]:
    decision_section = _narrative_section(report_data, "decision_chain")
    items = _section_items(decision_section) or report_data.user_decision_chain_analysis.items
    stages = {
        _string_value(item.get("decision_stage"))
        for item in items
        if isinstance(item, Mapping)
    }
    missing = sorted(FORMAL_DECISION_STAGES - stages)
    if not missing:
        return []
    return [
        _issue(
            report_id,
            1,
            issue_type="decision_chain_coverage",
            severity="medium",
            section_id="decision_chain",
            item_key=None,
            message=f"用户决策链未覆盖完整 5 阶段：{', '.join(missing)}。",
            suggestion="补齐信息触达、兴趣形成、能力理解、信任建立和下单决策五个阶段。",
            evidence_boundary="决策链缺阶段会导致用户为什么比较、为什么犹豫解释不完整。",
        )
    ]


def _research_scope_issues(
    report_id: str,
    report_data: ReportData,
) -> list[ReportQualityIssue]:
    scope_section = _narrative_section(report_data, "research_question_and_scope")
    text = _section_text(scope_section)
    required_terms = ("研究", "范围", "竞品", "数据")
    if all(term in text for term in required_terms):
        return []
    return [
        _issue(
            report_id,
            1,
            issue_type="research_scope_present",
            severity="high",
            section_id="research_question_and_scope",
            item_key=None,
            message="研究问题与分析范围没有清楚说明研究问题、数据范围或竞品选择口径。",
            suggestion="补充研究问题、数据来源、分析边界、竞品选择与排除口径。",
            evidence_boundary="没有范围声明时，读者无法判断结论可采纳边界。",
        )
    ]


def _unsupported_market_claim_issues(
    report_id: str,
    report_data: ReportData,
) -> list[ReportQualityIssue]:
    if _is_internet_ai_report(report_data):
        return _pattern_issues(
            report_id=report_id,
            report_data=report_data,
            pattern=UNSUPPORTED_MARKET_CLAIM_PATTERN,
            issue_type="no_unsupported_market_claim",
            message="报告出现可能无证据支撑的用户规模、下载量、排名、模型能力或定价表达。",
            suggestion="删除或改写为暂无可靠数据、建议复核，除非能绑定直接 Evidence。",
            evidence_boundary=(
                "本轮 AI 助手公开页快照不能支持用户规模、下载量、"
                "模型能力、排名和定价结论。"
            ),
        )
    return _pattern_issues(
        report_id=report_id,
        report_data=report_data,
        pattern=UNSUPPORTED_MARKET_CLAIM_PATTERN,
        issue_type="no_unsupported_market_claim",
        message="报告出现可能无证据支撑的市场规模、排名、销量、认证或份额表达。",
        suggestion="删除或改写为暂无可靠数据、建议复核，除非能绑定直接 Evidence。",
        evidence_boundary="本轮快照不能支持全网市场份额、排名、销量和认证结论。",
    )


def _safety_language_issues(
    report_id: str,
    report_data: ReportData,
) -> list[ReportQualityIssue]:
    if _is_internet_ai_report(report_data):
        return _pattern_issues(
            report_id=report_id,
            report_data=report_data,
            pattern=SAFETY_OVERCLAIM_PATTERN,
            issue_type="safety_conservative_language",
            message="报告中存在隐私、安全、模型能力或免费承诺的绝对化表达。",
            suggestion="改成保守表述，并明确证据边界或建议复核。",
            evidence_boundary="隐私、安全和模型能力相关表达必须保守，不能写成绝对承诺。",
        )
    return _pattern_issues(
        report_id=report_id,
        report_data=report_data,
        pattern=SAFETY_OVERCLAIM_PATTERN,
        issue_type="safety_conservative_language",
        message="报告中存在宠物安全、电器安全或除臭效果的绝对化表达。",
        suggestion="改成保守表述，并明确证据边界或建议复核。",
        evidence_boundary="安全和电器相关表达必须保守，不能写成绝对承诺。",
    )


def _action_owner_required_issues(
    report_id: str,
    report_data: ReportData,
) -> list[ReportQualityIssue]:
    opportunity_section = _narrative_section(report_data, "opportunity_map")
    items = (
        _section_items(opportunity_section)
        or report_data.product_strategy_recommendations.items
    )
    issues: list[ReportQualityIssue] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            continue
        has_owner = any(_string_value(item.get(key)) for key in OWNER_KEYS)
        has_boundary = bool(
            _string_value(item.get("evidence_boundary"))
            or _string_value(item.get("acceptance_signal"))
        )
        if has_owner and has_boundary:
            continue
        issues.append(
            _issue(
                report_id,
                len(issues) + 1,
                issue_type="action_owner_required",
                severity="high",
                section_id="opportunity_map",
                item_key=_item_key(item, index),
                message="机会/行动建议缺少责任方向、验收信号或证据边界。",
                suggestion=(
                    "为每条建议补齐 owner/responsibility_type、acceptance_signal "
                    "和 evidence_boundary。"
                ),
                evidence_boundary="行动建议必须可执行、可验收，并说明证据不足时不能声称什么。",
            )
        )
    return issues


def _pattern_issues(
    *,
    report_id: str,
    report_data: ReportData,
    pattern: re.Pattern[str],
    issue_type: str,
    message: str,
    suggestion: str,
    evidence_boundary: str,
) -> list[ReportQualityIssue]:
    issues: list[ReportQualityIssue] = []
    for section in _narrative_sections(report_data):
        section_id = _string_value(section.get("section_id")) or "narrative_report"
        for key, text in _narrative_display_texts(section):
            if not pattern.search(text):
                continue
            if any(term in text for term in ("暂无可靠数据", "建议复核", "不能", "不支持")):
                continue
            issues.append(
                _issue(
                    report_id,
                    len(issues) + 1,
                    issue_type=issue_type,
                    severity="high",
                    section_id=section_id,
                    item_key=key,
                    message=message,
                    suggestion=suggestion,
                    evidence_boundary=evidence_boundary,
                )
            )
    return issues


def _display_texts(section: ReportSection) -> list[tuple[str, str]]:
    texts: list[tuple[str, str]] = [("summary", section.summary)]
    for index, item in enumerate(section.items):
        key = _item_key(item, index)
        texts.extend((key, text) for text in _text_values(item))
    return texts


def _narrative_sections(report_data: ReportData) -> list[Mapping[str, Any]]:
    narrative_report = report_data.narrative_report
    if not isinstance(narrative_report, Mapping):
        return []
    sections = narrative_report.get("sections")
    if not isinstance(sections, list):
        return []
    return [section for section in sections if isinstance(section, Mapping)]


def _is_internet_ai_report(report_data: ReportData) -> bool:
    narrative_report = report_data.narrative_report
    if not isinstance(narrative_report, Mapping):
        return False
    domain_key = _string_value(narrative_report.get("domain_key"))
    return domain_key == "internet_ai_assistant"


def _narrative_section(
    report_data: ReportData,
    section_id: str,
) -> Mapping[str, Any]:
    for section in _narrative_sections(report_data):
        if section.get("section_id") == section_id:
            return section
    return {}


def _section_items(section: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    items = section.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, Mapping)]


def _section_text(section: Mapping[str, Any]) -> str:
    return " ".join(text for _, text in _narrative_display_texts(section))


def _narrative_display_texts(section: Mapping[str, Any]) -> list[tuple[str, str]]:
    texts: list[tuple[str, str]] = []
    title = _string_value(section.get("title"))
    if title:
        texts.append(("title", title))
    paragraphs = section.get("paragraphs")
    if isinstance(paragraphs, list):
        for index, paragraph in enumerate(paragraphs):
            text = _string_value(paragraph)
            if text:
                texts.append((f"paragraph_{index + 1}", text))
    for index, item in enumerate(_section_items(section)):
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
