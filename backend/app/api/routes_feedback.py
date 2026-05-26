from fastapi import APIRouter, Request, status

from app.api.dependencies import repository_session
from app.api.responses import ApiException, get_trace_id, success_response
from app.schemas import ApiResponse, HumanFeedbackCreateRequest, HumanFeedbackCreateResponse
from app.services import FeedbackService, FeedbackServiceError
from app.storage import ArtifactRepository, HumanFeedbackRepository, TaskRepository

router = APIRouter(prefix="/tasks", tags=["feedback"])


@router.post(
    "/{task_id}/feedback",
    response_model=ApiResponse[HumanFeedbackCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
def submit_task_feedback(
    task_id: str,
    payload: HumanFeedbackCreateRequest,
    request: Request,
):
    trace_id = get_trace_id(request)
    with repository_session(request.app) as session:
        service = _feedback_service(request, session)
        try:
            result = service.submit_feedback(task_id, payload)
        except FeedbackServiceError as exc:
            raise _api_exception(exc) from exc

    return success_response(result.model_dump(mode="json"), trace_id, status.HTTP_201_CREATED)


def _feedback_service(request: Request, session) -> FeedbackService:
    workflow_factory = getattr(request.app.state, "feedback_workflow_factory", None)
    kwargs = {}
    if workflow_factory is not None:
        kwargs["workflow_factory"] = workflow_factory
    return FeedbackService(
        task_repository=TaskRepository(session),
        feedback_repository=HumanFeedbackRepository(session),
        artifact_repository=ArtifactRepository(session),
        **kwargs,
    )


def _api_exception(exc: FeedbackServiceError) -> ApiException:
    return ApiException(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
