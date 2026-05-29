from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AnalysisTask,
    BattlefieldSliceSelection,
    FeedbackAction,
    FeedbackTargetType,
    HumanFeedback,
    HumanFeedbackCreateRequest,
    HumanFeedbackCreateResponse,
    TaskStatus,
)
from app.schemas.common import JsonObject
from app.services.battlefield_service import (
    BATTLEFIELD_ARTIFACT_TYPE,
    _battlefield_artifact_id,
    _build_battlefield_data,
)
from app.services.profile_service import PRODUCT_PROFILE_ARTIFACT_TYPE, _build_product_profile
from app.services.trace_service import TRACE_ARTIFACT_TYPE, _build_trace_data, _trace_artifact_id
from app.storage import ArtifactRepository, HumanFeedbackRepository, TaskRepository

HUMAN_FEEDBACK_EFFECT_ARTIFACT_TYPE = "human_feedback_effect"
LOCAL_RECOMPUTE_STATUS = "applied_local_update"

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
        updated_state = _apply_feedback_to_state(
            state=state,
            payload=payload,
            feedback=feedback,
            before_value=before_value,
            after_value=after_value,
            affected_ids=affected_ids,
        )
        saved_feedback = self.feedback_repository.save(feedback)
        updated_task = self._mark_task_for_reanalysis(
            task,
            saved_feedback,
            created_at,
            recompute_status=LOCAL_RECOMPUTE_STATUS,
        )
        updated_state["task"] = updated_task.model_dump(mode="json")
        cached_artifact_ids = self._cache_feedback_outputs(
            task=updated_task,
            state=updated_state,
        )
        self._save_feedback_effect(
            task=updated_task,
            feedback=saved_feedback,
            before_value=before_value,
            after_value=after_value,
            affected_ids=affected_ids,
            cached_artifact_ids=cached_artifact_ids,
            recompute_status=LOCAL_RECOMPUTE_STATUS,
            created_at=created_at,
        )
        return HumanFeedbackCreateResponse(
            feedback=saved_feedback,
            task_status=updated_task.status,
            recompute_status=LOCAL_RECOMPUTE_STATUS,
            affected_artifact_ids=affected_ids,
            metadata={
                "requires_analysis_recompute": False,
                "local_update_applied": True,
                "recompute_reason": "human_feedback_submitted",
                "cached_artifact_ids": cached_artifact_ids,
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
        cached_artifact_ids: list[str],
        recompute_status: str,
        created_at: datetime,
    ) -> None:
        effect = {
            "task_id": task.task_id,
            "effect_id": f"effect_{feedback.feedback_id}",
            "feedback_id": feedback.feedback_id,
            "recompute_status": recompute_status,
            "affected_artifact_ids": affected_ids,
            "cached_artifact_ids": cached_artifact_ids,
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
        *,
        recompute_status: str,
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
                "status": recompute_status,
                "created_at": created_at.isoformat(),
            }
        )
        metadata["human_feedback_reanalysis"] = history
        metadata["requires_analysis_recompute"] = False
        metadata["human_feedback_local_update"] = {
            "feedback_id": feedback.feedback_id,
            "status": recompute_status,
            "updated_at": created_at.isoformat(),
        }
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

    def _cache_feedback_outputs(
        self,
        *,
        task: AnalysisTask,
        state: Mapping[str, Any],
    ) -> list[str]:
        try:
            profile = _build_product_profile(dict(state))
            self.artifact_repository.save(
                PRODUCT_PROFILE_ARTIFACT_TYPE,
                profile.profile_id,
                profile,
            )

            selected_slice = BattlefieldSliceSelection()
            battlefield_id = _battlefield_artifact_id(task.task_id, selected_slice)
            battlefield = _build_battlefield_data(dict(state), selected_slice, battlefield_id)
            self.artifact_repository.save(
                BATTLEFIELD_ARTIFACT_TYPE,
                battlefield.battlefield_id,
                battlefield,
            )

            trace = _build_trace_data(
                task=task,
                state=state,
                trace_view_id=_trace_artifact_id(task.task_id),
            )
            self.artifact_repository.save(TRACE_ARTIFACT_TYPE, trace.trace_view_id, trace)
        except Exception as exc:
            raise FeedbackServiceError(
                "FEEDBACK_RECOMPUTE_FAILED",
                "Could not apply human feedback to cached analysis artifacts.",
                status_code=500,
                details={"task_id": task.task_id, "reason": exc.__class__.__name__},
            ) from exc

        return [profile.profile_id, battlefield.battlefield_id, trace.trace_view_id]


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


def _apply_feedback_to_state(
    *,
    state: Mapping[str, Any],
    payload: HumanFeedbackCreateRequest,
    feedback: HumanFeedback,
    before_value: JsonObject,
    after_value: JsonObject,
    affected_ids: list[str],
) -> dict[str, Any]:
    updated_state = deepcopy(dict(state))

    if payload.target_type in _PROFILE_FIELD_ALLOWLIST:
        _apply_profile_field_update(updated_state, payload, after_value)
    elif payload.target_type == FeedbackTargetType.CLAIM:
        _apply_claim_status_update(updated_state, payload, after_value)
    elif payload.target_type == FeedbackTargetType.EVIDENCE:
        _apply_evidence_note(updated_state, payload, after_value)
    elif payload.target_type == FeedbackTargetType.COMPETITION_EDGE:
        _apply_competition_edge_update(updated_state, payload)
    elif payload.target_type == FeedbackTargetType.SLICE:
        _apply_slice_update(updated_state, payload, after_value)

    _append_feedback_record(updated_state, feedback)
    _append_feedback_metadata(
        updated_state,
        payload=payload,
        feedback=feedback,
        before_value=before_value,
        after_value=after_value,
        affected_ids=affected_ids,
    )
    return updated_state


def _apply_profile_field_update(
    state: dict[str, Any],
    payload: HumanFeedbackCreateRequest,
    after_value: JsonObject,
) -> None:
    config = _PROFILE_FIELD_ALLOWLIST[payload.target_type]
    artifact = _find_mutable_artifact(
        state,
        state_field=str(config["state_field"]),
        id_field=str(config["field"]),
        target_id=payload.target_id,
    )
    artifact[str(after_value["field"])] = after_value["value"]


def _apply_claim_status_update(
    state: dict[str, Any],
    payload: HumanFeedbackCreateRequest,
    after_value: JsonObject,
) -> None:
    claim = _find_mutable_artifact(
        state,
        state_field="claims",
        id_field="claim_id",
        target_id=payload.target_id,
    )
    new_status = str(after_value["status"])
    claim["status"] = new_status
    risk_flags = _string_items(claim.get("risk_flags"))
    if new_status == "accepted":
        risk_flags = [flag for flag in risk_flags if flag != "unreliable_data"]
    elif "unreliable_data" not in risk_flags:
        risk_flags.append("unreliable_data")
    claim["risk_flags"] = risk_flags


def _apply_evidence_note(
    state: dict[str, Any],
    payload: HumanFeedbackCreateRequest,
    after_value: JsonObject,
) -> None:
    evidence = _find_mutable_artifact(
        state,
        state_field="evidences",
        id_field="evidence_id",
        target_id=payload.target_id,
    )
    metadata = evidence.get("metadata", {})
    evidence["metadata"] = dict(metadata) if isinstance(metadata, Mapping) else {}
    evidence["metadata"]["human_note"] = after_value["human_note"]


def _apply_competition_edge_update(
    state: dict[str, Any],
    payload: HumanFeedbackCreateRequest,
) -> None:
    edge = _find_mutable_artifact(
        state,
        state_field="competition_edges",
        id_field="edge_id",
        target_id=payload.target_id,
    )
    edge["human_adjusted"] = True
    edge["edge_score"] = 0
    risk_flags = _string_items(edge.get("risk_flags"))
    if "unreliable_data" not in risk_flags:
        risk_flags.append("unreliable_data")
    edge["risk_flags"] = risk_flags


def _apply_slice_update(
    state: dict[str, Any],
    payload: HumanFeedbackCreateRequest,
    after_value: JsonObject,
) -> None:
    field_name = str(after_value["field"])
    for edge in _mutable_mapping_items(state.get("competition_edges")):
        edge_slice = edge.get("slice")
        if not isinstance(edge_slice, dict) or not _slice_matches(edge_slice, payload.target_id):
            continue
        edge_slice[field_name] = after_value["value"]
        edge["human_adjusted"] = True


def _append_feedback_record(state: dict[str, Any], feedback: HumanFeedback) -> None:
    human_feedback = state.get("human_feedback")
    if not isinstance(human_feedback, list):
        human_feedback = []
    human_feedback.append(feedback.model_dump(mode="json"))
    state["human_feedback"] = human_feedback


def _append_feedback_metadata(
    state: dict[str, Any],
    *,
    payload: HumanFeedbackCreateRequest,
    feedback: HumanFeedback,
    before_value: JsonObject,
    after_value: JsonObject,
    affected_ids: list[str],
) -> None:
    metadata = state.get("metadata")
    metadata = dict(metadata) if isinstance(metadata, Mapping) else {}
    history = metadata.get("human_feedback_local_updates")
    if not isinstance(history, list):
        history = []
    history.append(
        {
            "feedback_id": feedback.feedback_id,
            "target_type": payload.target_type.value,
            "target_id": payload.target_id,
            "action": payload.action.value,
            "status": LOCAL_RECOMPUTE_STATUS,
            "affected_artifact_ids": affected_ids,
        }
    )
    metadata["human_feedback_local_updates"] = history
    metadata["requires_analysis_recompute"] = False

    if payload.target_type == FeedbackTargetType.CLAIM:
        _append_analysis_claim_diff(metadata, payload, feedback, before_value, after_value)
    elif payload.target_type in {FeedbackTargetType.COMPETITION_EDGE, FeedbackTargetType.SLICE}:
        _append_analysis_edge_diff(metadata, payload, feedback, before_value, after_value)

    state["metadata"] = metadata


def _append_analysis_claim_diff(
    metadata: JsonObject,
    payload: HumanFeedbackCreateRequest,
    feedback: HumanFeedback,
    before_value: JsonObject,
    after_value: JsonObject,
) -> None:
    recompute = _recompute_metadata(metadata)
    claim_diffs = [dict(item) for item in _mapping_items(recompute.get("claim_diffs"))]
    claim_diffs.append(
        {
            "claim_id": payload.target_id,
            "status": LOCAL_RECOMPUTE_STATUS,
            "before": before_value,
            "after": after_value,
            "feedback_id": feedback.feedback_id,
        }
    )
    recompute["claim_diffs"] = claim_diffs
    recompute["target_claim_ids"] = _dedupe(
        [*_string_items(recompute.get("target_claim_ids")), payload.target_id]
    )
    metadata["analysis_agent_recompute"] = recompute


def _append_analysis_edge_diff(
    metadata: JsonObject,
    payload: HumanFeedbackCreateRequest,
    feedback: HumanFeedback,
    before_value: JsonObject,
    after_value: JsonObject,
) -> None:
    recompute = _recompute_metadata(metadata)
    edge_diffs = [dict(item) for item in _mapping_items(recompute.get("diffs"))]
    edge_diffs.append(
        {
            "edge_id": payload.target_id,
            "status": LOCAL_RECOMPUTE_STATUS,
            "before": before_value,
            "after": after_value,
            "feedback_id": feedback.feedback_id,
        }
    )
    recompute["diffs"] = edge_diffs
    recompute["target_edge_ids"] = _dedupe(
        [*_string_items(recompute.get("target_edge_ids")), payload.target_id]
    )
    metadata["analysis_agent_recompute"] = recompute


def _recompute_metadata(metadata: JsonObject) -> JsonObject:
    recompute = metadata.get("analysis_agent_recompute")
    result = dict(recompute) if isinstance(recompute, Mapping) else {}
    result["run_id"] = result.get("run_id") or "human_feedback_local_update"
    result["status"] = LOCAL_RECOMPUTE_STATUS
    return result


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
        if _slice_matches(edge_slice, slice_id):
            return dict(edge_slice)
    return {}


def _slice_matches(edge_slice: Mapping[str, Any], slice_id: str) -> bool:
    candidate = "|".join(str(edge_slice.get(field) or "") for field in sorted(_SLICE_FIELDS))
    return slice_id in {candidate, str(edge_slice.get("price_band")), "default"}


def _find_mutable_artifact(
    state: dict[str, Any],
    *,
    state_field: str,
    id_field: str,
    target_id: str,
) -> dict[str, Any]:
    for item in _mutable_mapping_items(state.get(state_field)):
        if item.get(id_field) == target_id:
            return item
    raise FeedbackServiceError(
        "FEEDBACK_TARGET_NOT_FOUND",
        "Feedback target not found",
        status_code=404,
        details={"target_id": target_id, "target_field": id_field},
    )


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


def _mutable_mapping_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _string_items(value: Any) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _dedupe[T](items: Iterable[T]) -> list[T]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped
