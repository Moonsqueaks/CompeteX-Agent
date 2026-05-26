from fastapi import APIRouter, Request

from app.api.dependencies import repository_session
from app.api.responses import ApiException, get_trace_id, success_response
from app.schemas import ApiResponse, BattlefieldData
from app.services import BattlefieldService, BattlefieldServiceError
from app.storage import ArtifactRepository, TaskRepository

router = APIRouter(prefix="/tasks", tags=["battlefield"])


@router.get("/{task_id}/battlefield", response_model=ApiResponse[BattlefieldData])
def get_task_battlefield(
    task_id: str,
    request: Request,
    price_band: str | None = None,
    persona: str | None = None,
    scenario: str | None = None,
):
    trace_id = get_trace_id(request)
    with repository_session(request.app) as session:
        service = _battlefield_service(request, session)
        try:
            battlefield = service.get_battlefield(
                task_id,
                price_band=price_band,
                persona=persona,
                scenario=scenario,
            )
        except BattlefieldServiceError as exc:
            raise _api_exception(exc) from exc

    return success_response(battlefield.model_dump(mode="json"), trace_id)


def _battlefield_service(request: Request, session) -> BattlefieldService:
    workflow_factory = getattr(request.app.state, "battlefield_workflow_factory", None)
    kwargs = {}
    if workflow_factory is not None:
        kwargs["workflow_factory"] = workflow_factory
    return BattlefieldService(
        task_repository=TaskRepository(session),
        artifact_repository=ArtifactRepository(session),
        **kwargs,
    )


def _api_exception(exc: BattlefieldServiceError) -> ApiException:
    return ApiException(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
