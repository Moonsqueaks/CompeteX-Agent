import re
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from typing import Any

from app.graph import build_analysis_workflow, create_initial_state
from app.graph.workflow import ANALYSIS_NODE, COLLECTION_NODE, QA_NODE, WRITER_NODE
from app.schemas import (
    AgentMessage,
    AgentMessageType,
    AgentName,
    AgentRunLog,
    AnalysisTask,
    ReviewTask,
    TaskStatus,
    TokenUsageLog,
    ToolCallLog,
)
from app.schemas.common import JsonObject
from app.schemas.trace import (
    TraceDagEdge,
    TraceDagNode,
    TraceData,
    TraceDiff,
    TracePromptPreview,
)
from app.storage import ArtifactRepository, TaskRepository

TRACE_ARTIFACT_TYPE = "trace_data"

FAILED_NODE = "failed"
END_NODE = "end"
MAX_PROMPT_SUMMARY_CHARS = 180
_SENSITIVE_KEY_NAMES = {
    "api_key",
    "apikey",
    "authorization",
    "password",
    "secret",
    "access_token",
    "refresh_token",
}
_SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|authorization|secret|password)\s*[:=]\s*[^,\s]+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+"),
    re.compile(r"\bsk-[A-Za-z0-9._\-]{8,}\b"),
)

WorkflowFactory = Callable[[], Any]


class TraceServiceError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class TraceService:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        artifact_repository: ArtifactRepository,
        workflow_factory: WorkflowFactory = build_analysis_workflow,
    ) -> None:
        self.task_repository = task_repository
        self.artifact_repository = artifact_repository
        self.workflow_factory = workflow_factory

    def get_trace(self, task_id: str) -> TraceData:
        task = self.task_repository.get(task_id)
        if task is None:
            raise TraceServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task_id},
            )

        if task.status == TaskStatus.COMPLETED:
            cached = self.artifact_repository.get(
                task_id,
                TRACE_ARTIFACT_TYPE,
                _trace_artifact_id(task_id),
                TraceData,
            )
            if cached is not None:
                return TraceData.model_validate(cached)
            return self._generate_and_cache_trace(task)

        return _build_trace_data(
            task=task,
            state=None,
            trace_view_id=_trace_artifact_id(task_id),
        )

    def _generate_and_cache_trace(self, task: AnalysisTask) -> TraceData:
        try:
            workflow = self.workflow_factory()
            state = create_initial_state(task)
            result = workflow.invoke(state)
        except Exception as exc:
            raise TraceServiceError(
                "TRACE_GENERATION_FAILED",
                "Trace generation failed",
                status_code=500,
                details={"task_id": task.task_id, "reason": exc.__class__.__name__},
            ) from exc

        trace = _build_trace_data(
            task=task,
            state=result,
            trace_view_id=_trace_artifact_id(task.task_id),
        )
        self.artifact_repository.save(TRACE_ARTIFACT_TYPE, trace.trace_view_id, trace)
        return trace


def _build_trace_data(
    *,
    task: AnalysisTask,
    state: Mapping[str, Any] | None,
    trace_view_id: str,
) -> TraceData:
    workflow_metadata = _workflow_metadata(state)
    task_status = _state_task_status(task, state)
    workflow_status = str(workflow_metadata.get("status") or task_status)
    agent_runs = _model_list(state, "run_logs", AgentRunLog)
    tool_calls = _model_list(state, "tool_call_logs", ToolCallLog)
    token_usage = _model_list(state, "token_usage_logs", TokenUsageLog)
    qa_reviews = _model_list(state, "review_tasks", ReviewTask)
    messages = _model_list(state, "agent_messages", AgentMessage)
    revision_messages = [
        message
        for message in messages
        if message.message_type == AgentMessageType.REVISION_REQUEST
    ]

    trace = TraceData(
        trace_view_id=trace_view_id,
        task_id=task.task_id,
        task_status=task_status,
        workflow_status=workflow_status,
        generated_at=datetime.now(UTC),
        dag_nodes=_dag_nodes(agent_runs, workflow_metadata, workflow_status),
        dag_edges=_dag_edges(),
        agent_runs=agent_runs,
        tool_calls=tool_calls,
        token_usage=token_usage,
        qa_reviews=qa_reviews,
        revision_messages=revision_messages,
        diffs=_trace_diffs(state),
        prompt_previews=_prompt_previews(agent_runs),
        metadata=_trace_metadata(state, workflow_status),
    )
    return _redacted_trace(trace)


def _dag_nodes(
    agent_runs: list[AgentRunLog],
    workflow_metadata: JsonObject,
    workflow_status: str,
) -> list[TraceDagNode]:
    run_ids_by_agent: dict[str, list[str]] = {}
    status_by_agent: dict[str, str] = {}
    for run in agent_runs:
        agent_name = run.agent_name.value
        run_ids_by_agent.setdefault(agent_name, []).append(run.run_id)
        status_by_agent[agent_name] = run.status.value

    current_node = workflow_metadata.get("current_node")
    nodes = [
        _agent_node(
            node_id=COLLECTION_NODE,
            label="Collection Agent",
            agent_name=AgentName.COLLECTION,
            run_ids_by_agent=run_ids_by_agent,
            status_by_agent=status_by_agent,
            current_node=current_node,
        ),
        _agent_node(
            node_id=ANALYSIS_NODE,
            label="Analysis Agent",
            agent_name=AgentName.ANALYSIS,
            run_ids_by_agent=run_ids_by_agent,
            status_by_agent=status_by_agent,
            current_node=current_node,
        ),
        _agent_node(
            node_id=QA_NODE,
            label="QA Agent",
            agent_name=AgentName.QA,
            run_ids_by_agent=run_ids_by_agent,
            status_by_agent=status_by_agent,
            current_node=current_node,
        ),
        _agent_node(
            node_id=WRITER_NODE,
            label="Writer Agent",
            agent_name=AgentName.WRITER,
            run_ids_by_agent=run_ids_by_agent,
            status_by_agent=status_by_agent,
            current_node=current_node,
        ),
    ]
    nodes.append(
        TraceDagNode(
            node_id=FAILED_NODE,
            label="Failed",
            node_type="terminal",
            status="failed" if workflow_status == "failed" else "skipped",
            current=current_node == FAILED_NODE,
            failed=workflow_status == "failed",
            visible=True,
        )
    )
    nodes.append(
        TraceDagNode(
            node_id=END_NODE,
            label="End",
            node_type="terminal",
            status="succeeded" if workflow_status == "completed" else "pending",
            current=False,
            failed=False,
            visible=True,
        )
    )
    return nodes


def _agent_node(
    *,
    node_id: str,
    label: str,
    agent_name: AgentName,
    run_ids_by_agent: dict[str, list[str]],
    status_by_agent: dict[str, str],
    current_node: Any,
) -> TraceDagNode:
    status = status_by_agent.get(agent_name.value, "pending")
    return TraceDagNode(
        node_id=node_id,
        label=label,
        node_type="agent",
        agent_name=agent_name,
        status=status,
        run_ids=run_ids_by_agent.get(agent_name.value, []),
        current=current_node == node_id,
        failed=status == "failed",
        visible=True,
    )


def _dag_edges() -> list[TraceDagEdge]:
    return [
        TraceDagEdge(
            edge_id="edge_collection_analysis",
            source=COLLECTION_NODE,
            target=ANALYSIS_NODE,
            label="collection_complete",
        ),
        TraceDagEdge(
            edge_id="edge_analysis_qa",
            source=ANALYSIS_NODE,
            target=QA_NODE,
            label="analysis_complete",
        ),
        TraceDagEdge(
            edge_id="edge_qa_writer",
            source=QA_NODE,
            target=WRITER_NODE,
            label="qa_passed",
            condition="qa_status == passed",
        ),
        TraceDagEdge(
            edge_id="edge_qa_collection",
            source=QA_NODE,
            target=COLLECTION_NODE,
            label="collection_revision",
            condition="revision_target == collection_agent",
        ),
        TraceDagEdge(
            edge_id="edge_qa_analysis",
            source=QA_NODE,
            target=ANALYSIS_NODE,
            label="analysis_revision",
            condition="revision_target == analysis_agent",
        ),
        TraceDagEdge(
            edge_id="edge_qa_failed",
            source=QA_NODE,
            target=FAILED_NODE,
            label="failed",
            condition="qa_failed",
        ),
        TraceDagEdge(
            edge_id="edge_writer_end",
            source=WRITER_NODE,
            target=END_NODE,
            label="report_ready",
        ),
    ]


def _trace_diffs(state: Mapping[str, Any] | None) -> list[TraceDiff]:
    if state is None:
        return []
    metadata = state.get("metadata", {})
    if not isinstance(metadata, Mapping):
        return []

    diffs: list[TraceDiff] = []
    collection_repair = metadata.get("collection_agent_repair")
    if isinstance(collection_repair, Mapping):
        diffs.extend(_collection_repair_diffs(collection_repair))

    analysis_recompute = metadata.get("analysis_agent_recompute")
    if isinstance(analysis_recompute, Mapping):
        diffs.extend(_analysis_recompute_diffs(analysis_recompute))
    return diffs


def _collection_repair_diffs(repair: Mapping[str, Any]) -> list[TraceDiff]:
    result = []
    for index, diff in enumerate(_mapping_items(repair.get("diffs")), start=1):
        result.append(
            TraceDiff(
                diff_id=f"collection_repair_diff_{index:03d}",
                source="collection_agent_repair",
                target_type="evidence",
                target_id=str(diff.get("new_evidence_id") or diff.get("target_evidence_id")),
                status=str(diff.get("status") or "unknown"),
                before=_json_object(diff.get("before")),
                after=_json_object(diff.get("after")),
                revision_message_ids=_string_items(diff.get("revision_message_ids")),
                metadata={
                    "run_id": repair.get("run_id"),
                    "target_evidence_id": diff.get("target_evidence_id"),
                    "new_evidence_id": diff.get("new_evidence_id"),
                },
            )
        )
    return result


def _analysis_recompute_diffs(recompute: Mapping[str, Any]) -> list[TraceDiff]:
    result = []
    for index, diff in enumerate(_mapping_items(recompute.get("diffs")), start=1):
        result.append(
            TraceDiff(
                diff_id=f"analysis_edge_diff_{index:03d}",
                source="analysis_agent_recompute",
                target_type="competition_edge",
                target_id=str(diff.get("edge_id") or diff.get("target_id")),
                status=str(diff.get("status") or "recomputed"),
                before=_json_object(diff.get("before")),
                after=_json_object(diff.get("after")),
                revision_message_ids=_string_items(recompute.get("revision_message_ids")),
                metadata={
                    "run_id": recompute.get("run_id"),
                    "target_claim_ids": _string_items(recompute.get("target_claim_ids")),
                },
            )
        )
    for index, diff in enumerate(_mapping_items(recompute.get("claim_diffs")), start=1):
        result.append(
            TraceDiff(
                diff_id=f"analysis_claim_diff_{index:03d}",
                source="analysis_agent_recompute",
                target_type="claim",
                target_id=str(diff.get("claim_id") or diff.get("target_id")),
                status=str(diff.get("status") or "recomputed"),
                before=_json_object(diff.get("before")),
                after=_json_object(diff.get("after")),
                revision_message_ids=_string_items(recompute.get("revision_message_ids")),
                metadata={
                    "run_id": recompute.get("run_id"),
                    "target_edge_ids": _string_items(recompute.get("target_edge_ids")),
                },
            )
        )
    return result


def _prompt_previews(agent_runs: Iterable[AgentRunLog]) -> list[TracePromptPreview]:
    previews = []
    for index, run in enumerate(agent_runs, start=1):
        summary = run.input_summary or "Prompt input is folded; raw prompt is not exposed."
        previews.append(
            TracePromptPreview(
                preview_id=f"prompt_preview_{index:03d}",
                run_id=run.run_id,
                agent_name=run.agent_name,
                title=f"{run.agent_name.value} folded prompt preview",
                content_summary=_shorten(summary),
                folded=True,
                redacted=True,
            )
        )
    return previews


def _trace_metadata(state: Mapping[str, Any] | None, workflow_status: str) -> JsonObject:
    if state is None:
        return {
            "source": "task_record",
            "workflow_status": workflow_status,
            "counts": {
                "agent_runs": 0,
                "tool_calls": 0,
                "token_usage": 0,
                "qa_reviews": 0,
                "diffs": 0,
            },
        }

    metadata = state.get("metadata", {})
    workflow = metadata.get("workflow", {}) if isinstance(metadata, Mapping) else {}
    return {
        "source": "langgraph_workflow",
        "workflow": dict(workflow) if isinstance(workflow, Mapping) else {},
        "workflow_status": workflow_status,
        "counts": {
            "agent_runs": len(_list_items(state.get("run_logs"))),
            "tool_calls": len(_list_items(state.get("tool_call_logs"))),
            "token_usage": len(_list_items(state.get("token_usage_logs"))),
            "qa_reviews": len(_list_items(state.get("review_tasks"))),
            "diffs": len(_trace_diffs(state)),
        },
    }


def _redacted_trace(trace: TraceData) -> TraceData:
    return TraceData.model_validate(_redact_trace_value(trace.model_dump(mode="json")))


def _redact_trace_value(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        return "[REDACTED]"
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_sensitive_trace_key(key_text):
                redacted[key_text] = "[REDACTED]"
            else:
                redacted[key_text] = _redact_trace_value(item, depth + 1)
        return redacted
    if isinstance(value, list):
        return [_redact_trace_value(item, depth + 1) for item in value]
    if isinstance(value, tuple):
        return [_redact_trace_value(item, depth + 1) for item in value]
    if isinstance(value, str):
        redacted = value
        for pattern in _SENSITIVE_VALUE_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted
    return value


def _is_sensitive_trace_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in _SENSITIVE_KEY_NAMES or normalized.endswith("_api_key")


def _model_list[T](
    state: Mapping[str, Any] | None,
    field: str,
    model_type: type[T],
) -> list[T]:
    if state is None:
        return []
    return [model_type.model_validate(item) for item in _mapping_items(state.get(field))]


def _workflow_metadata(state: Mapping[str, Any] | None) -> JsonObject:
    if state is None:
        return {}
    metadata = state.get("metadata", {})
    if not isinstance(metadata, Mapping):
        return {}
    workflow = metadata.get("workflow", {})
    return dict(workflow) if isinstance(workflow, Mapping) else {}


def _state_task_status(task: AnalysisTask, state: Mapping[str, Any] | None) -> str:
    if state is None:
        return task.status.value
    task_payload = state.get("task", {})
    if isinstance(task_payload, Mapping) and isinstance(task_payload.get("status"), str):
        return str(task_payload["status"])
    return task.status.value


def _mapping_items(value: Any) -> list[Mapping[str, Any]]:
    return [item for item in _list_items(value) if isinstance(item, Mapping)]


def _list_items(value: Any) -> list[Any]:
    if isinstance(value, list | tuple):
        return list(value)
    return []


def _json_object(value: Any) -> JsonObject:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: Any) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _shorten(value: str) -> str:
    compact = " ".join(value.split())
    if len(compact) <= MAX_PROMPT_SUMMARY_CHARS:
        return compact
    return compact[: MAX_PROMPT_SUMMARY_CHARS - 3].rstrip() + "..."


def _trace_artifact_id(task_id: str) -> str:
    return f"trace_{task_id}"
