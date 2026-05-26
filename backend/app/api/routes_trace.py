from fastapi import APIRouter, Request

from app.api.dependencies import repository_session
from app.api.responses import ApiException, get_trace_id, success_response
from app.schemas import ApiResponse, TraceData
from app.services import TraceService, TraceServiceError
from app.storage import ArtifactRepository, TaskRepository

router = APIRouter(prefix="/tasks", tags=["trace"])


@router.get("/{task_id}/trace", response_model=ApiResponse[TraceData])
def get_task_trace(task_id: str, request: Request):
    trace_id = get_trace_id(request)
    with repository_session(request.app) as session:
        service = _trace_service(request, session)
        try:
            trace_data = service.get_trace(task_id)
        except TraceServiceError as exc:
            raise _api_exception(exc) from exc

    return success_response(trace_data.model_dump(mode="json"), trace_id)


def _trace_service(request: Request, session) -> TraceService:
    workflow_factory = getattr(request.app.state, "trace_workflow_factory", None)
    kwargs = {}
    if workflow_factory is not None:
        kwargs["workflow_factory"] = workflow_factory
    return TraceService(
        task_repository=TaskRepository(session),
        artifact_repository=ArtifactRepository(session),
        **kwargs,
    )


def _api_exception(exc: TraceServiceError) -> ApiException:
    return ApiException(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
