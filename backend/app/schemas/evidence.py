from datetime import datetime

from pydantic import Field

from app.schemas.common import ConfidenceLevel, EvidenceSourceType, JsonObject, StrictBaseModel


class Evidence(StrictBaseModel):
    evidence_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    source_type: EvidenceSourceType
    content_summary: str = Field(min_length=1)
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    limitations: str = Field(min_length=1)
    product_id: str | None = None
    source_url: str | None = None
    screenshot_path: str | None = None
    access_time: datetime | None = None
    metadata: JsonObject = Field(default_factory=dict)
