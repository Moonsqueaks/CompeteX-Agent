from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import (
    AnalysisTask,
    BattlefieldSliceSelection,
    ReportData,
    TaskStatus,
)
from app.services.battlefield_service import (
    BATTLEFIELD_ARTIFACT_TYPE,
    _battlefield_artifact_id,
    _build_battlefield_data,
)
from app.services.profile_service import PRODUCT_PROFILE_ARTIFACT_TYPE, _build_product_profile
from app.services.report_service import REPORT_ARTIFACT_TYPE
from app.services.trace_service import TRACE_ARTIFACT_TYPE, _build_trace_data, _trace_artifact_id
from app.storage import ArtifactRepository, TaskRepository

WorkflowFactory = Callable[[], Any]


class TaskExecutionError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class TaskExecutionService:
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

    def execute_task(self, task_id: str) -> AnalysisTask:
        task = self.task_repository.get(task_id)
        if task is None:
            raise TaskExecutionError(
                "TASK_NOT_FOUND",
                "Task not found",
                {"task_id": task_id},
            )
        if task.status == TaskStatus.COMPLETED:
            return task

        self.task_repository.update_status(task_id, TaskStatus.COLLECTING)
        task = self.task_repository.get(task_id) or task

        try:
            workflow = self.workflow_factory()
            result = workflow.invoke(create_initial_state(task))
            final_status = _status_from_result(result)
            self._cache_result_artifacts(task=task, result=result, final_status=final_status)
            return self._finish_task(task_id, task, result, final_status)
        except Exception as exc:
            return self._mark_failed(task_id, task, exc)

    def _cache_result_artifacts(
        self,
        *,
        task: AnalysisTask,
        result: Mapping[str, Any],
        final_status: TaskStatus,
    ) -> None:
        trace = _build_trace_data(
            task=task,
            state=result,
            trace_view_id=_trace_artifact_id(task.task_id),
        )
        self.artifact_repository.save(TRACE_ARTIFACT_TYPE, trace.trace_view_id, trace)

        if final_status != TaskStatus.COMPLETED:
            return

        profile = _build_product_profile(dict(result))
        self.artifact_repository.save(PRODUCT_PROFILE_ARTIFACT_TYPE, profile.profile_id, profile)

        selected_slice = BattlefieldSliceSelection()
        battlefield_id = _battlefield_artifact_id(task.task_id, selected_slice)
        battlefield = _build_battlefield_data(dict(result), selected_slice, battlefield_id)
        self.artifact_repository.save(
            BATTLEFIELD_ARTIFACT_TYPE,
            battlefield.battlefield_id,
            battlefield,
        )

        reports = result.get("reports")
        if isinstance(reports, list) and reports:
            report = ReportData.model_validate(reports[-1])
            self.artifact_repository.save(REPORT_ARTIFACT_TYPE, report.report_id, report)

    def _finish_task(
        self,
        task_id: str,
        task: AnalysisTask,
        result: Mapping[str, Any],
        final_status: TaskStatus,
    ) -> AnalysisTask:
        task_payload = result.get("task", {})
        state_metadata = result.get("metadata", {})
        metadata = dict(task.metadata)
        metadata["task_execution"] = {
            "completed_at": datetime.now(UTC).isoformat(),
            "status": final_status.value,
            "source": "langgraph_workflow",
            "workflow": _safe_mapping(state_metadata).get("workflow", {}),
            "artifact_counts": {
                "products": len(_list_value(result.get("products"))),
                "evidences": len(_list_value(result.get("evidences"))),
                "claims": len(_list_value(result.get("claims"))),
                "competition_edges": len(_list_value(result.get("competition_edges"))),
                "reports": len(_list_value(result.get("reports"))),
            },
        }
        if isinstance(task_payload, Mapping) and isinstance(task_payload.get("updated_at"), str):
            metadata["task_execution"]["state_updated_at"] = task_payload["updated_at"]

        self.task_repository.update_metadata(task_id, metadata)
        updated = self.task_repository.update_status(task_id, final_status)
        return updated or task

    def _mark_failed(self, task_id: str, task: AnalysisTask, exc: Exception) -> AnalysisTask:
        updated = self.task_repository.update_status(task_id, TaskStatus.FAILED) or task
        metadata = dict(updated.metadata)
        metadata["task_execution"] = {
            "completed_at": datetime.now(UTC).isoformat(),
            "status": TaskStatus.FAILED.value,
            "source": "langgraph_workflow",
            "failure_reason": exc.__class__.__name__,
            "failure_message": str(exc),
        }
        updated = self.task_repository.update_metadata(task_id, metadata) or updated
        self._cache_execution_failure_trace(task=updated, exc=exc)
        return self.task_repository.get(task_id) or updated

    def _cache_execution_failure_trace(self, *, task: AnalysisTask, exc: Exception) -> None:
        failure_state = create_initial_state(task)
        failure_state["task"]["status"] = TaskStatus.FAILED.value
        failure_state["task"]["updated_at"] = datetime.now(UTC).isoformat()
        failure_state["metadata"]["workflow"] = {
            "status": "failed",
            "current_node": "failed",
            "next_node": "failed",
            "failure_reason": exc.__class__.__name__,
            "failure_message": str(exc),
        }
        trace = _build_trace_data(
            task=task,
            state=failure_state,
            trace_view_id=_trace_artifact_id(task.task_id),
        )
        self.artifact_repository.save(TRACE_ARTIFACT_TYPE, trace.trace_view_id, trace)


def _status_from_result(result: Mapping[str, Any]) -> TaskStatus:
    task_payload = result.get("task", {})
    if isinstance(task_payload, Mapping):
        status = task_payload.get("status")
        if isinstance(status, str):
            try:
                return TaskStatus(status)
            except ValueError:
                return TaskStatus.FAILED
    return TaskStatus.FAILED


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list_value(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []
