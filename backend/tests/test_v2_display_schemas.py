from typing import Any

import pytest
from fastapi import FastAPI
from pydantic import BaseModel, ValidationError

from app.schemas import (
    ActionPriority,
    DecisionUsabilityStatus,
    DisplayStatus,
    EvidenceCredibilityStatus,
    JudgmentStrength,
    PMRelationshipLabel,
    ResponsibilityType,
    ThreatLevel,
)


@pytest.mark.parametrize(
    ("enum_class", "allowed_values"),
    [
        (
            JudgmentStrength,
            {"clear_judgment", "directional_judgment", "hypothesis_only"},
        ),
        (
            DecisionUsabilityStatus,
            {
                "ready_for_initial_decision",
                "decision_with_caution",
                "directional_reference_only",
            },
        ),
        (
            EvidenceCredibilityStatus,
            {"directly_adoptable", "cautious_reference", "insufficient_evidence"},
        ),
        (
            ThreatLevel,
            {"high_threat", "medium_threat", "low_threat", "high_score_needs_review"},
        ),
        (
            PMRelationshipLabel,
            {
                "head_to_head",
                "low_price_interception",
                "scenario_substitute",
                "trust_suppression",
                "content_seeding_competition",
            },
        ),
        (
            ActionPriority,
            {"p0_immediate", "p1_current_iteration", "p2_follow_up_validation"},
        ),
        (
            ResponsibilityType,
            {
                "product_feature",
                "content_expression",
                "pricing_strategy",
                "evidence_research",
            },
        ),
    ],
)
def test_v2_enums_only_expose_allowed_values(enum_class: Any, allowed_values: set[str]) -> None:
    assert {item.value for item in enum_class} == allowed_values


def test_display_status_accepts_v2_status_value_with_reason() -> None:
    status = DisplayStatus.model_validate(
        {
            "value": "ready_for_initial_decision",
            "label": "可用于初步决策",
            "reason": "关键结论有证据支持，QA 风险已解决。",
            "evidence_ids": ["ev_sku_02"],
            "trace_refs": ["qa_review:review_001"],
            "risk_flags": [],
        }
    )

    assert status.value == DecisionUsabilityStatus.READY
    assert status.reason.startswith("关键结论")


def test_display_status_rejects_unknown_status_value() -> None:
    with pytest.raises(ValidationError):
        DisplayStatus.model_validate(
            {
                "value": "confident_but_uncontrolled",
                "label": "非法状态",
                "reason": "该状态不在 2.0 固定标准内。",
            }
        )


def test_v2_display_schemas_can_be_included_in_openapi() -> None:
    class SchemaBundle(BaseModel):
        status: DisplayStatus
        judgment_strength: JudgmentStrength
        decision_usability: DecisionUsabilityStatus
        evidence_credibility: EvidenceCredibilityStatus
        threat_level: ThreatLevel
        pm_relationship_label: PMRelationshipLabel
        action_priority: ActionPriority
        responsibility_type: ResponsibilityType

    api = FastAPI()

    @api.get("/schema-test", response_model=SchemaBundle)
    def schema_test() -> dict[str, Any]:
        return {}

    schemas = api.openapi()["components"]["schemas"]
    expected_schema_names = {
        "ActionPriority",
        "DecisionUsabilityStatus",
        "DisplayStatus",
        "EvidenceCredibilityStatus",
        "JudgmentStrength",
        "PMRelationshipLabel",
        "ResponsibilityType",
        "ThreatLevel",
    }
    assert expected_schema_names.issubset(schemas)
