from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import pytest

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import AnalysisTask
from app.services.profile_service import _build_product_profile

TASK_ID = "task_profile_comparison"
CREATED_AT = datetime(2026, 5, 29, 4, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def completed_demo_state() -> dict[str, Any]:
    workflow = build_analysis_workflow()
    return workflow.invoke(create_initial_state(_stable_task()))


def test_profile_comparison_does_not_create_missing_alternative_competitor(
    completed_demo_state: dict[str, Any],
) -> None:
    state = deepcopy(completed_demo_state)
    state["competition_edges"] = [
        edge for edge in state["competition_edges"] if edge["competition_type"] == "direct"
    ]

    profile = _build_product_profile(state)

    comparison = profile.horizontal_comparison
    assert comparison is not None
    slots = {product.slot.value for product in comparison.compared_products}
    assert "target" in slots
    assert "highest_threat_direct_competitor" in slots
    assert "highest_threat_alternative" not in slots


def test_profile_comparison_each_judgment_has_evidence_drilldown(
    completed_demo_state: dict[str, Any],
) -> None:
    profile = _build_product_profile(completed_demo_state)

    comparison = profile.horizontal_comparison
    assert comparison is not None
    for dimension in comparison.dimensions:
        assert dimension.evidence_ids
        assert dimension.trace_refs
        assert all(value.evidence_ids for value in dimension.values)


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
