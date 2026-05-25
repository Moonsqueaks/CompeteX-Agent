from datetime import datetime

from pydantic import Field

from app.schemas.common import ConfidenceLevel, JsonObject, RiskFlag, StrictBaseModel


class ReviewInsight(StrictBaseModel):
    review_insight_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    created_at: datetime
    sku_id: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    market_signals: JsonObject = Field(default_factory=dict)
    limitations: str = Field(min_length=1)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
