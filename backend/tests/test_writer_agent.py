from datetime import UTC, datetime

from app.agents import analysis_agent_node, collection_agent_node, writer_agent_node
from app.graph import create_initial_state
from app.schemas import AnalysisTask
from app.services.llm_client import LLMCallResult, LLMTokenUsage

NOW = datetime(2026, 5, 24, 2, 0, tzinfo=UTC)
REQUIRED_SECTIONS = [
    "conclusion_summary",
    "competitive_landscape_judgment",
    "core_competitor_analysis",
    "user_decision_chain_analysis",
    "target_opportunities_and_risks",
    "product_strategy_recommendations",
    "evidence_quality_appendix",
    "analysis_process_appendix",
]


def _task(task_id: str = "task_writer_agent") -> AnalysisTask:
    return AnalysisTask(
        task_id=task_id,
        target_product_name="Demo automatic litter box",
        target_product_url="https://example.com/products/target",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        data_source_mode="demo_snapshot",
        status="created",
        research_text=None,
        created_at=NOW,
        updated_at=NOW,
        metadata={"demo": True},
    )


def _analysis_ready_state(task_id: str = "task_writer_agent") -> dict:
    state = create_initial_state(_task(task_id))
    collection_agent_node(state, now=NOW)
    analysis_agent_node(state, now=NOW)
    return state


def test_writer_agent_generates_all_required_report_sections() -> None:
    state = _analysis_ready_state("task_writer_sections")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}

    writer_agent_node(state, now=NOW, llm_client=_disabled_llm_client())

    report = state["reports"][0]
    assert report["section_order"] == REQUIRED_SECTIONS
    for section_id in REQUIRED_SECTIONS:
        assert report[section_id]["section_id"] == section_id
        assert report[section_id]["summary"]
    assert report["conclusion_summary"]["items"]
    assert report["target_opportunities_and_risks"]["items"]
    assert report["evidence_quality_appendix"]["items"]


def test_writer_report_core_findings_trace_back_to_evidence() -> None:
    state = _analysis_ready_state("task_writer_evidence")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}

    writer_agent_node(state, now=NOW, llm_client=_disabled_llm_client())

    findings = state["reports"][0]["core_competitor_analysis"]
    assert findings["items"]
    for item in findings["items"]:
        assert item["judgment_strength"]
        assert item["claims"]
        assert item["evidence_ids"]
        for claim in item["claims"]:
            assert claim["evidence_ids"]


def test_writer_report_plan_limits_user_facing_focus_items() -> None:
    state = _analysis_ready_state("task_writer_plan")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}

    writer_agent_node(state, now=NOW, llm_client=_disabled_llm_client())

    report = state["reports"][0]
    metadata = state["metadata"]["writer_agent"]["report_plan"]
    planned_edge_ids = metadata["planned_edge_ids"]

    assert 1 <= len(planned_edge_ids) <= 5
    assert len(report["core_competitor_analysis"]["items"]) <= 5
    assert len(report["competitive_landscape_judgment"]["items"]) <= 5
    assert len(report["product_strategy_recommendations"]["items"]) <= 3
    assert metadata["total_edge_count"] == len(state["competition_edges"])


def test_writer_report_marks_risk_claims_without_new_facts() -> None:
    state = _analysis_ready_state("task_writer_risk")
    top_edge = max(state["competition_edges"], key=lambda edge: edge["edge_score"])
    claim_id = top_edge["claim_ids"][0]
    risk_claim = next(claim for claim in state["claims"] if claim["claim_id"] == claim_id)
    risk_claim["status"] = "needs_review"
    risk_claim["risk_flags"] = ["missing_evidence"]

    writer_agent_node(state, now=NOW, llm_client=_disabled_llm_client())

    report = state["reports"][0]
    finding = next(
        item
        for item in report["core_competitor_analysis"]["items"]
        if item["edge_id"] == top_edge["edge_id"]
    )
    risk_claim_summary = report["evidence_quality_appendix"]["items"][0]["risk_claims"][0]

    assert "missing_evidence" in finding["risk_flags"]
    assert risk_claim_summary["claim_id"] == claim_id
    assert risk_claim_summary["status"] == "needs_review"
    recommendation = report["product_strategy_recommendations"]["items"][0]
    assert recommendation["is_inference"] is True
    assert recommendation["priority"]
    assert recommendation["responsibility_type"]


def test_writer_agent_records_trace_run_log() -> None:
    state = _analysis_ready_state("task_writer_trace")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}

    writer_agent_node(state, now=NOW, llm_client=_disabled_llm_client())

    writer_run_logs = [
        run_log for run_log in state["run_logs"] if run_log["agent_name"] == "writer_agent"
    ]
    assert writer_run_logs
    assert writer_run_logs[-1]["status"] == "succeeded"
    assert state["metadata"]["writer_agent"]["report_id"] == state["reports"][0]["report_id"]


def test_writer_agent_uses_llm_to_generate_report_paragraph_json() -> None:
    state = _analysis_ready_state("task_writer_llm")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}
    top_edge = max(state["competition_edges"], key=lambda edge: edge["edge_score"])
    client = _FakeWriterLLMClient(
        [
            LLMCallResult(
                data={
                    "insights": [
                        {
                            "product_id": top_edge["competitor_product_id"],
                            "summary": "用户主要在意清理是否省心。",
                            "pain_points": ["担心清理麻烦", "担心异味控制不稳定"],
                            "buying_reasons": ["希望减少铲屎频率"],
                            "objections": ["价格和维护成本需要解释清楚"],
                        }
                    ]
                },
                raw_text='{"insights":[]}',
                attempts=1,
                used_fallback=False,
                fallback_reason=None,
                errors=[],
                token_usage=LLMTokenUsage(
                    model_name="Doubao-Seed-2.0-lite",
                    prompt_tokens=7,
                    completion_tokens=4,
                    total_tokens=11,
                ),
                model_name="Doubao-Seed-2.0-lite",
            ),
        LLMCallResult(
            data={
                "sections": [
                    {
                        "section_id": "conclusion_summary",
                        "summary": "LLM 重新组织后的结论摘要，只基于现有证据表达。",
                        "items": [
                            {
                                "item_key": top_edge["edge_id"],
                                "conclusion": "目标产品当前最该关注这个直接竞品。",
                                "reason": "两者在同一使用场景下争夺省心清理诉求。",
                                "action": "优先把容量、除臭和维护成本讲清楚。",
                            }
                        ],
                    },
                    {
                        "section_id": "core_competitor_analysis",
                        "summary": "LLM 重新组织后的核心竞品拆解。",
                    },
                    {"section_id": "unknown_section", "summary": "不应被应用。"},
                    {"section_id": "competitive_landscape_judgment", "summary": "   "},
                ]
            },
            raw_text='{"sections":[]}',
            attempts=1,
            used_fallback=False,
            fallback_reason=None,
            errors=[],
            token_usage=LLMTokenUsage(
                model_name="Doubao-Seed-2.0-lite",
                prompt_tokens=31,
                completion_tokens=17,
                total_tokens=48,
            ),
            model_name="Doubao-Seed-2.0-lite",
        ),
            LLMCallResult(
                data={
                    "sections": [
                        {
                            "section_id": "conclusion_summary",
                            "items": [
                                {
                                    "item_key": top_edge["edge_id"],
                                    "paragraphs": [
                                        "目标产品需要优先解释这个直接竞品，因为用户会把两者放在同一组候选中比较。现有证据只支持围绕清理负担、除臭和维护成本展开分析，不能补写未被证据覆盖的销量或认证。",
                                        "从用户决策看，自动猫砂盆不是单纯比功能数量，而是比长期使用是否省心。报告应把核心差异写成可理解的购买理由，并明确证据不足处需要复核。",
                                    ],
                                }
                            ],
                        }
                    ]
                },
                raw_text='{"sections":[]}',
                attempts=1,
                used_fallback=False,
                fallback_reason=None,
                errors=[],
                token_usage=LLMTokenUsage(
                    model_name="Doubao-Seed-2.0-lite",
                    prompt_tokens=41,
                    completion_tokens=23,
                    total_tokens=64,
                ),
                model_name="Doubao-Seed-2.0-lite",
            ),
            LLMCallResult(
                data={
                    "overall_status": "pass",
                    "summary": "报告表达清楚，没有发现内部字段或过度断言。",
                    "issues": [],
                },
                raw_text='{"overall_status":"pass","summary":"ok","issues":[]}',
                attempts=1,
                used_fallback=False,
                fallback_reason=None,
                errors=[],
                token_usage=LLMTokenUsage(
                    model_name="Doubao-Seed-2.0-lite",
                    prompt_tokens=5,
                    completion_tokens=2,
                    total_tokens=7,
                ),
                model_name="Doubao-Seed-2.0-lite",
            ),
        ]
    )

    writer_agent_node(state, now=NOW, llm_client=client)

    report = state["reports"][0]
    assert (
        report["conclusion_summary"]["summary"]
        == "LLM 重新组织后的结论摘要，只基于现有证据表达。"
    )
    assert report["conclusion_summary"]["items"][0]["llm_paragraphs"] == {
        "conclusion": "目标产品当前最该关注这个直接竞品。",
        "reason": "两者在同一使用场景下争夺省心清理诉求。",
        "action": "优先把容量、除臭和维护成本讲清楚。",
    }
    assert report["conclusion_summary"]["items"][0]["llm_expanded_analysis"] == [
        "目标产品需要优先解释这个直接竞品，因为用户会把两者放在同一组候选中比较。现有证据只支持围绕清理负担、除臭和维护成本展开分析，不能补写未被证据覆盖的销量或认证。",
        "从用户决策看，自动猫砂盆不是单纯比功能数量，而是比长期使用是否省心。报告应把核心差异写成可理解的购买理由，并明确证据不足处需要复核。",
    ]
    assert report["target_opportunities_and_risks"]["items"][0]["llm_extracted_insights"][0][
        "pain_points"
    ] == ["担心清理麻烦", "担心异味控制不稳定"]
    assert (
        report["evidence_quality_appendix"]["items"][0]["llm_report_quality"]["质检状态"]
        == "通过"
    )
    assert report["core_competitor_analysis"]["summary"] == "LLM 重新组织后的核心竞品拆解。"
    assert (
        report["competitive_landscape_judgment"]["summary"]
        == "聚合价格带、人群和使用场景切片下的竞争格局。"
    )
    assert report["conclusion_summary"]["items"]
    assert report["core_competitor_analysis"]["claim_ids"]
    assert report["core_competitor_analysis"]["evidence_ids"]
    assert state["metadata"]["writer_agent"]["llm_rewrite"]["status"] == "applied"
    assert state["metadata"]["writer_agent"]["llm_rewrite"]["token_usage"]["total_tokens"] == 48
    assert state["metadata"]["writer_agent"]["llm_insight_extraction"]["status"] == "applied"
    assert state["metadata"]["writer_agent"]["llm_analysis_expansion"]["status"] == "applied"
    assert state["metadata"]["writer_agent"]["llm_quality_review"]["status"] == "applied"
    assert len(state["token_usage_logs"]) == 4
    assert state["token_usage_logs"][-1]["run_id"] == state["run_logs"][-1]["run_id"]
    assert state["token_usage_logs"][-1]["agent_name"] == "writer_agent"
    assert client.calls[0]["schema_name"] == "writer_review_selling_point_insight_extraction"
    assert client.calls[1]["schema_name"] == "writer_report_paragraph_generation"
    assert client.calls[2]["schema_name"] == "writer_report_analysis_expansion"
    assert client.calls[3]["schema_name"] == "writer_report_quality_review"
    assert "DOUBAO_API_KEY" not in client.calls[1]["user_prompt"]
    assert "competition_edges" in client.calls[1]["user_prompt"]
    assert "evidence" in client.calls[1]["user_prompt"]
    assert "extracted_user_insights" in client.calls[1]["user_prompt"]
    assert "knowledge_context" in client.calls[2]["user_prompt"]


def test_writer_agent_keeps_rule_report_when_llm_uses_fallback() -> None:
    state = _analysis_ready_state("task_writer_llm_fallback")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}
    client = _FakeWriterLLMClient(
        LLMCallResult(
            data={"sections": [{"section_id": "conclusion_summary", "summary": "不应替换"}]},
            raw_text=None,
            attempts=0,
            used_fallback=True,
            fallback_reason="LLM_API_KEY_MISSING",
            errors=[],
            token_usage=LLMTokenUsage(model_name="Doubao-Seed-2.0-lite"),
            model_name="Doubao-Seed-2.0-lite",
        )
    )

    writer_agent_node(state, now=NOW, llm_client=client)

    report = state["reports"][0]
    assert report["conclusion_summary"]["summary"].startswith("小佩自动猫砂盆")
    assert state["metadata"]["writer_agent"]["llm_rewrite"]["status"] == "fallback"
    assert (
        state["metadata"]["writer_agent"]["llm_rewrite"]["fallback_reason"]
        == "LLM_API_KEY_MISSING"
    )
    assert state["token_usage_logs"] == []


def _disabled_llm_client() -> "_FakeWriterLLMClient":
    return _FakeWriterLLMClient(
        LLMCallResult(
            data={"sections": []},
            raw_text=None,
            attempts=0,
            used_fallback=True,
            fallback_reason="LLM_DISABLED",
            errors=[],
            token_usage=LLMTokenUsage(model_name="Doubao-Seed-2.0-lite"),
            model_name="Doubao-Seed-2.0-lite",
        )
    )


class _FakeWriterLLMClient:
    def __init__(self, result: LLMCallResult | list[LLMCallResult]):
        self.results = result if isinstance(result, list) else [result]
        self.calls: list[dict[str, object]] = []

    def complete_json(self, **kwargs: object) -> LLMCallResult:
        self.calls.append(kwargs)
        result_index = min(len(self.calls) - 1, len(self.results) - 1)
        return self.results[result_index]
