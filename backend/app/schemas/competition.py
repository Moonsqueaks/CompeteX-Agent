from datetime import datetime

from pydantic import Field

from app.schemas.common import CompetitionType, DecisionStage, RiskFlag, StrictBaseModel


class CompetitionSlice(StrictBaseModel):
    price_band: str = Field(min_length=1)
    persona: str = Field(min_length=1)
    scenario: str = Field(min_length=1)


class ScoreBreakdown(StrictBaseModel):
    demand_substitutability: float = Field(ge=0, le=1)
    context_match: float = Field(ge=0, le=1)
    decision_stage_impact: float = Field(ge=0, le=1)
    evidence_confidence: float = Field(ge=0, le=1)
    market_signal_strength: float = Field(ge=0, le=1)


class CompetitionEdge(StrictBaseModel):
    edge_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    target_product_id: str = Field(min_length=1)
    competitor_product_id: str = Field(min_length=1)
    competition_type: CompetitionType
    slice: CompetitionSlice
    decision_stages: list[DecisionStage] = Field(min_length=1)
    edge_score: float = Field(ge=0, le=1)
    score_breakdown: ScoreBreakdown
    claim_ids: list[str] = Field(default_factory=list)
    human_adjusted: bool = False
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    created_at: datetime
