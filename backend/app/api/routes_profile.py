from fastapi import APIRouter, Request

from app.api.dependencies import repository_session
from app.api.responses import ApiException, get_trace_id, success_response
from app.schemas import ApiResponse, ProductProfileData
from app.services import ProfileService, ProfileServiceError
from app.storage import ArtifactRepository, TaskRepository

router = APIRouter(prefix="/tasks", tags=["profile"])


@router.get("/{task_id}/profile", response_model=ApiResponse[ProductProfileData])
def get_task_profile(task_id: str, request: Request):
    trace_id = get_trace_id(request)
    with repository_session(request.app) as session:
        service = ProfileService(
            task_repository=TaskRepository(session),
            artifact_repository=ArtifactRepository(session),
        )
        try:
            profile = service.get_product_profile(task_id)
        except ProfileServiceError as exc:
            raise ApiException(
                code=exc.code,
                message=exc.message,
                status_code=exc.status_code,
                details=exc.details,
            ) from exc

    return success_response(profile.model_dump(mode="json"), trace_id)
