from datetime import UTC, datetime
from pathlib import Path

from app.schemas import AnalysisScopeSummary, AnalysisTask, DataSourceMode
from app.services.analysis_scope_service import (
    SNAPSHOT_SCOPE_NOTICE,
    UNKNOWN_DATA_LABEL,
    build_analysis_scope_summary,
)
from app.services.snapshot_loader import load_demo_snapshot

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "task_analysis_scope"
CREATED_AT = datetime(2026, 5, 23, 0, 0, tzinfo=UTC)


def test_analysis_scope_summary_uses_frozen_demo_snapshot_scope() -> None:
    snapshot = load_demo_snapshot(task_id=TASK_ID, created_at=CREATED_AT)
    summary = build_analysis_scope_summary(
        task=_task(),
        products=snapshot.products,
        evidences=snapshot.evidences,
        snapshot_version=snapshot.snapshot_version,
    )

    assert isinstance(summary, AnalysisScopeSummary)
    assert summary.task_id == TASK_ID
    assert summary.category == "smart_pet_hardware"
    assert summary.subcategory == "automatic_litter_box"
    assert summary.data_source_mode == DataSourceMode.DEMO_SNAPSHOT
    assert summary.data_source_label == "用户提供的脱敏 SKU 快照"
    assert summary.scope_notice == SNAPSHOT_SCOPE_NOTICE
    assert summary.sku_count == 14
    assert summary.product_count == 14
    assert summary.evidence_count == 14
    assert summary.snapshot_version == "2026-05-23.step06.v1"
    assert summary.snapshot_date == "2026-05-23"
    assert summary.platforms == ["douyin_mall"]
    assert summary.platform_label == "douyin_mall"
    assert summary.source_description == "用户提供的脱敏抖音商品短链、商品页截图和价格截图。"


def test_analysis_scope_summary_marks_missing_access_time_as_unknown() -> None:
    snapshot = load_demo_snapshot(task_id=TASK_ID, created_at=CREATED_AT)
    summary = build_analysis_scope_summary(
        task=_task(),
        products=snapshot.products,
        evidences=snapshot.evidences,
        snapshot_version=snapshot.snapshot_version,
    )

    assert summary.access_time_range == UNKNOWN_DATA_LABEL
    assert summary.missing_fields == ["Evidence.access_time"]


def test_analysis_scope_summary_does_not_expose_local_paths_or_secrets() -> None:
    snapshot = load_demo_snapshot(task_id=TASK_ID, created_at=CREATED_AT)
    summary = build_analysis_scope_summary(
        task=_task(),
        products=snapshot.products,
        evidences=snapshot.evidences,
        snapshot_version=snapshot.snapshot_version,
    )

    dumped = summary.model_dump_json()

    assert str(PROJECT_ROOT) not in dumped
    assert PROJECT_ROOT.drive not in dumped
    assert "data/raw" not in dumped
    assert "raw_dir" not in dumped
    assert "api_key" not in dumped.lower()
    assert "sk-" not in dumped.lower()


def _task() -> AnalysisTask:
    return AnalysisTask(
        task_id=TASK_ID,
        target_product_name="小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
        target_product_url="https://v.douyin.com/mv8e4KRLLwc/",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        data_source_mode=DataSourceMode.DEMO_SNAPSHOT,
        status="completed",
        research_text="多猫家庭关注除臭稳定性、自动清理可靠性、维护成本和小户型摆放体验。",
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        metadata={},
    )
