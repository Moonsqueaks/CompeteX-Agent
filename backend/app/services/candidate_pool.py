import json
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from app.schemas.common import JsonObject
from app.services.domain_profiles import (
    DomainProfile,
    DomainProfileError,
    get_domain_profile,
)


@dataclass(frozen=True)
class CandidatePoolItem:
    product_id: str
    sku_id: str | None
    name: str
    role: str
    urls: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class CandidatePoolResult:
    domain_key: str
    pool_id: str
    pool_path: str
    pool_display_name: str
    source_description: str
    load_message: str
    gap_hint: str
    selected_target_id: str | None
    selected_target_sku_id: str | None
    selected_target_name: str | None
    selected_target_url: str | None
    target_match_basis: str
    target_match_confidence: str
    target_status: str
    candidate_count: int
    selected_for_analysis_count: int
    candidate_items: tuple[CandidatePoolItem, ...]

    def metadata(self) -> JsonObject:
        return {
            "candidate_discovery_mode": "builtin_candidates",
            "candidate_pool_id": self.pool_id,
            "candidate_pool_path": self.pool_path,
            "candidate_pool_name": self.pool_display_name,
            "candidate_pool_source": self.source_description,
            "candidate_pool_load_message": self.load_message,
            "candidate_gap_hint": self.gap_hint,
            "target_match_basis": self.target_match_basis,
            "target_match_confidence": self.target_match_confidence,
            "target_status": self.target_status,
            "candidate_count": self.candidate_count,
            "selected_for_analysis_count": self.selected_for_analysis_count,
            "selected_target_id": self.selected_target_id,
            "selected_target_sku_id": self.selected_target_sku_id,
            "candidate_pool_loaded": True,
            "candidate_source_type": "builtin_candidate_pool",
            "candidates": [
                {
                    "product_id": item.product_id,
                    "sku_id": item.sku_id,
                    "name": item.name,
                    "role": item.role,
                    "status": item.status,
                }
                for item in self.candidate_items
            ],
        }


class CandidatePoolError(Exception):
    def __init__(self, code: str, message: str, details: JsonObject | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def load_builtin_candidate_pool(
    *,
    domain_key: str,
    target_product_url: str | None = None,
    target_product_name: str | None = None,
) -> CandidatePoolResult:
    try:
        profile = get_domain_profile(domain_key)
    except DomainProfileError as exc:
        raise CandidatePoolError(exc.code, exc.message, exc.details) from exc

    payload = _read_candidate_snapshot(profile.candidate_pool.snapshot_path)
    items = _candidate_items(payload)
    if not items:
        raise CandidatePoolError(
            code="CANDIDATE_POOL_EMPTY",
            message="Candidate pool snapshot does not contain products.",
            details={"snapshot_path": _safe_path(profile.candidate_pool.snapshot_path)},
        )

    matched_item, basis, confidence = _match_target(
        items=items,
        profile=profile,
        target_product_url=target_product_url,
        target_product_name=target_product_name,
    )
    target_status = "target_matched" if matched_item is not None else "target_unmatched"
    candidate_items = _with_candidate_statuses(items, matched_item)
    candidate_count = (
        max(0, len(items) - 1) if matched_item is not None else len(items)
    )
    return CandidatePoolResult(
        domain_key=profile.domain_key,
        pool_id=profile.candidate_pool.pool_id,
        pool_path=_safe_path(profile.candidate_pool.snapshot_path),
        pool_display_name=profile.candidate_pool.display_name,
        source_description=profile.candidate_pool.source_description,
        load_message=profile.candidate_pool.load_message,
        gap_hint=profile.candidate_pool.gap_hint,
        selected_target_id=matched_item.product_id if matched_item else None,
        selected_target_sku_id=matched_item.sku_id if matched_item else None,
        selected_target_name=matched_item.name if matched_item else None,
        selected_target_url=_first_url(matched_item) if matched_item else None,
        target_match_basis=basis,
        target_match_confidence=confidence,
        target_status=target_status,
        candidate_count=candidate_count,
        selected_for_analysis_count=candidate_count,
        candidate_items=tuple(candidate_items),
    )


def _read_candidate_snapshot(path: Path) -> JsonObject:
    if not path.exists():
        raise CandidatePoolError(
            code="CANDIDATE_POOL_NOT_FOUND",
            message="Candidate pool snapshot file does not exist.",
            details={"snapshot_path": _safe_path(path)},
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise CandidatePoolError(
            code="CANDIDATE_POOL_INVALID_JSON",
            message="Candidate pool snapshot file is not valid JSON.",
            details={"snapshot_path": _safe_path(path), "line": exc.lineno, "column": exc.colno},
        ) from exc
    if not isinstance(payload, dict):
        raise CandidatePoolError(
            code="CANDIDATE_POOL_INVALID",
            message="Candidate pool snapshot root must be a JSON object.",
            details={"snapshot_path": _safe_path(path)},
        )
    return payload


def _candidate_items(snapshot: JsonObject) -> list[CandidatePoolItem]:
    if isinstance(snapshot.get("skus"), list):
        return [_sku_candidate_item(item) for item in snapshot["skus"] if isinstance(item, dict)]
    if isinstance(snapshot.get("products"), list):
        return [
            _internet_candidate_item(item)
            for item in snapshot["products"]
            if isinstance(item, dict)
        ]
    return []


def _sku_candidate_item(item: JsonObject) -> CandidatePoolItem:
    source = item.get("source") if isinstance(item.get("source"), dict) else {}
    source_url = _non_empty_text(source.get("source_url"))
    return CandidatePoolItem(
        product_id=str(item.get("product_id") or item.get("sku_id")),
        sku_id=_non_empty_text(item.get("sku_id")),
        name=str(item.get("name") or item.get("product_id") or item.get("sku_id")),
        role=str(item.get("role") or "candidate_loaded"),
        urls=tuple(_dedupe([source_url])),
        status="candidate_loaded",
    )


def _internet_candidate_item(item: JsonObject) -> CandidatePoolItem:
    urls: list[str | None] = []
    if isinstance(item.get("official_urls"), list):
        urls.extend(url for url in item["official_urls"] if isinstance(url, str))
    source = item.get("source") if isinstance(item.get("source"), dict) else {}
    urls.append(_non_empty_text(source.get("source_url")))
    return CandidatePoolItem(
        product_id=str(item.get("product_id") or item.get("sku_id")),
        sku_id=_non_empty_text(item.get("sku_id")),
        name=str(item.get("name") or item.get("product_id") or item.get("sku_id")),
        role=str(item.get("role") or "candidate_loaded"),
        urls=tuple(_dedupe(urls)),
        status="candidate_loaded",
    )


def _match_target(
    *,
    items: list[CandidatePoolItem],
    profile: DomainProfile,
    target_product_url: str | None,
    target_product_name: str | None,
) -> tuple[CandidatePoolItem | None, str, str]:
    requested_url = _normalize_url(target_product_url)
    has_request = requested_url is not None or _normalize_name(target_product_name) is not None
    if requested_url is not None:
        for item in items:
            if requested_url in {_normalize_url(url) for url in item.urls}:
                return item, "target_product_url", "exact"

    requested_name = _normalize_name(target_product_name)
    if requested_name is not None:
        for item in items:
            if requested_name in {
                _normalize_name(item.name),
                _normalize_name(item.product_id),
                _normalize_name(item.sku_id),
            }:
                return item, "target_product_name", "exact"
        if len(requested_name) >= 4:
            for item in items:
                item_name = _normalize_name(item.name)
                if item_name and (requested_name in item_name or item_name in requested_name):
                    return item, "target_product_name", "partial"

    if has_request:
        return None, "user_input_unmatched", "none"

    default_id = _normalize_name(profile.default_target_id)
    for item in items:
        if default_id in {_normalize_name(item.product_id), _normalize_name(item.sku_id)}:
            return item, "domain_profile.default_target_id", "default"
    return None, "user_input_unmatched", "none"


def _with_candidate_statuses(
    items: list[CandidatePoolItem],
    matched_item: CandidatePoolItem | None,
) -> list[CandidatePoolItem]:
    result = []
    for item in items:
        status = (
            "target_matched"
            if matched_item is not None and item.product_id == matched_item.product_id
            else "candidate_loaded"
        )
        result.append(
            CandidatePoolItem(
                product_id=item.product_id,
                sku_id=item.sku_id,
                name=item.name,
                role=item.role,
                urls=item.urls,
                status=status,
            )
        )
    return result


def _first_url(item: CandidatePoolItem | None) -> str | None:
    if item is None or not item.urls:
        return None
    return item.urls[0]


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


def _non_empty_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _dedupe(items: list[str | None]) -> list[str]:
    deduped = []
    for item in items:
        if isinstance(item, str) and item.strip() and item not in deduped:
            deduped.append(item)
    return deduped


def _safe_path(path: Path) -> str:
    try:
        from app.services.domain_profiles import PROJECT_ROOT

        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()
