from datetime import UTC, datetime

import pytest

from app.schemas import (
    CompetitionEdge,
    DisplayStatus,
    Evidence,
    EvidenceCredibilityStatus,
    PMRelationshipLabel,
    Product,
    ThreatLevel,
)
from app.services.battlefield_service import (
    _relationship_label,
    _relationship_label_explanation,
    _threat_level,
)

NOW = datetime(2026, 5, 29, 11, 0, tzinfo=UTC)


def test_relationship_label_maps_direct_competition_to_head_to_head() -> None:
    assert _label_for("direct", target_price=1599, competitor_price=1799) == (
        PMRelationshipLabel.HEAD_TO_HEAD
    )


def test_relationship_label_maps_low_price_direct_competition_to_interception() -> None:
    assert _label_for("direct", target_price=1599, competitor_price=899) == (
        PMRelationshipLabel.LOW_PRICE_INTERCEPTION
    )


def test_relationship_label_maps_alternative_to_scenario_substitute() -> None:
    assert _label_for("alternative", target_price=1599, competitor_price=1399) == (
        PMRelationshipLabel.SCENARIO_SUBSTITUTE
    )


def test_relationship_label_maps_trust_signal_to_trust_suppression() -> None:
    label = _label_for(
        "direct",
        target_price=1599,
        competitor_price=1499,
        competitor_summary="页面强调安全认证、售后质保和用户口碑。",
    )

    assert label == PMRelationshipLabel.TRUST_SUPPRESSION


def test_relationship_label_maps_content_cooccurrence_to_seeding_competition() -> None:
    assert _label_for("content_cooccurrence", target_price=1599, competitor_price=1499) == (
        PMRelationshipLabel.CONTENT_SEEDING_COMPETITION
    )


def test_relationship_label_maps_channel_to_low_price_interception() -> None:
    assert _label_for("channel", target_price=1599, competitor_price=1299) == (
        PMRelationshipLabel.LOW_PRICE_INTERCEPTION
    )


def test_high_score_low_credibility_edge_requires_review() -> None:
    credibility = DisplayStatus(
        value=EvidenceCredibilityStatus.INSUFFICIENT,
        label="证据不足",
        reason="缺少关键证据。",
        evidence_ids=[],
        trace_refs=[],
        risk_flags=[],
    )

    assert _threat_level(0.91, credibility) == ThreatLevel.HIGH_SCORE_NEEDS_REVIEW


@pytest.mark.parametrize("label", list(PMRelationshipLabel))
def test_relationship_label_explanation_is_not_empty(label: PMRelationshipLabel) -> None:
    assert _relationship_label_explanation(label)


def _label_for(
    competition_type: str,
    *,
    target_price: float,
    competitor_price: float,
    competitor_summary: str = "常规商品页证据。",
) -> PMRelationshipLabel:
    target = _product("prod_target", "target")
    competitor = _product("prod_competitor", "direct_competitor")
    evidences = {
        "ev_target": _evidence("ev_target", "prod_target", target_price, "目标商品页证据。"),
        "ev_competitor": _evidence(
            "ev_competitor",
            "prod_competitor",
            competitor_price,
            competitor_summary,
        ),
    }
    edge = _edge(competition_type)
    return _relationship_label(
        edge=edge,
        target=target,
        competitor=competitor,
        evidence_ids=list(evidences),
        evidences_by_id=evidences,
    )


def _product(product_id: str, role: str) -> Product:
    return Product(
        product_id=product_id,
        task_id="task_relationship_rules",
        sku_id=product_id.replace("prod_", "sku_"),
        name=f"{product_id} 自动猫砂盆",
        brand="测试品牌",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        role=role,
        created_at=NOW,
        evidence_ids=[],
        tags=[],
    )


def _evidence(
    evidence_id: str,
    product_id: str,
    price: float,
    summary: str,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        task_id="task_relationship_rules",
        product_id=product_id,
        source_type="douyin_sku_snapshot",
        source_url="https://example.com/product",
        screenshot_path="data/raw/test/price.png",
        access_time=NOW,
        content_summary=summary,
        confidence_level="medium",
        limitations="本地快照。",
        metadata={"price": {"display_price_yuan": price}},
    )


def _edge(competition_type: str) -> CompetitionEdge:
    return CompetitionEdge(
        edge_id=f"edge_{competition_type}",
        task_id="task_relationship_rules",
        target_product_id="prod_target",
        competitor_product_id="prod_competitor",
        competition_type=competition_type,
        slice={
            "price_band": "1500-2000",
            "persona": "多猫家庭",
            "scenario": "自动清理",
        },
        decision_stages=["information_reach", "decision_completion"],
        edge_score=0.82,
        score_breakdown={
            "demand_substitutability": 0.8,
            "context_match": 0.8,
            "decision_stage_impact": 0.8,
            "evidence_confidence": 0.8,
            "market_signal_strength": 0.8,
        },
        claim_ids=["claim_001"],
        created_at=NOW,
    )
