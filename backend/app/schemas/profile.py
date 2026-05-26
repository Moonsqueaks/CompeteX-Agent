from datetime import datetime

from pydantic import Field

from app.schemas.common import (
    ConfidenceLevel,
    EvidenceSourceType,
    JsonObject,
    RiskFlag,
    StrictBaseModel,
)
from app.schemas.product import FeatureTree, PricingModel, Product, UserPersona


class EvidenceSummary(StrictBaseModel):
    evidence_id: str = Field(min_length=1)
    source_type: EvidenceSourceType
    confidence_level: ConfidenceLevel
    content_summary: str = Field(min_length=1)
    limitations: str = Field(min_length=1)
    access_time_status: str = Field(min_length=1)
    product_id: str | None = None
    source_url: str | None = None
    screenshot_path: str | None = None
    access_time: datetime | None = None
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class PricingEvidenceSummary(StrictBaseModel):
    evidence_ids: list[str] = Field(default_factory=list)
    access_time_status: str = Field(min_length=1)
    access_time: datetime | None = None
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class ProductProfileData(StrictBaseModel):
    profile_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    generated_at: datetime
    product: Product
    feature_tree: FeatureTree
    pricing_model: PricingModel
    pricing_evidence: PricingEvidenceSummary
    user_persona: UserPersona
    evidence_summaries: list[EvidenceSummary] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)
