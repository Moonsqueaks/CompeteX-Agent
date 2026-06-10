from collections.abc import Mapping, Sequence

from app.schemas import (
    ConfidenceLevel,
    Evidence,
    EvidenceSourceType,
    ExtractedField,
    Product,
    PublicPageEnrichmentResult,
    PublicPageSnapshot,
)
from app.schemas.common import JsonObject
from app.services.public_page_parser import ParsedPublicPage


def build_public_page_evidence(
    *,
    task_id: str,
    product: Product,
    parsed_page: ParsedPublicPage,
    existing_evidences: Sequence[Evidence],
    evidence_index: int,
) -> tuple[Evidence | None, PublicPageEnrichmentResult]:
    extracted_fields = parsed_page.extracted_fields
    snapshot = parsed_page.snapshot
    if not extracted_fields:
        return None, PublicPageEnrichmentResult(
            url=snapshot.url,
            product_id=product.product_id,
            evidence_id=None,
            status="unavailable",
            extracted_fields=[],
            unavailable_fields=[
                "title",
                "price",
                "selling_point",
                "specification",
                "main_image_url",
            ],
            fallback_reason=parsed_page.unavailable_reason or "no_extractable_fields",
            metadata={"stage": "stage_1_known_url"},
        )

    original = _primary_snapshot_evidence(product, existing_evidences)
    filled_fields = _missing_fields_filled(original, extracted_fields)
    conflicts = _conflicts(original, extracted_fields, snapshot)
    evidence_id = f"ev_{product.product_id}_public_page_{evidence_index:03d}"
    metadata = {
        "stage": "stage_1_known_url",
        "source": "known_public_url",
        "fetcher": "httpx",
        "parser": "deterministic_html_parser",
        "llm_used": False,
        "known_url_source": snapshot.metadata.get("known_url_source"),
        "html_cache_path": snapshot.html_cache_path,
        "public_page_title": snapshot.title,
        "extracted_fields": [field.model_dump(mode="json") for field in extracted_fields],
        "missing_fields_filled": filled_fields,
        "conflicts": conflicts,
        "field_names": _dedupe(field.field_name for field in extracted_fields),
        "risk_flags": ["missing_screenshot"] if snapshot.screenshot_path is None else [],
    }
    evidence = Evidence(
        evidence_id=evidence_id,
        task_id=task_id,
        product_id=product.product_id,
        source_type=EvidenceSourceType.PUBLIC_PRODUCT_PAGE,
        source_url=snapshot.url,
        screenshot_path=snapshot.screenshot_path,
        access_time=snapshot.access_time,
        content_summary=_content_summary(product, extracted_fields, snapshot),
        confidence_level=_overall_confidence(extracted_fields),
        limitations=(
            "Stage 1 known URL enhancement. Facts are limited to explicit public page "
            "fields parsed from static HTML; no LLM-created facts and no screenshot capture "
            "in this first version."
        ),
        metadata=metadata,
    )
    return evidence, PublicPageEnrichmentResult(
        url=snapshot.url,
        product_id=product.product_id,
        evidence_id=evidence.evidence_id,
        status="evidence_generated",
        extracted_fields=extracted_fields,
        missing_fields_filled=filled_fields,
        conflicts=conflicts,
        unavailable_fields=[],
        fallback_reason=None,
        metadata={
            "stage": "stage_1_known_url",
            "source_type": EvidenceSourceType.PUBLIC_PRODUCT_PAGE.value,
        },
    )


def enrichment_result_payload(result: PublicPageEnrichmentResult) -> JsonObject:
    return result.model_dump(mode="json")


def _primary_snapshot_evidence(
    product: Product,
    evidences: Sequence[Evidence],
) -> Evidence | None:
    for evidence in evidences:
        if evidence.product_id == product.product_id:
            return evidence
    for evidence in evidences:
        if evidence.evidence_id in product.evidence_ids:
            return evidence
    return None


def _missing_fields_filled(
    original: Evidence | None,
    fields: Sequence[ExtractedField],
) -> list[str]:
    if original is None:
        return []
    missing_fields = _string_items(original.metadata.get("missing_fields"))
    filled: list[str] = []
    if "source.access_time" in missing_fields:
        filled.append("source.access_time")
    field_names = {field.field_name for field in fields}
    if "source.screenshot_path" in missing_fields and "main_image_url" in field_names:
        filled.append("source.main_image_url")
    if not original.content_summary and field_names:
        filled.extend(sorted(field_names))
    return _dedupe(filled)


def _conflicts(
    original: Evidence | None,
    fields: Sequence[ExtractedField],
    snapshot: PublicPageSnapshot,
) -> list[JsonObject]:
    if original is None:
        return []
    conflicts: list[JsonObject] = []
    original_price = original.metadata.get("price")
    if isinstance(original_price, Mapping):
        original_values = [
            str(value)
            for key, value in original_price.items()
            if key.endswith("price_yuan") and value is not None
        ]
        for field in fields:
            if field.field_name != "price":
                continue
            if original_values and not any(value in field.value for value in original_values):
                conflicts.append(
                    {
                        "field_name": "price",
                        "before": dict(original_price),
                        "after": field.value,
                        "source_url": snapshot.url,
                        "access_time": snapshot.access_time.isoformat(),
                        "recommended_action": "source_conflict_needs_review",
                    }
                )
    return conflicts


def _content_summary(
    product: Product,
    fields: Sequence[ExtractedField],
    snapshot: PublicPageSnapshot,
) -> str:
    grouped: dict[str, list[str]] = {}
    for field in fields:
        grouped.setdefault(field.field_name, []).append(field.value)
    parts = []
    for field_name in (
        "title",
        "price",
        "selling_point",
        "specification",
        "main_image_url",
        "brand",
    ):
        values = grouped.get(field_name)
        if values:
            parts.append(f"{field_name}: {_join(values[:2])}")
    if not parts:
        parts.append(snapshot.title or product.name)
    return (
        f"Public page enhancement for {product.name}: {_join(parts)}. "
        f"Accessed at {snapshot.access_time.isoformat()}."
    )


def _overall_confidence(fields: Sequence[ExtractedField]) -> ConfidenceLevel:
    if any(field.confidence_level == ConfidenceLevel.HIGH for field in fields):
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def _join(values: Sequence[str]) -> str:
    return "; ".join(value for value in values if value)


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _dedupe(items: Sequence[str]) -> list[str]:
    deduped: list[str] = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped


__all__ = [
    "build_public_page_evidence",
    "enrichment_result_payload",
]
