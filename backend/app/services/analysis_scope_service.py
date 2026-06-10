import re
from collections.abc import Iterable, Sequence
from datetime import datetime

from app.schemas import AnalysisScopeSummary, AnalysisTask, Evidence, Product
from app.schemas.common import DataSourceMode

UNKNOWN_DATA_LABEL = "暂无可靠数据"
SNAPSHOT_SCOPE_NOTICE = "本报告基于用户提供的脱敏 SKU 快照，不代表实时全网数据。"
SNAPSHOT_DATE_PATTERN = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})")


def build_analysis_scope_summary(
    *,
    task: AnalysisTask,
    products: Sequence[Product],
    evidences: Sequence[Evidence],
    snapshot_version: str | None = None,
) -> AnalysisScopeSummary:
    product_list = list(products)
    evidence_list = list(evidences)
    platform_values = _dedupe(
        _non_empty_str(evidence.metadata.get("platform")) for evidence in evidence_list
    )
    source_descriptions = _dedupe(
        _non_empty_str(evidence.metadata.get("source_description"))
        for evidence in evidence_list
    )
    access_time_range, access_time_missing_fields = _access_time_range(evidence_list)

    return AnalysisScopeSummary(
        task_id=task.task_id,
        category=task.category,
        subcategory=task.subcategory,
        data_source_mode=task.data_source_mode,
        data_source_label=_data_source_label(task.data_source_mode),
        scope_notice=SNAPSHOT_SCOPE_NOTICE,
        sku_count=_sku_count(product_list),
        product_count=len(product_list),
        evidence_count=len(evidence_list),
        platform_label="、".join(platform_values) if platform_values else UNKNOWN_DATA_LABEL,
        platforms=platform_values,
        source_description=(
            "；".join(source_descriptions) if source_descriptions else UNKNOWN_DATA_LABEL
        ),
        snapshot_version=snapshot_version,
        snapshot_date=_snapshot_date(snapshot_version),
        access_time_range=access_time_range,
        missing_fields=access_time_missing_fields,
        evidence_ids=[evidence.evidence_id for evidence in evidence_list],
    )


def _data_source_label(data_source_mode: DataSourceMode) -> str:
    if data_source_mode == DataSourceMode.SNAPSHOT_PLUS_LIVE:
        return "用户提供的脱敏 SKU 快照 + 已知公开 URL 增强（失败时降级，不搜索新竞品）"
    return "用户提供的脱敏 SKU 快照"


def _sku_count(products: Sequence[Product]) -> int:
    sku_ids = _dedupe(_non_empty_str(product.sku_id) for product in products)
    return len(sku_ids) if sku_ids else len(products)


def _snapshot_date(snapshot_version: str | None) -> str:
    value = _non_empty_str(snapshot_version)
    if value is None:
        return UNKNOWN_DATA_LABEL
    matched = SNAPSHOT_DATE_PATTERN.match(value)
    if matched is None:
        return UNKNOWN_DATA_LABEL
    return matched.group("date")


def _access_time_range(evidences: Sequence[Evidence]) -> tuple[str, list[str]]:
    if not evidences:
        return UNKNOWN_DATA_LABEL, ["Evidence.access_time"]

    access_times = [evidence.access_time for evidence in evidences if evidence.access_time]
    if len(access_times) != len(evidences):
        return UNKNOWN_DATA_LABEL, ["Evidence.access_time"]

    start = min(access_times)
    end = max(access_times)
    if start == end:
        return _format_datetime(start), []
    return f"{_format_datetime(start)} 至 {_format_datetime(end)}", []


def _format_datetime(value: datetime) -> str:
    return value.isoformat()


def _dedupe(values: Iterable[str | None]) -> list[str]:
    deduped = []
    for value in values:
        if value is not None and value not in deduped:
            deduped.append(value)
    return deduped


def _non_empty_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
