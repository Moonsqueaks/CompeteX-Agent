from datetime import datetime
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from app.schemas.battlefield import BattlefieldSliceSelection
from app.schemas.common import (
    ActionPriority,
    CandidateStrategy,
    DataSourceMode,
    DecisionUsabilityStatus,
    EvidenceCredibilityStatus,
    EvidenceSourceMode,
    JsonObject,
    JudgmentStrength,
    PMRelationshipLabel,
    ResponsibilityType,
    RiskFlag,
    StrictBaseModel,
    ThreatLevel,
)
from app.schemas.display import DisplayStatus


class OverviewDrilldownType(StrEnum):
    BATTLEFIELD = "battlefield"
    PROFILE = "profile"
    REPORT = "report"
    TRACE = "trace"
    EVIDENCE = "evidence"


class OverviewKeyCompetitorType(StrEnum):
    HIGHEST_THREAT_DIRECT = "highest_threat_direct_competitor"
    HIGHEST_THREAT_ALTERNATIVE = "highest_threat_alternative"
    HIGH_SCORE_NEEDS_REVIEW = "high_score_needs_review"


class OverviewFindingType(StrEnum):
    PRODUCT_OPPORTUNITY = "product_opportunity"
    EXPRESSION_OPPORTUNITY = "expression_opportunity"
    EVIDENCE_RISK = "evidence_risk"
    COMPETITION_RISK = "competition_risk"
    EXPRESSION_RISK = "expression_risk"
    COMPLIANCE_RISK = "compliance_risk"


class AnalysisScopeSummary(StrictBaseModel):
    task_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    subcategory: str = Field(min_length=1)
    data_source_mode: DataSourceMode
    evidence_source_mode: EvidenceSourceMode = EvidenceSourceMode.LOCAL_SNAPSHOT
    candidate_strategy: CandidateStrategy = CandidateStrategy.SNAPSHOT_POOL
    data_source_label: str = Field(min_length=1)
    scope_notice: str = Field(min_length=1)
    sku_count: int = Field(ge=0)
    product_count: int = Field(ge=0)
    evidence_count: int = Field(ge=0)
    platform_label: str = Field(min_length=1)
    platforms: list[str] = Field(default_factory=list)
    source_description: str = Field(min_length=1)
    snapshot_version: str | None = None
    snapshot_date: str = Field(min_length=1)
    access_time_range: str = Field(min_length=1)
    missing_fields: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class OverviewDrilldownReference(StrictBaseModel):
    reference_type: OverviewDrilldownType
    label: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    route: str = Field(min_length=1)


class ReferencedOverviewItem(StrictBaseModel):
    evidence_ids: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    drilldown_refs: list[OverviewDrilldownReference] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    missing_reference_reason: str | None = None

    @model_validator(mode="after")
    def mark_missing_evidence_or_trace_reference(self) -> "ReferencedOverviewItem":
        if self.evidence_ids or self.trace_refs:
            return self

        risk_flags = list(self.risk_flags)
        if RiskFlag.MISSING_EVIDENCE not in risk_flags:
            risk_flags.append(RiskFlag.MISSING_EVIDENCE)
        object.__setattr__(self, "risk_flags", risk_flags)
        if self.missing_reference_reason is None:
            object.__setattr__(
                self,
                "missing_reference_reason",
                "缺少 Evidence 或 Trace 下钻引用。",
            )
        return self


class OverviewConclusion(ReferencedOverviewItem):
    content: str = Field(min_length=1)


class OverviewKeyCompetitor(ReferencedOverviewItem):
    competitor_type: OverviewKeyCompetitorType
    product_id: str = Field(min_length=1)
    product_name: str = Field(min_length=1)
    relationship_label: PMRelationshipLabel
    threat_level: ThreatLevel
    evidence_credibility: DisplayStatus
    sku_id: str | None = None
    brand: str | None = None
    primary_image_path: str | None = None
    inclusion_reason: str = Field(min_length=1)

    @field_validator("evidence_credibility")
    @classmethod
    def evidence_credibility_must_use_evidence_status(
        cls,
        value: DisplayStatus,
    ) -> DisplayStatus:
        if not isinstance(value.value, EvidenceCredibilityStatus):
            raise ValueError("evidence_credibility must use EvidenceCredibilityStatus.")
        return value


class OverviewFinding(ReferencedOverviewItem):
    finding_id: str = Field(min_length=1)
    finding_type: OverviewFindingType
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)


class OverviewActionRecommendation(ReferencedOverviewItem):
    action_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: ActionPriority
    responsibility_type: ResponsibilityType
    expected_impact: str | None = None


class OverviewData(StrictBaseModel):
    overview_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    generated_at: datetime
    one_sentence_judgment: OverviewConclusion
    judgment_strength: DisplayStatus
    decision_usability: DisplayStatus
    status_reasons: list[str] = Field(default_factory=list)
    analysis_scope: AnalysisScopeSummary
    key_competitors: list[OverviewKeyCompetitor] = Field(default_factory=list)
    opportunities: list[OverviewFinding] = Field(default_factory=list, max_length=3)
    risk_points: list[OverviewFinding] = Field(default_factory=list, max_length=3)
    action_recommendations: list[OverviewActionRecommendation] = Field(
        default_factory=list,
        max_length=5,
    )
    current_slice: BattlefieldSliceSelection = Field(default_factory=BattlefieldSliceSelection)
    drilldown_refs: list[OverviewDrilldownReference] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)

    @field_validator("judgment_strength")
    @classmethod
    def judgment_strength_must_use_judgment_status(
        cls,
        value: DisplayStatus,
    ) -> DisplayStatus:
        if not isinstance(value.value, JudgmentStrength):
            raise ValueError("judgment_strength must use JudgmentStrength.")
        return value

    @field_validator("decision_usability")
    @classmethod
    def decision_usability_must_use_decision_status(
        cls,
        value: DisplayStatus,
    ) -> DisplayStatus:
        if not isinstance(value.value, DecisionUsabilityStatus):
            raise ValueError("decision_usability must use DecisionUsabilityStatus.")
        return value
