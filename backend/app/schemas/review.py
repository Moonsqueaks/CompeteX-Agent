from datetime import datetime

from pydantic import Field

from app.schemas.common import (
    AgentName,
    FeedbackAction,
    FeedbackTargetType,
    JsonObject,
    ReviewSeverity,
    ReviewStatus,
    ReviewTargetType,
    StrictBaseModel,
    TaskStatus,
)


class ReviewTask(StrictBaseModel):
    review_task_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    check_name: str = Field(min_length=1)
    issue_code: str = Field(min_length=1)
    severity: ReviewSeverity
    status: ReviewStatus = ReviewStatus.OPEN
    target_type: ReviewTargetType
    target_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    required_action: str = Field(min_length=1)
    created_at: datetime
    target_agent: AgentName | None = None
    related_claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    resolved_at: datetime | None = None


class HumanFeedback(StrictBaseModel):
    feedback_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    target_type: FeedbackTargetType
    target_id: str = Field(min_length=1)
    action: FeedbackAction
    before_value: JsonObject = Field(default_factory=dict)
    after_value: JsonObject = Field(default_factory=dict)
    reason: str = Field(min_length=1)
    created_at: datetime


class HumanFeedbackCreateRequest(StrictBaseModel):
    target_type: FeedbackTargetType
    target_id: str = Field(min_length=1)
    action: FeedbackAction
    after_value: JsonObject = Field(default_factory=dict)
    reason: str = Field(min_length=1)


class HumanFeedbackCreateResponse(StrictBaseModel):
    feedback: HumanFeedback
    task_status: TaskStatus
    recompute_status: str = Field(min_length=1)
    affected_artifact_ids: list[str] = Field(default_factory=list)
    metadata: JsonObject = Field(default_factory=dict)
