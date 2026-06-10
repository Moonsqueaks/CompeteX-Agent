from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from typing import Any, TypedDict, cast

from pydantic import BaseModel

from app.schemas import (
    AgentMessage,
    AgentRunLog,
    AnalysisTask,
    Claim,
    CompetitionEdge,
    CompetitorBattlecard,
    Evidence,
    FeatureTree,
    GapMatrixItem,
    HumanFeedback,
    KnowledgeArtifact,
    MarkdownReport,
    OpportunityItem,
    PricingModel,
    Product,
    ReportData,
    ReportQualityCheck,
    ReviewInsight,
    ReviewSignalCluster,
    ReviewTask,
    StrategyBrief,
    TokenUsageLog,
    ToolCallLog,
    UserPersona,
)
from app.schemas.common import JsonObject

ArtifactInput = BaseModel | Mapping[str, Any]


class TaskGraphState(TypedDict):
    task: JsonObject
    products: list[JsonObject]
    evidences: list[JsonObject]
    review_insights: list[JsonObject]
    feature_trees: list[JsonObject]
    pricing_models: list[JsonObject]
    user_personas: list[JsonObject]
    strategy_briefs: list[JsonObject]
    competitor_battlecards: list[JsonObject]
    gap_matrix_items: list[JsonObject]
    opportunity_items: list[JsonObject]
    review_signal_clusters: list[JsonObject]
    claims: list[JsonObject]
    competition_edges: list[JsonObject]
    review_tasks: list[JsonObject]
    human_feedback: list[JsonObject]
    agent_messages: list[JsonObject]
    run_logs: list[JsonObject]
    tool_call_logs: list[JsonObject]
    token_usage_logs: list[JsonObject]
    knowledge_artifacts: list[JsonObject]
    report_quality_checks: list[JsonObject]
    reports: list[JsonObject]
    markdown_reports: list[JsonObject]
    metadata: JsonObject


STATE_LIST_FIELDS = (
    "products",
    "evidences",
    "review_insights",
    "feature_trees",
    "pricing_models",
    "user_personas",
    "strategy_briefs",
    "competitor_battlecards",
    "gap_matrix_items",
    "opportunity_items",
    "review_signal_clusters",
    "claims",
    "competition_edges",
    "review_tasks",
    "human_feedback",
    "agent_messages",
    "run_logs",
    "tool_call_logs",
    "token_usage_logs",
    "knowledge_artifacts",
    "report_quality_checks",
    "reports",
    "markdown_reports",
)


def create_initial_state(task: AnalysisTask | Mapping[str, Any]) -> TaskGraphState:
    task_payload = _dump_artifact(task)
    _require_task_id(task_payload)

    return TaskGraphState(
        task=task_payload,
        products=[],
        evidences=[],
        review_insights=[],
        feature_trees=[],
        pricing_models=[],
        user_personas=[],
        strategy_briefs=[],
        competitor_battlecards=[],
        gap_matrix_items=[],
        opportunity_items=[],
        review_signal_clusters=[],
        claims=[],
        competition_edges=[],
        review_tasks=[],
        human_feedback=[],
        agent_messages=[],
        run_logs=[],
        tool_call_logs=[],
        token_usage_logs=[],
        knowledge_artifacts=[],
        report_quality_checks=[],
        reports=[],
        markdown_reports=[],
        metadata={},
    )


def append_product(state: TaskGraphState, product: Product | Mapping[str, Any]) -> TaskGraphState:
    return _append_artifact(state, "products", product)


def append_evidence(
    state: TaskGraphState,
    evidence: Evidence | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "evidences", evidence)


def append_review_insight(
    state: TaskGraphState,
    review_insight: ReviewInsight | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "review_insights", review_insight)


def append_feature_tree(
    state: TaskGraphState,
    feature_tree: FeatureTree | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "feature_trees", feature_tree)


def append_pricing_model(
    state: TaskGraphState,
    pricing_model: PricingModel | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "pricing_models", pricing_model)


def append_user_persona(
    state: TaskGraphState,
    user_persona: UserPersona | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "user_personas", user_persona)


def append_strategy_brief(
    state: TaskGraphState,
    strategy_brief: StrategyBrief | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "strategy_briefs", strategy_brief)


def append_competitor_battlecard(
    state: TaskGraphState,
    battlecard: CompetitorBattlecard | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "competitor_battlecards", battlecard)


def append_gap_matrix_item(
    state: TaskGraphState,
    gap_matrix_item: GapMatrixItem | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "gap_matrix_items", gap_matrix_item)


def append_opportunity_item(
    state: TaskGraphState,
    opportunity_item: OpportunityItem | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "opportunity_items", opportunity_item)


def append_review_signal_cluster(
    state: TaskGraphState,
    review_signal_cluster: ReviewSignalCluster | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "review_signal_clusters", review_signal_cluster)


def append_claim(state: TaskGraphState, claim: Claim | Mapping[str, Any]) -> TaskGraphState:
    return _append_artifact(state, "claims", claim)


def append_competition_edge(
    state: TaskGraphState,
    competition_edge: CompetitionEdge | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "competition_edges", competition_edge)


def append_review_task(
    state: TaskGraphState,
    review_task: ReviewTask | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "review_tasks", review_task)


def append_human_feedback(
    state: TaskGraphState,
    human_feedback: HumanFeedback | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "human_feedback", human_feedback)


def append_agent_message(
    state: TaskGraphState,
    agent_message: AgentMessage | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "agent_messages", agent_message)


def append_run_log(
    state: TaskGraphState,
    run_log: AgentRunLog | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "run_logs", run_log)


def append_tool_call_log(
    state: TaskGraphState,
    tool_call_log: ToolCallLog | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "tool_call_logs", tool_call_log)


def append_token_usage_log(
    state: TaskGraphState,
    token_usage_log: TokenUsageLog | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "token_usage_logs", token_usage_log)


def append_knowledge_artifact(
    state: TaskGraphState,
    knowledge_artifact: KnowledgeArtifact | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "knowledge_artifacts", knowledge_artifact)


def append_report_quality_check(
    state: TaskGraphState,
    report_quality_check: ReportQualityCheck | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "report_quality_checks", report_quality_check)


def append_report_data(
    state: TaskGraphState,
    report_data: ReportData | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "reports", report_data)


def append_markdown_report(
    state: TaskGraphState,
    markdown_report: MarkdownReport | Mapping[str, Any],
) -> TaskGraphState:
    return _append_artifact(state, "markdown_reports", markdown_report)


def serialize_state_for_trace(state: TaskGraphState) -> JsonObject:
    trace_payload: JsonObject = {
        "task": _dump_artifact(state["task"]),
        "metadata": _dump_artifact(state["metadata"]),
        "counts": {field: len(state[field]) for field in STATE_LIST_FIELDS},
    }

    for field in STATE_LIST_FIELDS:
        trace_payload[field] = [_dump_artifact(item) for item in state[field]]

    return trace_payload


def _append_artifact(
    state: TaskGraphState,
    field: str,
    artifact: ArtifactInput,
) -> TaskGraphState:
    state[field].append(_dump_artifact(artifact))
    return state


def _dump_artifact(artifact: ArtifactInput) -> JsonObject:
    payload = _to_jsonable(artifact)
    if not isinstance(payload, dict):
        raise TypeError("TaskGraphState artifacts must serialize to JSON objects.")
    return payload


def _require_task_id(task_payload: JsonObject) -> None:
    task_id = task_payload.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("TaskGraphState requires a non-empty task_id.")


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return cast(Any, value)
