from datetime import UTC, datetime

from app.schemas import (
    ConfidenceLevel,
    Evidence,
    ExtractedField,
    Product,
    PublicPageSnapshot,
)
from app.services.public_page_enrichment import build_public_page_evidence
from app.services.public_page_parser import ParsedPublicPage

NOW = datetime(2026, 6, 9, 10, 0, tzinfo=UTC)


def test_enrichment_generates_public_page_evidence_and_conflict_record() -> None:
    product = _product()
    parsed = ParsedPublicPage(
        snapshot=PublicPageSnapshot(
            url="https://example.com/product",
            domain="example.com",
            http_status=200,
            access_time=NOW,
            title="Known Product",
            html_cache_path="data/public_pages/example.html",
            metadata={"known_url_source": "snapshot.source_url"},
        ),
        extracted_fields=[
            ExtractedField(
                field_name="title",
                value="Known Product",
                source_snippet="Known Product",
                extraction_method="html_title",
                confidence_level=ConfidenceLevel.HIGH,
                limitations="explicit title",
            ),
            ExtractedField(
                field_name="price",
                value="1999 CNY",
                source_snippet="price 1999 CNY",
                extraction_method="json_ld:offers.price",
                confidence_level=ConfidenceLevel.HIGH,
                limitations="explicit price",
            ),
        ],
    )

    evidence, result = build_public_page_evidence(
        task_id="task_public",
        product=product,
        parsed_page=parsed,
        existing_evidences=[_local_evidence()],
        evidence_index=1,
    )

    assert evidence is not None
    assert evidence.source_type == "public_product_page"
    assert evidence.source_url == "https://example.com/product"
    assert evidence.access_time == NOW
    assert evidence.metadata["llm_used"] is False
    assert evidence.metadata["missing_fields_filled"] == ["source.access_time"]
    assert evidence.metadata["conflicts"][0]["field_name"] == "price"
    assert result.evidence_id == evidence.evidence_id
    assert result.status == "evidence_generated"


def test_enrichment_skips_evidence_when_no_fields_exist() -> None:
    evidence, result = build_public_page_evidence(
        task_id="task_public",
        product=_product(),
        parsed_page=ParsedPublicPage(
            snapshot=PublicPageSnapshot(
                url="https://example.com/blank",
                domain="example.com",
                http_status=200,
                access_time=NOW,
            ),
            extracted_fields=[],
            unavailable_reason="no_extractable_fields",
        ),
        existing_evidences=[_local_evidence()],
        evidence_index=1,
    )

    assert evidence is None
    assert result.status == "unavailable"
    assert result.fallback_reason == "no_extractable_fields"


def _product() -> Product:
    return Product(
        product_id="prod_public",
        task_id="task_public",
        name="Local Product",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        role="target",
        product_url="https://example.com/product",
        evidence_ids=["ev_local"],
        created_at=NOW,
    )


def _local_evidence() -> Evidence:
    return Evidence(
        evidence_id="ev_local",
        task_id="task_public",
        product_id="prod_public",
        source_type="douyin_sku_snapshot",
        content_summary="Local price 1599 CNY",
        confidence_level="medium",
        limitations="local snapshot",
        source_url="https://example.com/product",
        access_time=None,
        metadata={
            "price": {"display_price_yuan": 1599, "price_band": "1500-2000"},
            "missing_fields": ["source.access_time"],
        },
    )
