from fastapi import APIRouter, Request, status

from app.api.dependencies import repository_session
from app.api.responses import ApiException, get_trace_id, success_response
from app.schemas import ApiResponse, TaskCreateRequest, TaskCreateResponse, TaskStatusResponse
from app.services import TaskCreationError, TaskCreationService
from app.storage import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "",
    response_model=ApiResponse[TaskCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_task(payload: TaskCreateRequest, request: Request):
    trace_id = get_trace_id(request)
    with repository_session(request.app) as session:
        repository = TaskRepository(session)
        try:
            result = TaskCreationService(repository).create_task(payload)
        except TaskCreationError as exc:
            raise ApiException(
                code=exc.code,
                message=exc.message,
                status_code=status.HTTP_400_BAD_REQUEST,
                details=exc.details,
            ) from exc

    return success_response(result.model_dump(mode="json"), trace_id, status.HTTP_201_CREATED)


@router.get("/{task_id}", response_model=ApiResponse[TaskStatusResponse])
def get_task(task_id: str, request: Request):
    trace_id = get_trace_id(request)
    with repository_session(request.app) as session:
        repository = TaskRepository(session)
        task = repository.get(task_id)

    if task is None:
        raise ApiException(
            code="TASK_NOT_FOUND",
            message="Task not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"task_id": task_id},
        )

    result = TaskStatusResponse.from_task(task)
    return success_response(result.model_dump(mode="json"), trace_id)
