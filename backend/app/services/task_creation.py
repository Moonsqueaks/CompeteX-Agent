from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple
from uuid import uuid4

from app.schemas import AnalysisTask, DataSourceMode, Product, TaskCreateRequest, TaskCreateResponse
from app.security import redact_sensitive_text
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
        target_selection = _resolve_target_selection(snapshot, payload)
        now = datetime.now(UTC)
        research_text = _sanitize_research_text(payload.research_text)

        task = AnalysisTask(
            task_id=f"task_{uuid4().hex}",
            target_product_name=(
                (target_selection.product.name if target_selection.product else None)
                or payload.target_product_name
                or "User provided target product"
            ),
            target_product_url=(
                (target_selection.product.product_url if target_selection.product else None)
                or payload.target_product_url
            ),
            category=payload.category or snapshot.category,
            subcategory=payload.subcategory or snapshot.subcategory,
            data_source_mode=payload.data_source_mode,
            status="created",
            research_text=research_text,
            metadata=_task_metadata(
                snapshot=snapshot,
                target_selection=target_selection,
                data_source_mode=payload.data_source_mode,
                research_text_redacted=research_text != payload.research_text,
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


class TargetSelection(NamedTuple):
    product: Product | None
    sku_id: str | None
    selection: str
    match_basis: str | None
    match_confidence: str


def _default_target_product(snapshot: SnapshotLoadResult):
    for product in snapshot.products:
        if product.sku_id == snapshot.default_target_sku_id:
            return product
    raise TaskCreationError(
        code="DEFAULT_TARGET_NOT_FOUND",
        message="Default target product was not found in the demo snapshot.",
        details={"default_target_sku_id": snapshot.default_target_sku_id},
    )


def _resolve_target_selection(
    snapshot: SnapshotLoadResult,
    payload: TaskCreateRequest,
) -> TargetSelection:
    default_target = _default_target_product(snapshot)
    requested_name = _non_empty_text(payload.target_product_name)
    requested_url = _non_empty_text(payload.target_product_url)

    if requested_name is None and requested_url is None:
        return TargetSelection(
            product=default_target,
            sku_id=default_target.sku_id,
            selection="demo_default_target",
            match_basis="snapshot.default_target_sku_id",
            match_confidence="exact",
        )

    url_match = _match_product_by_url(snapshot.products, requested_url)
    if url_match is not None:
        return TargetSelection(
            product=url_match,
            sku_id=url_match.sku_id,
            selection="matched_snapshot_sku",
            match_basis="target_product_url",
            match_confidence="exact",
        )

    name_match, match_confidence = _match_product_by_name(snapshot.products, requested_name)
    if name_match is not None:
        return TargetSelection(
            product=name_match,
            sku_id=name_match.sku_id,
            selection="matched_snapshot_sku",
            match_basis="target_product_name",
            match_confidence=match_confidence,
        )

    return TargetSelection(
        product=None,
        sku_id=None,
        selection="user_input_unmatched",
        match_basis=None,
        match_confidence="none",
    )


def _match_product_by_url(
    products: list[Product],
    requested_url: str | None,
) -> Product | None:
    normalized_request = _normalize_url(requested_url)
    if normalized_request is None:
        return None
    for product in products:
        if _normalize_url(product.product_url) == normalized_request:
            return product
    return None


def _match_product_by_name(
    products: list[Product],
    requested_name: str | None,
) -> tuple[Product | None, str]:
    normalized_request = _normalize_name(requested_name)
    if normalized_request is None:
        return None, "none"

    candidates = [
        (product, _normalize_name(product.name), _normalize_name(product.brand))
        for product in products
    ]
    for product, product_name, brand in candidates:
        if normalized_request in {product_name, brand, _normalize_name(product.sku_id)}:
            return product, "exact"

    if len(normalized_request) < 4:
        return None, "none"
    for product, product_name, brand in candidates:
        candidate_values = [value for value in (product_name, brand) if value]
        if any(
            normalized_request in value or value in normalized_request
            for value in candidate_values
        ):
            return product, "partial"

    return None, "none"


def _task_metadata(
    *,
    snapshot: SnapshotLoadResult,
    target_selection: TargetSelection,
    data_source_mode: DataSourceMode,
    research_text_redacted: bool,
) -> dict:
    metadata = {
        "snapshot_version": snapshot.snapshot_version,
        "default_target_sku_id": snapshot.default_target_sku_id,
        "selected_target_sku_id": target_selection.sku_id,
        "target_selection": target_selection.selection,
        "target_selection_basis": target_selection.match_basis,
        "target_match_confidence": target_selection.match_confidence,
        "snapshot_source_path": _safe_snapshot_path(snapshot.source_path),
    }
    if target_selection.selection == "user_input_unmatched":
        metadata["target_selection_note"] = (
            "No local snapshot SKU matched the user input; downstream analysis uses a "
            "user-provided target with missing evidence."
        )
    if data_source_mode == DataSourceMode.SNAPSHOT_PLUS_LIVE:
        metadata["snapshot_plus_live_note"] = (
            "Stage 1 known URL enhancement is enabled. The system attempts public pages "
            "from task input and local snapshot source URLs, then degrades to local snapshot "
            "when policy, fetch, or parsing fails."
        )
        metadata["public_page_enhancement_stage"] = "stage_1_known_url"
        metadata["competitor_discovery_enabled"] = False
    if research_text_redacted:
        metadata["research_text_redacted"] = True
    return metadata


def _safe_snapshot_path(path: str) -> str:
    snapshot_path = Path(path)
    try:
        return snapshot_path.relative_to(Path(__file__).resolve().parents[3]).as_posix()
    except ValueError:
        return snapshot_path.name


def _sanitize_research_text(research_text: str | None) -> str | None:
    if research_text is None:
        return None
    return redact_sensitive_text(research_text)


def _normalize_url(value: str | None) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return text.rstrip("/").lower()


def _normalize_name(value: str | None) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return "".join(text.lower().split())


def _non_empty_text(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
