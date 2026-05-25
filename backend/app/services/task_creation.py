from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.schemas import AnalysisTask, DataSourceMode, TaskCreateRequest, TaskCreateResponse
from app.services.snapshot_loader import SnapshotLoaderError, SnapshotLoadResult, load_demo_snapshot
from app.storage.repositories import TaskRepository


class TaskCreationError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class TaskCreationService:
    def __init__(self, task_repository: TaskRepository):
        self.task_repository = task_repository

    def create_task(self, payload: TaskCreateRequest) -> TaskCreateResponse:
        snapshot = self._load_snapshot()
        default_target = _default_target_product(snapshot)
        uses_default_target = payload.target_product_name is None
        now = datetime.now(UTC)

        task = AnalysisTask(
            task_id=f"task_{uuid4().hex}",
            target_product_name=payload.target_product_name or default_target.name,
            target_product_url=payload.target_product_url or default_target.product_url,
            category=payload.category or snapshot.category,
            subcategory=payload.subcategory or snapshot.subcategory,
            data_source_mode=payload.data_source_mode,
            status="created",
            research_text=payload.research_text,
            metadata=_task_metadata(
                snapshot=snapshot,
                uses_default_target=uses_default_target,
                data_source_mode=payload.data_source_mode,
            ),
            created_at=now,
            updated_at=now,
        )
        created = self.task_repository.create(task)
        return TaskCreateResponse(task_id=created.task_id, status=created.status, task=created)

    def _load_snapshot(self) -> SnapshotLoadResult:
        try:
            return load_demo_snapshot(task_id="task_creation_preview")
        except SnapshotLoaderError as exc:
            raise TaskCreationError(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ) from exc


def _default_target_product(snapshot: SnapshotLoadResult):
    for product in snapshot.products:
        if product.sku_id == snapshot.default_target_sku_id:
            return product
    raise TaskCreationError(
        code="DEFAULT_TARGET_NOT_FOUND",
        message="Default target product was not found in the demo snapshot.",
        details={"default_target_sku_id": snapshot.default_target_sku_id},
    )


def _task_metadata(
    *,
    snapshot: SnapshotLoadResult,
    uses_default_target: bool,
    data_source_mode: DataSourceMode,
) -> dict:
    metadata = {
        "snapshot_version": snapshot.snapshot_version,
        "default_target_sku_id": snapshot.default_target_sku_id,
        "target_selection": "demo_default_target" if uses_default_target else "user_input",
        "snapshot_source_path": _safe_snapshot_path(snapshot.source_path),
    }
    if data_source_mode == DataSourceMode.SNAPSHOT_PLUS_LIVE:
        metadata["snapshot_plus_live_note"] = "MVP records this mode and uses local snapshot data."
    return metadata


def _safe_snapshot_path(path: str) -> str:
    snapshot_path = Path(path)
    try:
        return snapshot_path.relative_to(Path(__file__).resolve().parents[3]).as_posix()
    except ValueError:
        return snapshot_path.name
