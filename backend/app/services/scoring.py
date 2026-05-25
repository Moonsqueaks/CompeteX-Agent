import re
from collections.abc import Sequence
from statistics import mean

from pydantic import Field

from app.schemas import CompetitionSlice, Evidence, Product, ReviewInsight, ScoreBreakdown
from app.schemas.common import JsonObject, StrictBaseModel

SCORE_WEIGHTS: dict[str, float] = {
    "demand_substitutability": 0.30,
    "context_match": 0.25,
    "decision_stage_impact": 0.20,
    "evidence_confidence": 0.15,
    "market_signal_strength": 0.10,
}

PRICE_BAND_PATTERN = re.compile(r"(?P<low>\d+)\s*-\s*(?P<high>\d+)")

LOW_BUDGET_TERMS = (
    "low budget",
    "entry",
    "cheap",
    "0-100",
    "0-500",
    "低预算",
    "入门",
    "低价",
)
MULTI_CAT_TERMS = ("multi cat", "large space", "multi-cat", "多猫", "大空间", "超大", "大号")
ODOR_TERMS = ("odor", "deodor", "smell", "除臭", "控臭", "吸臭", "新风")
AUTO_CLEANING_TERMS = ("automatic", "auto", "self-clean", "免铲", "自动", "智能铲屎")
SMART_TERMS = ("smart", "app", "sensor", "智能", "电动", "感应", "可视")
SAFETY_TERMS = ("safe", "anti", "防", "安全", "感应")
SIZE_TERMS = ("large", "open", "大空间", "超大", "大号", "开放")
CAPABILITY_TERMS = AUTO_CLEANING_TERMS + ODOR_TERMS + SMART_TERMS + SIZE_TERMS


class DimensionScore(StrictBaseModel):
    score: float = Field(ge=0, le=1)
    weight: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    signals: JsonObject = Field(default_factory=dict)


class CompetitionScoreResult(StrictBaseModel):
    edge_score: float = Field(ge=0, le=1)
    score_breakdown: ScoreBreakdown
    explanations: dict[str, DimensionScore]


class ScoredCompetitor(StrictBaseModel):
    product: Product
    score: CompetitionScoreResult


def calculate_competition_edge_score(
    target_product: Product,
    competitor_product: Product,
    competition_slice: CompetitionSlice,
    evidences: Sequence[Evidence] | None = None,
    review_insights: Sequence[ReviewInsight] | None = None,
) -> CompetitionScoreResult:
    competitor_evidences = _evidences_for_product(competitor_product, evidences or ())
    competitor_insights = _insights_for_product(competitor_product, review_insights or ())
    competitor_text = _product_text(competitor_product, competitor_evidences, competitor_insights)

    explanations = {
        "demand_substitutability": _score_demand_substitutability(
            target_product,
            competitor_product,
            competitor_evidences,
            competitor_text,
            competition_slice,
        ),
        "context_match": _score_context_match(
            competitor_product,
            competitor_evidences,
            competitor_insights,
            competitor_text,
            competition_slice,
        ),
        "decision_stage_impact": _score_decision_stage_impact(
            competitor_evidences,
            competitor_text,
            competition_slice,
        ),
        "evidence_confidence": _score_evidence_confidence(competitor_evidences),
        "market_signal_strength": _score_market_signal_strength(
            competitor_evidences,
            competitor_insights,
        ),
    }
    score_breakdown = ScoreBreakdown(
        demand_substitutability=explanations["demand_substitutability"].score,
        context_match=explanations["context_match"].score,
        decision_stage_impact=explanations["decision_stage_impact"].score,
        evidence_confidence=explanations["evidence_confidence"].score,
        market_signal_strength=explanations["market_signal_strength"].score,
    )
    edge_score = _weighted_edge_score(score_breakdown)
    return CompetitionScoreResult(
        edge_score=edge_score,
        score_breakdown=score_breakdown,
        explanations=explanations,
    )


def rank_competitors_by_score(
    target_product: Product,
    competitors: Sequence[Product],
    competition_slice: CompetitionSlice,
    evidences: Sequence[Evidence] | None = None,
    review_insights: Sequence[ReviewInsight] | None = None,
) -> list[ScoredCompetitor]:
    scored = [
        ScoredCompetitor(
            product=competitor,
            score=calculate_competition_edge_score(
                target_product=target_product,
                competitor_product=competitor,
                competition_slice=competition_slice,
                evidences=evidences,
                review_insights=review_insights,
            ),
        )
        for competitor in competitors
    ]
    return sorted(scored, key=lambda item: item.score.edge_score, reverse=True)


def _weighted_edge_score(score_breakdown: ScoreBreakdown) -> float:
    return _clip(
        score_breakdown.demand_substitutability * SCORE_WEIGHTS["demand_substitutability"]
        + score_breakdown.context_match * SCORE_WEIGHTS["context_match"]
        + score_breakdown.decision_stage_impact * SCORE_WEIGHTS["decision_stage_impact"]
        + score_breakdown.evidence_confidence * SCORE_WEIGHTS["evidence_confidence"]
        + score_breakdown.market_signal_strength * SCORE_WEIGHTS["market_signal_strength"]
    )


def _score_demand_substitutability(
    target_product: Product,
    competitor_product: Product,
    competitor_evidences: Sequence[Evidence],
    competitor_text: str,
    competition_slice: CompetitionSlice,
) -> DimensionScore:
    target_type = _product_type(target_product, ())
    competitor_type = _product_type(competitor_product, competitor_evidences)
    competitor_role = str(competitor_product.role)
    reasons = []

    if target_type and competitor_type == target_type:
        score = 0.95
        reasons.append("Competitor has the same product type as the target.")
    elif competitor_role == "direct_competitor":
        score = 0.90
        reasons.append("Competitor is tagged as a direct competitor.")
    elif "litter_box" in competitor_type or "toilet" in competitor_type:
        score = 0.70
        reasons.append("Competitor solves a closely related litter-box task.")
    elif _keyword_score(competition_slice.scenario, competitor_text) >= 0.8:
        score = 0.55
        reasons.append("Competitor substitutes the slice-specific user need.")
    else:
        score = 0.35
        reasons.append("Competitor only weakly substitutes the target task.")

    if competitor_role in {"alternative", "channel_alternative"}:
        score = min(score, 0.65)
        reasons.append("Alternative role caps full task substitutability.")

    return _dimension(
        "demand_substitutability",
        score,
        reasons,
        {"target_product_type": target_type, "competitor_product_type": competitor_type},
    )


def _score_context_match(
    competitor_product: Product,
    competitor_evidences: Sequence[Evidence],
    competitor_insights: Sequence[ReviewInsight],
    competitor_text: str,
    competition_slice: CompetitionSlice,
) -> DimensionScore:
    competitor_price_band = _price_band(
        competitor_product,
        competitor_evidences,
        competitor_insights,
    )
    price_score = _price_band_match_score(competition_slice.price_band, competitor_price_band)
    persona_score = _persona_match_score(competition_slice.persona, competitor_text)
    scenario_score = _keyword_score(competition_slice.scenario, competitor_text)
    score = 0.45 * price_score + 0.25 * persona_score + 0.30 * scenario_score
    return _dimension(
        "context_match",
        score,
        [
            f"price_band_match={price_score:.2f}",
            f"persona_match={persona_score:.2f}",
            f"scenario_match={scenario_score:.2f}",
        ],
        {
            "slice_price_band": competition_slice.price_band,
            "competitor_price_band": competitor_price_band,
            "persona": competition_slice.persona,
            "scenario": competition_slice.scenario,
        },
    )


def _score_decision_stage_impact(
    competitor_evidences: Sequence[Evidence],
    competitor_text: str,
    competition_slice: CompetitionSlice,
) -> DimensionScore:
    capability_hits = _term_hits(competitor_text, CAPABILITY_TERMS)
    trust_hits = _term_hits(competitor_text, SAFETY_TERMS)
    scenario_score = _keyword_score(competition_slice.scenario, competitor_text)
    evidence_bonus = 0.10 if competitor_evidences else 0.0
    score = (
        0.35
        + min(0.25, 0.05 * len(capability_hits))
        + min(0.15, 0.05 * len(trust_hits))
        + 0.15 * scenario_score
        + evidence_bonus
    )
    return _dimension(
        "decision_stage_impact",
        score,
        [
            f"capability_terms={len(capability_hits)}",
            f"trust_terms={len(trust_hits)}",
            f"scenario_match={scenario_score:.2f}",
        ],
        {
            "capability_hits": capability_hits,
            "trust_hits": trust_hits,
            "evidence_count": len(competitor_evidences),
        },
    )


def _score_evidence_confidence(evidences: Sequence[Evidence]) -> DimensionScore:
    if not evidences:
        return _dimension(
            "evidence_confidence",
            0.20,
            ["No evidence is attached to this competitor."],
            {"evidence_count": 0},
        )

    evidence_scores = [_single_evidence_confidence(evidence) for evidence in evidences]
    score = mean(evidence_scores)
    missing_fields = {
        evidence.evidence_id: evidence.metadata.get("missing_fields", [])
        for evidence in evidences
        if evidence.metadata.get("missing_fields")
    }
    return _dimension(
        "evidence_confidence",
        score,
        [
            f"average_evidence_quality={score:.2f}",
            f"evidence_count={len(evidences)}",
        ],
        {"missing_fields": missing_fields},
    )


def _score_market_signal_strength(
    evidences: Sequence[Evidence],
    insights: Sequence[ReviewInsight],
) -> DimensionScore:
    sales = _sales_signal(evidences, insights)
    if sales is None:
        score = 0.25
        reasons = ["No sales or market signal is available."]
    elif sales >= 50000:
        score = 0.95
        reasons = ["Very strong sales signal in the local snapshot."]
    elif sales >= 10000:
        score = 0.85
        reasons = ["Strong sales signal in the local snapshot."]
    elif sales >= 3000:
        score = 0.75
        reasons = ["Moderate-to-strong sales signal in the local snapshot."]
    elif sales >= 1000:
        score = 0.65
        reasons = ["Moderate sales signal in the local snapshot."]
    elif sales >= 500:
        score = 0.50
        reasons = ["Limited sales signal in the local snapshot."]
    else:
        score = 0.40
        reasons = ["Weak sales signal in the local snapshot."]

    if insights:
        score += 0.03
        reasons.append("ReviewInsight is available as additional market context.")

    return _dimension("market_signal_strength", score, reasons, {"sales": sales})


def _single_evidence_confidence(evidence: Evidence) -> float:
    confidence_base = {
        "high": 0.95,
        "medium": 0.80,
        "low": 0.55,
        "unknown": 0.35,
    }[str(evidence.confidence_level)]
    complete_fields = sum(
        [
            bool(evidence.source_url),
            bool(evidence.screenshot_path),
            evidence.access_time is not None,
        ]
    )
    completeness_score = complete_fields / 3
    missing_fields = evidence.metadata.get("missing_fields", [])
    if missing_fields:
        completeness_score = max(0.0, completeness_score - 0.20 * len(missing_fields))
    return _clip(0.65 * confidence_base + 0.35 * completeness_score)


def _dimension(
    name: str,
    score: float,
    reasons: list[str],
    signals: JsonObject,
) -> DimensionScore:
    return DimensionScore(
        score=_clip(score),
        weight=SCORE_WEIGHTS[name],
        reasons=reasons,
        signals=signals,
    )


def _product_text(
    product: Product,
    evidences: Sequence[Evidence],
    insights: Sequence[ReviewInsight],
) -> str:
    parts = [product.name, product.brand or "", " ".join(product.tags)]
    parts.extend(evidence.content_summary for evidence in evidences)
    parts.extend(insight.summary for insight in insights)
    return " ".join(part for part in parts if part).lower()


def _product_type(product: Product, evidences: Sequence[Evidence]) -> str:
    for evidence in evidences:
        product_type = evidence.metadata.get("product_type")
        if isinstance(product_type, str) and product_type.strip():
            return product_type
    for tag in product.tags:
        if tag not in {str(product.role)} and not PRICE_BAND_PATTERN.fullmatch(tag):
            return tag
    return ""


def _price_band(
    product: Product,
    evidences: Sequence[Evidence],
    insights: Sequence[ReviewInsight],
) -> str | None:
    for evidence in evidences:
        price = evidence.metadata.get("price")
        if isinstance(price, dict) and isinstance(price.get("price_band"), str):
            return price["price_band"]
    for insight in insights:
        price_band = insight.market_signals.get("price_band")
        if isinstance(price_band, str):
            return price_band
    for tag in product.tags:
        if PRICE_BAND_PATTERN.fullmatch(tag):
            return tag
    return None


def _price_band_match_score(slice_band: str, competitor_band: str | None) -> float:
    if competitor_band is None:
        return 0.30
    if slice_band == competitor_band:
        return 1.00

    slice_range = _parse_price_band(slice_band)
    competitor_range = _parse_price_band(competitor_band)
    if slice_range is None or competitor_range is None:
        return 0.50 if slice_band in competitor_band or competitor_band in slice_band else 0.30

    slice_low, slice_high = slice_range
    competitor_low, competitor_high = competitor_range
    overlap = max(0, min(slice_high, competitor_high) - max(slice_low, competitor_low))
    if overlap > 0:
        return 0.80

    gap = max(slice_low, competitor_low) - min(slice_high, competitor_high)
    if gap <= 500:
        return 0.55
    return 0.25


def _parse_price_band(value: str) -> tuple[int, int] | None:
    match = PRICE_BAND_PATTERN.search(value)
    if not match:
        return None
    low = int(match.group("low"))
    high = int(match.group("high"))
    if high < low:
        return None
    return low, high


def _persona_match_score(persona: str, text: str) -> float:
    persona_text = persona.lower()
    if any(term in persona_text for term in LOW_BUDGET_TERMS):
        return _keyword_group_score(text, LOW_BUDGET_TERMS)
    if any(term in persona_text for term in MULTI_CAT_TERMS):
        return _keyword_group_score(text, MULTI_CAT_TERMS)
    if any(term in persona_text for term in ODOR_TERMS):
        return _keyword_group_score(text, ODOR_TERMS)
    return _keyword_score(persona, text)


def _keyword_score(query: str, text: str) -> float:
    query_text = query.lower()
    if any(term in query_text for term in ODOR_TERMS):
        return _keyword_group_score(text, ODOR_TERMS)
    if any(term in query_text for term in AUTO_CLEANING_TERMS):
        return _keyword_group_score(text, AUTO_CLEANING_TERMS)
    if any(term in query_text for term in SMART_TERMS):
        return _keyword_group_score(text, SMART_TERMS)
    if any(term in query_text for term in SIZE_TERMS):
        return _keyword_group_score(text, SIZE_TERMS)
    if query_text and query_text in text:
        return 1.00
    return 0.20


def _keyword_group_score(text: str, terms: Sequence[str]) -> float:
    hits = _term_hits(text, terms)
    if not hits:
        return 0.20
    return _clip(0.55 + 0.15 * min(len(hits), 3))


def _term_hits(text: str, terms: Sequence[str]) -> list[str]:
    return sorted({term for term in terms if term in text})


def _sales_signal(
    evidences: Sequence[Evidence],
    insights: Sequence[ReviewInsight],
) -> int | None:
    for evidence in evidences:
        sales = _coerce_int(evidence.metadata.get("sales"))
        if sales is not None:
            return sales
    for insight in insights:
        sales = _coerce_int(insight.market_signals.get("sales"))
        if sales is not None:
            return sales
    return None


def _coerce_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        digits = re.sub(r"\D", "", value)
        if digits:
            return int(digits)
    return None


def _evidences_for_product(product: Product, evidences: Sequence[Evidence]) -> list[Evidence]:
    return [
        evidence
        for evidence in evidences
        if evidence.product_id == product.product_id or evidence.evidence_id in product.evidence_ids
    ]


def _insights_for_product(
    product: Product,
    insights: Sequence[ReviewInsight],
) -> list[ReviewInsight]:
    return [insight for insight in insights if insight.product_id == product.product_id]


def _clip(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 4)
