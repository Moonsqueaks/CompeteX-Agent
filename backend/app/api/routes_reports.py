from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from app.api.dependencies import repository_session
from app.api.responses import ApiException, get_trace_id, success_response
from app.schemas import ApiResponse, ReportData
from app.services import (
    ReportService,
    ReportServiceError,
    WordReportService,
    WordReportServiceError,
)
from app.storage import ArtifactRepository, TaskRepository

router = APIRouter(prefix="/tasks", tags=["reports"])
DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


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


@router.post("/{task_id}/report/regenerate", response_model=ApiResponse[ReportData])
def regenerate_task_report(task_id: str, request: Request):
    trace_id = get_trace_id(request)
    with repository_session(request.app) as session:
        service = _report_service(request, session)
        try:
            report = service.regenerate_report_data(task_id)
        except ReportServiceError as exc:
            raise _api_exception(exc) from exc

    return success_response(report.model_dump(mode="json"), trace_id)


@router.get(
    "/{task_id}/report/docx",
    response_class=FileResponse,
    responses={
        200: {
            "content": {DOCX_MEDIA_TYPE: {}},
            "description": "Word .docx report download.",
        }
    },
)
def export_task_report_docx(task_id: str, request: Request):
    with repository_session(request.app) as session:
        service = _word_report_service(request, session)
        try:
            word_report = service.export_word_report(task_id)
        except WordReportServiceError as exc:
            raise _api_exception(exc) from exc

    return FileResponse(
        path=word_report.file_path,
        media_type=DOCX_MEDIA_TYPE,
        filename=word_report.file_name,
    )


def _report_service(request: Request, session) -> ReportService:
    workflow_factory = getattr(request.app.state, "report_workflow_factory", None)
    kwargs = {}
    if workflow_factory is not None:
        kwargs["workflow_factory"] = workflow_factory
    return ReportService(
        task_repository=TaskRepository(session),
        artifact_repository=ArtifactRepository(session),
        markdown_output_dir=getattr(request.app.state, "report_output_dir", None),
        **kwargs,
    )


def _word_report_service(request: Request, session) -> WordReportService:
    workflow_factory = getattr(request.app.state, "word_report_workflow_factory", None)
    kwargs = {}
    if workflow_factory is not None:
        kwargs["workflow_factory"] = workflow_factory
    return WordReportService(
        task_repository=TaskRepository(session),
        artifact_repository=ArtifactRepository(session),
        output_dir=getattr(request.app.state, "report_output_dir", None),
        **kwargs,
    )


def _api_exception(exc: ReportServiceError | WordReportServiceError) -> ApiException:
    return ApiException(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
