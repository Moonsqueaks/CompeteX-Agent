import pytest
from pydantic import ValidationError

from app.schemas import (
    BattlefieldExplanationSegment,
    BattlefieldFourPartExplanation,
    RiskFlag,
)


def test_unreferenced_explanation_segment_is_risk_marked() -> None:
    segment = BattlefieldExplanationSegment(
        text="无证据支撑的新增事实。",
        claim_ids=[],
        evidence_ids=[],
        trace_refs=[],
        risk_flags=[],
    )

    assert RiskFlag.MISSING_EVIDENCE in segment.risk_flags


def test_response_suggestion_must_be_marked_as_analysis_suggestion() -> None:
    segment = _segment()

    with pytest.raises(ValidationError):
        BattlefieldFourPartExplanation(
            why_competitor=segment,
            strength=segment,
            decision_stage_impact=segment,
            response_suggestion=_segment(is_analysis_suggestion=False),
        )


def _segment(is_analysis_suggestion: bool = False) -> BattlefieldExplanationSegment:
    return BattlefieldExplanationSegment(
        text="有证据支撑的解释。",
        claim_ids=["claim_001"],
        evidence_ids=["ev_001"],
        trace_refs=["analysis_agent:edge_001"],
        risk_flags=[],
        is_analysis_suggestion=is_analysis_suggestion,
    )
