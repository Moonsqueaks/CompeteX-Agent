from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.agent_message import AgentMessage
from app.schemas.common import AgentName, JsonObject, RunStatus, StrictBaseModel, ToolCallStatus
from app.schemas.review import ReviewTask


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


class TraceDagNode(StrictBaseModel):
    node_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    node_type: str = Field(min_length=1)
    status: str = Field(min_length=1)
    agent_name: AgentName | None = None
    run_ids: list[str] = Field(default_factory=list)
    current: bool = False
    failed: bool = False
    visible: bool = True


class TraceDagEdge(StrictBaseModel):
    edge_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    label: str = Field(min_length=1)
    condition: str | None = None


class TraceDiff(StrictBaseModel):
    diff_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    target_type: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    before: JsonObject = Field(default_factory=dict)
    after: JsonObject = Field(default_factory=dict)
    revision_message_ids: list[str] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)


class TracePromptPreview(StrictBaseModel):
    preview_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    agent_name: AgentName
    title: str = Field(min_length=1)
    content_summary: str = Field(min_length=1)
    folded: bool = True
    redacted: bool = True


class TraceData(StrictBaseModel):
    trace_view_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    task_status: str = Field(min_length=1)
    workflow_status: str = Field(min_length=1)
    generated_at: datetime
    dag_nodes: list[TraceDagNode] = Field(default_factory=list)
    dag_edges: list[TraceDagEdge] = Field(default_factory=list)
    agent_runs: list[AgentRunLog] = Field(default_factory=list)
    tool_calls: list[ToolCallLog] = Field(default_factory=list)
    token_usage: list[TokenUsageLog] = Field(default_factory=list)
    qa_reviews: list[ReviewTask] = Field(default_factory=list)
    revision_messages: list[AgentMessage] = Field(default_factory=list)
    diffs: list[TraceDiff] = Field(default_factory=list)
    prompt_previews: list[TracePromptPreview] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)
