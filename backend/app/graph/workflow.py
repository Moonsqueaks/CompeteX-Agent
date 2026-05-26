from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal

from app.graph.state import TaskGraphState, append_agent_message, append_run_log
from app.schemas import (
    AgentMessage,
    AgentMessageStatus,
    AgentMessageType,
    AgentName,
    AgentRunLog,
    RunStatus,
    TaskStatus,
)
from app.schemas.common import JsonObject

COLLECTION_NODE = "collection_agent"
ANALYSIS_NODE = "analysis_agent"
QA_NODE = "qa_agent"
WRITER_NODE = "writer_agent"

WorkflowRoute = Literal[
    "collection_agent",
    "analysis_agent",
    "writer_agent",
    "failed",
]
WorkflowNode = Callable[[TaskGraphState], TaskGraphState]

DEFAULT_MAX_REVISION_ROUNDS = 3


def build_analysis_workflow(
    *,
    max_revision_rounds: int = DEFAULT_MAX_REVISION_ROUNDS,
    collection_node: WorkflowNode | None = None,
    analysis_node: WorkflowNode | None = None,
    qa_node: WorkflowNode | None = None,
    writer_node: WorkflowNode | None = None,
):
    from langgraph.graph import END, StateGraph

    if collection_node is None or analysis_node is None or qa_node is None or writer_node is None:
        from app.agents import (
            analysis_agent_node,
            collection_agent_node,
            qa_agent_node,
            writer_agent_node,
        )

        collection_node = collection_node or collection_agent_node
        analysis_node = analysis_node or analysis_agent_node
        qa_node = qa_node or qa_agent_node
        writer_node = writer_node or writer_agent_node

    workflow = StateGraph(TaskGraphState)
    workflow.add_node(
        COLLECTION_NODE,
        _collection_workflow_node(collection_node),
    )
    workflow.add_node(
        ANALYSIS_NODE,
        _status_wrapped_node(
            node=analysis_node,
            status=TaskStatus.ANALYZING,
            current_node=ANALYSIS_NODE,
        ),
    )
    workflow.add_node(
        QA_NODE,
        _qa_workflow_node(qa_node=qa_node, max_revision_rounds=max_revision_rounds),
    )
    workflow.add_node(WRITER_NODE, _writer_workflow_node(writer_node))

    workflow.set_entry_point(COLLECTION_NODE)
    workflow.add_edge(COLLECTION_NODE, ANALYSIS_NODE)
    workflow.add_edge(ANALYSIS_NODE, QA_NODE)
    workflow.add_conditional_edges(
        QA_NODE,
        route_after_qa,
        {
            COLLECTION_NODE: COLLECTION_NODE,
            ANALYSIS_NODE: ANALYSIS_NODE,
            WRITER_NODE: WRITER_NODE,
            "failed": END,
        },
    )
    workflow.add_edge(WRITER_NODE, END)
    return workflow.compile()


def route_after_qa(state: TaskGraphState) -> WorkflowRoute:
    workflow_metadata = _workflow_metadata(state)
    if (
        workflow_metadata.get("status") == "failed"
        or workflow_metadata.get("next_node") == "failed"
    ):
        return "failed"

    qa_metadata = state["metadata"].get("qa_agent", {})
    if not isinstance(qa_metadata, dict):
        return "failed"
    if qa_metadata.get("qa_status") == "passed":
        return WRITER_NODE

    revision_target = qa_metadata.get("revision_target")
    if revision_target == AgentName.COLLECTION.value:
        return COLLECTION_NODE
    if revision_target == AgentName.ANALYSIS.value:
        return ANALYSIS_NODE
    return "failed"


def writer_checkpoint_node(state: TaskGraphState) -> TaskGraphState:
    started_at = datetime.now(UTC)
    task_id = str(state["task"]["task_id"])
    _set_task_status(state, TaskStatus.WRITING)
    append_run_log(
        state,
        AgentRunLog(
            run_id=_next_writer_run_id(state, task_id),
            task_id=task_id,
            agent_name=AgentName.WRITER,
            status=RunStatus.SKIPPED,
            started_at=started_at,
            ended_at=started_at,
            input_summary="Workflow reached Writer after QA passed.",
            output_summary="Writer Agent implementation is deferred to step 19.",
            error_message=None,
        ),
    )
    _set_task_status(state, TaskStatus.COMPLETED)
    workflow_metadata = _workflow_metadata(state)
    workflow_metadata["status"] = "completed"
    workflow_metadata["current_node"] = WRITER_NODE
    workflow_metadata["writer_status"] = "deferred_until_step_19"
    workflow_metadata["next_node"] = None
    state["metadata"]["workflow"] = workflow_metadata
    return state


def _writer_workflow_node(node: WorkflowNode) -> WorkflowNode:
    def wrapped(state: TaskGraphState) -> TaskGraphState:
        _set_task_status(state, TaskStatus.WRITING)
        _set_workflow_current_node(state, WRITER_NODE)
        result = node(state)
        workflow_metadata = _workflow_metadata(result)
        workflow_metadata["status"] = "completed"
        workflow_metadata["current_node"] = WRITER_NODE
        workflow_metadata["writer_status"] = "succeeded"
        workflow_metadata["next_node"] = None
        result["metadata"]["workflow"] = workflow_metadata
        return result

    return wrapped


def _collection_workflow_node(node: WorkflowNode) -> WorkflowNode:
    def wrapped(state: TaskGraphState) -> TaskGraphState:
        _set_task_status(state, TaskStatus.COLLECTING)
        _set_workflow_current_node(state, COLLECTION_NODE)
        result = node(state)
        _append_analysis_revision_after_collection_repair(result)
        return result

    return wrapped


def _status_wrapped_node(
    *,
    node: WorkflowNode,
    status: TaskStatus,
    current_node: str,
) -> WorkflowNode:
    def wrapped(state: TaskGraphState) -> TaskGraphState:
        _set_task_status(state, status)
        _set_workflow_current_node(state, current_node)
        return node(state)

    return wrapped


def _qa_workflow_node(
    *,
    qa_node: WorkflowNode,
    max_revision_rounds: int,
) -> WorkflowNode:
    def wrapped(state: TaskGraphState) -> TaskGraphState:
        _set_task_status(state, TaskStatus.REVIEWING)
        _set_workflow_current_node(state, QA_NODE)
        result = qa_node(state)
        workflow_metadata = _workflow_metadata(result)
        qa_metadata = result["metadata"].get("qa_agent", {})
        if not isinstance(qa_metadata, dict):
            return _mark_workflow_failed(
                result,
                reason="QA metadata is missing or invalid.",
            )

        if qa_metadata.get("qa_status") == "passed":
            workflow_metadata["next_node"] = WRITER_NODE
            workflow_metadata["status"] = "qa_passed"
            result["metadata"]["workflow"] = workflow_metadata
            return result

        revision_rounds = int(workflow_metadata.get("revision_rounds", 0)) + 1
        workflow_metadata["revision_rounds"] = revision_rounds
        workflow_metadata["max_revision_rounds"] = max_revision_rounds
        if revision_rounds > max_revision_rounds:
            result["metadata"]["workflow"] = workflow_metadata
            return _mark_workflow_failed(
                result,
                reason="Maximum QA revision rounds exceeded.",
            )

        next_node = route_after_qa(result)
        workflow_metadata["next_node"] = next_node
        workflow_metadata["status"] = "requires_revision"
        result["metadata"]["workflow"] = workflow_metadata
        return result

    return wrapped


def _append_analysis_revision_after_collection_repair(state: TaskGraphState) -> None:
    repair_summary = state["metadata"].get("collection_agent_repair")
    if not isinstance(repair_summary, dict):
        return
    run_id = repair_summary.get("run_id")
    workflow_metadata = _workflow_metadata(state)
    consumed_repair_run_ids = set(_string_items(workflow_metadata.get("analysis_repair_run_ids")))
    if not isinstance(run_id, str) or run_id in consumed_repair_run_ids:
        return

    target_evidence_ids = _string_items(repair_summary.get("target_evidence_ids"))
    new_evidence_ids = _string_items(repair_summary.get("new_evidence_ids"))
    claim_ids = _claim_ids_for_evidence_ids(state, target_evidence_ids)
    edge_ids = _edge_ids_for_claim_ids(state, claim_ids)
    if not claim_ids and not edge_ids:
        return

    message_index = len(
        [
            message
            for message in state["agent_messages"]
            if message.get("to_agent") == AgentName.ANALYSIS.value
        ]
    ) + 1
    append_agent_message(
        state,
        AgentMessage(
            message_id=(
                f"msg_{state['task']['task_id']}_qa_revision_analysis_after_collection_"
                f"{message_index:03d}"
            ),
            task_id=str(state["task"]["task_id"]),
            from_agent=AgentName.QA,
            to_agent=AgentName.ANALYSIS,
            message_type=AgentMessageType.REVISION_REQUEST,
            artifact_type="collection_repair_recompute",
            payload={
                "qa_status": "requires_revision",
                "target_agent": AgentName.ANALYSIS.value,
                "issue_codes": ["COLLECTION_REPAIR_REQUIRES_ANALYSIS_RECOMPUTE"],
                "collection_repair_run_id": run_id,
                "claim_ids": claim_ids,
                "competition_edge_ids": edge_ids,
                "targets": [
                    *_target_payloads("claim", claim_ids, claim_ids, new_evidence_ids),
                    *_target_payloads("competition_edge", edge_ids, claim_ids, new_evidence_ids),
                ],
            },
            evidence_ids=new_evidence_ids,
            status=AgentMessageStatus.REQUIRES_REVISION,
            created_at=datetime.now(UTC),
        ),
    )
    consumed_repair_run_ids.add(run_id)
    workflow_metadata["analysis_repair_run_ids"] = sorted(consumed_repair_run_ids)
    state["metadata"]["workflow"] = workflow_metadata


def _target_payloads(
    target_type: str,
    target_ids: list[str],
    claim_ids: list[str],
    evidence_ids: list[str],
) -> list[JsonObject]:
    return [
        {
            "target_type": target_type,
            "target_id": target_id,
            "issue_code": "COLLECTION_REPAIR_REQUIRES_ANALYSIS_RECOMPUTE",
            "related_claim_ids": claim_ids,
            "evidence_ids": evidence_ids,
        }
        for target_id in target_ids
    ]


def _mark_workflow_failed(state: TaskGraphState, *, reason: str) -> TaskGraphState:
    _set_task_status(state, TaskStatus.FAILED)
    workflow_metadata = _workflow_metadata(state)
    workflow_metadata["status"] = "failed"
    workflow_metadata["failure_reason"] = reason
    workflow_metadata["next_node"] = "failed"
    state["metadata"]["workflow"] = workflow_metadata
    return state


def _claim_ids_for_evidence_ids(
    state: TaskGraphState,
    evidence_ids: list[str],
) -> list[str]:
    return _dedupe(
        [
            claim["claim_id"]
            for claim in state["claims"]
            if set(_string_items(claim.get("evidence_ids"))).intersection(evidence_ids)
            and isinstance(claim.get("claim_id"), str)
        ]
    )


def _edge_ids_for_claim_ids(
    state: TaskGraphState,
    claim_ids: list[str],
) -> list[str]:
    return _dedupe(
        [
            edge["edge_id"]
            for edge in state["competition_edges"]
            if set(_string_items(edge.get("claim_ids"))).intersection(claim_ids)
            and isinstance(edge.get("edge_id"), str)
        ]
    )


def _set_workflow_current_node(state: TaskGraphState, current_node: str) -> None:
    workflow_metadata = _workflow_metadata(state)
    workflow_metadata["current_node"] = current_node
    workflow_metadata.setdefault("revision_rounds", 0)
    state["metadata"]["workflow"] = workflow_metadata


def _set_task_status(state: TaskGraphState, status: TaskStatus) -> None:
    state["task"]["status"] = status.value
    state["task"]["updated_at"] = datetime.now(UTC).isoformat()


def _workflow_metadata(state: TaskGraphState) -> JsonObject:
    metadata = state["metadata"].get("workflow", {})
    return dict(metadata) if isinstance(metadata, dict) else {}


def _next_writer_run_id(state: TaskGraphState, task_id: str) -> str:
    writer_run_count = sum(
        1 for run_log in state["run_logs"] if run_log.get("agent_name") == AgentName.WRITER.value
    )
    return f"run_{task_id}_writer_{writer_run_count + 1:03d}"


def _string_items(value: Any) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _dedupe(items: list[str]) -> list[str]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped


__all__ = [
    "ANALYSIS_NODE",
    "COLLECTION_NODE",
    "DEFAULT_MAX_REVISION_ROUNDS",
    "QA_NODE",
    "WRITER_NODE",
    "build_analysis_workflow",
    "route_after_qa",
    "writer_checkpoint_node",
]
