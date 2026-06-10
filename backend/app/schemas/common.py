from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict

JsonObject = dict[str, Any]


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class DataSourceMode(StrEnum):
    DEMO_SNAPSHOT = "demo_snapshot"
    SNAPSHOT_PLUS_LIVE = "snapshot_plus_live"
    BUILTIN_CANDIDATES = "builtin_candidates"


class EvidenceSourceMode(StrEnum):
    LOCAL_SNAPSHOT = "local_snapshot"
    SNAPSHOT_PLUS_KNOWN_PUBLIC_PAGE = "snapshot_plus_known_public_page"


class CandidateStrategy(StrEnum):
    SNAPSHOT_POOL = "snapshot_pool"
    BUILTIN_CANDIDATES = "builtin_candidates"


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


class ProductImageStatus(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"


class EvidenceSourceType(StrEnum):
    DOUYIN_SKU_SNAPSHOT = "douyin_sku_snapshot"
    DOUYIN_REVIEW_SNAPSHOT = "douyin_review_snapshot"
    USER_RESEARCH = "user_research"
    MANUAL_REVIEW = "manual_review"
    DERIVED_ARTIFACT = "derived_artifact"
    PUBLIC_PRODUCT_PAGE = "public_product_page"
    PUBLIC_BRAND_PAGE = "public_brand_page"
    OFFICIAL_PRODUCT_PAGE = "official_product_page"
    OFFICIAL_HELP_DOC = "official_help_doc"
    APP_STORE_PAGE = "app_store_page"
    OFFICIAL_RELEASE_NOTE = "official_release_note"


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
    BATTLECARD = "battlecard"
    GAP_MATRIX_ITEM = "gap_matrix_item"
    OPPORTUNITY_ITEM = "opportunity_item"
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


class JudgmentStrength(StrEnum):
    CLEAR = "clear_judgment"
    DIRECTIONAL = "directional_judgment"
    HYPOTHESIS = "hypothesis_only"


class DecisionUsabilityStatus(StrEnum):
    READY = "ready_for_initial_decision"
    CAUTION = "decision_with_caution"
    DIRECTIONAL_ONLY = "directional_reference_only"


class EvidenceCredibilityStatus(StrEnum):
    DIRECTLY_ADOPTABLE = "directly_adoptable"
    CAUTIOUS_REFERENCE = "cautious_reference"
    INSUFFICIENT = "insufficient_evidence"


class ThreatLevel(StrEnum):
    HIGH = "high_threat"
    MEDIUM = "medium_threat"
    LOW = "low_threat"
    HIGH_SCORE_NEEDS_REVIEW = "high_score_needs_review"


class PMRelationshipLabel(StrEnum):
    HEAD_TO_HEAD = "head_to_head"
    LOW_PRICE_INTERCEPTION = "low_price_interception"
    SCENARIO_SUBSTITUTE = "scenario_substitute"
    TRUST_SUPPRESSION = "trust_suppression"
    CONTENT_SEEDING_COMPETITION = "content_seeding_competition"


class ActionPriority(StrEnum):
    P0 = "p0_immediate"
    P1 = "p1_current_iteration"
    P2 = "p2_follow_up_validation"


class ResponsibilityType(StrEnum):
    PRODUCT_FEATURE = "product_feature"
    CONTENT_EXPRESSION = "content_expression"
    PRICING_STRATEGY = "pricing_strategy"
    EVIDENCE_RESEARCH = "evidence_research"
