from datetime import datetime

from pydantic import Field

from app.schemas.common import ConfidenceLevel, JsonObject, StrictBaseModel


class KnowledgeSource(StrictBaseModel):
    source_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    source_name: str = Field(min_length=1)
    source_url: str | None = None
    access_time: datetime | None = None
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    limitations: list[str] = Field(default_factory=list)


class KnowledgeItem(StrictBaseModel):
    item_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    dimension: str = Field(min_length=1)
    content: str = Field(min_length=1)
    use_policy: str = Field(min_length=1)
    source_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)


class KnowledgeArtifact(StrictBaseModel):
    knowledge_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    subcategory: str = Field(min_length=1)
    generated_at: datetime
    retrieval_mode: str = Field(min_length=1)
    external_search_performed: bool = False
    query_context: JsonObject = Field(default_factory=dict)
    sources: list[KnowledgeSource] = Field(default_factory=list)
    items: list[KnowledgeItem] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)
