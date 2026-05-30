from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.common import (
    CompetitionType,
    ConfidenceLevel,
    DecisionStage,
    EvidenceSourceType,
    JsonObject,
    PMRelationshipLabel,
    ProductRole,
    RiskFlag,
    StrictBaseModel,
    ThreatLevel,
)
from app.schemas.competition import ScoreBreakdown
from app.schemas.display import DisplayStatus


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
    primary_image_path: str | None = None
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


class BattlefieldExplanationSegment(StrictBaseModel):
    text: str = Field(min_length=1)
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    is_analysis_suggestion: bool = False

    @model_validator(mode="after")
    def mark_unreferenced_segment_as_risky(self) -> "BattlefieldExplanationSegment":
        if self.claim_ids or self.evidence_ids:
            return self
        risk_flags = list(self.risk_flags)
        if RiskFlag.MISSING_EVIDENCE not in risk_flags:
            risk_flags.append(RiskFlag.MISSING_EVIDENCE)
        object.__setattr__(self, "risk_flags", risk_flags)
        return self


class BattlefieldFourPartExplanation(StrictBaseModel):
    why_competitor: BattlefieldExplanationSegment
    strength: BattlefieldExplanationSegment
    decision_stage_impact: BattlefieldExplanationSegment
    response_suggestion: BattlefieldExplanationSegment

    @model_validator(mode="after")
    def response_must_be_marked_as_analysis_suggestion(self) -> "BattlefieldFourPartExplanation":
        if not self.response_suggestion.is_analysis_suggestion:
            raise ValueError("response_suggestion must be marked as analysis suggestion.")
        return self


class BattlefieldKeyRelation(StrictBaseModel):
    edge_id: str = Field(min_length=1)
    target_product_id: str = Field(min_length=1)
    competitor_product_id: str = Field(min_length=1)
    competitor_product_name: str = Field(min_length=1)
    competitor_brand: str | None = None
    competitor_primary_image_path: str | None = None
    relationship_label: PMRelationshipLabel
    relationship_label_explanation: str = Field(min_length=1)
    threat_level: ThreatLevel
    evidence_credibility: DisplayStatus
    inclusion_reason: str = Field(min_length=1)
    four_part_explanation: BattlefieldFourPartExplanation
    action_suggestion: str = Field(min_length=1)
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    is_default_visible: bool = True


class BattlefieldRelationFilter(StrictBaseModel):
    include_all_relations: bool = False
    default_limit: int = Field(default=5, ge=1)
    total_relation_count: int = Field(ge=0)
    visible_relation_count: int = Field(ge=0)
    can_expand_all: bool = False


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
    key_relations: list[BattlefieldKeyRelation] = Field(default_factory=list)
    relation_filter: BattlefieldRelationFilter | None = None
    score_explanations: list[BattlefieldScoreExplanation] = Field(default_factory=list)
    decision_chain: list[BattlefieldDecisionChainStage] = Field(default_factory=list)
    evidence_cards: list[BattlefieldEvidenceCard] = Field(default_factory=list)
    qa_summary: BattlefieldQASummary
    metadata: JsonObject = Field(default_factory=dict)
