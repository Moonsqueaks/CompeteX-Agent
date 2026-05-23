from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import FastAPI
from pydantic import BaseModel, ValidationError

from app.schemas import (
    AgentMessage,
    AgentRunLog,
    AnalysisTask,
    Claim,
    ClaimStatus,
    CompetitionEdge,
    Evidence,
    FeatureTree,
    HumanFeedback,
    PricingModel,
    Product,
    ReviewTask,
    RiskFlag,
    TokenUsageLog,
    ToolCallLog,
    UserPersona,
)

NOW = datetime(2026, 5, 22, 2, 0, tzinfo=UTC)


def analysis_task_payload() -> dict[str, Any]:
    return {
        "task_id": "task_001",
        "target_product_name": "Demo automatic litter box",
        "target_product_url": "https://example.com/products/target",
        "category": "smart_pet_hardware",
        "subcategory": "automatic_litter_box",
        "data_source_mode": "demo_snapshot",
        "status": "created",
        "research_text": "Interview summary",
        "created_at": NOW,
        "updated_at": NOW,
        "metadata": {"demo": True},
    }


def agent_message_payload() -> dict[str, Any]:
    return {
        "message_id": "msg_001",
        "task_id": "task_001",
        "from_agent": "qa_agent",
        "to_agent": "collection_agent",
        "message_type": "revision_request",
        "artifact_type": "claim_evidence_check",
        "payload": {
            "claim_id": "claim_001",
            "missing_fields": ["access_time"],
            "required_action": "Attach snapshot access time.",
        },
        "evidence_ids": [],
        "status": "requires_revision",
        "created_at": NOW,
    }


def product_payload() -> dict[str, Any]:
    return {
        "product_id": "prod_target",
        "task_id": "task_001",
        "sku_id": "sku_02",
        "role": "target",
        "name": "Demo automatic litter box",
        "brand": "Demo Brand",
        "shop_name": "Demo Shop",
        "category": "smart_pet_hardware",
        "subcategory": "automatic_litter_box",
        "product_url": "https://example.com/products/target",
        "evidence_ids": ["ev_001"],
        "tags": ["odor_control"],
        "created_at": NOW,
    }


def feature_tree_payload() -> dict[str, Any]:
    return {
        "feature_tree_id": "ft_001",
        "task_id": "task_001",
        "product_id": "prod_target",
        "cleaning_capability": ["automatic_scooping"],
        "odor_control": ["sealed_bin"],
        "safety_features": ["presence_detection"],
        "smart_features": ["app_reminder"],
        "maintenance_cost": ["liner_bags"],
        "evidence_ids": ["ev_001"],
        "risk_flags": [],
    }


def pricing_model_payload() -> dict[str, Any]:
    return {
        "pricing_model_id": "price_001",
        "task_id": "task_001",
        "product_id": "prod_target",
        "list_price": 1999.0,
        "final_price": 1599.0,
        "currency": "CNY",
        "price_band": "1500-2000",
        "promotions": ["coupon"],
        "bundle_description": "device with starter kit",
        "evidence_ids": ["ev_001"],
        "access_time": NOW,
        "risk_flags": [],
    }


def user_persona_payload() -> dict[str, Any]:
    return {
        "persona_id": "persona_001",
        "task_id": "task_001",
        "product_id": "prod_target",
        "personas": ["multi_cat_household"],
        "pain_points": ["manual_cleaning_burden"],
        "scenarios": ["odor_sensitive_apartment"],
        "decision_factors": ["cleaning_reliability"],
        "evidence_ids": ["ev_001"],
        "is_inference": True,
        "risk_flags": [],
    }


def evidence_payload() -> dict[str, Any]:
    return {
        "evidence_id": "ev_001",
        "task_id": "task_001",
        "product_id": "prod_target",
        "source_type": "douyin_sku_snapshot",
        "source_url": "https://example.com/products/target",
        "screenshot_path": "data/raw/sku_02/price.png",
        "access_time": NOW,
        "content_summary": "Snapshot includes price, selling points, and review count.",
        "confidence_level": "medium",
        "limitations": "Local snapshot, not a live page.",
        "metadata": {"sku_id": "sku_02"},
    }


def claim_payload() -> dict[str, Any]:
    return {
        "claim_id": "claim_001",
        "task_id": "task_001",
        "claim_type": "pricing_advantage",
        "content": "Competitor A is more price-attractive in this slice.",
        "evidence_ids": ["ev_001"],
        "confidence": 0.78,
        "is_inference": False,
        "risk_flags": [],
        "status": "accepted",
        "created_at": NOW,
    }


def competition_edge_payload() -> dict[str, Any]:
    return {
        "edge_id": "edge_001",
        "task_id": "task_001",
        "target_product_id": "prod_target",
        "competitor_product_id": "prod_a",
        "competition_type": "direct",
        "slice": {
            "price_band": "1500-2000",
            "persona": "multi_cat_household",
            "scenario": "odor_control",
        },
        "decision_stages": ["capability_understanding", "decision_completion"],
        "edge_score": 0.82,
        "score_breakdown": {
            "demand_substitutability": 0.9,
            "context_match": 0.85,
            "decision_stage_impact": 0.75,
            "evidence_confidence": 0.7,
            "market_signal_strength": 0.75,
        },
        "claim_ids": ["claim_001"],
        "human_adjusted": False,
        "risk_flags": [],
        "created_at": NOW,
    }


def review_task_payload() -> dict[str, Any]:
    return {
        "review_task_id": "review_001",
        "task_id": "task_001",
        "check_name": "price_access_time",
        "issue_code": "MISSING_ACCESS_TIME",
        "severity": "error",
        "status": "open",
        "target_agent": "collection_agent",
        "target_type": "evidence",
        "target_id": "ev_001",
        "message": "Price evidence is missing access time.",
        "required_action": "Add access time or mark unavailable.",
        "related_claim_ids": ["claim_001"],
        "evidence_ids": ["ev_001"],
        "created_at": NOW,
        "resolved_at": None,
    }


def human_feedback_payload() -> dict[str, Any]:
    return {
        "feedback_id": "hf_001",
        "task_id": "task_001",
        "target_type": "claim",
        "target_id": "claim_001",
        "action": "mark_needs_review",
        "before_value": {"status": "accepted"},
        "after_value": {"status": "needs_review"},
        "reason": "Evidence needs manual review.",
        "created_at": NOW,
    }


def agent_run_log_payload() -> dict[str, Any]:
    return {
        "run_id": "run_001",
        "task_id": "task_001",
        "agent_name": "collection_agent",
        "status": "succeeded",
        "started_at": NOW,
        "ended_at": NOW,
        "input_summary": "Load local SKU snapshots.",
        "output_summary": "Loaded products and evidence.",
        "error_message": None,
    }


def tool_call_log_payload() -> dict[str, Any]:
    return {
        "tool_call_id": "tool_001",
        "task_id": "task_001",
        "run_id": "run_001",
        "tool_name": "snapshot_loader",
        "arguments_summary": {"path": "data/snapshots"},
        "status": "succeeded",
        "started_at": NOW,
        "ended_at": NOW,
        "duration_ms": 35,
        "error_message": None,
    }


def token_usage_log_payload() -> dict[str, Any]:
    return {
        "usage_id": "usage_001",
        "task_id": "task_001",
        "run_id": "run_001",
        "agent_name": "analysis_agent",
        "model_name": "rules",
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "created_at": NOW,
    }


SCHEMA_CASES: tuple[tuple[type[BaseModel], Any, str], ...] = (
    (AnalysisTask, analysis_task_payload, "task_id"),
    (AgentMessage, agent_message_payload, "message_id"),
    (Product, product_payload, "product_id"),
    (FeatureTree, feature_tree_payload, "feature_tree_id"),
    (PricingModel, pricing_model_payload, "pricing_model_id"),
    (UserPersona, user_persona_payload, "persona_id"),
    (Evidence, evidence_payload, "evidence_id"),
    (Claim, claim_payload, "claim_id"),
    (CompetitionEdge, competition_edge_payload, "edge_id"),
    (ReviewTask, review_task_payload, "review_task_id"),
    (HumanFeedback, human_feedback_payload, "feedback_id"),
    (AgentRunLog, agent_run_log_payload, "run_id"),
    (ToolCallLog, tool_call_log_payload, "tool_call_id"),
    (TokenUsageLog, token_usage_log_payload, "usage_id"),
)


@pytest.mark.parametrize(("schema", "payload_factory", "required_field"), SCHEMA_CASES)
def test_core_schema_accepts_valid_examples(
    schema: type[BaseModel],
    payload_factory: Any,
    required_field: str,
) -> None:
    model = schema.model_validate(payload_factory())

    dumped = model.model_dump(mode="json")
    assert dumped[required_field]


@pytest.mark.parametrize(("schema", "payload_factory", "required_field"), SCHEMA_CASES)
def test_core_schema_rejects_missing_required_fields(
    schema: type[BaseModel],
    payload_factory: Any,
    required_field: str,
) -> None:
    payload = payload_factory()
    payload.pop(required_field)

    with pytest.raises(ValidationError):
        schema.model_validate(payload)


def test_core_schema_field_names_use_snake_case() -> None:
    for schema, _, _ in SCHEMA_CASES:
        for field_name in schema.model_fields:
            assert field_name == field_name.lower()
            assert "-" not in field_name


def test_claim_without_evidence_is_marked_as_risky() -> None:
    payload = claim_payload()
    payload["evidence_ids"] = []
    payload["risk_flags"] = []
    payload["status"] = "accepted"

    claim = Claim.model_validate(payload)

    assert RiskFlag.MISSING_EVIDENCE in claim.risk_flags
    assert claim.status == ClaimStatus.NEEDS_REVIEW


@pytest.mark.parametrize("edge_score", [0, 1])
def test_competition_edge_accepts_score_boundaries(edge_score: float) -> None:
    payload = competition_edge_payload()
    payload["edge_score"] = edge_score

    edge = CompetitionEdge.model_validate(payload)

    assert edge.edge_score == edge_score


@pytest.mark.parametrize("edge_score", [-0.01, 1.01])
def test_competition_edge_rejects_score_out_of_range(edge_score: float) -> None:
    payload = competition_edge_payload()
    payload["edge_score"] = edge_score

    with pytest.raises(ValidationError):
        CompetitionEdge.model_validate(payload)


def test_competition_edge_rejects_breakdown_scores_out_of_range() -> None:
    payload = competition_edge_payload()
    payload["score_breakdown"]["evidence_confidence"] = 1.01

    with pytest.raises(ValidationError):
        CompetitionEdge.model_validate(payload)


def test_token_usage_total_must_match_prompt_and_completion_tokens() -> None:
    payload = token_usage_log_payload()
    payload["total_tokens"] = 1

    with pytest.raises(ValidationError):
        TokenUsageLog.model_validate(payload)


def test_core_schemas_can_be_included_in_openapi() -> None:
    class SchemaBundle(BaseModel):
        task: AnalysisTask
        message: AgentMessage
        product: Product
        feature_tree: FeatureTree
        pricing_model: PricingModel
        user_persona: UserPersona
        evidence: Evidence
        claim: Claim
        competition_edge: CompetitionEdge
        review_task: ReviewTask
        human_feedback: HumanFeedback
        agent_run_log: AgentRunLog
        tool_call_log: ToolCallLog
        token_usage_log: TokenUsageLog

    api = FastAPI()

    @api.get("/schema-test", response_model=SchemaBundle)
    def schema_test() -> dict[str, Any]:
        return {}

    schemas = api.openapi()["components"]["schemas"]
    expected_schema_names = {
        "AnalysisTask",
        "AgentMessage",
        "Product",
        "FeatureTree",
        "PricingModel",
        "UserPersona",
        "Evidence",
        "Claim",
        "CompetitionEdge",
        "ReviewTask",
        "HumanFeedback",
        "AgentRunLog",
        "ToolCallLog",
        "TokenUsageLog",
    }
    assert expected_schema_names.issubset(schemas)
