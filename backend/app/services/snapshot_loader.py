import json
from datetime import UTC, datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any
from urllib.parse import quote

from pydantic import Field, ValidationError

from app.schemas import (
    ConfidenceLevel,
    Evidence,
    EvidenceSourceType,
    Product,
    ProductImageStatus,
    ProductRole,
    ReviewInsight,
)
from app.schemas.common import JsonObject, StrictBaseModel
from app.services.product_image_metadata import product_main_image_url

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SNAPSHOT_PATH = PROJECT_ROOT / "data" / "snapshots" / "demo_sku_snapshot.json"
RAW_ASSET_DIR = PROJECT_ROOT / "data" / "raw"
RAW_ASSET_URL_PREFIX = "/assets/raw"
REMOTE_IMAGE_FIELDS = (
    "primary_image_url",
    "main_image_url",
    "image_url",
    "image",
    "thumbnail_url",
)
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

REQUIRED_TOP_LEVEL_FIELDS = {
    "snapshot_version",
    "category",
    "subcategory",
    "default_target_sku_id",
    "qa_revision_fixture",
    "skus",
}
REQUIRED_SKU_FIELDS = {
    "sku_id",
    "product_id",
    "role",
    "name",
    "brand",
    "product_type",
    "price",
    "selling_points",
    "review_summary",
    "source",
}
REQUIRED_PRICE_FIELDS = {
    "currency",
    "display_price_yuan",
    "min_price_yuan",
    "max_price_yuan",
    "price_band",
    "price_note",
}
REQUIRED_SOURCE_FIELDS = {
    "platform",
    "source_url",
    "raw_dir",
    "screenshot_path",
    "access_time",
    "source_description",
    "limitations",
}
NULLABLE_EVIDENCE_FIELDS = {
    "source.access_time": ("source", "access_time"),
    "source.screenshot_path": ("source", "screenshot_path"),
}


class SnapshotLoaderError(Exception):
    def __init__(self, code: str, message: str, details: JsonObject | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class SnapshotLoadResult(StrictBaseModel):
    snapshot_version: str = Field(min_length=1)
    category: str = Field(min_length=1)
    subcategory: str = Field(min_length=1)
    default_target_sku_id: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    products: list[Product]
    evidences: list[Evidence]
    review_insights: list[ReviewInsight]
    qa_revision_fixture: JsonObject = Field(default_factory=dict)


def load_demo_snapshot(
    task_id: str,
    snapshot_path: Path | str | None = None,
    created_at: datetime | None = None,
    link_metadata_path: Path | str | None = None,
    target_sku_id: str | None = None,
    target_product_name: str | None = None,
    target_product_url: str | None = None,
) -> SnapshotLoadResult:
    path = Path(snapshot_path) if snapshot_path is not None else DEFAULT_SNAPSHOT_PATH
    loaded_at = created_at or datetime.now(UTC)
    snapshot = _read_snapshot(path)
    _validate_snapshot_contract(snapshot, path)
    selected_target_sku_id = _selected_target_sku_id(snapshot, target_sku_id, path)
    synthetic_target = _synthetic_target_product_payload(
        snapshot=snapshot,
        task_id=task_id,
        created_at=loaded_at,
        target_sku_id=selected_target_sku_id,
        target_product_name=target_product_name,
        target_product_url=target_product_url,
    )

    try:
        products = [
            _sku_to_product(
                sku=sku,
                snapshot=snapshot,
                task_id=task_id,
                created_at=loaded_at,
                link_metadata_path=link_metadata_path,
                selected_target_sku_id=selected_target_sku_id,
                has_synthetic_target=synthetic_target is not None,
            )
            for sku in snapshot["skus"]
        ]
        if synthetic_target is not None:
            products.append(synthetic_target)
        evidences = [_sku_to_evidence(sku=sku, task_id=task_id) for sku in snapshot["skus"]]
        synthetic_evidence = _synthetic_target_evidence_payload(
            synthetic_target=synthetic_target,
            task_id=task_id,
            target_product_url=target_product_url,
            access_time=loaded_at,
        )
        if synthetic_evidence is not None:
            evidences.append(synthetic_evidence)
        review_insights = [
            _sku_to_review_insight(sku=sku, task_id=task_id, created_at=loaded_at)
            for sku in snapshot["skus"]
        ]
        return SnapshotLoadResult.model_validate(
            {
                "snapshot_version": snapshot["snapshot_version"],
                "category": snapshot["category"],
                "subcategory": snapshot["subcategory"],
                "default_target_sku_id": snapshot["default_target_sku_id"],
                "source_path": str(path),
                "products": products,
                "evidences": evidences,
                "review_insights": review_insights,
                "qa_revision_fixture": snapshot["qa_revision_fixture"],
            }
        )
    except ValidationError as exc:
        raise SnapshotLoaderError(
            code="SNAPSHOT_SCHEMA_VALIDATION_FAILED",
            message="Snapshot content could not be converted into project schemas.",
            details={"path": str(path), "validation_error": str(exc)},
        ) from exc


def _read_snapshot(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SnapshotLoaderError(
            code="SNAPSHOT_NOT_FOUND",
            message="Snapshot file does not exist.",
            details={"path": str(path)},
        )

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise SnapshotLoaderError(
            code="SNAPSHOT_INVALID_JSON",
            message="Snapshot file is not valid JSON.",
            details={"path": str(path), "line": exc.lineno, "column": exc.colno},
        ) from exc

    if not isinstance(payload, dict):
        raise SnapshotLoaderError(
            code="SNAPSHOT_CONTRACT_INVALID",
            message="Snapshot root must be a JSON object.",
            details={"path": str(path), "field": "$"},
        )
    return payload


def _validate_snapshot_contract(snapshot: dict[str, Any], path: Path) -> None:
    _require_fields(snapshot, REQUIRED_TOP_LEVEL_FIELDS, str(path), "$")
    if not isinstance(snapshot["skus"], list) or not snapshot["skus"]:
        raise SnapshotLoaderError(
            code="SNAPSHOT_CONTRACT_INVALID",
            message="Snapshot must contain a non-empty skus list.",
            details={"path": str(path), "field": "skus"},
        )

    sku_ids = set()
    for index, sku in enumerate(snapshot["skus"]):
        field_path = f"skus[{index}]"
        if not isinstance(sku, dict):
            raise SnapshotLoaderError(
                code="SNAPSHOT_CONTRACT_INVALID",
                message="Each SKU item must be a JSON object.",
                details={"path": str(path), "field": field_path},
            )
        _require_fields(sku, REQUIRED_SKU_FIELDS, str(path), field_path)
        _require_fields(sku["price"], REQUIRED_PRICE_FIELDS, str(path), f"{field_path}.price")
        _require_fields(sku["source"], REQUIRED_SOURCE_FIELDS, str(path), f"{field_path}.source")
        sku_ids.add(sku["sku_id"])

    if snapshot["default_target_sku_id"] not in sku_ids:
        raise SnapshotLoaderError(
            code="SNAPSHOT_CONTRACT_INVALID",
            message="Default target SKU is not present in skus.",
            details={
                "path": str(path),
                "field": "default_target_sku_id",
                "value": snapshot["default_target_sku_id"],
            },
        )


def _require_fields(
    value: Any,
    required_fields: set[str],
    path: str,
    field_path: str,
) -> None:
    if not isinstance(value, dict):
        raise SnapshotLoaderError(
            code="SNAPSHOT_CONTRACT_INVALID",
            message="Snapshot field must be a JSON object.",
            details={"path": path, "field": field_path},
        )

    missing = sorted(required_fields - set(value))
    if missing:
        raise SnapshotLoaderError(
            code="SNAPSHOT_CONTRACT_INVALID",
            message="Snapshot is missing required fields.",
            details={"path": path, "field": field_path, "missing_fields": missing},
        )


def _sku_to_product(
    sku: dict[str, Any],
    snapshot: dict[str, Any],
    task_id: str,
    created_at: datetime,
    link_metadata_path: Path | str | None = None,
    selected_target_sku_id: str | None = None,
    has_synthetic_target: bool = False,
) -> Product:
    primary_image = _derive_primary_image(sku, link_metadata_path=link_metadata_path)
    return Product.model_validate(
        {
            "product_id": sku["product_id"],
            "task_id": task_id,
            "sku_id": sku["sku_id"],
            "name": sku["name"],
            "brand": sku["brand"],
            "category": snapshot["category"],
            "subcategory": snapshot["subcategory"],
            "role": _role_for_sku(
                sku=sku,
                selected_target_sku_id=selected_target_sku_id,
                has_synthetic_target=has_synthetic_target,
            ),
            "product_url": sku["source"]["source_url"],
            "primary_image_path": primary_image["url"],
            "primary_image_url": primary_image["url"],
            "primary_image_source_path": primary_image["source_path"],
            "primary_image_status": primary_image["status"],
            "evidence_ids": [_evidence_id(sku)],
            "tags": _compact_strings(
                sku["product_type"],
                sku["price"]["price_band"],
                sku["role"],
            ),
            "created_at": created_at,
        }
    )


def _selected_target_sku_id(
    snapshot: dict[str, Any],
    target_sku_id: str | None,
    path: Path,
) -> str | None:
    sku_id = _non_empty_str(target_sku_id)
    if sku_id is None:
        return None

    if any(sku.get("sku_id") == sku_id for sku in snapshot["skus"]):
        return sku_id

    raise SnapshotLoaderError(
        code="TARGET_SKU_NOT_FOUND",
        message="Requested target SKU is not present in the demo snapshot.",
        details={"path": str(path), "target_sku_id": sku_id},
    )


def _role_for_sku(
    *,
    sku: dict[str, Any],
    selected_target_sku_id: str | None,
    has_synthetic_target: bool,
) -> str:
    sku_id = sku["sku_id"]
    original_role = sku["role"]
    if selected_target_sku_id is not None:
        if sku_id == selected_target_sku_id:
            return ProductRole.TARGET.value
        if original_role == ProductRole.TARGET.value:
            return ProductRole.DIRECT_COMPETITOR.value
    elif has_synthetic_target and original_role == ProductRole.TARGET.value:
        return ProductRole.DIRECT_COMPETITOR.value
    return original_role


def _synthetic_target_product_payload(
    *,
    snapshot: dict[str, Any],
    task_id: str,
    created_at: datetime,
    target_sku_id: str | None,
    target_product_name: str | None,
    target_product_url: str | None,
) -> Product | None:
    if target_sku_id is not None:
        return None

    name = _non_empty_str(target_product_name)
    url = _non_empty_str(target_product_url)
    if name is None and url is None:
        return None

    return Product(
        product_id=f"prod_{task_id}_user_target",
        task_id=task_id,
        sku_id=None,
        name=name or "User provided target product",
        brand=None,
        category=snapshot["category"],
        subcategory=snapshot["subcategory"],
        role=ProductRole.TARGET,
        product_url=url,
        primary_image_path=None,
        primary_image_url=None,
        primary_image_source_path=None,
        primary_image_status=ProductImageStatus.MISSING,
        evidence_ids=[f"ev_{task_id}_user_target_input"],
        tags=[
            "user_input_target",
            snapshot["subcategory"],
            ProductRole.TARGET.value,
        ],
        created_at=created_at,
    )


def _synthetic_target_evidence_payload(
    *,
    synthetic_target: Product | None,
    task_id: str,
    target_product_url: str | None,
    access_time: datetime,
) -> Evidence | None:
    if synthetic_target is None:
        return None

    return Evidence(
        evidence_id=f"ev_{task_id}_user_target_input",
        task_id=task_id,
        product_id=synthetic_target.product_id,
        source_type=EvidenceSourceType.USER_RESEARCH,
        source_url=_non_empty_str(target_product_url),
        screenshot_path=None,
        access_time=access_time,
        content_summary=(
            "Task input identified this product as the analysis target, but no matching "
            "local SKU snapshot was found."
        ),
        confidence_level=ConfidenceLevel.LOW,
        limitations=(
            "This evidence only records the user-provided target identity. It does not "
            "support price, sales, certification, feature, or ranking claims."
        ),
        metadata={
            "source": "task.target_product_input",
            "target_selection": "user_input_unmatched",
            "missing_fields": ["snapshot.sku_match"],
        },
    )


def _derive_primary_image(
    sku: dict[str, Any],
    *,
    link_metadata_path: Path | str | None = None,
) -> dict[str, str | ProductImageStatus | None]:
    source = sku["source"]
    metadata_image_url = product_main_image_url(
        sku_id=_non_empty_str(sku.get("sku_id")),
        product_id=_non_empty_str(sku.get("product_id")),
        metadata_path=link_metadata_path,
    )
    if metadata_image_url is not None:
        return {
            "url": metadata_image_url,
            "source_path": metadata_image_url,
            "status": ProductImageStatus.AVAILABLE,
        }

    remote_image_url = _first_remote_image_url(sku, source)
    if remote_image_url is not None:
        return {
            "url": remote_image_url,
            "source_path": remote_image_url,
            "status": ProductImageStatus.AVAILABLE,
        }

    screenshot_path = _non_empty_str(source.get("screenshot_path"))
    screenshot_url = _local_raw_asset_url(screenshot_path)
    if screenshot_url is not None:
        return {
            "url": screenshot_url,
            "source_path": screenshot_path,
            "status": ProductImageStatus.AVAILABLE,
        }

    raw_dir_image_path = _first_raw_dir_image_path(source.get("raw_dir"))
    raw_dir_image_url = _local_raw_asset_url(raw_dir_image_path)
    if raw_dir_image_url is not None:
        return {
            "url": raw_dir_image_url,
            "source_path": _project_relative_path(raw_dir_image_path),
            "status": ProductImageStatus.AVAILABLE,
        }

    return {
        "url": None,
        "source_path": None,
        "status": ProductImageStatus.MISSING,
    }


def _first_remote_image_url(*containers: dict[str, Any]) -> str | None:
    for container in containers:
        for field_name in REMOTE_IMAGE_FIELDS:
            value = _non_empty_str(container.get(field_name))
            if value is not None and value.startswith(("http://", "https://")):
                return value
    return None


def _local_raw_asset_url(path_value: Any) -> str | None:
    path = _resolve_project_path(path_value)
    if path is None or path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        return None
    try:
        raw_relative_path = path.relative_to(RAW_ASSET_DIR.resolve())
    except ValueError:
        return None
    if not path.exists() or not path.is_file():
        return None
    encoded_path = quote(raw_relative_path.as_posix(), safe="/")
    return f"{RAW_ASSET_URL_PREFIX}/{encoded_path}"


def _first_raw_dir_image_path(path_value: Any) -> Path | None:
    raw_dir = _resolve_project_path(path_value)
    if raw_dir is None or not raw_dir.exists() or not raw_dir.is_dir():
        return None

    for path in sorted(raw_dir.iterdir(), key=lambda item: item.name.lower()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            return path
    return None


def _resolve_project_path(path_value: Any) -> Path | None:
    value = _non_empty_str(path_value)
    if value is None:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def _project_relative_path(path_value: Any) -> str | None:
    path = _resolve_project_path(path_value)
    if path is None:
        return None
    try:
        return path.relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return None


def _sku_to_evidence(sku: dict[str, Any], task_id: str) -> Evidence:
    source = sku["source"]
    return Evidence.model_validate(
        {
            "evidence_id": _evidence_id(sku),
            "task_id": task_id,
            "product_id": sku["product_id"],
            "source_type": EvidenceSourceType.DOUYIN_SKU_SNAPSHOT,
            "source_url": source["source_url"],
            "screenshot_path": source["screenshot_path"],
            "access_time": source["access_time"],
            "content_summary": _content_summary(sku),
            "confidence_level": ConfidenceLevel.MEDIUM,
            "limitations": source["limitations"],
            "metadata": {
                "sku_id": sku["sku_id"],
                "role": sku["role"],
                "product_type": sku["product_type"],
                "price": sku["price"],
                "platform": source["platform"],
                "raw_dir": source["raw_dir"],
                "source_description": source["source_description"],
                "sales": source.get("sales"),
                "missing_fields": _missing_evidence_fields(sku),
            },
        }
    )


def _sku_to_review_insight(
    sku: dict[str, Any],
    task_id: str,
    created_at: datetime,
) -> ReviewInsight:
    source = sku["source"]
    return ReviewInsight.model_validate(
        {
            "review_insight_id": f"ri_{sku['sku_id']}",
            "task_id": task_id,
            "product_id": sku["product_id"],
            "sku_id": sku["sku_id"],
            "summary": sku["review_summary"],
            "evidence_ids": [_evidence_id(sku)],
            "confidence_level": ConfidenceLevel.MEDIUM,
            "market_signals": {
                "sales": source.get("sales"),
                "price_band": sku["price"]["price_band"],
                "source": "demo_sku_snapshot.review_summary",
            },
            "limitations": (
                f"{source['limitations']}；评论洞察来自本地快照摘要，尚未执行独立评论聚类。"
            ),
            "risk_flags": [],
            "created_at": created_at,
        }
    )


def _content_summary(sku: dict[str, Any]) -> str:
    selling_points = "、".join(sku["selling_points"])
    price = sku["price"]["display_price_yuan"]
    return (
        f"{sku['name']} 本地快照：到手价约 {price} CNY；"
        f"核心卖点：{selling_points}；评论摘要：{sku['review_summary']}"
    )


def _missing_evidence_fields(sku: dict[str, Any]) -> list[str]:
    missing_fields = []
    for public_name, path_parts in NULLABLE_EVIDENCE_FIELDS.items():
        current: Any = sku
        for part in path_parts:
            current = current[part]
        if current is None:
            missing_fields.append(public_name)
    return missing_fields


def _evidence_id(sku: dict[str, Any]) -> str:
    return f"ev_{sku['sku_id']}"


def _compact_strings(*values: Any) -> list[str]:
    return [value for value in values if isinstance(value, str) and value.strip()]


def _non_empty_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
