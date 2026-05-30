from pydantic import Field

from app.schemas.common import (
    ActionPriority,
    DecisionUsabilityStatus,
    EvidenceCredibilityStatus,
    JudgmentStrength,
    PMRelationshipLabel,
    ResponsibilityType,
    RiskFlag,
    StrictBaseModel,
    ThreatLevel,
)

type DisplayStatusValue = (
    JudgmentStrength
    | DecisionUsabilityStatus
    | EvidenceCredibilityStatus
    | ThreatLevel
    | PMRelationshipLabel
    | ActionPriority
    | ResponsibilityType
)


class DisplayStatus(StrictBaseModel):
    value: DisplayStatusValue
    label: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
