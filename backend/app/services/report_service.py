from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import AnalysisTask, MarkdownReport, ReportData, TaskStatus
from app.services.markdown_renderer import MarkdownRenderError, render_markdown_report
from app.storage import ArtifactRepository, TaskRepository

REPORT_ARTIFACT_TYPE = "report_data"
MARKDOWN_REPORT_ARTIFACT_TYPE = "markdown_report"

WorkflowFactory = Callable[[], Any]


class ReportServiceError(Exception):
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


class ReportService:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        artifact_repository: ArtifactRepository,
        workflow_factory: WorkflowFactory = build_analysis_workflow,
        markdown_output_dir: Path | str | None = None,
    ) -> None:
        self.task_repository = task_repository
        self.artifact_repository = artifact_repository
        self.workflow_factory = workflow_factory
        self.markdown_output_dir = markdown_output_dir

    def get_report_data(self, task_id: str) -> ReportData:
        task = self._get_completed_task(task_id)
        cached_report = self._latest_report(task_id)
        if cached_report is not None:
            return cached_report
        return self._generate_and_cache_report(task)

    def export_markdown_report(self, task_id: str) -> MarkdownReport:
        report = self.get_report_data(task_id)
        try:
            markdown_report = render_markdown_report(
                report,
                output_dir=self.markdown_output_dir,
            )
        except (MarkdownRenderError, OSError) as exc:
            raise ReportServiceError(
                "MARKDOWN_EXPORT_FAILED",
                "Markdown export failed",
                status_code=500,
                details={
                    "task_id": task_id,
                    "report_id": report.report_id,
                    "reason": exc.__class__.__name__,
                },
            ) from exc

        self.artifact_repository.save(
            MARKDOWN_REPORT_ARTIFACT_TYPE,
            markdown_report.markdown_report_id,
            markdown_report,
        )
        return markdown_report

    def _get_completed_task(self, task_id: str) -> AnalysisTask:
        task = self.task_repository.get(task_id)
        if task is None:
            raise ReportServiceError(
                "TASK_NOT_FOUND",
                "Task not found",
                status_code=404,
                details={"task_id": task_id},
            )
        if task.status != TaskStatus.COMPLETED:
            raise ReportServiceError(
                "REPORT_NOT_READY",
                "Report is only available after the task is completed.",
                status_code=409,
                details={"task_id": task_id, "status": task.status.value},
            )
        return task

    def _latest_report(self, task_id: str) -> ReportData | None:
        reports = self.artifact_repository.list_by_task(
            task_id,
            REPORT_ARTIFACT_TYPE,
            ReportData,
        )
        if not reports:
            return None
        return ReportData.model_validate(reports[-1])

    def _generate_and_cache_report(self, task: AnalysisTask) -> ReportData:
        try:
            workflow = self.workflow_factory()
            state = create_initial_state(task)
            result = workflow.invoke(state)
        except Exception as exc:
            raise ReportServiceError(
                "REPORT_GENERATION_FAILED",
                "Report generation failed",
                status_code=500,
                details={"task_id": task.task_id, "reason": exc.__class__.__name__},
            ) from exc

        if result["task"].get("status") != TaskStatus.COMPLETED.value or not result["reports"]:
            raise ReportServiceError(
                "REPORT_GENERATION_FAILED",
                "Report generation did not produce a completed report.",
                status_code=500,
                details={
                    "task_id": task.task_id,
                    "workflow_status": result["task"].get("status"),
                },
            )

        report = ReportData.model_validate(result["reports"][-1])
        self.artifact_repository.save(REPORT_ARTIFACT_TYPE, report.report_id, report)
        return report
