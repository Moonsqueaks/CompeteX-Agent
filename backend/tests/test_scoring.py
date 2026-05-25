from datetime import UTC, datetime

from app.schemas import CompetitionSlice, Evidence, Product, ReviewInsight
from app.services import (
    SCORE_WEIGHTS,
    calculate_competition_edge_score,
    rank_competitors_by_score,
)

NOW = datetime(2026, 5, 24, 2, 0, tzinfo=UTC)


def _product(
    product_id: str,
    role: str,
    product_type: str,
    price_band: str,
    name: str = "Demo product",
) -> Product:
    return Product(
        product_id=product_id,
        task_id="task_scoring",
        sku_id=product_id.replace("prod_", "sku_"),
        name=name,
        brand="Demo Brand",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        role=role,
        product_url=f"https://example.com/{product_id}",
        evidence_ids=[f"ev_{product_id}"],
        tags=[product_type, price_band, role],
        created_at=NOW,
    )


def _evidence(
    product: Product,
    *,
    confidence_level: str = "medium",
    access_time: datetime | None = NOW,
    screenshot_path: str | None = "data/raw/demo/price.png",
    sales: int = 1500,
    summary: str = "Automatic cleaning, odor control, smart sensor, large space.",
) -> Evidence:
    price_band = next(tag for tag in product.tags if "-" in tag)
    product_type = product.tags[0]
    return Evidence(
        evidence_id=f"ev_{product.product_id}",
        task_id=product.task_id,
        product_id=product.product_id,
        source_type="douyin_sku_snapshot",
        source_url=f"https://example.com/{product.product_id}",
        screenshot_path=screenshot_path,
        access_time=access_time,
        content_summary=summary,
        confidence_level=confidence_level,
        limitations="Local snapshot, not a live page.",
        metadata={
            "product_type": product_type,
            "price": {"price_band": price_band},
            "sales": sales,
            "missing_fields": [] if access_time is not None else ["source.access_time"],
        },
    )


def _review_insight(product: Product, sales: int = 1500) -> ReviewInsight:
    price_band = next(tag for tag in product.tags if "-" in tag)
    return ReviewInsight(
        review_insight_id=f"ri_{product.product_id}",
        task_id=product.task_id,
        product_id=product.product_id,
        sku_id=product.sku_id,
        summary="Review snapshot highlights cleaning convenience and odor control.",
        evidence_ids=product.evidence_ids,
        confidence_level="medium",
        market_signals={"sales": sales, "price_band": price_band},
        limitations="Local review summary only.",
        risk_flags=[],
        created_at=NOW,
    )


def _target() -> Product:
    return _product(
        product_id="prod_target",
        role="target",
        product_type="automatic_litter_box",
        price_band="1500-2000",
        name="Target automatic litter box",
    )


def test_score_total_uses_documented_weights() -> None:
    target = _target()
    competitor = _product(
        "prod_direct",
        "direct_competitor",
        "automatic_litter_box",
        "1500-2000",
    )
    score = calculate_competition_edge_score(
        target_product=target,
        competitor_product=competitor,
        competition_slice=CompetitionSlice(
            price_band="1500-2000",
            persona="multi cat household",
            scenario="automatic cleaning",
        ),
        evidences=[_evidence(competitor)],
        review_insights=[_review_insight(competitor)],
    )

    expected = round(
        score.score_breakdown.demand_substitutability
        * SCORE_WEIGHTS["demand_substitutability"]
        + score.score_breakdown.context_match * SCORE_WEIGHTS["context_match"]
        + score.score_breakdown.decision_stage_impact
        * SCORE_WEIGHTS["decision_stage_impact"]
        + score.score_breakdown.evidence_confidence * SCORE_WEIGHTS["evidence_confidence"]
        + score.score_breakdown.market_signal_strength
        * SCORE_WEIGHTS["market_signal_strength"],
        4,
    )

    assert score.edge_score == expected
    assert set(score.explanations) == set(SCORE_WEIGHTS)


def test_score_dimensions_are_bounded_and_explainable() -> None:
    target = _target()
    competitor = _product("prod_alt", "alternative", "cat_litter", "0-100")

    score = calculate_competition_edge_score(
        target_product=target,
        competitor_product=competitor,
        competition_slice=CompetitionSlice(
            price_band="0-100",
            persona="low budget shoppers",
            scenario="odor control",
        ),
        evidences=[_evidence(competitor, summary="Low budget cat litter with odor control.")],
        review_insights=[_review_insight(competitor, sales=70000)],
    )

    dumped = score.score_breakdown.model_dump()
    assert all(0 <= value <= 1 for value in dumped.values())
    for dimension, explanation in score.explanations.items():
        assert 0 <= explanation.score <= 1
        assert explanation.weight == SCORE_WEIGHTS[dimension]
        assert explanation.reasons


def test_low_evidence_confidence_lowers_total_score() -> None:
    target = _target()
    competitor = _product(
        "prod_direct",
        "direct_competitor",
        "automatic_litter_box",
        "1500-2000",
    )
    competition_slice = CompetitionSlice(
        price_band="1500-2000",
        persona="multi cat household",
        scenario="automatic cleaning",
    )

    high_confidence = calculate_competition_edge_score(
        target,
        competitor,
        competition_slice,
        evidences=[_evidence(competitor, confidence_level="high", sales=3000)],
    )
    low_confidence = calculate_competition_edge_score(
        target,
        competitor,
        competition_slice,
        evidences=[
            _evidence(
                competitor,
                confidence_level="low",
                access_time=None,
                screenshot_path=None,
                sales=3000,
            )
        ],
    )

    assert low_confidence.score_breakdown.evidence_confidence < (
        high_confidence.score_breakdown.evidence_confidence
    )
    assert low_confidence.edge_score < high_confidence.edge_score


def test_different_slices_change_competitor_ranking() -> None:
    target = _target()
    automatic_competitor = _product(
        "prod_auto",
        "direct_competitor",
        "automatic_litter_box",
        "1500-2000",
        name="Premium automatic litter box",
    )
    odor_alternative = _product(
        "prod_odor",
        "alternative",
        "deodorizer_additive",
        "0-100",
        name="Low budget deodorizer additive",
    )
    evidences = [
        _evidence(
            automatic_competitor,
            sales=1500,
            summary="Automatic cleaning, smart sensor, large space, odor control.",
        ),
        _evidence(
            odor_alternative,
            sales=70000,
            summary="Low budget deodorizer additive with strong odor control.",
        ),
    ]

    premium_auto_ranking = rank_competitors_by_score(
        target,
        [automatic_competitor, odor_alternative],
        CompetitionSlice(
            price_band="1500-2000",
            persona="multi cat household",
            scenario="automatic cleaning",
        ),
        evidences=evidences,
    )
    low_budget_odor_ranking = rank_competitors_by_score(
        target,
        [automatic_competitor, odor_alternative],
        CompetitionSlice(
            price_band="0-100",
            persona="low budget shoppers",
            scenario="odor control",
        ),
        evidences=evidences,
    )

    assert premium_auto_ranking[0].product.product_id == "prod_auto"
    assert low_budget_odor_ranking[0].product.product_id == "prod_odor"
    assert premium_auto_ranking[0].score.edge_score > premium_auto_ranking[1].score.edge_score
    assert low_budget_odor_ranking[0].score.edge_score > low_budget_odor_ranking[1].score.edge_score
