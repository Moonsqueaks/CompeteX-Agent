from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.agent_message import AgentMessage
from app.schemas.common import (
    AgentName,
    ConfidenceLevel,
    EvidenceSourceType,
    JsonObject,
    ReviewSeverity,
    ReviewStatus,
    ReviewTargetType,
    RiskFlag,
    RunStatus,
    StrictBaseModel,
    ToolCallStatus,
)
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
    business_impact: str = Field(
        default="记录了分析流程中的结构化变化，需结合变更前后内容判断业务影响。",
        min_length=1,
    )
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


class TraceEvidenceItem(StrictBaseModel):
    evidence_id: str = Field(min_length=1)
    product_id: str | None = None
    source_type: EvidenceSourceType
    confidence_level: ConfidenceLevel
    access_time: datetime | None = None
    access_time_status: str = Field(min_length=1)
    content_summary: str = Field(min_length=1)
    limitations: str = Field(min_length=1)
    source_url: str | None = None
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    navigation: JsonObject = Field(default_factory=dict)


class TraceEvidenceChain(StrictBaseModel):
    chain_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    claim_content: str = Field(min_length=1)
    claim_status: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    is_inference: bool
    report_section_ids: list[str] = Field(default_factory=list)
    evidence_items: list[TraceEvidenceItem] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    navigation: JsonObject = Field(default_factory=dict)


class TraceQualityRecord(StrictBaseModel):
    quality_record_id: str = Field(min_length=1)
    review_task_id: str = Field(min_length=1)
    check_item: str = Field(min_length=1)
    issue_code: str = Field(min_length=1)
    severity: ReviewSeverity
    target_type: ReviewTargetType
    target_id: str = Field(min_length=1)
    target_agent: AgentName | None = None
    status: ReviewStatus
    resolved: bool
    needs_attention: bool
    issue_summary: str = Field(min_length=1)
    required_action: str = Field(min_length=1)
    action_result: str = Field(min_length=1)
    related_claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    navigation: JsonObject = Field(default_factory=dict)


class TraceProcessView(StrictBaseModel):
    technical_details_folded: bool = True
    default_tab: str = "evidence_chain"
    dag_node_count: int = Field(ge=0)
    agent_run_count: int = Field(ge=0)
    tool_call_count: int = Field(ge=0)
    token_usage_count: int = Field(ge=0)
    prompt_preview_count: int = Field(ge=0)


class TraceDrilldownTarget(StrictBaseModel):
    target_id: str = Field(min_length=1)
    tab: str = Field(min_length=1)
    label: str = Field(min_length=1)
    query: JsonObject = Field(default_factory=dict)


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
    evidence_chains: list[TraceEvidenceChain] = Field(default_factory=list)
    quality_records: list[TraceQualityRecord] = Field(default_factory=list)
    process_view: TraceProcessView | None = None
    drilldown_targets: list[TraceDrilldownTarget] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)
