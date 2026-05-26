from fastapi import APIRouter, Request

from app.api.dependencies import repository_session
from app.api.responses import ApiException, get_trace_id, success_response
from app.schemas import ApiResponse, MarkdownReport, ReportData
from app.services import ReportService, ReportServiceError
from app.storage import ArtifactRepository, TaskRepository

router = APIRouter(prefix="/tasks", tags=["reports"])


@router.get("/{task_id}/report", response_model=ApiResponse[ReportData])
def get_task_report(task_id: str, request: Request):
    trace_id = get_trace_id(request)
    with repository_session(request.app) as session:
        service = _report_service(request, session)
        try:
            report = service.get_report_data(task_id)
        except ReportServiceError as exc:
            raise _api_exception(exc) from exc

    return success_response(report.model_dump(mode="json"), trace_id)


@router.get(
    "/{task_id}/report/markdown",
    response_model=ApiResponse[MarkdownReport],
)
def export_task_report_markdown(task_id: str, request: Request):
    trace_id = get_trace_id(request)
    with repository_session(request.app) as session:
        service = _report_service(request, session)
        try:
            markdown_report = service.export_markdown_report(task_id)
        except ReportServiceError as exc:
            raise _api_exception(exc) from exc

    return success_response(markdown_report.model_dump(mode="json"), trace_id)


def _report_service(request: Request, session) -> ReportService:
    return ReportService(
        task_repository=TaskRepository(session),
        artifact_repository=ArtifactRepository(session),
        markdown_output_dir=getattr(request.app.state, "report_output_dir", None),
    )


def _api_exception(exc: ReportServiceError) -> ApiException:
    return ApiException(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
