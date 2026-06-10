from datetime import datetime

from pydantic import Field

from app.schemas.common import ConfidenceLevel, JsonObject, StrictBaseModel


class ExtractedField(StrictBaseModel):
    field_name: str = Field(min_length=1)
    value: str = Field(min_length=1)
    source_snippet: str = Field(min_length=1)
    extraction_method: str = Field(min_length=1)
    confidence_level: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    limitations: str = Field(min_length=1)


class PublicPageSnapshot(StrictBaseModel):
    url: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    http_status: int | None = Field(default=None, ge=100, le=599)
    access_time: datetime
    title: str | None = None
    text_summary: str | None = None
    html_cache_path: str | None = None
    screenshot_path: str | None = None
    parse_status: str = Field(default="fetched", min_length=1)
    content_type: str | None = None
    response_size_bytes: int = Field(default=0, ge=0)
    metadata: JsonObject = Field(default_factory=dict)


class PublicPageEnrichmentResult(StrictBaseModel):
    url: str = Field(min_length=1)
    product_id: str | None = None
    evidence_id: str | None = None
    status: str = Field(min_length=1)
    extracted_fields: list[ExtractedField] = Field(default_factory=list)
    missing_fields_filled: list[str] = Field(default_factory=list)
    conflicts: list[JsonObject] = Field(default_factory=list)
    unavailable_fields: list[str] = Field(default_factory=list)
    fallback_reason: str | None = None
    metadata: JsonObject = Field(default_factory=dict)
