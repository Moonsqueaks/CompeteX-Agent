from fastapi import APIRouter, Request

from app.api.dependencies import repository_session
from app.api.responses import ApiException, get_trace_id, success_response
from app.schemas import ApiResponse, OverviewData
from app.services import OverviewService, OverviewServiceError
from app.storage import ArtifactRepository, TaskRepository

router = APIRouter(prefix="/tasks", tags=["overview"])


@router.get("/{task_id}/overview", response_model=ApiResponse[OverviewData])
def get_task_overview(
    task_id: str,
    request: Request,
    price_band: str | None = None,
    persona: str | None = None,
    scenario: str | None = None,
):
    trace_id = get_trace_id(request)
    with repository_session(request.app) as session:
        service = _overview_service(request, session)
        try:
            overview = service.get_overview(
                task_id,
                price_band=price_band,
                persona=persona,
                scenario=scenario,
            )
        except OverviewServiceError as exc:
            raise _api_exception(exc) from exc

    return success_response(overview.model_dump(mode="json"), trace_id)


def _overview_service(request: Request, session) -> OverviewService:
    workflow_factory = getattr(request.app.state, "overview_workflow_factory", None)
    kwargs = {}
    if workflow_factory is not None:
        kwargs["workflow_factory"] = workflow_factory
    return OverviewService(
        task_repository=TaskRepository(session),
        artifact_repository=ArtifactRepository(session),
        **kwargs,
    )


def _api_exception(exc: OverviewServiceError) -> ApiException:
    return ApiException(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
