from datetime import datetime
from enum import StrEnum

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
    missing_fields: list[str] = Field(default_factory=list)
    missing_reason: str | None = None
    pricing_note: str | None = None


class PricingEvidenceSummary(StrictBaseModel):
    evidence_ids: list[str] = Field(default_factory=list)
    access_time_status: str = Field(min_length=1)
    access_time: datetime | None = None
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class ProfileComparisonSlot(StrEnum):
    TARGET = "target"
    HIGHEST_THREAT_DIRECT = "highest_threat_direct_competitor"
    HIGHEST_THREAT_ALTERNATIVE = "highest_threat_alternative"


class ProfileComparisonDimensionKey(StrEnum):
    PRICE_BAND = "price_band"
    CORE_SELLING_POINTS = "core_selling_points"
    PERSONA = "persona"
    SCENARIO = "scenario"
    EVIDENCE_CREDIBILITY = "evidence_credibility"


class TargetComparisonStatus(StrEnum):
    ADVANTAGE = "advantage"
    PARITY = "parity"
    WEAKNESS = "weakness"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ProfileComparisonProduct(StrictBaseModel):
    slot: ProfileComparisonSlot
    product_id: str = Field(min_length=1)
    product_name: str = Field(min_length=1)
    brand: str | None = None
    primary_image_path: str | None = None
    product_url: str | None = None


class ProfileComparisonValue(StrictBaseModel):
    product_id: str = Field(min_length=1)
    value: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)


class ProfileComparisonDimension(StrictBaseModel):
    dimension_key: ProfileComparisonDimensionKey
    dimension_label: str = Field(min_length=1)
    values: list[ProfileComparisonValue] = Field(default_factory=list)
    target_status: TargetComparisonStatus
    status_reason: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    trace_refs: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class ProductProfileComparison(StrictBaseModel):
    target_product_id: str = Field(min_length=1)
    compared_products: list[ProfileComparisonProduct] = Field(default_factory=list)
    dimensions: list[ProfileComparisonDimension] = Field(default_factory=list)


class ProductProfileData(StrictBaseModel):
    profile_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    generated_at: datetime
    product: Product
    feature_tree: FeatureTree
    pricing_model: PricingModel
    pricing_evidence: PricingEvidenceSummary
    user_persona: UserPersona
    horizontal_comparison: ProductProfileComparison | None = None
    evidence_summaries: list[EvidenceSummary] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)
