from datetime import datetime

from pydantic import Field

from app.schemas.common import (
    ProductImageStatus,
    ProductRole,
    RiskFlag,
    StrictBaseModel,
)


class Product(StrictBaseModel):
    product_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    subcategory: str = Field(min_length=1)
    role: ProductRole
    created_at: datetime
    sku_id: str | None = None
    brand: str | None = None
    shop_name: str | None = None
    product_url: str | None = None
    primary_image_path: str | None = None
    primary_image_url: str | None = None
    primary_image_source_path: str | None = None
    primary_image_status: ProductImageStatus = ProductImageStatus.MISSING
    evidence_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class FeatureTree(StrictBaseModel):
    feature_tree_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    cleaning_capability: list[str] = Field(default_factory=list)
    odor_control: list[str] = Field(default_factory=list)
    safety_features: list[str] = Field(default_factory=list)
    smart_features: list[str] = Field(default_factory=list)
    maintenance_cost: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class PricingModel(StrictBaseModel):
    pricing_model_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    price_band: str = Field(min_length=1)
    currency: str = Field(default="CNY", min_length=3, max_length=3)
    list_price: float | None = Field(default=None, ge=0)
    final_price: float | None = Field(default=None, ge=0)
    promotions: list[str] = Field(default_factory=list)
    bundle_description: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    access_time: datetime | None = None
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class UserPersona(StrictBaseModel):
    persona_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    personas: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    scenarios: list[str] = Field(default_factory=list)
    decision_factors: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    is_inference: bool = True
    risk_flags: list[RiskFlag] = Field(default_factory=list)
