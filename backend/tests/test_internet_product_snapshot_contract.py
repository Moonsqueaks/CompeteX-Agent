import json
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = PROJECT_ROOT / "data" / "snapshots" / "internet_ai_assistant_snapshot.json"

REQUIRED_PRODUCT_FIELDS = {
    "sku_id",
    "product_id",
    "role",
    "name",
    "brand",
    "product_type",
    "pricing",
    "source",
    "evidence_items",
}
REQUIRED_EVIDENCE_FIELDS = {
    "evidence_id",
    "product_id",
    "source_type",
    "source_url",
    "screenshot_path",
    "access_time",
    "content_summary",
    "confidence_level",
    "limitations",
    "metadata",
}


def _snapshot() -> dict[str, Any]:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def test_internet_snapshot_exists_and_contains_expected_product_set() -> None:
    snapshot = _snapshot()
    product_ids = {product["product_id"] for product in snapshot["products"]}

    assert snapshot["snapshot_version"] == "internet_ai_assistant_v1"
    assert snapshot["domain_key"] == "internet_ai_assistant"
    assert snapshot["default_target_product_id"] == "doubao"
    assert len(snapshot["products"]) >= 5
    assert {"doubao", "kimi", "deepseek", "qianwen", "yuanbao"}.issubset(product_ids)


def test_each_internet_product_has_required_fields_and_evidence() -> None:
    snapshot = _snapshot()

    for product in snapshot["products"]:
        assert REQUIRED_PRODUCT_FIELDS.issubset(product)
        assert product["name"].strip()
        assert product["product_id"].strip()
        assert product["evidence_items"]
        for evidence in product["evidence_items"]:
            assert REQUIRED_EVIDENCE_FIELDS.issubset(evidence)
            assert evidence["source_url"] or evidence["metadata"].get("local_source_note")
            assert evidence["content_summary"].strip()


def test_qa_revision_fixture_intentionally_misses_and_repairs_screenshot() -> None:
    snapshot = _snapshot()
    fixture = snapshot["qa_revision_fixture"]
    fixture_product = next(
        product
        for product in snapshot["products"]
        if product["product_id"] == fixture["product_id"]
    )
    fixture_evidence = next(
        evidence
        for evidence in fixture_product["evidence_items"]
        if evidence["evidence_id"] == fixture["evidence_id"]
    )

    assert fixture["missing_fields"] == ["source.screenshot_path"]
    assert fixture_evidence["screenshot_path"] is None
    assert (PROJECT_ROOT / fixture["repair_evidence"]["screenshot_path"]).exists()


def test_internet_snapshot_does_not_include_sensitive_private_fields() -> None:
    serialized = SNAPSHOT_PATH.read_text(encoding="utf-8")
    lower_serialized = serialized.lower()
    forbidden_literals = [
        "api_key",
        "apikey",
        "authorization",
        "bearer ",
        "password",
        "secret",
        "cookie",
        "phone",
        "手机号",
        "身份证",
        "account_id",
        "openid",
    ]

    for literal in forbidden_literals:
        assert literal not in lower_serialized
    assert re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)", serialized) is None
