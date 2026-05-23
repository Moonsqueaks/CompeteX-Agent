from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict

JsonObject = dict[str, Any]


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class DataSourceMode(StrEnum):
    DEMO_SNAPSHOT = "demo_snapshot"
    SNAPSHOT_PLUS_LIVE = "snapshot_plus_live"


class TaskStatus(StrEnum):
    CREATED = "created"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    REVIEWING = "reviewing"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL_FAILED = "partial_failed"
    HUMAN_REVIEWING = "human_reviewing"


class AgentName(StrEnum):
    ORCHESTRATOR = "orchestrator"
    COLLECTION = "collection_agent"
    ANALYSIS = "analysis_agent"
    QA = "qa_agent"
    WRITER = "writer_agent"
    HUMAN = "human"


class AgentMessageType(StrEnum):
    ARTIFACT_READY = "artifact_ready"
    REVISION_REQUEST = "revision_request"
    STATUS_UPDATE = "status_update"
    ERROR = "error"


class AgentMessageStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    PROCESSED = "processed"
    REQUIRES_REVISION = "requires_revision"
    RESOLVED = "resolved"
    FAILED = "failed"


class ProductRole(StrEnum):
    TARGET = "target"
    DIRECT_COMPETITOR = "direct_competitor"
    ALTERNATIVE = "alternative"
    CHANNEL_ALTERNATIVE = "channel_alternative"
    REFERENCE = "reference"


class EvidenceSourceType(StrEnum):
    DOUYIN_SKU_SNAPSHOT = "douyin_sku_snapshot"
    DOUYIN_REVIEW_SNAPSHOT = "douyin_review_snapshot"
    USER_RESEARCH = "user_research"
    MANUAL_REVIEW = "manual_review"
    DERIVED_ARTIFACT = "derived_artifact"


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class RiskFlag(StrEnum):
    MISSING_EVIDENCE = "missing_evidence"
    MISSING_ACCESS_TIME = "missing_access_time"
    MISSING_SCREENSHOT = "missing_screenshot"
    UNSUPPORTED_INFERENCE = "unsupported_inference"
    SENSITIVE_CLAIM = "sensitive_claim"
    SINGLE_REVIEW_OVERGENERALIZED = "single_review_overgeneralized"
    CONFLICTING_ANALYSIS = "conflicting_analysis"
    UNRELIABLE_DATA = "unreliable_data"


class ClaimStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    DRAFT = "draft"


class CompetitionType(StrEnum):
    DIRECT = "direct"
    ALTERNATIVE = "alternative"
    CHANNEL = "channel"
    CONTENT_COOCCURRENCE = "content_cooccurrence"


class DecisionStage(StrEnum):
    INFORMATION_REACH = "information_reach"
    INTEREST_FORMATION = "interest_formation"
    CAPABILITY_UNDERSTANDING = "capability_understanding"
    TRUST_BUILDING = "trust_building"
    DECISION_COMPLETION = "decision_completion"


class ReviewSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class ReviewStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    WAIVED = "waived"


class ReviewTargetType(StrEnum):
    TASK = "task"
    PRODUCT = "product"
    EVIDENCE = "evidence"
    CLAIM = "claim"
    COMPETITION_EDGE = "competition_edge"
    REPORT = "report"


class FeedbackTargetType(StrEnum):
    PRODUCT = "product"
    FEATURE_TREE = "feature_tree"
    PRICING_MODEL = "pricing_model"
    USER_PERSONA = "user_persona"
    CLAIM = "claim"
    EVIDENCE = "evidence"
    COMPETITION_EDGE = "competition_edge"
    SLICE = "slice"


class FeedbackAction(StrEnum):
    UPDATE_FIELD = "update_field"
    ADD_COMPETITOR = "add_competitor"
    REMOVE_COMPETITOR = "remove_competitor"
    MARK_ACCEPTED = "mark_accepted"
    MARK_REJECTED = "mark_rejected"
    MARK_NEEDS_REVIEW = "mark_needs_review"
    ADD_NOTE = "add_note"


class RunStatus(StrEnum):
    STARTED = "started"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REQUIRES_REVISION = "requires_revision"
    SKIPPED = "skipped"


class ToolCallStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
