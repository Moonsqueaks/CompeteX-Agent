import json
from functools import lru_cache
from json import JSONDecodeError
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LINK_METADATA_PATH = PROJECT_ROOT / "data" / "snapshots" / "link_metadata.json"
PRODUCT_IMAGE_FIELDS = (
    "primary_image_url",
    "main_image_url",
    "image_url",
    "image",
    "thumbnail_url",
)


def product_main_image_url_for_sku(
    sku_id: str | None,
    *,
    metadata_path: Path | str | None = None,
) -> str | None:
    if sku_id is None:
        return None
    return load_product_main_image_urls(metadata_path=metadata_path).get(f"sku:{sku_id}")


def product_main_image_url_for_product(
    product_id: str | None,
    *,
    metadata_path: Path | str | None = None,
) -> str | None:
    if product_id is None:
        return None
    return load_product_main_image_urls(metadata_path=metadata_path).get(f"product:{product_id}")


def product_main_image_url(
    *,
    sku_id: str | None = None,
    product_id: str | None = None,
    metadata_path: Path | str | None = None,
) -> str | None:
    urls = load_product_main_image_urls(metadata_path=metadata_path)
    normalized_sku_id = _non_empty_str(sku_id)
    normalized_product_id = _non_empty_str(product_id)
    if normalized_sku_id is not None:
        image_url = urls.get(f"sku:{normalized_sku_id}")
        if image_url is not None:
            return image_url
    inferred_sku_id = _sku_id_from_internal_product_id(normalized_product_id)
    if inferred_sku_id is not None:
        image_url = urls.get(f"sku:{inferred_sku_id}")
        if image_url is not None:
            return image_url
    if normalized_product_id is not None:
        image_url = urls.get(f"product:{normalized_product_id}")
        if image_url is not None:
            return image_url
    return None


def load_product_main_image_urls(
    *,
    metadata_path: Path | str | None = None,
) -> dict[str, str]:
    if metadata_path is None:
        return _load_default_product_main_image_urls()
    return _read_product_main_image_urls(Path(metadata_path))


@lru_cache(maxsize=1)
def _load_default_product_main_image_urls() -> dict[str, str]:
    return _read_product_main_image_urls(DEFAULT_LINK_METADATA_PATH)


def _read_product_main_image_urls(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except JSONDecodeError:
        return {}
    if not isinstance(payload, list):
        return {}

    urls: dict[str, str] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        image_url = _first_remote_image_url(item)
        if image_url is None:
            continue
        sku_id = _non_empty_str(item.get("sku_id"))
        product_id = _non_empty_str(item.get("product_id"))
        if sku_id is not None:
            urls[f"sku:{sku_id}"] = image_url
        if product_id is not None:
            urls[f"product:{product_id}"] = image_url
    return urls


def _first_remote_image_url(container: dict[str, Any]) -> str | None:
    for field_name in PRODUCT_IMAGE_FIELDS:
        value = _non_empty_str(container.get(field_name))
        if value is not None and value.startswith(("http://", "https://")):
            return value
    return None


def _non_empty_str(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def _sku_id_from_internal_product_id(product_id: str | None) -> str | None:
    if product_id is None or not product_id.startswith("prod_sku_"):
        return None
    sku_suffix = product_id.removeprefix("prod_")
    return sku_suffix if sku_suffix.startswith("sku_") else None
