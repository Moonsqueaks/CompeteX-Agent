from datetime import UTC, datetime

from app.schemas import Evidence, Product, ProductImageStatus, ProductRole, ReviewInsight
from app.services.internet_product_snapshot_loader import load_internet_product_snapshot

TASK_ID = "task_internet_snapshot_loader"
CREATED_AT = datetime(2026, 6, 10, 3, 26, tzinfo=UTC)


def test_internet_product_loader_reads_five_products() -> None:
    result = load_internet_product_snapshot(task_id=TASK_ID, created_at=CREATED_AT)

    assert result.domain_key == "internet_ai_assistant"
    assert result.default_target_product_id == "doubao"
    assert len(result.products) == 5
    assert len(result.evidences) >= 5
    assert len(result.review_insights) == 5
    assert {product.product_id for product in result.products} == {
        "doubao",
        "kimi",
        "deepseek",
        "qianwen",
        "yuanbao",
    }


def test_internet_product_loader_marks_doubao_as_target_and_competitors_correctly() -> None:
    result = load_internet_product_snapshot(task_id=TASK_ID, created_at=CREATED_AT)
    product_by_id = {product.product_id: product for product in result.products}

    assert product_by_id["doubao"].role == ProductRole.TARGET
    assert product_by_id["doubao"].sku_id == "ip_doubao"
    assert product_by_id["kimi"].role == ProductRole.DIRECT_COMPETITOR
    assert product_by_id["deepseek"].role == ProductRole.DIRECT_COMPETITOR
    assert product_by_id["qianwen"].role == ProductRole.DIRECT_COMPETITOR
    assert product_by_id["yuanbao"].role == ProductRole.DIRECT_COMPETITOR


def test_internet_product_loader_links_each_product_to_evidence_and_browser_asset() -> None:
    result = load_internet_product_snapshot(task_id=TASK_ID, created_at=CREATED_AT)
    evidence_ids = {evidence.evidence_id for evidence in result.evidences}

    for product in result.products:
        assert product.evidence_ids
        assert set(product.evidence_ids).issubset(evidence_ids)
        assert product.primary_image_status == ProductImageStatus.AVAILABLE
        assert product.primary_image_url is not None
        assert product.primary_image_url.startswith("/assets/raw/internet_ai_assistant/")


def test_internet_product_loader_preserves_missing_fields_for_qa_repair() -> None:
    result = load_internet_product_snapshot(task_id=TASK_ID, created_at=CREATED_AT)
    kimi_evidence = next(evidence for evidence in result.evidences if evidence.product_id == "kimi")

    assert kimi_evidence.evidence_id == "ev_ip_kimi_homepage"
    assert kimi_evidence.screenshot_path is None
    assert kimi_evidence.metadata["missing_fields"] == ["source.screenshot_path"]
    assert result.qa_revision_fixture["product_id"] == "kimi"
    assert result.qa_revision_fixture["evidence_id"] == "ev_ip_kimi_homepage"


def test_internet_product_loader_marks_deepseek_api_pricing_gap() -> None:
    result = load_internet_product_snapshot(task_id=TASK_ID, created_at=CREATED_AT)
    deepseek_evidence = next(
        evidence
        for evidence in result.evidences
        if evidence.evidence_id == "ev_ip_deepseek_homepage"
    )

    assert deepseek_evidence.product_id == "deepseek"
    assert deepseek_evidence.metadata["missing_fields"] == ["pricing.api_price_table"]
    assert deepseek_evidence.metadata["missing_reason"] == (
        "DeepSeek API 价格页或价格截图尚未进入本地 Evidence"
    )


def test_internet_product_loader_outputs_pydantic_schemas() -> None:
    result = load_internet_product_snapshot(task_id=TASK_ID, created_at=CREATED_AT)

    assert all(isinstance(product, Product) for product in result.products)
    assert all(isinstance(evidence, Evidence) for evidence in result.evidences)
    assert all(isinstance(insight, ReviewInsight) for insight in result.review_insights)
    assert result.model_dump(mode="json")["domain_key"] == "internet_ai_assistant"


def test_internet_product_loader_can_override_target_product() -> None:
    result = load_internet_product_snapshot(
        task_id=TASK_ID,
        created_at=CREATED_AT,
        target_product_id="kimi",
    )
    product_by_id = {product.product_id: product for product in result.products}

    assert product_by_id["kimi"].role == ProductRole.TARGET
    assert product_by_id["doubao"].role == ProductRole.DIRECT_COMPETITOR
