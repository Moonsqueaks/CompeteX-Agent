from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple
from uuid import uuid4

from app.schemas import (
    AnalysisTask,
    CandidateStrategy,
    DataSourceMode,
    EvidenceSourceMode,
    Product,
    TaskCreateRequest,
    TaskCreateResponse,
)
from app.security import redact_sensitive_text
from app.services.candidate_pool import (
    CandidatePoolError,
    CandidatePoolResult,
    load_builtin_candidate_pool,
)
from app.services.domain_profiles import (
    INTERNET_AI_ASSISTANT_DOMAIN,
    DomainProfile,
    DomainProfileError,
    get_domain_profile,
    infer_domain_key,
    profile_payload,
)
from app.services.internet_product_snapshot_loader import (
    InternetProductSnapshotLoaderError,
    InternetProductSnapshotLoadResult,
    load_internet_product_snapshot,
)
from app.services.snapshot_loader import SnapshotLoaderError, SnapshotLoadResult, load_demo_snapshot
from app.storage.repositories import TaskRepository

SnapshotResult = SnapshotLoadResult | InternetProductSnapshotLoadResult


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
        profile = self._resolve_domain_profile(payload)
        snapshot = self._load_snapshot(profile)
        candidate_pool_result = self._load_candidate_pool(profile, payload)
        target_selection = (
            _resolve_target_selection_from_candidate_pool(
                snapshot=snapshot,
                candidate_pool_result=candidate_pool_result,
                payload=payload,
            )
            if candidate_pool_result is not None
            else _resolve_target_selection(snapshot, payload)
        )
        now = datetime.now(UTC)
        research_text = _sanitize_research_text(payload.research_text)

        task = AnalysisTask(
            task_id=f"task_{uuid4().hex}",
            target_product_name=(
                (target_selection.product.name if target_selection.product else None)
                or (candidate_pool_result.selected_target_name if candidate_pool_result else None)
                or payload.target_product_name
                or "User provided target product"
            ),
            target_product_url=(
                (target_selection.product.product_url if target_selection.product else None)
                or (candidate_pool_result.selected_target_url if candidate_pool_result else None)
                or payload.target_product_url
            ),
            category=payload.category or snapshot.category,
            subcategory=payload.subcategory or snapshot.subcategory,
            data_source_mode=payload.data_source_mode,
            evidence_source_mode=payload.evidence_source_mode,
            candidate_strategy=payload.candidate_strategy,
            status="created",
            research_text=research_text,
            metadata=_task_metadata(
                profile=profile,
                snapshot=snapshot,
                target_selection=target_selection,
                data_source_mode=payload.data_source_mode,
                evidence_source_mode=payload.evidence_source_mode,
                candidate_strategy=payload.candidate_strategy,
                research_text_redacted=research_text != payload.research_text,
                candidate_pool_result=candidate_pool_result,
            ),
            created_at=now,
            updated_at=now,
        )
        created = self.task_repository.create(task)
        return TaskCreateResponse(task_id=created.task_id, status=created.status, task=created)

    def _resolve_domain_profile(self, payload: TaskCreateRequest) -> DomainProfile:
        domain_key = infer_domain_key(
            payload.category,
            payload.subcategory,
            payload.target_product_url,
            payload.target_product_name,
        )
        try:
            return get_domain_profile(domain_key)
        except DomainProfileError as exc:
            raise TaskCreationError(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ) from exc

    def _load_snapshot(self, profile: DomainProfile) -> SnapshotResult:
        try:
            if profile.domain_key == INTERNET_AI_ASSISTANT_DOMAIN:
                return load_internet_product_snapshot(
                    task_id="task_creation_preview",
                    snapshot_path=profile.snapshot_path,
                )
            return load_demo_snapshot(
                task_id="task_creation_preview",
                snapshot_path=profile.snapshot_path,
            )
        except (SnapshotLoaderError, InternetProductSnapshotLoaderError) as exc:
            raise TaskCreationError(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ) from exc

    def _load_candidate_pool(
        self,
        profile: DomainProfile,
        payload: TaskCreateRequest,
    ) -> CandidatePoolResult | None:
        if payload.candidate_strategy != CandidateStrategy.BUILTIN_CANDIDATES:
            return None
        try:
            return load_builtin_candidate_pool(
                domain_key=profile.domain_key,
                target_product_url=payload.target_product_url,
                target_product_name=payload.target_product_name,
            )
        except CandidatePoolError as exc:
            raise TaskCreationError(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ) from exc


class TargetSelection(NamedTuple):
    product: Product | None
    sku_id: str | None
    product_id: str | None
    selection: str
    match_basis: str | None
    match_confidence: str


def _default_target_product(snapshot: SnapshotResult):
    default_target_id = _default_target_id(snapshot)
    for product in snapshot.products:
        if product.sku_id == default_target_id or product.product_id == default_target_id:
            return product
    raise TaskCreationError(
        code="DEFAULT_TARGET_NOT_FOUND",
        message="Default target product was not found in the snapshot.",
        details={"default_target_id": default_target_id},
    )


def _resolve_target_selection(
    snapshot: SnapshotResult,
    payload: TaskCreateRequest,
) -> TargetSelection:
    default_target = _default_target_product(snapshot)
    requested_name = _non_empty_text(payload.target_product_name)
    requested_url = _non_empty_text(payload.target_product_url)

    if requested_name is None and requested_url is None:
        return TargetSelection(
            product=default_target,
            sku_id=default_target.sku_id,
            product_id=default_target.product_id,
            selection="demo_default_target",
            match_basis="snapshot.default_target_id",
            match_confidence="exact",
        )

    url_match = _match_product_by_url(snapshot.products, requested_url)
    if url_match is not None:
        return TargetSelection(
            product=url_match,
            sku_id=url_match.sku_id,
            product_id=url_match.product_id,
            selection="matched_snapshot_sku",
            match_basis="target_product_url",
            match_confidence="exact",
        )

    name_match, match_confidence = _match_product_by_name(snapshot.products, requested_name)
    if name_match is not None:
        return TargetSelection(
            product=name_match,
            sku_id=name_match.sku_id,
            product_id=name_match.product_id,
            selection="matched_snapshot_sku",
            match_basis="target_product_name",
            match_confidence=match_confidence,
        )

    return TargetSelection(
        product=None,
        sku_id=None,
        product_id=None,
        selection="user_input_unmatched",
        match_basis=None,
        match_confidence="none",
    )


def _resolve_target_selection_from_candidate_pool(
    *,
    snapshot: SnapshotResult,
    candidate_pool_result: CandidatePoolResult,
    payload: TaskCreateRequest,
) -> TargetSelection:
    if candidate_pool_result.selected_target_id is None:
        return TargetSelection(
            product=None,
            sku_id=None,
            product_id=None,
            selection="user_input_unmatched",
            match_basis=candidate_pool_result.target_match_basis,
            match_confidence=candidate_pool_result.target_match_confidence,
        )

    matched_product = _product_by_candidate_pool_result(snapshot, candidate_pool_result)
    if matched_product is None:
        return _resolve_target_selection(snapshot, payload)
    return TargetSelection(
        product=matched_product,
        sku_id=matched_product.sku_id,
        product_id=matched_product.product_id,
        selection="matched_candidate_pool",
        match_basis=candidate_pool_result.target_match_basis,
        match_confidence=candidate_pool_result.target_match_confidence,
    )


def _product_by_candidate_pool_result(
    snapshot: SnapshotResult,
    candidate_pool_result: CandidatePoolResult,
) -> Product | None:
    for product in snapshot.products:
        if product.product_id == candidate_pool_result.selected_target_id:
            return product
        if product.sku_id and product.sku_id == candidate_pool_result.selected_target_sku_id:
            return product
    return None


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
        (
            product,
            _normalize_name(product.name),
            _normalize_name(product.brand),
            _normalize_name(product.product_id),
        )
        for product in products
    ]
    for product, product_name, brand, product_id in candidates:
        if normalized_request in {
            product_name,
            brand,
            product_id,
            _normalize_name(product.sku_id),
        }:
            return product, "exact"

    if len(normalized_request) < 4:
        return None, "none"
    for product, product_name, brand, product_id in candidates:
        candidate_values = [value for value in (product_name, brand, product_id) if value]
        if any(
            normalized_request in value or value in normalized_request
            for value in candidate_values
        ):
            return product, "partial"

    return None, "none"


def _task_metadata(
    *,
    profile: DomainProfile,
    snapshot: SnapshotResult,
    target_selection: TargetSelection,
    data_source_mode: DataSourceMode,
    evidence_source_mode: EvidenceSourceMode,
    candidate_strategy: CandidateStrategy,
    research_text_redacted: bool,
    candidate_pool_result: CandidatePoolResult | None,
) -> dict:
    metadata = {
        "domain_key": profile.domain_key,
        "domain_profile": profile_payload(profile),
        "snapshot_version": snapshot.snapshot_version,
        "default_target_id": _default_target_id(snapshot),
        "default_target_sku_id": getattr(snapshot, "default_target_sku_id", None),
        "default_target_product_id": getattr(snapshot, "default_target_product_id", None),
        "selected_target_product_id": target_selection.product_id,
        "selected_target_sku_id": target_selection.sku_id,
        "target_selection": target_selection.selection,
        "target_selection_basis": target_selection.match_basis,
        "target_match_confidence": target_selection.match_confidence,
        "data_source_mode": data_source_mode.value,
        "evidence_source_mode": evidence_source_mode.value,
        "candidate_strategy": candidate_strategy.value,
        "snapshot_source_path": _safe_snapshot_path(snapshot.source_path),
    }
    if target_selection.selection == "user_input_unmatched":
        metadata["target_selection_note"] = (
            "No local snapshot SKU matched the user input; downstream analysis uses a "
            "user-provided target with missing evidence."
        )
    if evidence_source_mode == EvidenceSourceMode.SNAPSHOT_PLUS_KNOWN_PUBLIC_PAGE:
        metadata["snapshot_plus_live_note"] = (
            "Stage 1 known URL enhancement is enabled. The system attempts public pages "
            "from task input and local snapshot source URLs, then degrades to local snapshot "
            "when policy, fetch, or parsing fails."
        )
        metadata["public_page_enhancement_stage"] = "stage_1_known_url"
        metadata["competitor_discovery_enabled"] = False
    if candidate_pool_result is not None:
        metadata.update(candidate_pool_result.metadata())
        metadata["candidate_strategy"] = candidate_strategy.value
        metadata["competitor_discovery_enabled"] = False
    if research_text_redacted:
        metadata["research_text_redacted"] = True
    return metadata


def _default_target_id(snapshot: SnapshotResult) -> str:
    default_sku_id = getattr(snapshot, "default_target_sku_id", None)
    if isinstance(default_sku_id, str) and default_sku_id.strip():
        return default_sku_id
    return snapshot.default_target_product_id


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
