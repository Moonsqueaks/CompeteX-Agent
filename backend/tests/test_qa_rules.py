from datetime import UTC, datetime

import pytest

from app.schemas import Claim, CompetitionEdge, CompetitionSlice, Evidence, ScoreBreakdown
from app.services import run_qa_rules

NOW = datetime(2026, 5, 24, 2, 0, tzinfo=UTC)
TASK_ID = "task_qa_rules"


def _evidence(
    evidence_id: str = "ev_001",
    *,
    access_time: datetime | None = NOW,
    screenshot_path: str | None = "data/raw/sku_01/price.png",
    source_type: str = "douyin_sku_snapshot",
    content_summary: str = "商品页显示自动清理功能。",
    metadata: dict | None = None,
) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        task_id=TASK_ID,
        product_id="prod_001",
        source_type=source_type,
        source_url="https://example.com/product",
        screenshot_path=screenshot_path,
        access_time=access_time,
        content_summary=content_summary,
        confidence_level="medium",
        limitations="Local snapshot.",
        metadata=metadata or {},
    )


def _claim(
    claim_id: str = "claim_001",
    *,
    evidence_ids: list[str] | None = None,
    content: str = "商品页证据显示该产品具备自动清理能力。",
    is_inference: bool = False,
    risk_flags: list[str] | None = None,
) -> Claim:
    return Claim(
        claim_id=claim_id,
        task_id=TASK_ID,
        claim_type="feature_fact",
        content=content,
        evidence_ids=evidence_ids if evidence_ids is not None else ["ev_001"],
        confidence=0.82,
        is_inference=is_inference,
        risk_flags=risk_flags or [],
        status="accepted",
        created_at=NOW,
    )


def _edge(
    edge_id: str = "edge_001",
    *,
    claim_ids: list[str] | None = None,
    risk_flags: list[str] | None = None,
    evidence_confidence: float = 0.8,
) -> CompetitionEdge:
    return CompetitionEdge(
        edge_id=edge_id,
        task_id=TASK_ID,
        target_product_id="prod_target",
        competitor_product_id="prod_001",
        competition_type="direct",
        slice=CompetitionSlice(
            price_band="1000-1500",
            persona="多猫家庭",
            scenario="自动清理",
        ),
        decision_stages=["capability_understanding"],
        edge_score=0.76,
        score_breakdown=ScoreBreakdown(
            demand_substitutability=0.8,
            context_match=0.7,
            decision_stage_impact=0.8,
            evidence_confidence=evidence_confidence,
            market_signal_strength=0.6,
        ),
        claim_ids=claim_ids if claim_ids is not None else ["claim_001"],
        risk_flags=risk_flags or [],
        created_at=NOW,
    )


def test_qa_rules_flags_claim_missing_evidence_ids() -> None:
    claim = _claim(evidence_ids=[])

    review_tasks = run_qa_rules(
        task_id=TASK_ID,
        claims=[claim],
        evidences=[],
        now=NOW,
    )

    assert review_tasks[0].issue_code == "CLAIM_MISSING_EVIDENCE"
    assert review_tasks[0].target_type == "claim"
    assert review_tasks[0].target_agent == "analysis_agent"
    assert review_tasks[0].related_claim_ids == ["claim_001"]


def test_qa_rules_flags_missing_price_access_time_for_collection() -> None:
    evidence = _evidence(
        access_time=None,
        metadata={"price": {"display_price_yuan": 999, "price_band": "500-1000"}},
    )
    claim = _claim(
        content="该竞品在 500-1000 价格带存在价格优势，该判断为推断。",
        is_inference=True,
    )

    review_tasks = run_qa_rules(
        task_id=TASK_ID,
        claims=[claim],
        evidences=[evidence],
        now=NOW,
    )

    access_time_task = next(
        task
        for task in review_tasks
        if task.issue_code == "TIMELY_EVIDENCE_MISSING_ACCESS_TIME"
    )
    assert access_time_task.target_type == "evidence"
    assert access_time_task.target_id == "ev_001"
    assert access_time_task.target_agent == "collection_agent"
    assert access_time_task.evidence_ids == ["ev_001"]


def test_qa_rules_flags_missing_screenshot_for_critical_price_evidence() -> None:
    evidence = _evidence(
        screenshot_path=None,
        metadata={"price": {"display_price_yuan": 999, "price_band": "500-1000"}},
    )
    claim = _claim(
        content="该竞品在 500-1000 价格带存在价格优势，该判断为推断。",
        is_inference=True,
    )

    review_tasks = run_qa_rules(
        task_id=TASK_ID,
        claims=[claim],
        evidences=[evidence],
        now=NOW,
    )

    assert any(
        task.issue_code == "CRITICAL_EVIDENCE_MISSING_SCREENSHOT"
        and task.target_agent == "collection_agent"
        for task in review_tasks
    )


def test_qa_rules_flags_unmarked_inference_for_analysis() -> None:
    evidence = _evidence()
    claim = _claim(
        content="基于规则评分判断该产品存在替代竞争关系。",
        is_inference=False,
    )

    review_tasks = run_qa_rules(
        task_id=TASK_ID,
        claims=[claim],
        evidences=[evidence],
        now=NOW,
    )

    assert [task.issue_code for task in review_tasks] == ["INFERENCE_NOT_MARKED"]
    assert review_tasks[0].target_agent == "analysis_agent"


def test_qa_rules_flags_single_review_overgeneralization() -> None:
    evidence = _evidence(
        source_type="douyin_review_snapshot",
        content_summary="单条评论提到除臭体验不错。",
        metadata={"review_count": 1},
    )
    claim = _claim(
        content="评论普遍认为该产品除臭体验很好。",
        is_inference=True,
    )

    review_tasks = run_qa_rules(
        task_id=TASK_ID,
        claims=[claim],
        evidences=[evidence],
        now=NOW,
    )

    assert [task.issue_code for task in review_tasks] == ["SINGLE_REVIEW_OVERGENERALIZED"]
    assert review_tasks[0].severity == "warning"


@pytest.mark.parametrize(
    "content",
    [
        "该猫砂盆绝对安全，并通过所有认证，无任何风险。",
        "宠物使用完全安全，夹猫风险为零。",
        "该设备通过所有电器安全认证，认证齐全。",
        "医疗级护理效果可以治疗宠物皮肤问题。",
    ],
)
def test_qa_rules_flags_sensitive_absolute_claim_language(content: str) -> None:
    evidence = _evidence()
    claim = _claim(content=content)

    review_tasks = run_qa_rules(
        task_id=TASK_ID,
        claims=[claim],
        evidences=[evidence],
        now=NOW,
    )

    assert [task.issue_code for task in review_tasks] == [
        "SENSITIVE_CLAIM_NEEDS_CONSERVATIVE_LANGUAGE"
    ]
    assert review_tasks[0].target_agent == "analysis_agent"


def test_qa_rules_flags_competition_edge_risk_flags() -> None:
    evidence = _evidence()
    claim = _claim()
    edge = _edge(risk_flags=["missing_evidence"], evidence_confidence=0.2)

    review_tasks = run_qa_rules(
        task_id=TASK_ID,
        claims=[claim],
        evidences=[evidence],
        competition_edges=[edge],
        now=NOW,
    )

    issue_codes = {task.issue_code for task in review_tasks}
    assert "EDGE_MISSING_EVIDENCE" in issue_codes
    assert "EDGE_UNRELIABLE_DATA" in issue_codes


def test_qa_rules_allows_qualified_claim_to_pass() -> None:
    evidence = _evidence()
    claim = _claim()
    edge = _edge()

    review_tasks = run_qa_rules(
        task_id=TASK_ID,
        claims=[claim],
        evidences=[evidence],
        competition_edges=[edge],
        now=NOW,
    )

    assert review_tasks == []
