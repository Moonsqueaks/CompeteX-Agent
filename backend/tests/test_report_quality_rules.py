from datetime import UTC, datetime

from app.schemas import ReportData, ReportSection
from app.services.report_quality_rules import (
    ReportQualityRules,
    apply_report_quality_rules_to_appendix,
)


def test_report_quality_rules_marks_duplicate_body_text() -> None:
    report = _report_with_sections(
        competitive_landscape_judgment=_section(
            "competitive_landscape_judgment",
            items=[
                {
                    "item_key": "landscape_1",
                    "analysis": (
                        "目标产品需要把自动清理、除臭和维护成本讲清楚，"
                        "否则用户会转向竞品。"
                    ),
                    "recommendation": "把卖点改写成用户收益。",
                }
            ],
        ),
        core_competitor_analysis=_section(
            "core_competitor_analysis",
            items=[
                {
                    "item_key": "battlecard_1",
                    "analysis": (
                        "目标产品需要把自动清理、除臭和维护成本讲清楚，"
                        "否则用户会转向竞品。"
                    ),
                    "target_response": "补充对比话术。",
                }
            ],
        ),
    )

    quality_check = ReportQualityRules().check(report_data=report)

    assert quality_check.status == "needs_revision"
    assert any(issue.issue_type == "duplicated_fact" for issue in quality_check.issues)


def test_report_quality_rules_marks_recommendations_without_action_or_owner() -> None:
    report = _report_with_sections(
        product_strategy_recommendations=_section(
            "product_strategy_recommendations",
            items=[
                {
                    "item_key": "opp_1",
                    "title": "强化核心卖点",
                    "expected_impact": "降低用户理解成本。",
                }
            ],
        )
    )

    quality_check = ReportQualityRules().check(report_data=report)

    assert quality_check.status == "needs_revision"
    assert any(issue.issue_type == "missing_action_owner" for issue in quality_check.issues)


def test_report_quality_rules_requires_full_opportunity_priority_ladder() -> None:
    report = _report_with_sections(
        product_strategy_recommendations=_section(
            "product_strategy_recommendations",
            items=[
                {
                    "item_key": "opp_1",
                    "recommendation": "先改写核心卖点表达。",
                    "owner": "content_ops",
                    "priority": "p0_immediate",
                    "acceptance_signal": "首屏能说清主要差异。",
                    "evidence_boundary": "只基于现有快照证据。",
                },
                {
                    "item_key": "opp_2",
                    "recommendation": "补齐除臭和维护成本证据。",
                    "owner": "research",
                    "priority": "p0_immediate",
                    "acceptance_signal": "证据链补齐后再写确定表述。",
                    "evidence_boundary": "缺失处建议复核。",
                },
                {
                    "item_key": "opp_3",
                    "recommendation": "把竞品异议整理为客服话术。",
                    "owner": "operations",
                    "priority": "p0_immediate",
                    "acceptance_signal": "话术覆盖核心疑问。",
                    "evidence_boundary": "不补写销量或认证。",
                },
            ],
        )
    )

    quality_check = ReportQualityRules().check(report_data=report)

    assert quality_check.status == "needs_revision"
    assert any(issue.issue_type == "opportunity_min_count" for issue in quality_check.issues)


def test_report_quality_rules_marks_overclaim_without_evidence_boundary() -> None:
    report = _report_with_sections(
        conclusion_summary=_section(
            "conclusion_summary",
            items=[
                {
                    "item_key": "summary_1",
                    "conclusion": "目标产品一定是当前类目唯一领先方案。",
                    "reason": "文案表达更集中。",
                    "action": "继续强化核心卖点。",
                }
            ],
        )
    )

    quality_check = ReportQualityRules().check(report_data=report)

    assert quality_check.status == "needs_revision"
    assert any(issue.issue_type == "evidence_overclaim" for issue in quality_check.issues)


def test_report_quality_rules_marks_internal_id_leakage_in_display_text() -> None:
    report = _report_with_sections(
        core_competitor_analysis=_section(
            "core_competitor_analysis",
            items=[
                {
                    "item_key": "battlecard_1",
                    "why_users_compare": "用户会看到 edge_prod_sku_02_prod_sku_04_3 这条关系。",
                    "target_response": "把内部编号换成竞品名称。",
                }
            ],
        )
    )

    quality_check = ReportQualityRules().check(report_data=report)

    assert quality_check.status == "needs_revision"
    assert any(issue.issue_type == "internal_id_leak" for issue in quality_check.issues)


def test_report_quality_rules_appendix_keeps_human_readable_summary() -> None:
    report = _report_with_sections(
        product_strategy_recommendations=_section(
            "product_strategy_recommendations",
            items=[{"item_key": "opp_1", "title": "关注除臭表达"}],
        )
    )
    quality_check = ReportQualityRules().check(report_data=report)

    apply_report_quality_rules_to_appendix(report, quality_check)

    appendix_item = report.evidence_quality_appendix.items[0]
    assert appendix_item["rule_report_quality"]["质检状态"] == "需要修正"
    assert appendix_item["rule_report_quality"]["问题列表"]


def _report_with_sections(**overrides: ReportSection) -> ReportData:
    sections = {
        "conclusion_summary": _section(
            "conclusion_summary",
            items=[
                {
                    "item_key": "summary_ok",
                    "conclusion": "目标产品需要优先解释省心和可信。",
                    "reason": "核心竞品在同类需求中形成替代压力。",
                    "action": "先优化首屏对比话术。",
                    "evidence_ids": ["ev_1"],
                }
            ],
        ),
        "competitive_landscape_judgment": _section(
            "competitive_landscape_judgment",
            items=[
                {
                    "item_key": "landscape_ok",
                    "competition_meaning": "该切片说明用户会横向比较清理和除臭。",
                    "action": "补齐价格解释。",
                    "evidence_ids": ["ev_1"],
                }
            ],
        ),
        "core_competitor_analysis": _section(
            "core_competitor_analysis",
            items=[
                {
                    "item_key": "battlecard_ok",
                    "why_users_compare": "解决同一类清理负担。",
                    "target_response": "突出可视化和维护成本解释。",
                    "evidence_ids": ["ev_1"],
                }
            ],
        ),
        "user_decision_chain_analysis": _section(
            "user_decision_chain_analysis",
            items=[
                {
                    "item_key": "decision_ok",
                    "business_meaning": "用户会在信任建立阶段被售后信息影响。",
                    "action": "补齐售后说明。",
                    "evidence_ids": ["ev_1"],
                }
            ],
        ),
        "target_opportunities_and_risks": _section(
            "target_opportunities_and_risks",
            items=[
                {
                    "item_key": "gap_ok",
                    "dimension": "表达差距",
                    "impact_on_decision": "影响用户理解长期成本。",
                    "recommendation": "把维护成本写成用户收益。",
                    "evidence_ids": ["ev_1"],
                }
            ],
        ),
        "product_strategy_recommendations": _section(
            "product_strategy_recommendations",
            items=[
                {
                    "item_key": "opp_ok",
                    "recommendation": "重写核心竞品对比话术。",
                    "owner": "content_ops",
                    "expected_impact": "提升首屏理解效率。",
                    "evidence_ids": ["ev_1"],
                }
            ],
        ),
        "evidence_quality_appendix": _section("evidence_quality_appendix", items=[{}]),
        "analysis_process_appendix": _section("analysis_process_appendix", items=[{}]),
    }
    sections.update(overrides)
    return ReportData(
        report_id="report_quality_rules_test",
        task_id="task_quality_rules_test",
        generated_at=datetime(2026, 6, 8, tzinfo=UTC),
        section_order=[
            "conclusion_summary",
            "competitive_landscape_judgment",
            "core_competitor_analysis",
            "user_decision_chain_analysis",
            "target_opportunities_and_risks",
            "product_strategy_recommendations",
            "evidence_quality_appendix",
            "analysis_process_appendix",
        ],
        **sections,
    )


def _section(section_id: str, *, items: list[dict[str, object]]) -> ReportSection:
    return ReportSection(
        section_id=section_id,
        title=section_id,
        summary=f"{section_id} summary",
        items=items,
        claim_ids=["claim_1"],
        evidence_ids=["ev_1"],
        risk_flags=[],
    )
