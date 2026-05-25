from collections.abc import Generator
from contextlib import contextmanager

from fastapi import APIRouter, FastAPI, Request, status
from sqlalchemy.orm import Session, sessionmaker

from app.api.responses import ApiException, get_trace_id, success_response
from app.schemas import ApiResponse, TaskCreateRequest, TaskCreateResponse, TaskStatusResponse
from app.services import TaskCreationError, TaskCreationService
from app.storage import TaskRepository, create_database_engine, create_session_factory, init_db

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "",
    response_model=ApiResponse[TaskCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_task(payload: TaskCreateRequest, request: Request):
    trace_id = get_trace_id(request)
    with _task_repository(request.app) as repository:
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
    with _task_repository(request.app) as repository:
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


@contextmanager
def _task_repository(app: FastAPI) -> Generator[TaskRepository]:
    session_factory = _get_session_factory(app)
    session = session_factory()
    try:
        yield TaskRepository(session)
    finally:
        session.close()


def _get_session_factory(app: FastAPI) -> sessionmaker[Session]:
    session_factory = getattr(app.state, "session_factory", None)
    if session_factory is not None:
        return session_factory

    database_url = getattr(app.state, "database_url", None)
    engine = create_database_engine(database_url)
    init_db(engine)
    session_factory = create_session_factory(engine)
    app.state.engine = engine
    app.state.session_factory = session_factory
    return session_factory
