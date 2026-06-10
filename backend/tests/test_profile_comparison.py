from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import pytest

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import AnalysisTask
from app.services.profile_service import (
    PROFILE_COMPARISON_VALUE_VERSION,
    PROFILE_EVIDENCE_GAP_VERSION,
    _build_product_profile,
    _profile_cache_requires_refresh,
)

TASK_ID = "task_profile_comparison"
CREATED_AT = datetime(2026, 5, 29, 4, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def completed_demo_state() -> dict[str, Any]:
    workflow = build_analysis_workflow()
    return workflow.invoke(create_initial_state(_stable_task()))


def test_profile_comparison_does_not_create_missing_alternative_competitor(
    completed_demo_state: dict[str, Any],
) -> None:
    state = deepcopy(completed_demo_state)
    state["competition_edges"] = [
        edge for edge in state["competition_edges"] if edge["competition_type"] == "direct"
    ]

    profile = _build_product_profile(state)

    comparison = profile.horizontal_comparison
    assert comparison is not None
    slots = {product.slot.value for product in comparison.compared_products}
    assert "target" in slots
    assert "highest_threat_direct_competitor" in slots
    assert "highest_threat_alternative" not in slots


def test_profile_comparison_each_judgment_has_evidence_drilldown(
    completed_demo_state: dict[str, Any],
) -> None:
    profile = _build_product_profile(completed_demo_state)

    comparison = profile.horizontal_comparison
    assert comparison is not None
    for dimension in comparison.dimensions:
        assert dimension.evidence_ids
        assert dimension.trace_refs
        assert all(value.evidence_ids for value in dimension.values)


def test_profile_comparison_uses_competitor_snapshot_evidence_for_readable_values(
    completed_demo_state: dict[str, Any],
) -> None:
    profile = _build_product_profile(completed_demo_state)

    comparison = profile.horizontal_comparison
    assert comparison is not None
    competitor_ids = {
        product.product_id
        for product in comparison.compared_products
        if product.slot.value != "target"
    }
    readable_dimensions = [
        dimension
        for dimension in comparison.dimensions
        if dimension.dimension_key.value
        in {"core_selling_points", "persona", "scenario"}
    ]

    assert competitor_ids
    for dimension in readable_dimensions:
        values_by_product = {value.product_id: value.value for value in dimension.values}
        competitor_values = [
            values_by_product[product_id]
            for product_id in competitor_ids
            if product_id in values_by_product
        ]
        assert competitor_values
        assert any(value != "暂无可靠数据" for value in competitor_values)


def test_profile_comparison_uses_ai_assistant_evidence_for_competitor_values() -> None:
    profile = _build_product_profile(_ai_assistant_profile_state())

    comparison = profile.horizontal_comparison
    assert comparison is not None
    values_by_dimension = {
        dimension.dimension_key.value: {
            value.product_id: value.value for value in dimension.values
        }
        for dimension in comparison.dimensions
    }

    deepseek_values = " ".join(
        values_by_dimension[dimension_key]["deepseek"]
        for dimension_key in ("core_selling_points", "persona", "scenario")
    )
    assert "对话问答" in deepseek_values
    assert "编程与推理" in deepseek_values
    assert "开发者" in deepseek_values
    assert "长文档研究" in deepseek_values
    assert "铲屎" not in deepseek_values
    assert "猫砂" not in deepseek_values
    assert "防外溅" not in deepseek_values


def test_profile_exposes_deepseek_pricing_gap_for_human_review() -> None:
    profile = _build_product_profile(_ai_assistant_profile_state())
    deepseek_evidence = next(
        evidence
        for evidence in profile.evidence_summaries
        if evidence.evidence_id == "ev_ip_deepseek_homepage"
    )

    assert profile.metadata["evidence_gap_profile_version"] == PROFILE_EVIDENCE_GAP_VERSION
    assert deepseek_evidence.product_id == "deepseek"
    assert deepseek_evidence.missing_fields == ["pricing.api_price_table"]
    assert deepseek_evidence.missing_reason == (
        "DeepSeek API 价格页或价格截图尚未进入本地 Evidence"
    )


def test_profile_cache_refreshes_legacy_ai_profile_without_deepseek_gap_state() -> None:
    state = _ai_assistant_profile_state()
    for evidence in state["evidences"]:
        if evidence["evidence_id"] == "ev_ip_deepseek_homepage":
            evidence["metadata"] = {
                key: value
                for key, value in evidence["metadata"].items()
                if key not in {"missing_fields", "missing_reason"}
            }
    profile = _build_product_profile(state).model_copy(
        update={"metadata": {"comparison_value_profile_version": PROFILE_COMPARISON_VALUE_VERSION}}
    )

    assert _profile_cache_requires_refresh(_ai_assistant_task(), profile)


def _stable_task() -> AnalysisTask:
    return AnalysisTask(
        task_id=TASK_ID,
        target_product_name="小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
        target_product_url="https://v.douyin.com/mv8e4KRLLwc/",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        data_source_mode="demo_snapshot",
        status="created",
        research_text="多猫家庭关注除臭稳定性、自动清理可靠性、维护成本和小户型摆放体验。",
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        metadata={},
    )


def _ai_assistant_task() -> AnalysisTask:
    return AnalysisTask(
        task_id="task_ai_profile_comparison",
        target_product_name="豆包",
        target_product_url="https://www.doubao.com/chat/",
        category="互联网产品",
        subcategory="AI 助手",
        data_source_mode="builtin_candidates",
        status="completed",
        research_text="演示 AI 助手竞品分析，需要复核 DeepSeek API 定价证据缺口。",
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        metadata={"domain_key": "internet_ai_assistant"},
    )


def _ai_assistant_profile_state() -> dict[str, Any]:
    created_at = CREATED_AT.isoformat()
    return {
        "task": {
            "task_id": "task_ai_profile_comparison",
            "target_product_name": "豆包",
            "category": "互联网产品",
            "subcategory": "AI 助手",
            "status": "completed",
        },
        "products": [
            {
                "product_id": "doubao",
                "task_id": "task_ai_profile_comparison",
                "sku_id": "ip_doubao",
                "name": "豆包",
                "brand": "字节跳动",
                "category": "互联网产品",
                "subcategory": "AI 助手",
                "role": "target",
                "product_url": "https://www.doubao.com/chat/",
                "evidence_ids": ["ev_ip_doubao_homepage"],
                "tags": ["general_ai_assistant", "知识工作者", "日常问答"],
                "created_at": created_at,
            },
            {
                "product_id": "deepseek",
                "task_id": "task_ai_profile_comparison",
                "sku_id": "ip_deepseek",
                "name": "DeepSeek",
                "brand": "DeepSeek",
                "category": "互联网产品",
                "subcategory": "AI 助手",
                "role": "direct_competitor",
                "product_url": "https://www.deepseek.com/",
                "evidence_ids": ["ev_ip_deepseek_homepage"],
                "tags": [
                    "general_ai_assistant",
                    "知识工作者",
                    "开发者",
                    "企业团队",
                    "长文档研究",
                    "编程推理",
                ],
                "created_at": created_at,
            },
        ],
        "evidences": [
            {
                "evidence_id": "ev_ip_doubao_homepage",
                "task_id": "task_ai_profile_comparison",
                "product_id": "doubao",
                "source_type": "official_product_page",
                "source_url": "https://www.doubao.com/chat/",
                "screenshot_path": "data/raw/internet_ai_assistant/doubao/homepage.png",
                "access_time": created_at,
                "content_summary": "豆包官方公开页显示 AI 助手入口和对话问答能力。",
                "confidence_level": "medium",
                "limitations": "公开页快照，不代表实时下载量或排名。",
                "metadata": {
                    "domain_key": "internet_ai_assistant",
                    "product_type": "general_ai_assistant",
                    "feature_modules": {
                        "conversation": ["开始对话"],
                        "content_creation": ["内容创作"],
                    },
                    "platforms": ["web"],
                    "pricing": {"pricing_note": "暂无可靠定价数据"},
                    "price": {"price_band": "unknown"},
                },
            },
            {
                "evidence_id": "ev_ip_deepseek_homepage",
                "task_id": "task_ai_profile_comparison",
                "product_id": "deepseek",
                "source_type": "official_product_page",
                "source_url": "https://www.deepseek.com/",
                "screenshot_path": "data/raw/internet_ai_assistant/deepseek/homepage.png",
                "access_time": created_at,
                "content_summary": (
                    "DeepSeek 官方公开页面显示 AI 对话、API 开放平台、"
                    "深度研究和编程推理相关入口。"
                ),
                "confidence_level": "medium",
                "limitations": "公开页快照，不代表实时下载量或排名。",
                "metadata": {
                    "domain_key": "internet_ai_assistant",
                    "product_type": "general_ai_assistant",
                    "feature_modules": {
                        "conversation": ["开始对话"],
                        "search_or_research": ["研究"],
                        "coding_or_reasoning": ["DeepSeek Coder", "API 文档"],
                        "agent_or_workflow": ["Agent 能力"],
                        "ecosystem_integration": ["网页版", "开放平台"],
                    },
                    "platforms": ["web"],
                    "pricing": {"pricing_note": "暂无可靠定价数据"},
                    "price": {"price_band": "unknown"},
                    "missing_fields": ["pricing.api_price_table"],
                    "missing_reason": "DeepSeek API 价格页或价格截图尚未进入本地 Evidence",
                },
            },
        ],
        "feature_trees": [
            {
                "feature_tree_id": "ft_doubao",
                "task_id": "task_ai_profile_comparison",
                "product_id": "doubao",
                "cleaning_capability": ["对话问答"],
                "odor_control": ["搜索与深度研究"],
                "safety_features": ["生态与分发入口"],
                "smart_features": ["内容创作"],
                "maintenance_cost": ["商业模式/付费层：暂无可靠数据"],
                "evidence_ids": ["ev_ip_doubao_homepage"],
                "risk_flags": [],
            }
        ],
        "pricing_models": [
            {
                "pricing_model_id": "pm_doubao",
                "task_id": "task_ai_profile_comparison",
                "product_id": "doubao",
                "price_band": "暂无可靠数据",
                "currency": "CNY",
                "list_price": None,
                "final_price": None,
                "promotions": ["暂无可靠定价数据"],
                "bundle_description": "暂无可靠定价数据",
                "evidence_ids": ["ev_ip_doubao_homepage"],
                "access_time": created_at,
                "risk_flags": [],
            }
        ],
        "user_personas": [
            {
                "persona_id": "persona_doubao",
                "task_id": "task_ai_profile_comparison",
                "product_id": "doubao",
                "personas": ["知识工作者", "内容创作者"],
                "pain_points": ["内容创作与多格式输出"],
                "scenarios": ["日常问答", "内容创作"],
                "decision_factors": ["核心能力覆盖"],
                "evidence_ids": ["ev_ip_doubao_homepage"],
                "is_inference": True,
                "risk_flags": [],
            }
        ],
        "competition_edges": [
            {
                "edge_id": "edge_doubao_deepseek",
                "task_id": "task_ai_profile_comparison",
                "target_product_id": "doubao",
                "competitor_product_id": "deepseek",
                "competition_type": "direct",
                "slice": {
                    "price_band": "暂无可靠数据",
                    "persona": "开发者",
                    "scenario": "编程推理",
                },
                "decision_stages": ["capability_understanding"],
                "edge_score": 0.8,
                "score_breakdown": {
                    "demand_substitutability": 0.9,
                    "context_match": 0.8,
                    "decision_stage_impact": 0.8,
                    "evidence_confidence": 0.8,
                    "market_signal_strength": 0.6,
                },
                "claim_ids": ["claim_doubao_deepseek"],
                "human_adjusted": False,
                "risk_flags": [],
                "created_at": created_at,
            }
        ],
    }
