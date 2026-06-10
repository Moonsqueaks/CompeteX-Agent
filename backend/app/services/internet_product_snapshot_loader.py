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
from app.services.domain_profiles import INTERNET_AI_ASSISTANT_PROFILE, PROJECT_ROOT

DEFAULT_INTERNET_PRODUCT_SNAPSHOT_PATH = INTERNET_AI_ASSISTANT_PROFILE.snapshot_path
RAW_ASSET_DIR = PROJECT_ROOT / "data" / "raw"
RAW_ASSET_URL_PREFIX = "/assets/raw"
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
SOURCE_TYPE_MAP = {
    "official_product_page": EvidenceSourceType.OFFICIAL_PRODUCT_PAGE,
    "official_help_doc": EvidenceSourceType.OFFICIAL_HELP_DOC,
    "app_store_page": EvidenceSourceType.APP_STORE_PAGE,
    "official_release_note": EvidenceSourceType.OFFICIAL_RELEASE_NOTE,
    "manual_review": EvidenceSourceType.MANUAL_REVIEW,
}


class InternetProductSnapshotLoaderError(Exception):
    def __init__(self, code: str, message: str, details: JsonObject | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class InternetProductSnapshotLoadResult(StrictBaseModel):
    snapshot_version: str = Field(min_length=1)
    domain_key: str = Field(min_length=1)
    category: str = Field(min_length=1)
    subcategory: str = Field(min_length=1)
    default_target_product_id: str = Field(min_length=1)
    source_path: str = Field(min_length=1)
    products: list[Product]
    evidences: list[Evidence]
    review_insights: list[ReviewInsight]
    qa_revision_fixture: JsonObject = Field(default_factory=dict)


def load_internet_product_snapshot(
    *,
    task_id: str,
    snapshot_path: Path | str | None = None,
    created_at: datetime | None = None,
    target_product_id: str | None = None,
    target_product_name: str | None = None,
    target_product_url: str | None = None,
) -> InternetProductSnapshotLoadResult:
    path = (
        Path(snapshot_path)
        if snapshot_path is not None
        else DEFAULT_INTERNET_PRODUCT_SNAPSHOT_PATH
    )
    loaded_at = created_at or datetime.now(UTC)
    snapshot = _read_snapshot(path)
    _validate_snapshot_contract(snapshot, path)
    selected_target_id = _selected_target_id(snapshot, target_product_id)
    synthetic_target = _synthetic_target_product(
        snapshot=snapshot,
        task_id=task_id,
        created_at=loaded_at,
        selected_target_id=selected_target_id,
        target_product_name=target_product_name,
        target_product_url=target_product_url,
    )

    try:
        products = [
            _product_payload_to_product(
                item=item,
                snapshot=snapshot,
                task_id=task_id,
                created_at=loaded_at,
                selected_target_id=selected_target_id,
                has_synthetic_target=synthetic_target is not None,
            )
            for item in snapshot["products"]
        ]
        if synthetic_target is not None:
            products.append(synthetic_target)
        evidences = [
            evidence
            for item in snapshot["products"]
            for evidence in _product_payload_to_evidences(item=item, task_id=task_id)
        ]
        synthetic_evidence = _synthetic_target_evidence(
            synthetic_target=synthetic_target,
            task_id=task_id,
            target_product_url=target_product_url,
            access_time=loaded_at,
        )
        if synthetic_evidence is not None:
            evidences.append(synthetic_evidence)
        review_insights = [
            _product_payload_to_review_insight(
                item=item,
                task_id=task_id,
                created_at=loaded_at,
            )
            for item in snapshot["products"]
        ]
        return InternetProductSnapshotLoadResult.model_validate(
            {
                "snapshot_version": snapshot["snapshot_version"],
                "domain_key": snapshot["domain_key"],
                "category": snapshot["category"],
                "subcategory": snapshot["subcategory"],
                "default_target_product_id": snapshot["default_target_product_id"],
                "source_path": str(path),
                "products": products,
                "evidences": evidences,
                "review_insights": review_insights,
                "qa_revision_fixture": snapshot["qa_revision_fixture"],
            }
        )
    except ValidationError as exc:
        raise InternetProductSnapshotLoaderError(
            code="INTERNET_SNAPSHOT_SCHEMA_VALIDATION_FAILED",
            message="Internet product snapshot content could not be converted.",
            details={"path": str(path), "validation_error": str(exc)},
        ) from exc


def _read_snapshot(path: Path) -> JsonObject:
    if not path.exists():
        raise InternetProductSnapshotLoaderError(
            code="INTERNET_SNAPSHOT_NOT_FOUND",
            message="Internet product snapshot file does not exist.",
            details={"path": str(path)},
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise InternetProductSnapshotLoaderError(
            code="INTERNET_SNAPSHOT_INVALID_JSON",
            message="Internet product snapshot file is not valid JSON.",
            details={"path": str(path), "line": exc.lineno, "column": exc.colno},
        ) from exc
    if not isinstance(payload, dict):
        raise InternetProductSnapshotLoaderError(
            code="INTERNET_SNAPSHOT_CONTRACT_INVALID",
            message="Internet product snapshot root must be a JSON object.",
            details={"path": str(path), "field": "$"},
        )
    return payload


def _validate_snapshot_contract(snapshot: JsonObject, path: Path) -> None:
    required = {
        "snapshot_version",
        "domain_key",
        "category",
        "subcategory",
        "default_target_product_id",
        "qa_revision_fixture",
        "products",
    }
    _require_fields(snapshot, required, str(path), "$")
    if snapshot["domain_key"] != "internet_ai_assistant":
        raise InternetProductSnapshotLoaderError(
            code="INTERNET_SNAPSHOT_CONTRACT_INVALID",
            message="Internet product snapshot domain_key is invalid.",
            details={"path": str(path), "domain_key": snapshot["domain_key"]},
        )
    products = snapshot["products"]
    if not isinstance(products, list) or not products:
        raise InternetProductSnapshotLoaderError(
            code="INTERNET_SNAPSHOT_CONTRACT_INVALID",
            message="Internet product snapshot must contain a non-empty products list.",
            details={"path": str(path), "field": "products"},
        )
    product_ids = set()
    for index, product in enumerate(products):
        field_path = f"products[{index}]"
        if not isinstance(product, dict):
            raise InternetProductSnapshotLoaderError(
                code="INTERNET_SNAPSHOT_CONTRACT_INVALID",
                message="Each internet product item must be a JSON object.",
                details={"path": str(path), "field": field_path},
            )
        _require_fields(
            product,
            {
                "sku_id",
                "product_id",
                "role",
                "name",
                "brand",
                "product_type",
                "pricing",
                "source",
                "evidence_items",
            },
            str(path),
            field_path,
        )
        if not isinstance(product["evidence_items"], list) or not product["evidence_items"]:
            raise InternetProductSnapshotLoaderError(
                code="INTERNET_SNAPSHOT_CONTRACT_INVALID",
                message="Each internet product needs at least one evidence item.",
                details={"path": str(path), "field": f"{field_path}.evidence_items"},
            )
        product_ids.add(product["product_id"])
    if snapshot["default_target_product_id"] not in product_ids:
        raise InternetProductSnapshotLoaderError(
            code="INTERNET_SNAPSHOT_CONTRACT_INVALID",
            message="Default internet target product is not present.",
            details={
                "path": str(path),
                "default_target_product_id": snapshot["default_target_product_id"],
            },
        )


def _require_fields(value: Any, required: set[str], path: str, field_path: str) -> None:
    if not isinstance(value, dict):
        raise InternetProductSnapshotLoaderError(
            code="INTERNET_SNAPSHOT_CONTRACT_INVALID",
            message="Snapshot field must be a JSON object.",
            details={"path": path, "field": field_path},
        )
    missing = sorted(required - set(value))
    if missing:
        raise InternetProductSnapshotLoaderError(
            code="INTERNET_SNAPSHOT_CONTRACT_INVALID",
            message="Internet product snapshot is missing required fields.",
            details={"path": path, "field": field_path, "missing_fields": missing},
        )


def _selected_target_id(snapshot: JsonObject, target_product_id: str | None) -> str | None:
    product_id = _non_empty_str(target_product_id)
    if product_id is None:
        return None
    if any(item.get("product_id") == product_id for item in snapshot["products"]):
        return product_id
    raise InternetProductSnapshotLoaderError(
        code="TARGET_INTERNET_PRODUCT_NOT_FOUND",
        message="Requested target product is not present in the internet snapshot.",
        details={"target_product_id": product_id},
    )


def _product_payload_to_product(
    *,
    item: JsonObject,
    snapshot: JsonObject,
    task_id: str,
    created_at: datetime,
    selected_target_id: str | None,
    has_synthetic_target: bool,
) -> Product:
    primary_image_path = _primary_image_path(item)
    primary_image_url = _local_raw_asset_url(primary_image_path)
    evidence_ids = [
        evidence["evidence_id"]
        for evidence in item["evidence_items"]
        if isinstance(evidence, dict) and isinstance(evidence.get("evidence_id"), str)
    ]
    return Product(
        product_id=str(item["product_id"]),
        task_id=task_id,
        sku_id=str(item["sku_id"]),
        name=str(item["name"]),
        brand=str(item["brand"]),
        category=str(snapshot["category"]),
        subcategory=str(snapshot["subcategory"]),
        role=_role_for_product(
            item=item,
            selected_target_id=selected_target_id,
            has_synthetic_target=has_synthetic_target,
        ),
        product_url=_source_url(item),
        primary_image_path=primary_image_url or primary_image_path,
        primary_image_url=primary_image_url or primary_image_path,
        primary_image_source_path=primary_image_path,
        primary_image_status=(
            ProductImageStatus.AVAILABLE if primary_image_path else ProductImageStatus.MISSING
        ),
        evidence_ids=evidence_ids,
        tags=_compact_strings(
            str(item.get("product_type") or ""),
            *_string_items(item.get("platforms")),
            *_string_items(item.get("target_users")),
            *_string_items(item.get("core_scenarios")),
            _pricing_band(item),
            str(item.get("role") or ""),
        ),
        created_at=created_at,
    )


def _role_for_product(
    *,
    item: JsonObject,
    selected_target_id: str | None,
    has_synthetic_target: bool,
) -> ProductRole:
    product_id = item["product_id"]
    original_role = str(item["role"])
    if selected_target_id is not None:
        if product_id == selected_target_id:
            return ProductRole.TARGET
        if original_role == ProductRole.TARGET.value:
            return ProductRole.DIRECT_COMPETITOR
    elif has_synthetic_target and original_role == ProductRole.TARGET.value:
        return ProductRole.DIRECT_COMPETITOR
    return ProductRole(original_role)


def _product_payload_to_evidences(*, item: JsonObject, task_id: str) -> list[Evidence]:
    evidences = []
    for evidence_item in item["evidence_items"]:
        if not isinstance(evidence_item, dict):
            continue
        metadata = dict(evidence_item.get("metadata") or {})
        metadata.setdefault("product_type", item.get("product_type"))
        metadata.setdefault("platforms", item.get("platforms", []))
        metadata.setdefault("pricing", item.get("pricing", {}))
        metadata["price"] = _pricing_as_score_compatible_price(item.get("pricing"))
        metadata.setdefault("role", item.get("role"))
        metadata.setdefault("sku_id", item.get("sku_id"))
        metadata["missing_fields"] = _missing_evidence_fields(evidence_item, metadata)
        evidences.append(
            Evidence(
                evidence_id=str(evidence_item["evidence_id"]),
                task_id=task_id,
                product_id=str(evidence_item.get("product_id") or item["product_id"]),
                source_type=_evidence_source_type(evidence_item.get("source_type")),
                source_url=_non_empty_str(evidence_item.get("source_url")),
                screenshot_path=_non_empty_str(evidence_item.get("screenshot_path")),
                access_time=_parse_datetime(evidence_item.get("access_time")),
                content_summary=str(evidence_item["content_summary"]),
                confidence_level=ConfidenceLevel(
                    str(evidence_item.get("confidence_level") or "unknown")
                ),
                limitations=str(evidence_item.get("limitations") or "暂无来源局限性说明。"),
                metadata=metadata,
            )
        )
    return evidences


def _product_payload_to_review_insight(
    *,
    item: JsonObject,
    task_id: str,
    created_at: datetime,
) -> ReviewInsight:
    evidence_ids = [
        evidence["evidence_id"]
        for evidence in item["evidence_items"]
        if isinstance(evidence, dict) and isinstance(evidence.get("evidence_id"), str)
    ]
    return ReviewInsight(
        review_insight_id=f"ri_ip_{item['product_id']}",
        task_id=task_id,
        product_id=str(item["product_id"]),
        sku_id=str(item["sku_id"]),
        summary=_review_summary(item),
        evidence_ids=evidence_ids,
        confidence_level=ConfidenceLevel.MEDIUM,
        market_signals={
            "source": "internet_ai_assistant_snapshot",
            "platforms": item.get("platforms", []),
            "core_scenarios": item.get("core_scenarios", []),
            "price_band": _pricing_band(item),
            "sales": None,
        },
        limitations="互联网产品快照来自官方公开页，本轮不代表实时市场份额、下载量或排名。",
        risk_flags=[],
        created_at=created_at,
    )


def _synthetic_target_product(
    *,
    snapshot: JsonObject,
    task_id: str,
    created_at: datetime,
    selected_target_id: str | None,
    target_product_name: str | None,
    target_product_url: str | None,
) -> Product | None:
    if selected_target_id is not None:
        return None
    name = _non_empty_str(target_product_name)
    url = _non_empty_str(target_product_url)
    if name is None and url is None:
        return None
    return Product(
        product_id=f"prod_{task_id}_internet_user_target",
        task_id=task_id,
        sku_id=None,
        name=name or "User provided internet product",
        brand=None,
        category=str(snapshot["category"]),
        subcategory=str(snapshot["subcategory"]),
        role=ProductRole.TARGET,
        product_url=url,
        primary_image_path=None,
        primary_image_url=None,
        primary_image_source_path=None,
        primary_image_status=ProductImageStatus.MISSING,
        evidence_ids=[f"ev_{task_id}_internet_user_target_input"],
        tags=["user_input_target", snapshot["subcategory"], ProductRole.TARGET.value],
        created_at=created_at,
    )


def _synthetic_target_evidence(
    *,
    synthetic_target: Product | None,
    task_id: str,
    target_product_url: str | None,
    access_time: datetime,
) -> Evidence | None:
    if synthetic_target is None:
        return None
    return Evidence(
        evidence_id=f"ev_{task_id}_internet_user_target_input",
        task_id=task_id,
        product_id=synthetic_target.product_id,
        source_type=EvidenceSourceType.USER_RESEARCH,
        source_url=_non_empty_str(target_product_url),
        screenshot_path=None,
        access_time=access_time,
        content_summary=(
            "Task input identified this internet product as the target, but no matching "
            "local internet product snapshot was found."
        ),
        confidence_level=ConfidenceLevel.LOW,
        limitations=(
            "This evidence only records user-provided target identity. It does not support "
            "pricing, ranking, active user scale, model capability, or market-share claims."
        ),
        metadata={
            "source": "task.target_product_input",
            "target_selection": "target_unmatched",
            "missing_fields": ["snapshot.product_match"],
        },
    )


def _evidence_source_type(value: Any) -> EvidenceSourceType:
    source_type = SOURCE_TYPE_MAP.get(str(value or ""))
    if source_type is None:
        return EvidenceSourceType.OFFICIAL_PRODUCT_PAGE
    return source_type


def _missing_evidence_fields(evidence_item: JsonObject, metadata: JsonObject) -> list[str]:
    fields = _string_items(metadata.get("missing_fields"))
    if evidence_item.get("screenshot_path") is None:
        fields.append("source.screenshot_path")
    if evidence_item.get("access_time") is None:
        fields.append("source.access_time")
    return _dedupe(fields)


def _pricing_as_score_compatible_price(value: Any) -> JsonObject:
    pricing = value if isinstance(value, dict) else {}
    return {
        "currency": pricing.get("currency") or "CNY",
        "price_band": pricing.get("pricing_band") or "unknown",
        "display_price_yuan": pricing.get("final_price"),
        "min_price_yuan": pricing.get("final_price"),
        "max_price_yuan": pricing.get("list_price"),
        "price_note": pricing.get("pricing_note") or "暂无可靠数据",
    }


def _pricing_band(item: JsonObject) -> str:
    pricing = item.get("pricing")
    if isinstance(pricing, dict):
        return str(pricing.get("pricing_band") or "unknown")
    return "unknown"


def _source_url(item: JsonObject) -> str | None:
    source = item.get("source") if isinstance(item.get("source"), dict) else {}
    source_url = _non_empty_str(source.get("source_url"))
    if source_url:
        return source_url
    urls = item.get("official_urls")
    if isinstance(urls, list):
        for url in urls:
            if (text := _non_empty_str(url)) is not None:
                return text
    return None


def _primary_image_path(item: JsonObject) -> str | None:
    screenshots = item.get("screenshots")
    if isinstance(screenshots, list):
        for screenshot in screenshots:
            if (text := _non_empty_str(screenshot)) is not None:
                return text
    source = item.get("source") if isinstance(item.get("source"), dict) else {}
    return _non_empty_str(source.get("screenshot_path"))


def _local_raw_asset_url(path_value: Any) -> str | None:
    value = _non_empty_str(path_value)
    if value is None:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path = path.resolve()
    if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        return None
    try:
        relative = path.relative_to(RAW_ASSET_DIR.resolve())
    except ValueError:
        return None
    if not path.exists() or not path.is_file():
        return None
    return f"{RAW_ASSET_URL_PREFIX}/{quote(relative.as_posix(), safe='/')}"


def _review_summary(item: JsonObject) -> str:
    scenarios = "、".join(_string_items(item.get("core_scenarios")))
    users = "、".join(_string_items(item.get("target_users")))
    return (
        f"{item['name']} 官方公开页快照显示的目标人群/场景线索："
        f"{users or '暂无可靠数据'}；{scenarios or '暂无可靠数据'}。"
    )


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    text = _non_empty_str(value)
    if text is None:
        return None
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _compact_strings(*values: Any) -> list[str]:
    items: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip():
            items.append(value)
    return _dedupe(items)


def _string_items(value: Any) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _non_empty_str(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _dedupe(items: list[str]) -> list[str]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped
