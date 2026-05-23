import json
import re
from pathlib import Path
from typing import Any

from app.schemas import Evidence, Product

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = PROJECT_ROOT / "data" / "snapshots" / "demo_sku_snapshot.json"
DEMO_TASK_ID = "task_demo_snapshot_contract"
CREATED_AT = "2026-05-23T00:00:00+08:00"

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


def _snapshot() -> dict[str, Any]:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def _to_product(sku: dict[str, Any], snapshot: dict[str, Any]) -> Product:
    return Product.model_validate(
        {
            "product_id": sku["product_id"],
            "task_id": DEMO_TASK_ID,
            "sku_id": sku["sku_id"],
            "name": sku["name"],
            "brand": sku["brand"],
            "category": snapshot["category"],
            "subcategory": snapshot["subcategory"],
            "role": sku["role"],
            "product_url": sku["source"]["source_url"],
            "evidence_ids": [f"ev_{sku['sku_id']}"],
            "tags": [sku["product_type"], sku["price"]["price_band"]],
            "created_at": CREATED_AT,
        }
    )


def _to_evidence(sku: dict[str, Any]) -> Evidence:
    source = sku["source"]
    return Evidence.model_validate(
        {
            "evidence_id": f"ev_{sku['sku_id']}",
            "task_id": DEMO_TASK_ID,
            "product_id": sku["product_id"],
            "source_type": "douyin_sku_snapshot",
            "source_url": source["source_url"],
            "screenshot_path": source["screenshot_path"],
            "access_time": source["access_time"],
            "content_summary": (
                f"{sku['name']} snapshot: price {sku['price']['display_price_yuan']} CNY; "
                f"selling points: {', '.join(sku['selling_points'])}; "
                f"review summary: {sku['review_summary']}"
            ),
            "confidence_level": "medium",
            "limitations": source["limitations"],
            "metadata": {
                "sku_id": sku["sku_id"],
                "source_description": source["source_description"],
                "sales": source.get("sales"),
            },
        }
    )


def test_final_demo_snapshot_exists_and_has_at_least_eight_skus() -> None:
    snapshot = _snapshot()

    assert snapshot["snapshot_version"]
    assert snapshot["category"] == "smart_pet_hardware"
    assert snapshot["subcategory"] == "automatic_litter_box"
    assert len(snapshot["skus"]) >= 8
    assert any(sku["sku_id"] == snapshot["default_target_sku_id"] for sku in snapshot["skus"])


def test_each_sku_has_required_snapshot_contract_fields() -> None:
    snapshot = _snapshot()

    for sku in snapshot["skus"]:
        assert REQUIRED_SKU_FIELDS.issubset(sku)
        assert REQUIRED_PRICE_FIELDS.issubset(sku["price"])
        assert REQUIRED_SOURCE_FIELDS.issubset(sku["source"])
        assert sku["name"].strip()
        assert sku["brand"].strip()
        assert sku["selling_points"]
        assert sku["review_summary"].strip()
        assert sku["source"]["source_description"].strip()


def test_every_sku_can_be_converted_to_product_and_evidence_schema() -> None:
    snapshot = _snapshot()

    products = [_to_product(sku, snapshot) for sku in snapshot["skus"]]
    evidences = [_to_evidence(sku) for sku in snapshot["skus"]]

    assert len(products) == len(snapshot["skus"])
    assert len(evidences) == len(snapshot["skus"])
    assert {product.sku_id for product in products} == {sku["sku_id"] for sku in snapshot["skus"]}
    assert all(evidence.source_type == "douyin_sku_snapshot" for evidence in evidences)


def test_qa_revision_fixture_intentionally_misses_configured_evidence_field() -> None:
    snapshot = _snapshot()
    fixture = snapshot["qa_revision_fixture"]
    fixture_sku = next(sku for sku in snapshot["skus"] if sku["sku_id"] == fixture["sku_id"])

    missing_fields = set(fixture["missing_fields"])
    assert missing_fields & {"source.access_time", "source.screenshot_path"}
    if "source.access_time" in missing_fields:
        assert fixture_sku["source"]["access_time"] is None
        assert fixture["repair_evidence"]["access_time"]
    if "source.screenshot_path" in missing_fields:
        assert fixture_sku["source"]["screenshot_path"] is None
        assert fixture["repair_evidence"]["screenshot_path"]


def test_referenced_raw_dirs_and_available_screenshots_exist() -> None:
    snapshot = _snapshot()

    for sku in snapshot["skus"]:
        raw_dir = PROJECT_ROOT / sku["source"]["raw_dir"]
        assert raw_dir.exists()
        screenshot_path = sku["source"]["screenshot_path"]
        if screenshot_path is not None:
            assert (PROJECT_ROOT / screenshot_path).exists()


def test_demo_snapshot_does_not_include_sensitive_private_fields() -> None:
    serialized = SNAPSHOT_PATH.read_text(encoding="utf-8")

    forbidden_literals = [
        "api_key",
        "apikey",
        "authorization",
        "bearer ",
        "password",
        "secret",
        "token",
        "phone",
        "手机号",
        "身份证",
        "地址",
        "account_id",
        "user_id",
        "openid",
    ]
    for literal in forbidden_literals:
        assert literal not in serialized.lower()

    mainland_phone_pattern = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
    assert mainland_phone_pattern.search(serialized) is None
