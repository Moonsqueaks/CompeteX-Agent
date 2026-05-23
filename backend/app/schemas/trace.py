from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.common import AgentName, JsonObject, RunStatus, StrictBaseModel, ToolCallStatus


class AgentRunLog(StrictBaseModel):
    run_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    agent_name: AgentName
    status: RunStatus
    started_at: datetime
    ended_at: datetime | None = None
    input_summary: str | None = None
    output_summary: str | None = None
    error_message: str | None = None


class ToolCallLog(StrictBaseModel):
    tool_call_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    tool_name: str = Field(min_length=1)
    arguments_summary: JsonObject = Field(default_factory=dict)
    status: ToolCallStatus
    started_at: datetime
    ended_at: datetime | None = None
    duration_ms: int | None = Field(default=None, ge=0)
    error_message: str | None = None


class TokenUsageLog(StrictBaseModel):
    usage_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    agent_name: AgentName
    model_name: str = Field(min_length=1)
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    created_at: datetime

    @model_validator(mode="after")
    def validate_total_tokens(self) -> "TokenUsageLog":
        expected_total = self.prompt_tokens + self.completion_tokens
        if self.total_tokens != expected_total:
            raise ValueError("total_tokens must equal prompt_tokens + completion_tokens")
        return self
