from pathlib import Path

import pytest

from app.services.domain_profiles import (
    INTERNET_AI_ASSISTANT_DOMAIN,
    SMART_LITTER_BOX_DOMAIN,
    DomainProfileError,
    get_domain_profile,
    infer_domain_key,
    profile_payload,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_smart_litter_box_profile_keeps_existing_snapshot_path() -> None:
    profile = get_domain_profile(SMART_LITTER_BOX_DOMAIN)
    payload = profile_payload(profile)

    assert profile.snapshot_path == PROJECT_ROOT / "data" / "snapshots" / "demo_sku_snapshot.json"
    assert profile.category == "smart_pet_hardware"
    assert profile.subcategory == "automatic_litter_box"
    assert payload["candidate_pool"]["pool_id"] == "smart_litter_box_v1"


def test_internet_ai_assistant_profile_uses_internet_snapshot_and_candidate_pool() -> None:
    profile = get_domain_profile(INTERNET_AI_ASSISTANT_DOMAIN)
    payload = profile_payload(profile)

    assert profile.snapshot_path == (
        PROJECT_ROOT / "data" / "snapshots" / "internet_ai_assistant_snapshot.json"
    )
    assert profile.default_target_id == "doubao"
    assert profile.candidate_pool.pool_id == "internet_ai_assistant_v1"
    assert "official_url" in profile.candidate_pool.target_match_fields
    assert payload["domain_key"] == INTERNET_AI_ASSISTANT_DOMAIN
    assert payload["candidate_pool"]["candidate_roles"] == [
        "target",
        "direct_competitor",
        "alternative",
        "reference",
    ]


def test_infer_domain_key_from_category_subcategory_and_known_url() -> None:
    assert infer_domain_key("互联网产品", "AI 助手") == INTERNET_AI_ASSISTANT_DOMAIN
    assert infer_domain_key("internet_product", None) == INTERNET_AI_ASSISTANT_DOMAIN
    assert (
        infer_domain_key(None, None, target_product_url="https://www.doubao.com/chat/")
        == INTERNET_AI_ASSISTANT_DOMAIN
    )
    assert infer_domain_key("smart_pet_hardware", "automatic_litter_box") == SMART_LITTER_BOX_DOMAIN


def test_unknown_domain_profile_raises_standard_error() -> None:
    with pytest.raises(DomainProfileError) as exc_info:
        get_domain_profile("not_a_domain")

    assert exc_info.value.code == "UNKNOWN_DOMAIN"
    assert exc_info.value.details == {"domain_key": "not_a_domain"}
