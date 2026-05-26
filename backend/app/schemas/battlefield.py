from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import (
    CompetitionType,
    ConfidenceLevel,
    DecisionStage,
    EvidenceSourceType,
    JsonObject,
    ProductRole,
    RiskFlag,
    StrictBaseModel,
)
from app.schemas.competition import ScoreBreakdown


class BattlefieldSliceSelection(StrictBaseModel):
    price_band: str | None = None
    persona: str | None = None
    scenario: str | None = None


class BattlefieldSliceOption(StrictBaseModel):
    price_band: str
    persona: str
    scenario: str
    edge_count: int = Field(ge=0)
    top_edge_score: float = Field(ge=0, le=1)


class BattlefieldGraphNode(StrictBaseModel):
    node_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    role: ProductRole
    brand: str | None = None
    shop_name: str | None = None
    product_url: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class BattlefieldClaimReference(StrictBaseModel):
    claim_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    status: str = Field(min_length=1)
    is_inference: bool
    evidence_ids: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class BattlefieldGraphEdge(StrictBaseModel):
    edge_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    target_product_id: str = Field(min_length=1)
    competitor_product_id: str = Field(min_length=1)
    competition_type: CompetitionType
    slice: BattlefieldSliceSelection
    decision_stages: list[DecisionStage] = Field(min_length=1)
    edge_score: float = Field(ge=0, le=1)
    score_breakdown: ScoreBreakdown
    score_explanations: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    claim_refs: list[BattlefieldClaimReference] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    risk_status: Literal["normal", "at_risk"] = "normal"
    human_adjusted: bool = False


class BattlefieldScoreExplanation(StrictBaseModel):
    edge_id: str = Field(min_length=1)
    edge_score: float = Field(ge=0, le=1)
    score_breakdown: ScoreBreakdown
    explanations: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class BattlefieldDecisionChainStage(StrictBaseModel):
    stage: DecisionStage
    edge_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    average_edge_score: float = Field(ge=0, le=1)


class BattlefieldEvidenceCard(StrictBaseModel):
    evidence_id: str = Field(min_length=1)
    product_id: str | None = None
    source_type: EvidenceSourceType
    source_url: str | None = None
    screenshot_path: str | None = None
    access_time: datetime | None = None
    access_time_status: Literal["available", "missing"]
    confidence_level: ConfidenceLevel
    content_summary: str = Field(min_length=1)
    limitations: str = Field(min_length=1)
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class BattlefieldQASummary(StrictBaseModel):
    qa_status: Literal["passed", "needs_attention"]
    review_task_count: int = Field(ge=0)
    open_review_task_count: int = Field(ge=0)
    resolved_review_task_count: int = Field(ge=0)
    revision_message_count: int = Field(ge=0)
    risk_edge_ids: list[str] = Field(default_factory=list)
    risk_claim_ids: list[str] = Field(default_factory=list)
    review_task_ids: list[str] = Field(default_factory=list)


class BattlefieldData(StrictBaseModel):
    battlefield_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    generated_at: datetime
    selected_slice: BattlefieldSliceSelection
    available_slices: list[BattlefieldSliceOption] = Field(default_factory=list)
    graph_nodes: list[BattlefieldGraphNode] = Field(default_factory=list)
    graph_edges: list[BattlefieldGraphEdge] = Field(default_factory=list)
    score_explanations: list[BattlefieldScoreExplanation] = Field(default_factory=list)
    decision_chain: list[BattlefieldDecisionChainStage] = Field(default_factory=list)
    evidence_cards: list[BattlefieldEvidenceCard] = Field(default_factory=list)
    qa_summary: BattlefieldQASummary
    metadata: JsonObject = Field(default_factory=dict)
