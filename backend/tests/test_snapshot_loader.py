import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.schemas import Evidence, Product, ReviewInsight
from app.services.snapshot_loader import SnapshotLoaderError, load_demo_snapshot

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = PROJECT_ROOT / "data" / "snapshots" / "demo_sku_snapshot.json"
TASK_ID = "task_snapshot_loader"
CREATED_AT = datetime(2026, 5, 23, 0, 0, tzinfo=UTC)


def test_snapshot_loader_reads_all_demo_skus() -> None:
    result = load_demo_snapshot(task_id=TASK_ID, created_at=CREATED_AT)

    assert result.snapshot_version
    assert result.category == "smart_pet_hardware"
    assert result.subcategory == "automatic_litter_box"
    assert result.default_target_sku_id == "sku_02"
    assert len(result.products) == 14
    assert len(result.evidences) == 14
    assert len(result.review_insights) == 14
    assert {product.sku_id for product in result.products} == {
        evidence.metadata["sku_id"] for evidence in result.evidences
    }


def test_snapshot_loader_marks_default_target_product() -> None:
    result = load_demo_snapshot(task_id=TASK_ID, created_at=CREATED_AT)

    target_product = next(
        product for product in result.products if product.sku_id == result.default_target_sku_id
    )

    assert target_product.role == "target"
    assert target_product.name == "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆"
    assert target_product.evidence_ids == ["ev_sku_02"]


def test_snapshot_loader_preserves_missing_evidence_fields() -> None:
    result = load_demo_snapshot(task_id=TASK_ID, created_at=CREATED_AT)

    qa_evidence = next(
        evidence for evidence in result.evidences if evidence.metadata["sku_id"] == "sku_01"
    )

    assert qa_evidence.access_time is None
    assert qa_evidence.screenshot_path == "data/raw/sku_01/QQ图片20260523155546.jpg"
    assert qa_evidence.metadata["missing_fields"] == ["source.access_time"]
    assert result.qa_revision_fixture["repair_evidence"]["access_time"]


def test_snapshot_loader_outputs_pydantic_schemas() -> None:
    result = load_demo_snapshot(task_id=TASK_ID, created_at=CREATED_AT)

    assert all(isinstance(product, Product) for product in result.products)
    assert all(isinstance(evidence, Evidence) for evidence in result.evidences)
    assert all(isinstance(insight, ReviewInsight) for insight in result.review_insights)
    assert all(insight.evidence_ids for insight in result.review_insights)
    assert result.model_dump(mode="json")["products"][0]["task_id"] == TASK_ID


def test_snapshot_loader_rejects_invalid_json_with_diagnostic_error(tmp_path: Path) -> None:
    invalid_path = tmp_path / "invalid_snapshot.json"
    invalid_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SnapshotLoaderError) as exc_info:
        load_demo_snapshot(task_id=TASK_ID, snapshot_path=invalid_path, created_at=CREATED_AT)

    assert exc_info.value.code == "SNAPSHOT_INVALID_JSON"
    assert exc_info.value.details["path"] == str(invalid_path)
    assert "line" in exc_info.value.details


def test_snapshot_loader_reports_missing_file_with_diagnostic_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing_snapshot.json"

    with pytest.raises(SnapshotLoaderError) as exc_info:
        load_demo_snapshot(task_id=TASK_ID, snapshot_path=missing_path, created_at=CREATED_AT)

    assert exc_info.value.code == "SNAPSHOT_NOT_FOUND"
    assert exc_info.value.message == "Snapshot file does not exist."
    assert exc_info.value.details == {"path": str(missing_path)}


def test_snapshot_loader_rejects_invalid_contract_with_diagnostic_error(tmp_path: Path) -> None:
    invalid_path = tmp_path / "invalid_contract.json"
    payload = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    payload["skus"][0].pop("source")
    invalid_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(SnapshotLoaderError) as exc_info:
        load_demo_snapshot(task_id=TASK_ID, snapshot_path=invalid_path, created_at=CREATED_AT)

    assert exc_info.value.code == "SNAPSHOT_CONTRACT_INVALID"
    assert exc_info.value.details["field"] == "skus[0]"
    assert exc_info.value.details["missing_fields"] == ["source"]
