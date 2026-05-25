from datetime import datetime

from pydantic import Field, field_validator

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


class TaskCreateRequest(StrictBaseModel):
    target_product_name: str | None = None
    target_product_url: str | None = None
    category: str | None = None
    subcategory: str | None = None
    data_source_mode: DataSourceMode = DataSourceMode.DEMO_SNAPSHOT
    research_text: str | None = None

    @field_validator("target_product_name", "category", "subcategory")
    @classmethod
    def reject_blank_required_context(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank.")
        return stripped

    @field_validator("target_product_url", "research_text")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class TaskCreateResponse(StrictBaseModel):
    task_id: str = Field(min_length=1)
    status: TaskStatus
    task: AnalysisTask


class TaskStatusResponse(StrictBaseModel):
    task_id: str = Field(min_length=1)
    target_product_name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    subcategory: str = Field(min_length=1)
    data_source_mode: DataSourceMode
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    target_product_url: str | None = None

    @classmethod
    def from_task(cls, task: AnalysisTask) -> "TaskStatusResponse":
        return cls(
            task_id=task.task_id,
            target_product_name=task.target_product_name,
            target_product_url=task.target_product_url,
            category=task.category,
            subcategory=task.subcategory,
            data_source_mode=task.data_source_mode,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
