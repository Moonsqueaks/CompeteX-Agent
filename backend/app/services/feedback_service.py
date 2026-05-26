from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AnalysisTask,
    FeedbackAction,
    FeedbackTargetType,
    HumanFeedback,
    HumanFeedbackCreateRequest,
    HumanFeedbackCreateResponse,
    TaskStatus,
)
from app.schemas.common import JsonObject
from app.storage import ArtifactRepository, HumanFeedbackRepository, TaskRepository

HUMAN_FEEDBACK_EFFECT_ARTIFACT_TYPE = "human_feedback_effect"

WorkflowFactory = Callable[[], Any]

_REVIEWABLE_STATUSES = {TaskStatus.COMPLETED, TaskStatus.HUMAN_REVIEWING}

_PROFILE_FIELD_ALLOWLIST = {
    FeedbackTargetType.PRODUCT: {
        "field": "product_id",
        "state_field": "products",
        "allowed_fields": {"name", "brand", "shop_name", "product_url", "tags"},
    },
    FeedbackTargetType.FEATURE_TREE: {
        "field": "feature_tree_id",
        "state_field": "feature_trees",
        "allowed_fields": {
            "cleaning_capability",
            "odor_control",
            "safety_features",
            "smart_features",
            "maintenance_cost",
        },
    },
    FeedbackTargetType.PRICING_MODEL: {
        "field": "pricing_model_id",
        "state_field": "pricing_models",
        "allowed_fields": {"price_band", "promotions", "bundle_description"},
    },
    FeedbackTargetType.USER_PERSONA: {
        "field": "persona_id",
        "state_field": "user_personas",
        "allowed_fields": {"personas", "pain_points", "scenarios", "decision_factors"},
    },
}

_CLAIM_STATUS_BY_ACTION = {
    FeedbackAction.MARK_ACCEPTED: "accepted",
    FeedbackAction.MARK_REJECTED: "rejected",
    FeedbackAction.MARK_NEEDS_REVIEW: "needs_review",
}

_SLICE_FIELDS = {"price_band", "persona", "scenario"}


class FeedbackServiceError(Exception):
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


class FeedbackService:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        feedback_repository: HumanFeedbackRepository,
        artifact_repository: ArtifactRepository,
        workflow_factory: WorkflowFactory = build_analysis_workflow,
    ) -> None:
        self.task_repository = task_repository
        self.feedback_repository = feedback_repository
        self.artifact_repository = artifact_repository
        self.workflow_factory = workflow_factory

    def submit_feedback(
        self,
        task_id: str,
        payload: HumanFeedbackCreateRequest,
    ) -> HumanFeedbackCreateResponse:
        task = self._get_reviewable_task(task_id)
        state = self._build_context_state(task)
        before_value, after_value, affected_ids = _feedback_values(state, payload)
        created_at = datetime.now(UTC)
        feedback = HumanFeedback(
            feedback_id=f"hf_{task_id}_{uuid4().hex[:12]}",
            task_id=task_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
            action=payload.action,
            before_value=before_value,
            after_value=after_value,
            reason=payload.reason.strip(),
            created_at=created_at,
        )
        saved_feedback = self.feedback_repository.save(feedback)
        self._save_feedback_effect(
            task=task,
            feedback=saved_feedback,
            before_value=before_value,
            after_value=after_value,
            affected_ids=affected_ids,
            created_at=created_at,
        )
        updated_task = self._mark_task_for_reanalysis(task, saved_feedback, created_at)
        return HumanFeedbackCreateResponse(
            feedback=saved_feedback,
            task_status=updated_task.status,
            recompute_status="marked_for_reanalysis",
            affected_artifact_ids=affected_ids,
            metadata={
                "requires_analysis_recompute": True,
                "recompute_reason": "human_feedback_submitted",
            },
        )

    def _get_reviewable_task(self, task_id: str) -> AnalysisTask:
        task = self.task_repository.get(task_id)
        if task is None:
            raise FeedbackServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task_id},
            )
        if task.status not in _REVIEWABLE_STATUSES:
            raise FeedbackServiceError(
                "FEEDBACK_NOT_READY",
                "Human feedback is only available after the task has completed.",
                status_code=409,
                details={"task_id": task_id, "status": task.status.value},
            )
        return task

    def _build_context_state(self, task: AnalysisTask) -> Mapping[str, Any]:
        try:
            workflow = self.workflow_factory()
            state = create_initial_state(task)
            return workflow.invoke(state)
        except Exception as exc:
            raise FeedbackServiceError(
                "FEEDBACK_CONTEXT_FAILED",
                "Could not build feedback context from the current analysis artifacts.",
                status_code=500,
                details={"task_id": task.task_id, "reason": exc.__class__.__name__},
            ) from exc

    def _save_feedback_effect(
        self,
        *,
        task: AnalysisTask,
        feedback: HumanFeedback,
        before_value: JsonObject,
        after_value: JsonObject,
        affected_ids: list[str],
        created_at: datetime,
    ) -> None:
        effect = {
            "task_id": task.task_id,
            "effect_id": f"effect_{feedback.feedback_id}",
            "feedback_id": feedback.feedback_id,
            "recompute_status": "marked_for_reanalysis",
            "affected_artifact_ids": affected_ids,
            "before_value": before_value,
            "after_value": after_value,
            "created_at": created_at.isoformat(),
        }
        self.artifact_repository.save(
            HUMAN_FEEDBACK_EFFECT_ARTIFACT_TYPE,
            effect["effect_id"],
            effect,
        )

    def _mark_task_for_reanalysis(
        self,
        task: AnalysisTask,
        feedback: HumanFeedback,
        created_at: datetime,
    ) -> AnalysisTask:
        metadata = dict(task.metadata)
        history = metadata.get("human_feedback_reanalysis", [])
        if not isinstance(history, list):
            history = []
        history.append(
            {
                "feedback_id": feedback.feedback_id,
                "target_type": feedback.target_type.value,
                "target_id": feedback.target_id,
                "action": feedback.action.value,
                "status": "marked_for_reanalysis",
                "created_at": created_at.isoformat(),
            }
        )
        metadata["human_feedback_reanalysis"] = history
        metadata["requires_analysis_recompute"] = True
        self.task_repository.update_metadata(task.task_id, metadata, updated_at=created_at)
        updated = self.task_repository.update_status(
            task.task_id,
            TaskStatus.HUMAN_REVIEWING,
            updated_at=created_at,
        )
        if updated is None:
            raise FeedbackServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task.task_id},
            )
        return updated


def _feedback_values(
    state: Mapping[str, Any],
    payload: HumanFeedbackCreateRequest,
) -> tuple[JsonObject, JsonObject, list[str]]:
    if payload.target_type in _PROFILE_FIELD_ALLOWLIST:
        return _profile_update_values(state, payload)
    if payload.target_type == FeedbackTargetType.CLAIM:
        return _claim_status_values(state, payload)
    if payload.target_type == FeedbackTargetType.EVIDENCE:
        return _evidence_note_values(state, payload)
    if payload.target_type == FeedbackTargetType.COMPETITION_EDGE:
        return _competition_edge_values(state, payload)
    if payload.target_type == FeedbackTargetType.SLICE:
        return _slice_values(state, payload)
    raise _not_allowed(payload, "Unsupported feedback target type.")


def _profile_update_values(
    state: Mapping[str, Any],
    payload: HumanFeedbackCreateRequest,
) -> tuple[JsonObject, JsonObject, list[str]]:
    if payload.action != FeedbackAction.UPDATE_FIELD:
        raise _not_allowed(payload, "Product profile targets only support update_field.")
    config = _PROFILE_FIELD_ALLOWLIST[payload.target_type]
    artifact = _find_artifact(
        state,
        state_field=str(config["state_field"]),
        id_field=str(config["field"]),
        target_id=payload.target_id,
    )
    field_name = _required_string(payload.after_value, "field")
    if field_name not in config["allowed_fields"]:
        raise _invalid_payload(
            payload,
            f"Field '{field_name}' is not allowed for {payload.target_type.value}.",
        )
    if "value" not in payload.after_value:
        raise _invalid_payload(payload, "after_value.value is required.")
    return (
        {"field": field_name, "value": artifact.get(field_name)},
        {"field": field_name, "value": payload.after_value["value"]},
        [payload.target_id],
    )


def _claim_status_values(
    state: Mapping[str, Any],
    payload: HumanFeedbackCreateRequest,
) -> tuple[JsonObject, JsonObject, list[str]]:
    if payload.action not in _CLAIM_STATUS_BY_ACTION:
        raise _not_allowed(payload, "Claim feedback only supports claim status actions.")
    claim = _find_artifact(
        state,
        state_field="claims",
        id_field="claim_id",
        target_id=payload.target_id,
    )
    new_status = _CLAIM_STATUS_BY_ACTION[payload.action]
    return (
        {"status": claim.get("status")},
        {"status": new_status},
        [payload.target_id, *_string_items(claim.get("evidence_ids"))],
    )


def _evidence_note_values(
    state: Mapping[str, Any],
    payload: HumanFeedbackCreateRequest,
) -> tuple[JsonObject, JsonObject, list[str]]:
    if payload.action != FeedbackAction.ADD_NOTE:
        raise _not_allowed(payload, "Evidence feedback only supports add_note.")
    evidence = _find_artifact(
        state,
        state_field="evidences",
        id_field="evidence_id",
        target_id=payload.target_id,
    )
    note = _required_string(payload.after_value, "note")
    metadata = evidence.get("metadata", {})
    before_note = metadata.get("human_note") if isinstance(metadata, Mapping) else None
    return (
        {"human_note": before_note},
        {"human_note": note},
        [payload.target_id],
    )


def _competition_edge_values(
    state: Mapping[str, Any],
    payload: HumanFeedbackCreateRequest,
) -> tuple[JsonObject, JsonObject, list[str]]:
    if payload.action != FeedbackAction.REMOVE_COMPETITOR:
        raise _not_allowed(
            payload,
            "Competition edge feedback only supports remove_competitor in this API step.",
        )
    edge = _find_artifact(
        state,
        state_field="competition_edges",
        id_field="edge_id",
        target_id=payload.target_id,
    )
    return (
        {
            "edge_id": edge.get("edge_id"),
            "competitor_product_id": edge.get("competitor_product_id"),
            "human_adjusted": edge.get("human_adjusted"),
            "removed": False,
        },
        {
            "edge_id": edge.get("edge_id"),
            "competitor_product_id": edge.get("competitor_product_id"),
            "human_adjusted": True,
            "removed": True,
        },
        [payload.target_id, str(edge.get("competitor_product_id"))],
    )


def _slice_values(
    state: Mapping[str, Any],
    payload: HumanFeedbackCreateRequest,
) -> tuple[JsonObject, JsonObject, list[str]]:
    if payload.action != FeedbackAction.UPDATE_FIELD:
        raise _not_allowed(payload, "Slice feedback only supports update_field.")
    field_name = _required_string(payload.after_value, "field")
    if field_name not in _SLICE_FIELDS:
        raise _invalid_payload(payload, f"Field '{field_name}' is not allowed for slice.")
    if "value" not in payload.after_value or not isinstance(payload.after_value["value"], str):
        raise _invalid_payload(payload, "after_value.value must be a string.")
    matching_slice = _matching_slice(state, payload.target_id)
    return (
        {
            "slice_id": payload.target_id,
            "field": field_name,
            "value": matching_slice.get(field_name),
        },
        {
            "slice_id": payload.target_id,
            "field": field_name,
            "value": payload.after_value["value"],
        },
        [payload.target_id],
    )


def _matching_slice(state: Mapping[str, Any], slice_id: str) -> JsonObject:
    for edge in _mapping_items(state.get("competition_edges")):
        edge_slice = edge.get("slice")
        if not isinstance(edge_slice, Mapping):
            continue
        candidate = "|".join(str(edge_slice.get(field) or "") for field in sorted(_SLICE_FIELDS))
        if slice_id in {candidate, str(edge_slice.get("price_band")), "default"}:
            return dict(edge_slice)
    return {}


def _find_artifact(
    state: Mapping[str, Any],
    *,
    state_field: str,
    id_field: str,
    target_id: str,
) -> Mapping[str, Any]:
    for item in _mapping_items(state.get(state_field)):
        if item.get(id_field) == target_id:
            return item
    raise FeedbackServiceError(
        "FEEDBACK_TARGET_NOT_FOUND",
        "Feedback target not found",
        status_code=404,
        details={"target_id": target_id, "target_field": id_field},
    )


def _required_string(value: JsonObject, key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise FeedbackServiceError(
            "FEEDBACK_INVALID_PAYLOAD",
            f"after_value.{key} must be a non-empty string.",
            status_code=400,
            details={"field": key},
        )
    return item.strip()


def _not_allowed(payload: HumanFeedbackCreateRequest, reason: str) -> FeedbackServiceError:
    return FeedbackServiceError(
        "FEEDBACK_NOT_ALLOWED",
        reason,
        status_code=400,
        details={
            "target_type": payload.target_type.value,
            "action": payload.action.value,
        },
    )


def _invalid_payload(payload: HumanFeedbackCreateRequest, reason: str) -> FeedbackServiceError:
    return FeedbackServiceError(
        "FEEDBACK_INVALID_PAYLOAD",
        reason,
        status_code=400,
        details={
            "target_type": payload.target_type.value,
            "action": payload.action.value,
        },
    )


def _mapping_items(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_items(value: Any) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]
