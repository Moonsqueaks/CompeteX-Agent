from datetime import datetime

from pydantic import Field

from app.schemas.common import (
    ActionPriority,
    JsonObject,
    ResponsibilityType,
    RiskFlag,
    StrictBaseModel,
)


class StrategyBrief(StrictBaseModel):
    strategy_brief_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    business_question: str = Field(min_length=1)
    target_segment: str = Field(min_length=1)
    primary_competition_axis: str = Field(min_length=1)
    decision_owner_view: str = Field(min_length=1)
    evidence_boundary: str = Field(min_length=1)
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    is_inference: bool = True
    confidence: float = Field(ge=0, le=1)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    created_at: datetime


class CompetitorBattlecard(StrictBaseModel):
    battlecard_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    competitor_id: str = Field(min_length=1)
    competitor_name: str = Field(min_length=1)
    why_users_compare: str = Field(min_length=1)
    competitor_strengths: list[str] = Field(min_length=1)
    competitor_weaknesses: list[str] = Field(default_factory=list)
    target_response: str = Field(min_length=1)
    sales_objection: str = Field(min_length=1)
    response_talk_track: str = Field(min_length=1)
    priority: ActionPriority
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    is_inference: bool = True
    confidence: float = Field(ge=0, le=1)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    created_at: datetime


class GapMatrixItem(StrictBaseModel):
    gap_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    dimension: str = Field(min_length=1)
    target_status: str = Field(min_length=1)
    competitor_reference: str = Field(min_length=1)
    impact_on_decision: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    is_inference: bool = True
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    created_at: datetime


class OpportunityItem(StrictBaseModel):
    opportunity_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    opportunity_type: str = Field(min_length=1)
    target_segment: str = Field(min_length=1)
    why_now: str = Field(min_length=1)
    expected_impact: str = Field(min_length=1)
    effort_level: float = Field(ge=0, le=1)
    priority_score: float = Field(ge=0, le=1)
    priority: ActionPriority
    confidence: float = Field(ge=0, le=1)
    owner: ResponsibilityType
    linked_gaps: list[str] = Field(default_factory=list)
    linked_battlecards: list[str] = Field(default_factory=list)
    linked_evidence_ids: list[str] = Field(default_factory=list)
    evidence_boundary: str = Field(min_length=1)
    is_inference: bool = True
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    created_at: datetime


class ReportQualityIssue(StrictBaseModel):
    issue_id: str = Field(min_length=1)
    issue_type: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    section_id: str | None = None
    item_key: str | None = None
    message: str = Field(min_length=1)
    suggestion: str = Field(min_length=1)
    evidence_boundary: str = Field(min_length=1)


class ReportQualityCheck(StrictBaseModel):
    quality_check_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    report_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    issues: list[ReportQualityIssue] = Field(default_factory=list)
    metrics: JsonObject = Field(default_factory=dict)
    created_at: datetime
