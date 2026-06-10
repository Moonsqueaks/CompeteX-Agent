from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.agents.writer import writer_agent_node
from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AnalysisTask,
    BattlefieldSliceSelection,
    ConfidenceLevel,
    Evidence,
    EvidenceSourceType,
    FeedbackAction,
    FeedbackTargetType,
    HumanFeedback,
    HumanFeedbackCreateRequest,
    HumanFeedbackCreateResponse,
    ReportData,
    TaskStatus,
)
from app.schemas.common import JsonObject
from app.services.battlefield_service import (
    BATTLEFIELD_ARTIFACT_TYPE,
    _battlefield_artifact_id,
    _build_battlefield_data,
)
from app.services.llm_client import LLMClient, LLMSettings
from app.services.profile_service import PRODUCT_PROFILE_ARTIFACT_TYPE, _build_product_profile
from app.services.report_service import REPORT_ARTIFACT_TYPE, redact_report_data
from app.services.trace_service import TRACE_ARTIFACT_TYPE, _build_trace_data, _trace_artifact_id
from app.storage import ArtifactRepository, HumanFeedbackRepository, TaskRepository

HUMAN_FEEDBACK_EFFECT_ARTIFACT_TYPE = "human_feedback_effect"
LOCAL_RECOMPUTE_STATUS = "applied_local_update"
DEEPSEEK_PRODUCT_ID = "deepseek"
DEEPSEEK_PRICING_FIELD = "pricing.api_price_table"
DEEPSEEK_PRICING_EVIDENCE_ID = "ev_ip_deepseek_api_pricing_user_upload_001"

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
_STRUCTURED_ANALYSIS_FIELD_ALLOWLIST = {
    FeedbackTargetType.BATTLECARD: {
        "field": "battlecard_id",
        "state_field": "competitor_battlecards",
        "allowed_fields": {
            "competitor_tier",
            "threat_level",
            "evidence_status",
            "do_not_overclaim",
            "target_response",
            "response_talk_track",
        },
    },
    FeedbackTargetType.GAP_MATRIX_ITEM: {
        "field": "gap_id",
        "state_field": "gap_matrix_items",
        "allowed_fields": {
            "gap_type",
            "dimension",
            "evidence_status",
            "next_step_owner",
            "recommendation",
        },
    },
    FeedbackTargetType.OPPORTUNITY_ITEM: {
        "field": "opportunity_id",
        "state_field": "opportunity_items",
        "allowed_fields": {
            "priority",
            "owner",
            "action_type",
            "acceptance_signal",
            "must_not_claim",
            "evidence_boundary",
        },
    },
}


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

            report = _build_feedback_report(
                task=task,
                state=state,
                existing_reports=self.artifact_repository.list_by_task(
                    task.task_id,
                    REPORT_ARTIFACT_TYPE,
                    ReportData,
                ),
            )
            self.artifact_repository.save(REPORT_ARTIFACT_TYPE, report.report_id, report)

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

        return [
            profile.profile_id,
            battlefield.battlefield_id,
            report.report_id,
            trace.trace_view_id,
        ]


def _feedback_values(
    state: Mapping[str, Any],
    payload: HumanFeedbackCreateRequest,
) -> tuple[JsonObject, JsonObject, list[str]]:
    if payload.target_type in _PROFILE_FIELD_ALLOWLIST:
        return _profile_update_values(state, payload)
    if payload.target_type in _STRUCTURED_ANALYSIS_FIELD_ALLOWLIST:
        return _structured_analysis_values(state, payload)
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
    elif payload.target_type in _STRUCTURED_ANALYSIS_FIELD_ALLOWLIST:
        _apply_structured_analysis_update(updated_state, payload, after_value)
    elif payload.target_type == FeedbackTargetType.CLAIM:
        _apply_claim_status_update(updated_state, payload, after_value)
    elif payload.target_type == FeedbackTargetType.EVIDENCE:
        _apply_evidence_note(updated_state, payload, feedback, after_value)
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


def _build_feedback_report(
    *,
    task: AnalysisTask,
    state: Mapping[str, Any],
    existing_reports: list[ReportData],
) -> ReportData:
    report_state = deepcopy(dict(state))
    report_state["task"] = task.model_dump(mode="json")
    report_state["reports"] = [
        ReportData.model_validate(report).model_dump(mode="json")
        for report in existing_reports
    ]
    metadata = report_state.get("metadata")
    report_state["metadata"] = dict(metadata) if isinstance(metadata, Mapping) else {}
    qa_metadata = report_state["metadata"].get("qa_agent")
    qa_metadata = dict(qa_metadata) if isinstance(qa_metadata, Mapping) else {}
    qa_metadata.setdefault("qa_status", "passed")
    report_state["metadata"]["qa_agent"] = qa_metadata

    writer_agent_node(
        report_state,
        now=datetime.now(UTC),
        llm_client=_feedback_local_llm_client(),
    )
    if not report_state.get("reports"):
        raise FeedbackServiceError(
            "FEEDBACK_RECOMPUTE_FAILED",
            "Human feedback did not produce a refreshed report artifact.",
            status_code=500,
            details={"task_id": task.task_id, "reason": "missing_report"},
        )
    return redact_report_data(ReportData.model_validate(report_state["reports"][-1]))


def _feedback_local_llm_client() -> LLMClient:
    return LLMClient(
        settings=LLMSettings(
            enabled=False,
            provider="doubao",
            api_key="",
            base_url="",
            model="Doubao-Seed-2.0-lite",
        )
    )


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


def _apply_structured_analysis_update(
    state: dict[str, Any],
    payload: HumanFeedbackCreateRequest,
    after_value: JsonObject,
) -> None:
    config = _STRUCTURED_ANALYSIS_FIELD_ALLOWLIST[payload.target_type]
    artifact = _find_mutable_artifact(
        state,
        state_field=str(config["state_field"]),
        id_field=str(config["field"]),
        target_id=payload.target_id,
    )
    field_name = str(after_value["field"])
    artifact[field_name] = after_value["value"]


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
    feedback: HumanFeedback,
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
    if not _is_deepseek_pricing_supplement(evidence, after_value):
        return

    field_filled = str(after_value["field_filled"])
    existing_missing_fields = _string_items(evidence["metadata"].get("missing_fields"))
    evidence["metadata"]["missing_fields"] = [
        field for field in existing_missing_fields if field != field_filled
    ]
    evidence["metadata"]["missing_fields_filled"] = _dedupe(
        [*_string_items(evidence["metadata"].get("missing_fields_filled")), field_filled]
    )
    evidence["metadata"]["pricing_gap_status"] = "filled_by_human_review"
    evidence["metadata"]["supplemental_evidence_id"] = DEEPSEEK_PRICING_EVIDENCE_ID

    supplement = _deepseek_pricing_evidence(
        source_evidence=evidence,
        feedback=feedback,
        after_value=after_value,
    )
    _upsert_evidence(state, supplement)
    _link_evidence_to_product(
        state,
        product_id=DEEPSEEK_PRODUCT_ID,
        evidence_id=DEEPSEEK_PRICING_EVIDENCE_ID,
    )
    _update_deepseek_pricing_model(state, feedback.created_at)
    related_claim_ids = _link_evidence_to_deepseek_claims(state, payload.target_id)
    _refresh_deepseek_edges(state, related_claim_ids)


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
            "before": before_value,
            "after": after_value,
            "reason": feedback.reason,
        }
    )
    metadata["human_feedback_local_updates"] = history
    metadata["requires_analysis_recompute"] = False

    if payload.target_type == FeedbackTargetType.CLAIM:
        _append_analysis_claim_diff(metadata, payload, feedback, before_value, after_value)
    elif payload.target_type in {FeedbackTargetType.COMPETITION_EDGE, FeedbackTargetType.SLICE}:
        _append_analysis_edge_diff(metadata, payload, feedback, before_value, after_value)
    elif _is_deepseek_pricing_after_value(after_value):
        _append_deepseek_pricing_recompute_diff(
            metadata,
            feedback=feedback,
            before_value=before_value,
            after_value=after_value,
        )

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


def _append_deepseek_pricing_recompute_diff(
    metadata: JsonObject,
    *,
    feedback: HumanFeedback,
    before_value: JsonObject,
    after_value: JsonObject,
) -> None:
    recompute = _recompute_metadata(metadata)
    new_evidence_id = str(after_value.get("new_evidence_id") or DEEPSEEK_PRICING_EVIDENCE_ID)
    claim_ids = _string_items(after_value.get("related_claim_ids"))
    edge_ids = _string_items(after_value.get("related_edge_ids"))
    claim_diffs = [dict(item) for item in _mapping_items(recompute.get("claim_diffs"))]
    for claim_id in claim_ids:
        claim_diffs.append(
            {
                "claim_id": claim_id,
                "status": LOCAL_RECOMPUTE_STATUS,
                "before": {
                    "evidence_ids": _string_items(before_value.get("linked_evidence_ids")),
                    "pricing.api_price_table": "missing",
                },
                "after": {
                    "evidence_ids": _dedupe(
                        [
                            *_string_items(before_value.get("linked_evidence_ids")),
                            new_evidence_id,
                        ]
                    ),
                    "pricing.api_price_table": "available",
                },
                "feedback_id": feedback.feedback_id,
            }
        )
    edge_diffs = [dict(item) for item in _mapping_items(recompute.get("diffs"))]
    for edge_id in edge_ids:
        edge_diffs.append(
            {
                "edge_id": edge_id,
                "status": LOCAL_RECOMPUTE_STATUS,
                "before": {"pricing.api_price_table": "missing"},
                "after": {"pricing.api_price_table": "available"},
                "feedback_id": feedback.feedback_id,
            }
        )
    recompute["claim_diffs"] = claim_diffs
    recompute["diffs"] = edge_diffs
    recompute["target_claim_ids"] = _dedupe(
        [*_string_items(recompute.get("target_claim_ids")), *claim_ids]
    )
    recompute["target_edge_ids"] = _dedupe(
        [*_string_items(recompute.get("target_edge_ids")), *edge_ids]
    )
    recompute["pricing_gap"] = {
        "product_id": DEEPSEEK_PRODUCT_ID,
        "field_filled": DEEPSEEK_PRICING_FIELD,
        "new_evidence_id": new_evidence_id,
        "status": "available",
    }
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


def _structured_analysis_values(
    state: Mapping[str, Any],
    payload: HumanFeedbackCreateRequest,
) -> tuple[JsonObject, JsonObject, list[str]]:
    if payload.action != FeedbackAction.UPDATE_FIELD:
        raise _not_allowed(payload, "Structured analysis targets only support update_field.")
    config = _STRUCTURED_ANALYSIS_FIELD_ALLOWLIST[payload.target_type]
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
    if _after_value_field_filled(payload.after_value) == DEEPSEEK_PRICING_FIELD:
        return _deepseek_pricing_supplement_values(
            state=state,
            payload=payload,
            evidence=evidence,
            note=note,
            before_note=before_note,
        )
    return (
        {"human_note": before_note},
        {"human_note": note},
        [payload.target_id],
    )


def _deepseek_pricing_supplement_values(
    *,
    state: Mapping[str, Any],
    payload: HumanFeedbackCreateRequest,
    evidence: Mapping[str, Any],
    note: str,
    before_note: Any,
) -> tuple[JsonObject, JsonObject, list[str]]:
    if str(evidence.get("product_id") or "") != DEEPSEEK_PRODUCT_ID:
        raise _invalid_payload(
            payload,
            "DeepSeek pricing supplement must target DeepSeek evidence.",
        )
    metadata = evidence.get("metadata", {})
    metadata = metadata if isinstance(metadata, Mapping) else {}
    missing_fields = _string_items(metadata.get("missing_fields"))
    if DEEPSEEK_PRICING_FIELD not in missing_fields:
        raise _invalid_payload(
            payload,
            "DeepSeek pricing supplement must target an open pricing evidence gap.",
        )
    source_url = _optional_string(payload.after_value, "source_url")
    screenshot_path = _optional_string(payload.after_value, "screenshot_path")
    if source_url is None and screenshot_path is None:
        raise _invalid_payload(
            payload,
            "DeepSeek pricing supplement requires source_url or screenshot_path.",
        )
    content_summary = _optional_string(payload.after_value, "content_summary") or (
        "用户补充 DeepSeek API 定价证据；系统未自动解析价格数值，需按来源人工复核。"
    )
    related_claim_ids = _deepseek_related_claim_ids(state, str(evidence.get("evidence_id") or ""))
    related_edge_ids = _deepseek_related_edge_ids(state, related_claim_ids)
    before_value = {
        "human_note": before_note,
        "missing_fields": missing_fields,
        "pricing_gap_status": metadata.get("pricing_gap_status") or "missing",
        "linked_evidence_ids": [str(evidence.get("evidence_id"))],
    }
    after_value = {
        "human_note": note,
        "field_filled": DEEPSEEK_PRICING_FIELD,
        "new_evidence_id": DEEPSEEK_PRICING_EVIDENCE_ID,
        "source_url": source_url,
        "screenshot_path": screenshot_path,
        "content_summary": content_summary,
        "pricing_gap_status": "available",
        "related_claim_ids": related_claim_ids,
        "related_edge_ids": related_edge_ids,
    }
    affected_ids = _dedupe(
        [
            payload.target_id,
            DEEPSEEK_PRICING_EVIDENCE_ID,
            DEEPSEEK_PRODUCT_ID,
            f"pm_{DEEPSEEK_PRODUCT_ID}",
            *related_claim_ids,
            *related_edge_ids,
        ]
    )
    return before_value, after_value, affected_ids


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


def _is_deepseek_pricing_supplement(
    evidence: Mapping[str, Any],
    after_value: Mapping[str, Any],
) -> bool:
    return (
        str(evidence.get("product_id") or "") == DEEPSEEK_PRODUCT_ID
        and _is_deepseek_pricing_after_value(after_value)
    )


def _is_deepseek_pricing_after_value(after_value: Mapping[str, Any]) -> bool:
    return _after_value_field_filled(after_value) == DEEPSEEK_PRICING_FIELD


def _after_value_field_filled(after_value: Mapping[str, Any]) -> str | None:
    value = after_value.get("field_filled")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _deepseek_pricing_evidence(
    *,
    source_evidence: Mapping[str, Any],
    feedback: HumanFeedback,
    after_value: Mapping[str, Any],
) -> JsonObject:
    content_summary = str(after_value.get("content_summary") or "").strip()
    source_url = _optional_string(after_value, "source_url")
    screenshot_path = _optional_string(after_value, "screenshot_path")
    confidence_level = (
        ConfidenceLevel.MEDIUM if source_url and screenshot_path else ConfidenceLevel.LOW
    )
    evidence = Evidence(
        evidence_id=DEEPSEEK_PRICING_EVIDENCE_ID,
        task_id=str(source_evidence["task_id"]),
        product_id=DEEPSEEK_PRODUCT_ID,
        source_type=EvidenceSourceType.MANUAL_REVIEW,
        source_url=source_url,
        screenshot_path=screenshot_path,
        access_time=feedback.created_at,
        content_summary=content_summary
        or "用户补充 DeepSeek API 定价证据；系统未自动解析价格数值，需按来源人工复核。",
        confidence_level=confidence_level,
        limitations=(
            "该 Evidence 来自人工补充的 URL 或截图说明；系统只记录可复核来源，"
            "不自动抽取或写死 API 价格数值，仍需关注访问时间和页面变更。"
        ),
        metadata={
            "evidence_origin": "user_upload",
            "evidence_purpose": "fill_pricing_gap",
            "field_filled": DEEPSEEK_PRICING_FIELD,
            "pricing_gap_status": "available",
            "source_evidence_id": source_evidence.get("evidence_id"),
            "feedback_id": feedback.feedback_id,
            "human_note": after_value.get("human_note"),
            "missing_fields": [],
        },
    )
    return evidence.model_dump(mode="json")


def _upsert_evidence(state: dict[str, Any], evidence: JsonObject) -> None:
    evidences = state.get("evidences")
    if not isinstance(evidences, list):
        state["evidences"] = [evidence]
        return
    for index, item in enumerate(evidences):
        if isinstance(item, dict) and item.get("evidence_id") == evidence["evidence_id"]:
            evidences[index] = evidence
            return
    evidences.append(evidence)


def _link_evidence_to_product(
    state: dict[str, Any],
    *,
    product_id: str,
    evidence_id: str,
) -> None:
    product = _find_mutable_artifact(
        state,
        state_field="products",
        id_field="product_id",
        target_id=product_id,
    )
    product["evidence_ids"] = _dedupe([*_string_items(product.get("evidence_ids")), evidence_id])


def _update_deepseek_pricing_model(state: dict[str, Any], access_time: datetime) -> None:
    pricing_models = state.get("pricing_models")
    if not isinstance(pricing_models, list):
        pricing_models = []
        state["pricing_models"] = pricing_models
    pricing_model = next(
        (
            item
            for item in pricing_models
            if isinstance(item, dict) and item.get("product_id") == DEEPSEEK_PRODUCT_ID
        ),
        None,
    )
    note = "DeepSeek API 定价证据已由人工补充；具体价格数值需按来源页面或截图人工复核。"
    if pricing_model is None:
        pricing_models.append(
            {
                "pricing_model_id": f"pm_{DEEPSEEK_PRODUCT_ID}",
                "task_id": str(state["task"]["task_id"]),
                "product_id": DEEPSEEK_PRODUCT_ID,
                "price_band": "api_pricing_verified",
                "currency": "CNY",
                "list_price": None,
                "final_price": None,
                "promotions": [note],
                "bundle_description": note,
                "evidence_ids": [DEEPSEEK_PRICING_EVIDENCE_ID],
                "access_time": access_time.isoformat(),
                "risk_flags": [],
            }
        )
        return

    pricing_model["price_band"] = "api_pricing_verified"
    pricing_model["promotions"] = _dedupe([*_string_items(pricing_model.get("promotions")), note])
    pricing_model["bundle_description"] = note
    pricing_model["evidence_ids"] = _dedupe(
        [*_string_items(pricing_model.get("evidence_ids")), DEEPSEEK_PRICING_EVIDENCE_ID]
    )
    pricing_model["access_time"] = access_time.isoformat()
    pricing_model["risk_flags"] = [
        flag
        for flag in _string_items(pricing_model.get("risk_flags"))
        if flag not in {"missing_evidence", "missing_access_time", "unreliable_data"}
    ]


def _link_evidence_to_deepseek_claims(state: dict[str, Any], source_evidence_id: str) -> list[str]:
    claim_ids: list[str] = []
    for claim in _mutable_mapping_items(state.get("claims")):
        if not _is_deepseek_related_claim(claim, source_evidence_id):
            continue
        claim["evidence_ids"] = _dedupe(
            [*_string_items(claim.get("evidence_ids")), DEEPSEEK_PRICING_EVIDENCE_ID]
        )
        claim["risk_flags"] = [
            flag
            for flag in _string_items(claim.get("risk_flags"))
            if flag not in {"missing_evidence", "unreliable_data"}
        ]
        claim_id = claim.get("claim_id")
        if isinstance(claim_id, str):
            claim_ids.append(claim_id)
    return _dedupe(claim_ids)


def _refresh_deepseek_edges(state: dict[str, Any], related_claim_ids: list[str]) -> None:
    related_claim_set = set(related_claim_ids)
    for edge in _mutable_mapping_items(state.get("competition_edges")):
        if (
            edge.get("competitor_product_id") != DEEPSEEK_PRODUCT_ID
            and not related_claim_set.intersection(_string_items(edge.get("claim_ids")))
        ):
            continue
        score_breakdown = edge.get("score_breakdown")
        if not isinstance(score_breakdown, dict):
            continue
        before_confidence = _coerce_float(score_breakdown.get("evidence_confidence")) or 0.0
        after_confidence = max(before_confidence, 0.72)
        score_breakdown["evidence_confidence"] = round(after_confidence, 2)
        edge_score = _coerce_float(edge.get("edge_score"))
        if edge_score is not None and after_confidence > before_confidence:
            edge["edge_score"] = round(
                min(1.0, edge_score + (after_confidence - before_confidence) * 0.15),
                2,
            )
        edge["risk_flags"] = [
            flag
            for flag in _string_items(edge.get("risk_flags"))
            if flag not in {"missing_evidence", "unreliable_data"}
        ]


def _deepseek_related_claim_ids(state: Mapping[str, Any], source_evidence_id: str) -> list[str]:
    return _dedupe(
        [
            str(claim["claim_id"])
            for claim in _mapping_items(state.get("claims"))
            if isinstance(claim.get("claim_id"), str)
            and _is_deepseek_related_claim(claim, source_evidence_id)
        ]
    )


def _deepseek_related_edge_ids(
    state: Mapping[str, Any],
    related_claim_ids: list[str],
) -> list[str]:
    related_claim_set = set(related_claim_ids)
    return _dedupe(
        [
            str(edge["edge_id"])
            for edge in _mapping_items(state.get("competition_edges"))
            if isinstance(edge.get("edge_id"), str)
            and (
                edge.get("competitor_product_id") == DEEPSEEK_PRODUCT_ID
                or related_claim_set.intersection(_string_items(edge.get("claim_ids")))
            )
        ]
    )


def _is_deepseek_related_claim(claim: Mapping[str, Any], source_evidence_id: str) -> bool:
    evidence_ids = _string_items(claim.get("evidence_ids"))
    if source_evidence_id in evidence_ids:
        return True
    text = " ".join(
        str(part)
        for part in (
            claim.get("claim_type"),
            claim.get("content"),
            " ".join(evidence_ids),
        )
        if part
    ).lower()
    return "deepseek" in text or "deepseek" in " ".join(evidence_ids).lower()


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


def _optional_string(value: Mapping[str, Any], key: str) -> str | None:
    item = value.get(key)
    if not isinstance(item, str):
        return None
    stripped = item.strip()
    return stripped or None


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


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
