from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime

from app.graph import (
    TaskGraphState,
    append_agent_message,
    append_review_task,
    append_run_log,
)
from app.schemas import (
    AgentMessage,
    AgentMessageStatus,
    AgentMessageType,
    AgentName,
    AgentRunLog,
    Claim,
    CompetitionEdge,
    Evidence,
    ReviewTask,
    RunStatus,
)
from app.schemas.common import JsonObject
from app.services import run_qa_rules

PASSED = "passed"
REQUIRES_REVISION = "requires_revision"
ALLOWED_REVISION_TARGETS = (AgentName.COLLECTION, AgentName.ANALYSIS, AgentName.WRITER)
REVISION_TARGET_PRIORITY = (AgentName.COLLECTION, AgentName.ANALYSIS, AgentName.WRITER)


def qa_agent_node(
    state: TaskGraphState,
    *,
    now: datetime | None = None,
) -> TaskGraphState:
    run_started_at = now or datetime.now(UTC)
    task_id = str(state["task"]["task_id"])
    run_id = _next_qa_run_id(state, task_id)
    claims = [Claim.model_validate(item) for item in state["claims"]]
    evidences = [Evidence.model_validate(item) for item in state["evidences"]]
    competition_edges = [
        CompetitionEdge.model_validate(item) for item in state["competition_edges"]
    ]

    try:
        review_tasks = run_qa_rules(
            task_id=task_id,
            claims=claims,
            evidences=evidences,
            competition_edges=competition_edges,
            now=run_started_at,
        )
        for review_task in review_tasks:
            append_review_task(state, review_task)

        revision_messages = _append_revision_messages(
            state=state,
            task_id=task_id,
            review_tasks=review_tasks,
            created_at=run_started_at,
        )
        qa_status = REQUIRES_REVISION if review_tasks else PASSED
        primary_target = _primary_revision_target(review_tasks)

        state["metadata"]["qa_agent"] = {
            "qa_status": qa_status,
            "passed": not review_tasks,
            "review_task_count": len(review_tasks),
            "revision_target": primary_target.value if primary_target else None,
            "revision_targets": [
                target.value for target in _ordered_revision_targets(review_tasks)
            ],
            "review_task_ids": [task.review_task_id for task in review_tasks],
            "revision_message_ids": [message.message_id for message in revision_messages],
            "issue_counts": _issue_counts(review_tasks),
            "severity_counts": _severity_counts(review_tasks),
        }
        append_run_log(
            state,
            AgentRunLog(
                run_id=run_id,
                task_id=task_id,
                agent_name=AgentName.QA,
                status=RunStatus.REQUIRES_REVISION if review_tasks else RunStatus.SUCCEEDED,
                started_at=run_started_at,
                ended_at=run_started_at,
                input_summary=(
                    f"Review {len(claims)} claims, {len(evidences)} evidence records "
                    f"and {len(competition_edges)} competition edges."
                ),
                output_summary=_output_summary(review_tasks),
                error_message=None,
            ),
        )
        return state
    except Exception as exc:
        append_run_log(
            state,
            AgentRunLog(
                run_id=run_id,
                task_id=task_id,
                agent_name=AgentName.QA,
                status=RunStatus.FAILED,
                started_at=run_started_at,
                ended_at=run_started_at,
                input_summary=(
                    f"Review {len(claims)} claims, {len(evidences)} evidence records "
                    f"and {len(competition_edges)} competition edges."
                ),
                output_summary=None,
                error_message=str(exc),
            ),
        )
        raise


def _append_revision_messages(
    *,
    state: TaskGraphState,
    task_id: str,
    review_tasks: Sequence[ReviewTask],
    created_at: datetime,
) -> list[AgentMessage]:
    messages = []
    for target_agent in _ordered_revision_targets(review_tasks):
        target_tasks = _review_tasks_for_target(review_tasks, target_agent)
        message = _revision_request_message(
            task_id=task_id,
            target_agent=target_agent,
            review_tasks=target_tasks,
            created_at=created_at,
        )
        append_agent_message(state, message)
        messages.append(message)
    return messages


def _revision_request_message(
    *,
    task_id: str,
    target_agent: AgentName,
    review_tasks: Sequence[ReviewTask],
    created_at: datetime,
) -> AgentMessage:
    return AgentMessage(
        message_id=f"msg_{task_id}_qa_revision_{target_agent.value}",
        task_id=task_id,
        from_agent=AgentName.QA,
        to_agent=target_agent,
        message_type=AgentMessageType.REVISION_REQUEST,
        artifact_type="qa_review",
        payload={
            "qa_status": REQUIRES_REVISION,
            "target_agent": target_agent.value,
            "review_task_ids": [task.review_task_id for task in review_tasks],
            "issue_codes": _dedupe(task.issue_code for task in review_tasks),
            "severity_counts": _severity_counts(review_tasks),
            "required_actions": _dedupe(task.required_action for task in review_tasks),
            "targets": [_review_task_payload(task) for task in review_tasks],
        },
        evidence_ids=_dedupe(
            evidence_id
            for review_task in review_tasks
            for evidence_id in review_task.evidence_ids
        ),
        status=AgentMessageStatus.REQUIRES_REVISION,
        created_at=created_at,
    )


def _review_task_payload(review_task: ReviewTask) -> JsonObject:
    return {
        "review_task_id": review_task.review_task_id,
        "check_name": review_task.check_name,
        "issue_code": review_task.issue_code,
        "severity": review_task.severity.value,
        "target_type": review_task.target_type.value,
        "target_id": review_task.target_id,
        "message": review_task.message,
        "required_action": review_task.required_action,
        "related_claim_ids": review_task.related_claim_ids,
        "evidence_ids": review_task.evidence_ids,
    }


def _review_tasks_for_target(
    review_tasks: Sequence[ReviewTask],
    target_agent: AgentName,
) -> list[ReviewTask]:
    return [task for task in review_tasks if _safe_target_agent(task) == target_agent]


def _ordered_revision_targets(review_tasks: Sequence[ReviewTask]) -> list[AgentName]:
    targets = {_safe_target_agent(task) for task in review_tasks}
    return [target for target in REVISION_TARGET_PRIORITY if target in targets]


def _primary_revision_target(review_tasks: Sequence[ReviewTask]) -> AgentName | None:
    targets = _ordered_revision_targets(review_tasks)
    return targets[0] if targets else None


def _safe_target_agent(review_task: ReviewTask) -> AgentName:
    if review_task.target_agent in ALLOWED_REVISION_TARGETS:
        return review_task.target_agent
    return AgentName.ANALYSIS


def _issue_counts(review_tasks: Sequence[ReviewTask]) -> JsonObject:
    counts: dict[str, int] = defaultdict(int)
    for review_task in review_tasks:
        counts[review_task.issue_code] += 1
    return dict(sorted(counts.items()))


def _severity_counts(review_tasks: Sequence[ReviewTask]) -> JsonObject:
    counts: dict[str, int] = defaultdict(int)
    for review_task in review_tasks:
        counts[review_task.severity.value] += 1
    return dict(sorted(counts.items()))


def _output_summary(review_tasks: Sequence[ReviewTask]) -> str:
    if not review_tasks:
        return "QA passed with no review tasks."
    targets = ", ".join(target.value for target in _ordered_revision_targets(review_tasks))
    return f"QA found {len(review_tasks)} review tasks; revision targets: {targets}."


def _next_qa_run_id(state: TaskGraphState, task_id: str) -> str:
    qa_run_count = sum(
        1 for run_log in state["run_logs"] if run_log.get("agent_name") == AgentName.QA.value
    )
    if qa_run_count == 0:
        return f"run_{task_id}_qa"
    return f"run_{task_id}_qa_{qa_run_count + 1:03d}"


def _dedupe(items: Iterable[str]) -> list[str]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped
