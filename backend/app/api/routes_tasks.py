from fastapi import APIRouter, BackgroundTasks, Request, status

from app.api.dependencies import repository_session
from app.api.responses import ApiException, get_trace_id, success_response
from app.schemas import ApiResponse, TaskCreateRequest, TaskCreateResponse, TaskStatusResponse
from app.services import TaskCreationError, TaskCreationService, TaskExecutionService
from app.storage import ArtifactRepository, TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "",
    response_model=ApiResponse[TaskCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_task(payload: TaskCreateRequest, request: Request, background_tasks: BackgroundTasks):
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

    _start_task_execution(request, background_tasks, result.task_id)
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


def _start_task_execution(
    request: Request,
    background_tasks: BackgroundTasks,
    task_id: str,
) -> None:
    if not getattr(request.app.state, "auto_start_task_execution", False):
        return

    if getattr(request.app.state, "run_task_execution_inline", False):
        _execute_task_for_app(request.app, task_id)
        return

    background_tasks.add_task(_execute_task_for_app, request.app, task_id)


def _execute_task_for_app(app, task_id: str) -> None:
    with repository_session(app) as session:
        workflow_factory = getattr(app.state, "task_execution_workflow_factory", None)
        kwargs = {}
        if workflow_factory is not None:
            kwargs["workflow_factory"] = workflow_factory
        TaskExecutionService(
            task_repository=TaskRepository(session),
            artifact_repository=ArtifactRepository(session),
            **kwargs,
        ).execute_task(task_id)
