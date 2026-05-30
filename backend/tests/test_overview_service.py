from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import pytest

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AnalysisTask,
    BattlefieldSliceSelection,
    DecisionUsabilityStatus,
    OverviewData,
)
from app.services.overview_service import _build_overview_data

TASK_ID = "task_overview_service"
CREATED_AT = datetime(2026, 5, 29, 4, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def completed_demo_state() -> dict[str, Any]:
    workflow = build_analysis_workflow()
    return workflow.invoke(create_initial_state(_stable_task()))


def test_overview_service_builds_pm_readable_overview_from_frozen_demo(
    completed_demo_state: dict[str, Any],
) -> None:
    overview = _build_overview_data(
        completed_demo_state,
        BattlefieldSliceSelection(),
        "overview_task_overview_service_all",
    )

    assert isinstance(overview, OverviewData)
    assert overview.task_id == TASK_ID
    assert overview.analysis_scope.sku_count == 14
    assert overview.analysis_scope.scope_notice == (
        "本报告基于用户提供的脱敏 SKU 快照，不代表实时全网数据。"
    )
    assert overview.one_sentence_judgment.content.startswith("小佩自动猫砂盆")
    assert overview.decision_usability.value == DecisionUsabilityStatus.READY
    assert overview.key_competitors
    assert overview.key_competitors[0].evidence_ids
    assert overview.action_recommendations


def test_overview_service_does_not_mark_unresolved_qa_risk_as_ready(
    completed_demo_state: dict[str, Any],
) -> None:
    state = deepcopy(completed_demo_state)
    state["review_tasks"][0]["status"] = "open"
    state["review_tasks"][0]["severity"] = "error"

    overview = _build_overview_data(
        state,
        BattlefieldSliceSelection(),
        "overview_task_overview_service_open_qa",
    )

    assert overview.decision_usability.value != DecisionUsabilityStatus.READY
    assert overview.decision_usability.value == DecisionUsabilityStatus.DIRECTIONAL_ONLY


def test_overview_service_changes_key_competitor_order_when_slice_changes(
    completed_demo_state: dict[str, Any],
) -> None:
    overall = _build_overview_data(
        completed_demo_state,
        BattlefieldSliceSelection(),
        "overview_task_overview_service_all",
    )
    price_slice = _build_overview_data(
        completed_demo_state,
        BattlefieldSliceSelection(price_band="1000-1500"),
        "overview_task_overview_service_1000_1500",
    )

    overall_ids = [competitor.product_id for competitor in overall.key_competitors]
    price_slice_ids = [competitor.product_id for competitor in price_slice.key_competitors]

    assert overall_ids
    assert price_slice_ids
    assert overall_ids != price_slice_ids


def test_overview_main_copy_does_not_expose_raw_schema_field_names(
    completed_demo_state: dict[str, Any],
) -> None:
    overview = _build_overview_data(
        completed_demo_state,
        BattlefieldSliceSelection(),
        "overview_task_overview_service_copy",
    )

    main_copy = "\n".join(_main_copy_lines(overview))

    assert "Product" not in main_copy
    assert "Claim" not in main_copy
    assert "Evidence" not in main_copy


def _stable_task() -> AnalysisTask:
    return AnalysisTask(
        task_id=TASK_ID,
        target_product_name="小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
        target_product_url="https://v.douyin.com/mv8e4KRLLwc/",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        data_source_mode="demo_snapshot",
        status="created",
        research_text="多猫家庭关注除臭稳定性、自动清理可靠性、维护成本和小户型摆放体验。",
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        metadata={},
    )


def _main_copy_lines(overview: OverviewData) -> list[str]:
    lines = [
        overview.one_sentence_judgment.content,
        overview.judgment_strength.label,
        overview.judgment_strength.reason,
        overview.decision_usability.label,
        overview.decision_usability.reason,
        *overview.status_reasons,
    ]
    for competitor in overview.key_competitors:
        lines.extend(
            [
                competitor.product_name,
                competitor.inclusion_reason,
                competitor.evidence_credibility.label,
                competitor.evidence_credibility.reason,
            ]
        )
    for finding in [*overview.opportunities, *overview.risk_points]:
        lines.extend([finding.title, finding.description])
    for action in overview.action_recommendations:
        lines.extend([action.title, action.description, action.expected_impact or ""])
    return lines
