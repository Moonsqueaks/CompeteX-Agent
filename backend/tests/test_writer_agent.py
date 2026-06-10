import json
import re
from datetime import UTC, datetime
from pathlib import Path

from app.agents import analysis_agent_node, collection_agent_node, writer_agent_node
from app.graph import create_initial_state
from app.schemas import AnalysisTask
from app.services.llm_client import LLMCallResult, LLMTokenUsage

NOW = datetime(2026, 5, 24, 2, 0, tzinfo=UTC)
FORMAL_REPORT_SKELETON_PATH = Path(__file__).parent / "fixtures" / "formal_report_skeleton.json"
FORMAL_REPORT_SKELETON = json.loads(FORMAL_REPORT_SKELETON_PATH.read_text(encoding="utf-8"))
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
FORMAL_NARRATIVE_SECTIONS = FORMAL_REPORT_SKELETON["section_ids"]
FORMAL_REPORT_MINIMUMS = FORMAL_REPORT_SKELETON["minimums"]


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


def test_formal_report_skeleton_fixture_freezes_acceptance_contract() -> None:
    raw_fixture = FORMAL_REPORT_SKELETON_PATH.read_text(encoding="utf-8")

    assert FORMAL_NARRATIVE_SECTIONS == [
        "report_info",
        "executive_summary",
        "research_question_and_scope",
        "category_context",
        "competitor_selection",
        "competitive_landscape",
        "core_competitor_battlecards",
        "decision_chain",
        "gap_matrix",
        "opportunity_map",
        "risk_and_evidence_boundary",
        "appendix_traceability",
    ]
    assert FORMAL_REPORT_MINIMUMS["battlecard_count"] == 3
    assert FORMAL_REPORT_MINIMUMS["gap_matrix_count"] == 6
    assert FORMAL_REPORT_MINIMUMS["gap_type_count"] == 3
    assert FORMAL_REPORT_MINIMUMS["opportunity_count"] == 3
    assert FORMAL_REPORT_MINIMUMS["decision_stage_count"] == 5
    assert "not final demo data" in FORMAL_REPORT_SKELETON["description"]
    assert not re.search(r"(api[_ -]?key|1[3-9]\d{9}|account_id|secret|token)", raw_fixture, re.I)


def test_writer_agent_generates_all_required_report_sections() -> None:
    state = _analysis_ready_state("task_writer_sections")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}

    writer_agent_node(state, now=NOW, llm_client=_disabled_llm_client())

    report = state["reports"][0]
    narrative_report = report["narrative_report"]
    assert report["section_order"] == REQUIRED_SECTIONS
    assert narrative_report["mode"] == "planned_then_written"
    assert len(narrative_report["themes"]) >= 3
    narrative_sections = narrative_report["sections"]
    assert [section["section_id"] for section in narrative_sections] == FORMAL_NARRATIVE_SECTIONS
    section_by_id = {section["section_id"]: section for section in narrative_sections}
    assert section_by_id["core_competitor_battlecards"]["items"]
    assert section_by_id["gap_matrix"]["items"]
    assert section_by_id["opportunity_map"]["items"]
    assert section_by_id["decision_chain"]["items"]
    for section_id in REQUIRED_SECTIONS:
        assert report[section_id]["section_id"] == section_id
        assert report[section_id]["summary"]
    assert report["conclusion_summary"]["items"]
    assert report["target_opportunities_and_risks"]["items"]
    assert report["evidence_quality_appendix"]["items"]
    assert state["report_quality_checks"]
    assert state["report_quality_checks"][0]["report_id"] == report["report_id"]
    assert state["report_quality_checks"][0]["status"] in {"passed", "needs_revision"}
    assert "rule_report_quality" in report["evidence_quality_appendix"]["items"][0]
    assert state["metadata"]["writer_agent"]["report_quality_rules"]["issue_count"] >= 0


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


def test_writer_report_planner_consumes_analysis_artifacts() -> None:
    state = _analysis_ready_state("task_writer_artifact_planner")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}

    writer_agent_node(state, now=NOW, llm_client=_disabled_llm_client())

    report = state["reports"][0]
    executive_item = report["conclusion_summary"]["items"][0]
    battlecard_item = report["core_competitor_analysis"]["items"][0]
    gap_item = report["target_opportunities_and_risks"]["items"][0]
    opportunity_item = report["product_strategy_recommendations"]["items"][0]

    assert report["conclusion_summary"]["title"] == "执行摘要"
    assert executive_item["largest_threat"]
    assert executive_item["largest_opportunity"]
    assert executive_item["first_action"]
    assert executive_item["evidence_boundary"]

    assert battlecard_item["battlecard_id"]
    assert battlecard_item["why_users_compare"]
    assert battlecard_item["target_response"]
    assert battlecard_item["response_talk_track"]
    assert battlecard_item["claims"]
    assert battlecard_item["evidence_ids"]

    assert report["target_opportunities_and_risks"]["title"] == "差距矩阵"
    assert gap_item["dimension"]
    assert gap_item["impact_on_decision"]
    assert gap_item["recommendation"]
    assert gap_item["claim_ids"]
    assert gap_item["evidence_ids"]

    assert report["product_strategy_recommendations"]["title"] == "机会地图与优先级"
    assert opportunity_item["owner"]
    assert opportunity_item["expected_impact"]
    assert opportunity_item["evidence_boundary"]
    assert opportunity_item["linked_gaps"] or opportunity_item["linked_battlecards"]

    body_section_ids = [
        "conclusion_summary",
        "competitive_landscape_judgment",
        "core_competitor_analysis",
        "user_decision_chain_analysis",
        "target_opportunities_and_risks",
        "product_strategy_recommendations",
    ]
    body_text = " ".join(
        str(report[section_id]["items"]) for section_id in body_section_ids
    )
    assert "content_summary" not in body_text


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
            _llm_result(
                {
                    "sections": [
                        {
                            "section_id": "executive_summary",
                            "title": "执行摘要",
                            "paragraphs": [
                                "目标产品当前优先关注少数核心竞品，不再罗列全部结构化关系。",
                                "用户比较的核心是清理省心、除臭可信、容量够用和维护成本可接受。",
                                "下一步应先补齐会影响购买决策的证据，再优化页面卖点表达。",
                            ],
                        },
                        {
                            "section_id": "competitive_landscape",
                            "title": "竞争格局",
                            "paragraphs": [
                                "竞争压力集中在相近价格带、相近人群和相近自动清理场景。",
                            ],
                        },
                        {
                            "section_id": "core_competitors",
                            "title": "核心竞品",
                            "paragraphs": [
                                "核心竞品只展开最容易被用户横向比较的三个对象。",
                            ],
                        },
                        {
                            "section_id": "decision_chain",
                            "title": "用户决策链",
                            "paragraphs": [
                                "用户会在能力理解、信任建立和最终下单阶段重新权衡竞品。",
                            ],
                        },
                        {
                            "section_id": "action_recommendations",
                            "title": "行动建议",
                            "paragraphs": [
                                "优先改页面对比表达，补齐除臭、容量、维护成本和用户异议证据。",
                            ],
                        },
                    ]
                },
                prompt_tokens=12,
                completion_tokens=9,
            ),
            _llm_result(
                {
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
                        {"section_id": "unknown_section", "summary": "不应被应用。"},
                    ]
                },
                prompt_tokens=10,
                completion_tokens=8,
            ),
            _llm_result(
                {
                    "sections": [
                        {
                            "section_id": "core_competitor_analysis",
                            "summary": "LLM 重新组织后的核心竞品拆解。",
                        }
                    ]
                },
                prompt_tokens=9,
                completion_tokens=7,
            ),
            _llm_result(
                {
                    "sections": [
                        {"section_id": "competitive_landscape_judgment", "summary": "   "}
                    ]
                },
                prompt_tokens=8,
                completion_tokens=6,
            ),
            _llm_result(
                {
                    "sections": [
                        {
                            "section_id": "product_strategy_recommendations",
                            "summary": "LLM 重新组织后的行动建议。",
                        }
                    ]
                },
                prompt_tokens=6,
                completion_tokens=4,
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
    rewrite_metadata = state["metadata"]["writer_agent"]["llm_rewrite"]
    assert rewrite_metadata["status"] == "applied"
    assert rewrite_metadata["stage_count"] == 4
    assert rewrite_metadata["applied_stage_count"] == 4
    assert rewrite_metadata["token_usage"]["total_tokens"] == 58
    assert [stage["schema_name"] for stage in rewrite_metadata["stages"]] == [
        "writer_report_conclusion_generation",
        "writer_report_core_competitor_generation",
        "writer_report_competitive_slice_generation",
        "writer_report_action_recommendation_generation",
    ]
    assert state["metadata"]["writer_agent"]["llm_insight_extraction"]["status"] == "applied"
    assert state["metadata"]["writer_agent"]["narrative_report"]["status"] == "applied"
    narrative_sections = report["narrative_report"]["sections"]
    assert [section["section_id"] for section in narrative_sections] == FORMAL_NARRATIVE_SECTIONS
    narrative_by_id = {section["section_id"]: section for section in narrative_sections}
    assert narrative_by_id["executive_summary"]["title"] == "执行摘要"
    assert "结构化关系" in narrative_by_id["executive_summary"]["paragraphs"][0]
    assert narrative_by_id["core_competitor_battlecards"]["items"]
    assert narrative_by_id["gap_matrix"]["items"]
    assert narrative_by_id["opportunity_map"]["items"]
    assert state["metadata"]["writer_agent"]["llm_analysis_expansion"]["status"] == "applied"
    assert state["metadata"]["writer_agent"]["llm_quality_review"]["status"] == "applied"
    knowledge_metadata = state["metadata"]["writer_agent"]["knowledge_retrieval"]
    assert knowledge_metadata["status"] == "succeeded"
    assert knowledge_metadata["external_search_performed"] is False
    assert state["knowledge_artifacts"]
    assert state["knowledge_artifacts"][0]["retrieval_mode"] == "local_static_category_framework"
    assert len(state["token_usage_logs"]) == 8
    assert state["token_usage_logs"][-1]["run_id"] == state["run_logs"][-1]["run_id"]
    assert state["token_usage_logs"][-1]["agent_name"] == "writer_agent"
    assert client.calls[0]["schema_name"] == "writer_review_selling_point_insight_extraction"
    assert client.calls[1]["schema_name"] == "writer_formal_narrative_report_generation"
    assert client.calls[2]["schema_name"] == "writer_report_conclusion_generation"
    assert client.calls[3]["schema_name"] == "writer_report_core_competitor_generation"
    assert client.calls[4]["schema_name"] == "writer_report_competitive_slice_generation"
    assert client.calls[5]["schema_name"] == "writer_report_action_recommendation_generation"
    assert client.calls[6]["schema_name"] == "writer_report_analysis_expansion"
    assert client.calls[7]["schema_name"] == "writer_report_quality_review"
    assert "DOUBAO_API_KEY" not in client.calls[1]["user_prompt"]
    assert "competition_edges" in client.calls[1]["user_prompt"]
    assert "evidence" in client.calls[1]["user_prompt"]
    assert "extracted_user_insights" in client.calls[1]["user_prompt"]
    assert "knowledge_artifact" in client.calls[1]["user_prompt"]
    assert "总体判断" in client.calls[2]["system_prompt"]
    assert "核心竞品" in client.calls[3]["system_prompt"]
    assert "竞争切片" in client.calls[4]["system_prompt"]
    assert "行动建议" in client.calls[5]["system_prompt"]
    assert "knowledge_artifact" in client.calls[5]["user_prompt"]
    assert "local_static_category_framework" in client.calls[5]["user_prompt"]


def test_writer_agent_repairs_failed_quality_items_once() -> None:
    state = _analysis_ready_state("task_writer_quality_repair")
    state["metadata"]["qa_agent"] = {"qa_status": "passed"}
    top_edge = max(state["competition_edges"], key=lambda edge: edge["edge_score"])
    repair_paragraph = (
        "目标产品需要把核心竞品的拦截点讲得更直接：用户最关心的是清理是否省心、"
        "异味能否控制、维护成本是否可接受。现有证据只能支持这些方向性判断，"
        "价格和认证等信息不足处应保留复核提示。"
    )
    client = _FakeWriterLLMClient(
        [
            _llm_result({"insights": []}, prompt_tokens=2, completion_tokens=1),
            _llm_result(
                {
                    "sections": [
                        {
                            "section_id": "executive_summary",
                            "title": "执行摘要",
                            "paragraphs": ["先形成报告主线，再展开重点章节。"],
                        }
                    ]
                },
                prompt_tokens=3,
                completion_tokens=2,
            ),
            _llm_result(
                {
                    "sections": [
                        {
                            "section_id": "conclusion_summary",
                            "items": [
                                {
                                    "item_key": top_edge["edge_id"],
                                    "conclusion": "Edge Id: edge_prod_sku_02_prod_sku_04_3。",
                                    "reason": "依据 3 条判断和 4 条证据，结论较强。",
                                    "action": "继续查看 evidence_id。",
                                }
                            ],
                        }
                    ]
                },
                prompt_tokens=5,
                completion_tokens=4,
            ),
            _llm_result({"sections": []}, prompt_tokens=1, completion_tokens=1),
            _llm_result({"sections": []}, prompt_tokens=1, completion_tokens=1),
            _llm_result({"sections": []}, prompt_tokens=1, completion_tokens=1),
            _llm_result(
                {
                    "sections": [
                        {
                            "section_id": "conclusion_summary",
                            "items": [
                                {
                                    "item_key": top_edge["edge_id"],
                                    "paragraphs": [
                                        (
                                            "Edge Id: edge_prod_sku_02_prod_sku_04_3，"
                                            "依据 3 条判断和 4 条证据。"
                                        ),
                                    ],
                                }
                            ],
                        }
                    ]
                },
                prompt_tokens=5,
                completion_tokens=4,
            ),
            _llm_result(
                {
                    "overall_status": "needs_revision",
                    "summary": "报告存在内部字段和审计口径，需要二次修正。",
                    "issues": [
                        {
                            "issue_type": "internal_field",
                            "severity": "high",
                            "section_id": "conclusion_summary",
                            "item_key": top_edge["edge_id"],
                            "location": f"conclusion_summary/{top_edge['edge_id']}",
                            "message": "段落暴露 Edge Id 和证据计数口径。",
                            "suggestion": "改成用户能读懂的竞争判断和行动建议。",
                        }
                    ],
                },
                prompt_tokens=6,
                completion_tokens=3,
            ),
            _llm_result(
                {
                    "sections": [
                        {
                            "section_id": "conclusion_summary",
                            "items": [
                                {
                                    "item_key": top_edge["edge_id"],
                                    "conclusion": "目标产品需要优先解释核心竞品的省心清理优势。",
                                    "reason": "用户会围绕除臭、容量和维护成本做横向比较。",
                                    "action": "把证据充足的卖点放前，证据不足处提示复核。",
                                    "paragraphs": [repair_paragraph],
                                }
                            ],
                        }
                    ]
                },
                prompt_tokens=8,
                completion_tokens=6,
            ),
        ]
    )

    writer_agent_node(state, now=NOW, llm_client=client)

    report = state["reports"][0]
    repaired_item = report["conclusion_summary"]["items"][0]
    quality_record = report["evidence_quality_appendix"]["items"][0]["llm_report_quality"]
    assert repaired_item["llm_expanded_analysis"] == [repair_paragraph]
    assert repaired_item["llm_paragraphs"] == {
        "conclusion": "目标产品需要优先解释核心竞品的省心清理优势。",
        "reason": "用户会围绕除臭、容量和维护成本做横向比较。",
        "action": "把证据充足的卖点放前，证据不足处提示复核。",
    }
    assert "Edge Id" not in " ".join(repaired_item["llm_expanded_analysis"])
    assert quality_record["质检状态"] == "已自动修正"
    assert quality_record["自动修正"]["状态"] == "已修正"
    assert state["metadata"]["writer_agent"]["llm_quality_repair"]["status"] == "applied"
    assert len(state["token_usage_logs"]) == 9
    assert client.calls[8]["schema_name"] == "writer_report_quality_repair"
    assert top_edge["edge_id"] in client.calls[8]["user_prompt"]
    assert "writer_report_quality_repair" not in client.calls[7]["schema_name"]


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


def _llm_result(
    data: dict,
    *,
    prompt_tokens: int,
    completion_tokens: int,
) -> LLMCallResult:
    return LLMCallResult(
        data=data,
        raw_text="{}",
        attempts=1,
        used_fallback=False,
        fallback_reason=None,
        errors=[],
        token_usage=LLMTokenUsage(
            model_name="Doubao-Seed-2.0-lite",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
        model_name="Doubao-Seed-2.0-lite",
    )


class _FakeWriterLLMClient:
    def __init__(self, result: LLMCallResult | list[LLMCallResult]):
        self.results = result if isinstance(result, list) else [result]
        self.calls: list[dict[str, object]] = []

    def complete_json(self, **kwargs: object) -> LLMCallResult:
        self.calls.append(kwargs)
        result_index = min(len(self.calls) - 1, len(self.results) - 1)
        return self.results[result_index]
