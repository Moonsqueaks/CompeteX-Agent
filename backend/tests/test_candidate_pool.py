from app.services.candidate_pool import load_builtin_candidate_pool
from app.services.domain_profiles import INTERNET_AI_ASSISTANT_DOMAIN, SMART_LITTER_BOX_DOMAIN


def test_cat_litter_builtin_candidate_pool_matches_target_url() -> None:
    result = load_builtin_candidate_pool(
        domain_key=SMART_LITTER_BOX_DOMAIN,
        target_product_url="https://v.douyin.com/mv8e4KRLLwc/",
    )
    metadata = result.metadata()

    assert result.selected_target_sku_id == "sku_02"
    assert result.target_match_basis == "target_product_url"
    assert result.candidate_count == 13
    assert metadata["candidate_discovery_mode"] == "builtin_candidates"
    assert metadata["candidate_pool_loaded"] is True
    assert metadata["candidate_source_type"] == "builtin_candidate_pool"


def test_internet_builtin_candidate_pool_matches_doubao_and_loads_core_competitors() -> None:
    result = load_builtin_candidate_pool(
        domain_key=INTERNET_AI_ASSISTANT_DOMAIN,
        target_product_url="https://www.doubao.com/chat/",
    )
    item_by_id = {item.product_id: item for item in result.candidate_items}

    assert result.selected_target_id == "doubao"
    assert result.selected_target_sku_id == "ip_doubao"
    assert result.target_match_basis == "target_product_url"
    assert result.candidate_count == 4
    assert {"kimi", "deepseek", "qianwen", "yuanbao"}.issubset(item_by_id)
    assert item_by_id["doubao"].status == "target_matched"
    assert item_by_id["kimi"].status == "candidate_loaded"


def test_builtin_candidate_pool_keeps_unmatched_target_as_evidence_gap() -> None:
    result = load_builtin_candidate_pool(
        domain_key=INTERNET_AI_ASSISTANT_DOMAIN,
        target_product_url="https://example.com/not-in-pool",
        target_product_name="Unmatched Product",
    )
    metadata = result.metadata()

    assert result.selected_target_id is None
    assert result.selected_target_sku_id is None
    assert result.target_status == "target_unmatched"
    assert result.target_match_basis == "user_input_unmatched"
    assert result.candidate_count == 5
    assert metadata["target_status"] == "target_unmatched"
    assert all(item.status == "candidate_loaded" for item in result.candidate_items)
