from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from pydantic import BaseModel, ValidationError

from app.schemas import (
    ActionPriority,
    EvidenceCredibilityStatus,
    OverviewData,
    ResponsibilityType,
    RiskFlag,
)

NOW = datetime(2026, 5, 29, 9, 0, tzinfo=UTC)


def test_overview_data_accepts_valid_pm_readable_example() -> None:
    overview = OverviewData.model_validate(_overview_payload())

    assert overview.one_sentence_judgment.content.startswith("目标产品")
    assert overview.analysis_scope.sku_count == 14
    assert overview.key_competitors[0].evidence_credibility.value == (
        EvidenceCredibilityStatus.DIRECTLY_ADOPTABLE
    )
    assert overview.action_recommendations[0].priority == ActionPriority.P0
    assert overview.action_recommendations[0].responsibility_type == (
        ResponsibilityType.CONTENT_EXPRESSION
    )


@pytest.mark.parametrize("missing_field", ["priority", "responsibility_type"])
def test_overview_action_recommendation_requires_priority_and_responsibility(
    missing_field: str,
) -> None:
    payload = _overview_payload()
    payload["action_recommendations"][0].pop(missing_field)

    with pytest.raises(ValidationError):
        OverviewData.model_validate(payload)


def test_overview_key_conclusion_without_drilldown_reference_is_marked_risky() -> None:
    payload = _overview_payload()
    payload["opportunities"][0]["evidence_ids"] = []
    payload["opportunities"][0]["trace_refs"] = []

    overview = OverviewData.model_validate(payload)
    opportunity = overview.opportunities[0]

    assert RiskFlag.MISSING_EVIDENCE in opportunity.risk_flags
    assert opportunity.missing_reference_reason == "缺少 Evidence 或 Trace 下钻引用。"


def test_overview_unshowable_key_conclusion_is_rejected() -> None:
    payload = _overview_payload()
    payload["one_sentence_judgment"]["content"] = ""

    with pytest.raises(ValidationError):
        OverviewData.model_validate(payload)


def test_overview_schemas_can_be_included_in_openapi() -> None:
    class SchemaBundle(BaseModel):
        overview: OverviewData

    api = FastAPI()

    @api.get("/schema-test", response_model=SchemaBundle)
    def schema_test() -> dict[str, Any]:
        return {}

    schemas = api.openapi()["components"]["schemas"]
    expected_schema_names = {
        "AnalysisScopeSummary",
        "OverviewActionRecommendation",
        "OverviewConclusion",
        "OverviewData",
        "OverviewDrilldownReference",
        "OverviewDrilldownType",
        "OverviewFinding",
        "OverviewFindingType",
        "OverviewKeyCompetitor",
        "OverviewKeyCompetitorType",
    }
    assert expected_schema_names.issubset(schemas)


def _overview_payload() -> dict[str, Any]:
    return {
        "overview_id": "overview_task_001",
        "task_id": "task_001",
        "generated_at": NOW,
        "one_sentence_judgment": {
            "content": "目标产品在中高价格带具备直接竞争力，但内容证据仍需补强。",
            "evidence_ids": ["ev_sku_02"],
            "trace_refs": ["analysis_agent:run_001"],
            "drilldown_refs": [_drilldown("battlefield", "查看竞争图谱", "edge_sku_02_sku_01")],
            "risk_flags": [],
        },
        "judgment_strength": _display_status(
            "directional_judgment",
            "方向性判断",
            "核心关系有证据支撑，但仍存在部分访问时间缺失。",
        ),
        "decision_usability": _display_status(
            "decision_with_caution",
            "谨慎用于决策",
            "QA 打回已解决，但历史缺失字段仍需在 Trace 中保留。",
        ),
        "status_reasons": ["存在可追溯 Evidence；部分访问时间缺失。"],
        "analysis_scope": _analysis_scope_payload(),
        "key_competitors": [
            {
                "competitor_type": "highest_threat_direct_competitor",
                "product_id": "prod_competitor_001",
                "sku_id": "sku_01",
                "product_name": "竞品自动猫砂盆",
                "brand": "竞品品牌",
                "primary_image_path": "/assets/raw/sku_01/cover.jpg",
                "relationship_label": "head_to_head",
                "threat_level": "high_threat",
                "evidence_credibility": _display_status(
                    "directly_adoptable",
                    "可直接采用",
                    "价格、卖点和截图证据均可追溯。",
                ),
                "inclusion_reason": "在同一价格带和多猫家庭场景下分数最高。",
                "evidence_ids": ["ev_sku_01"],
                "trace_refs": ["analysis_agent:edge_sku_02_sku_01"],
                "drilldown_refs": [
                    _drilldown("battlefield", "查看竞争关系", "edge_sku_02_sku_01")
                ],
                "risk_flags": [],
            }
        ],
        "opportunities": [
            {
                "finding_id": "opp_content_001",
                "finding_type": "expression_opportunity",
                "title": "强化除臭证据表达",
                "description": "详情页可优先补充除臭稳定性证据，降低直接竞品拦截。",
                "evidence_ids": ["ev_sku_02"],
                "trace_refs": ["writer_agent:report_001"],
                "drilldown_refs": [_drilldown("report", "查看报告章节", "recommendations")],
                "risk_flags": [],
            }
        ],
        "risk_points": [
            {
                "finding_id": "risk_evidence_001",
                "finding_type": "evidence_risk",
                "title": "访问时间不完整",
                "description": "部分证据访问时间缺失，不能当作实时价格判断。",
                "evidence_ids": ["ev_sku_01"],
                "trace_refs": ["qa_agent:review_001"],
                "drilldown_refs": [_drilldown("trace", "查看 QA 打回", "review_001")],
                "risk_flags": ["missing_access_time"],
            }
        ],
        "action_recommendations": [
            {
                "action_id": "action_001",
                "title": "补齐详情页除臭证据",
                "description": "优先补充与除臭稳定性相关的截图证据和说明。",
                "priority": "p0_immediate",
                "responsibility_type": "content_expression",
                "expected_impact": "降低高威胁直接竞品的内容拦截。",
                "evidence_ids": ["ev_sku_02"],
                "trace_refs": ["analysis_agent:claim_001"],
                "drilldown_refs": [_drilldown("profile", "查看产品画像", "prod_target")],
                "risk_flags": [],
            }
        ],
        "current_slice": {
            "price_band": "1500-2000",
            "persona": "multi_cat_household",
            "scenario": "odor_control",
        },
        "drilldown_refs": [_drilldown("trace", "查看证据与过程", "trace_task_001")],
        "metadata": {"source": "schema_test"},
    }


def _analysis_scope_payload() -> dict[str, Any]:
    return {
        "task_id": "task_001",
        "category": "smart_pet_hardware",
        "subcategory": "automatic_litter_box",
        "data_source_mode": "demo_snapshot",
        "data_source_label": "用户提供的脱敏 SKU 快照",
        "scope_notice": "本报告基于用户提供的脱敏 SKU 快照，不代表实时全网数据。",
        "sku_count": 14,
        "product_count": 14,
        "evidence_count": 14,
        "platform_label": "douyin_mall",
        "platforms": ["douyin_mall"],
        "source_description": "用户提供的脱敏抖音商品短链、商品页截图和价格截图。",
        "snapshot_version": "2026-05-23.step06.v1",
        "snapshot_date": "2026-05-23",
        "access_time_range": "暂无可靠数据",
        "missing_fields": ["Evidence.access_time"],
        "evidence_ids": ["ev_sku_01", "ev_sku_02"],
    }


def _display_status(value: str, label: str, reason: str) -> dict[str, Any]:
    return {
        "value": value,
        "label": label,
        "reason": reason,
        "evidence_ids": ["ev_sku_02"],
        "trace_refs": ["analysis_agent:run_001"],
        "risk_flags": [],
    }


def _drilldown(reference_type: str, label: str, target_id: str) -> dict[str, str]:
    return {
        "reference_type": reference_type,
        "label": label,
        "target_id": target_id,
        "route": f"/{reference_type}/{target_id}",
    }
