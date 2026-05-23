from datetime import datetime

from pydantic import Field

from app.schemas.common import DataSourceMode, JsonObject, StrictBaseModel, TaskStatus


class AnalysisTask(StrictBaseModel):
    task_id: str = Field(min_length=1)
    target_product_name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    subcategory: str = Field(min_length=1)
    data_source_mode: DataSourceMode = DataSourceMode.DEMO_SNAPSHOT
    status: TaskStatus = TaskStatus.CREATED
    created_at: datetime
    updated_at: datetime
    target_product_url: str | None = None
    research_text: str | None = None
    metadata: JsonObject = Field(default_factory=dict)
