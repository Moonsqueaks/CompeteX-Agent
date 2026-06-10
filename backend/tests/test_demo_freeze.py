import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from app.graph import build_analysis_workflow, create_initial_state
from app.schemas import AnalysisTask, TaskCreateRequest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = PROJECT_ROOT / "data" / "snapshots" / "demo_sku_snapshot.json"
INTERNET_SNAPSHOT_PATH = (
    PROJECT_ROOT / "data" / "snapshots" / "internet_ai_assistant_snapshot.json"
)
STABLE_INPUT = {
    "target_product_name": "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆",
    "target_product_url": "https://v.douyin.com/mv8e4KRLLwc/",
    "category": "smart_pet_hardware",
    "subcategory": "automatic_litter_box",
    "data_source_mode": "demo_snapshot",
    "research_text": "多猫家庭关注除臭稳定性、自动清理可靠性、维护成本和小户型摆放体验。",
}
INTERNET_STABLE_INPUT = {
    "target_product_name": None,
    "target_product_url": "https://www.doubao.com/chat/",
    "category": "互联网产品",
    "subcategory": "AI 助手",
    "data_source_mode": "builtin_candidates",
    "research_text": (
        "演示聚焦通用 AI 助手在长文档研究、内容创作、编程推理、办公协作、"
        "商业模式和隐私安全边界上的竞争关系。"
    ),
}
EXPECTED_SNAPSHOT_SHA256 = (
    "8E8303BEB9E157ACF90929352493DD00330952F09438E94443A4D98E8C01111F"
)
EXPECTED_INTERNET_SNAPSHOT_SHA256 = (
    "C38F59B1BEB58AB47178E024B42EEEE5FF3C9455C2FFE0172CC2197B3D4B4DE3"
)
REQUIRED_REPORT_SECTIONS = [
    "conclusion_summary",
    "competitive_landscape_judgment",
    "core_competitor_analysis",
    "user_decision_chain_analysis",
    "target_opportunities_and_risks",
    "product_strategy_recommendations",
    "evidence_quality_appendix",
    "analysis_process_appendix",
]


def test_demo_freeze_files_lock_snapshot_and_stable_input() -> None:
    snapshot = _load_json(SNAPSHOT_PATH)

    assert _sha256(SNAPSHOT_PATH) == EXPECTED_SNAPSHOT_SHA256
    assert snapshot["snapshot_version"] == "2026-05-23.step06.v1"
    assert snapshot["default_target_sku_id"] == "sku_02"
    TaskCreateRequest.model_validate(STABLE_INPUT)


def test_frozen_qa_revision_fixture_remains_reproducible() -> None:
    snapshot = _load_json(SNAPSHOT_PATH)
    fixture = snapshot["qa_revision_fixture"]

    assert fixture["sku_id"] == "sku_01"
    assert fixture["missing_fields"] == ["source.access_time"]
    assert fixture["repair_evidence"]["access_time"] == "2026-05-23T16:00:59+08:00"
    assert fixture["repair_evidence"]["screenshot_path"] == (
        "data/raw/sku_01/QQ图片20260523155546.jpg"
    )

    sku_01 = next(sku for sku in snapshot["skus"] if sku["sku_id"] == "sku_01")
    assert sku_01["source"]["access_time"] is None


def test_internet_ai_assistant_freeze_files_lock_snapshot_and_stable_input() -> None:
    snapshot = _load_json(INTERNET_SNAPSHOT_PATH)

    assert _sha256(INTERNET_SNAPSHOT_PATH) == EXPECTED_INTERNET_SNAPSHOT_SHA256
    assert snapshot["snapshot_version"] == "internet_ai_assistant_v1"
    assert snapshot["domain_key"] == "internet_ai_assistant"
    assert snapshot["default_target_product_id"] == "doubao"
    assert {
        product["product_id"] for product in snapshot["products"]
    }.issuperset({"doubao", "kimi", "deepseek", "qianwen", "yuanbao"})
    TaskCreateRequest.model_validate(INTERNET_STABLE_INPUT)


def test_internet_ai_assistant_frozen_qa_revision_fixture_remains_reproducible() -> None:
    snapshot = _load_json(INTERNET_SNAPSHOT_PATH)
    fixture = snapshot["qa_revision_fixture"]

    assert fixture["product_id"] == "kimi"
    assert fixture["evidence_id"] == "ev_ip_kimi_homepage"
    assert fixture["missing_fields"] == ["source.screenshot_path"]
    assert fixture["repair_evidence"]["screenshot_path"] == (
        "data/raw/internet_ai_assistant/kimi/homepage.png"
    )

    kimi = next(product for product in snapshot["products"] if product["product_id"] == "kimi")
    evidence = next(
        item for item in kimi["evidence_items"] if item["evidence_id"] == "ev_ip_kimi_homepage"
    )
    assert evidence["screenshot_path"] is None


def test_same_frozen_demo_input_produces_stable_result_shape_and_report_sections() -> None:
    first = _run_demo_workflow("task_demo_freeze_001")
    second = _run_demo_workflow("task_demo_freeze_002")

    assert first == second
    assert first["task_status"] == "completed"
    assert first["agent_run_counts"] == {
        "analysis_agent": 2,
        "collection_agent": 2,
        "qa_agent": 2,
        "writer_agent": 1,
    }
    assert first["qa_issue_codes"] == ["TIMELY_EVIDENCE_MISSING_ACCESS_TIME"]
    assert first["qa_review_statuses"] == ["resolved"]
    assert first["diff_sources"] == ["analysis_agent_recompute", "collection_agent_repair"]
    assert first["report_sections"] == REQUIRED_REPORT_SECTIONS
    assert first["qa_summary"]["qa_status"] == "passed"
    assert first["qa_summary"]["current_review_task_count"] == 0
    assert first["qa_summary"]["historical_review_task_count"] == 1
    assert first["qa_summary"]["resolved_review_task_count"] == 1
    assert first["qa_summary"]["revision_message_count"] == 2
    assert first["repaired_evidence_used"] is True


def test_same_frozen_internet_ai_assistant_input_produces_stable_result_shape() -> None:
    first = _run_internet_demo_workflow("task_internet_demo_freeze_001")
    second = _run_internet_demo_workflow("task_internet_demo_freeze_002")

    assert first == second
    assert first["task_status"] == "completed"
    assert first["target_product_id"] == "doubao"
    assert first["competitor_ids"] == ["deepseek", "kimi", "qianwen", "yuanbao"]
    assert first["agent_run_counts"] == {
        "analysis_agent": 2,
        "collection_agent": 2,
        "qa_agent": 2,
        "writer_agent": 1,
    }
    assert first["qa_issue_codes"] == ["CRITICAL_EVIDENCE_MISSING_SCREENSHOT"]
    assert first["qa_review_statuses"] == ["resolved"]
    assert first["diff_sources"] == ["analysis_agent_recompute", "collection_agent_repair"]
    assert first["qa_summary"]["qa_status"] == "passed"
    assert first["qa_summary"]["current_review_task_count"] == 0
    assert first["qa_summary"]["historical_review_task_count"] == 1
    assert first["qa_summary"]["resolved_review_task_count"] == 1
    assert first["qa_summary"]["revision_message_count"] == 2
    assert first["report_sections"] == REQUIRED_REPORT_SECTIONS
    assert first["narrative_domain_key"] == "internet_ai_assistant"
    assert first["narrative_sections"] == [
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
    assert first["candidate_pool_loaded"] is True
    assert first["candidate_pool_id"] == "internet_ai_assistant_v1"
    assert first["repaired_kimi_screenshot"] == "data/raw/internet_ai_assistant/kimi/homepage.png"
    assert first["uses_ai_assistant_context"] is True
    assert first["contains_forbidden_hardware_terms"] is False


def _run_demo_workflow(task_id: str) -> dict:
    workflow = build_analysis_workflow()
    result = workflow.invoke(create_initial_state(_stable_task(task_id)))
    report = result["reports"][-1]
    battlefield = report["competitive_landscape_judgment"]
    qa_item = report["evidence_quality_appendix"]["items"][0]
    qa_summary = qa_item["qa_agent"]
    repaired_evidence_used = any(
        "ev_sku_01_repair_001" in claim.get("evidence_ids", [])
        for item in report["core_competitor_analysis"]["items"]
        for claim in item.get("claims", [])
    )

    return {
        "agent_run_counts": dict(
            sorted(Counter(run["agent_name"] for run in result["run_logs"]).items())
        ),
        "battlefield_item_count": len(battlefield["items"]),
        "claim_count": len(result["claims"]),
        "diff_sources": _diff_sources(result),
        "edge_count": len(result["competition_edges"]),
        "evidence_count": len(result["evidences"]),
        "product_count": len(result["products"]),
        "qa_issue_codes": sorted({review["issue_code"] for review in result["review_tasks"]}),
        "qa_review_statuses": sorted({review["status"] for review in result["review_tasks"]}),
        "qa_summary": {
            "current_review_task_count": qa_summary["review_task_count"],
            "historical_review_task_count": qa_item["review_task_count"],
            "qa_status": qa_summary["qa_status"],
            "resolved_review_task_count": len(qa_summary["resolved_review_task_ids"]),
            "revision_message_count": qa_item["revision_message_count"],
        },
        "repaired_evidence_used": repaired_evidence_used,
        "report_sections": report["section_order"],
        "task_status": result["task"]["status"],
    }


def _run_internet_demo_workflow(task_id: str) -> dict:
    workflow = build_analysis_workflow()
    result = workflow.invoke(create_initial_state(_internet_stable_task(task_id)))
    report = result["reports"][-1]
    qa_item = report["evidence_quality_appendix"]["items"][0]
    qa_summary = qa_item["qa_agent"]
    narrative_report = report["narrative_report"]
    visible_report_text = json.dumps(narrative_report["sections"], ensure_ascii=False)
    repaired_kimi_screenshot = next(
        evidence["screenshot_path"]
        for evidence in result["evidences"]
        if evidence["metadata"].get("repaired_from_evidence_id") == "ev_ip_kimi_homepage"
    )

    return {
        "agent_run_counts": dict(
            sorted(Counter(run["agent_name"] for run in result["run_logs"]).items())
        ),
        "candidate_pool_id": result["task"]["metadata"]["candidate_pool_id"],
        "candidate_pool_loaded": result["task"]["metadata"]["candidate_pool_loaded"],
        "claim_count": len(result["claims"]),
        "competitor_ids": sorted(
            {
                edge["competitor_product_id"]
                for edge in result["competition_edges"]
                if edge["target_product_id"] == "doubao"
            }
        ),
        "diff_sources": _diff_sources(result),
        "edge_count": len(result["competition_edges"]),
        "evidence_count": len(result["evidences"]),
        "narrative_domain_key": narrative_report["domain_key"],
        "narrative_sections": [
            section["section_id"] for section in narrative_report["sections"]
        ],
        "product_count": len(result["products"]),
        "qa_issue_codes": sorted({review["issue_code"] for review in result["review_tasks"]}),
        "qa_review_statuses": sorted({review["status"] for review in result["review_tasks"]}),
        "qa_summary": {
            "current_review_task_count": qa_summary["review_task_count"],
            "historical_review_task_count": qa_item["review_task_count"],
            "qa_status": qa_summary["qa_status"],
            "resolved_review_task_count": len(qa_summary["resolved_review_task_ids"]),
            "revision_message_count": qa_item["revision_message_count"],
        },
        "repaired_kimi_screenshot": repaired_kimi_screenshot,
        "report_sections": report["section_order"],
        "target_product_id": result["task"]["metadata"]["selected_target_product_id"],
        "task_status": result["task"]["status"],
        "uses_ai_assistant_context": (
            "商业模式/付费层" in visible_report_text
            and "AI 助手公开页快照" in visible_report_text
            and "用户规模" in visible_report_text
        ),
        "contains_forbidden_hardware_terms": any(
            term in visible_report_text
            for term in ("自动猫砂盆", "自动清理", "除臭", "铲屎", "宠物安全", "电器认证")
        ),
    }


def _stable_task(task_id: str) -> AnalysisTask:
    payload = STABLE_INPUT
    now = datetime(2026, 5, 29, 4, 0, tzinfo=UTC)
    return AnalysisTask(
        task_id=task_id,
        target_product_name=payload["target_product_name"],
        target_product_url=payload["target_product_url"],
        category=payload["category"],
        subcategory=payload["subcategory"],
        data_source_mode=payload["data_source_mode"],
        status="created",
        research_text=payload["research_text"],
        created_at=now,
        updated_at=now,
        metadata={"demo_freeze": True},
    )


def _internet_stable_task(task_id: str) -> AnalysisTask:
    payload = INTERNET_STABLE_INPUT
    now = datetime(2026, 6, 10, 12, 0, tzinfo=UTC)
    return AnalysisTask(
        task_id=task_id,
        target_product_name=payload["target_product_name"] or "豆包",
        target_product_url=payload["target_product_url"],
        category=payload["category"],
        subcategory=payload["subcategory"],
        data_source_mode=payload["data_source_mode"],
        status="created",
        research_text=payload["research_text"],
        created_at=now,
        updated_at=now,
        metadata={
            "demo_freeze": True,
            "domain_key": "internet_ai_assistant",
            "selected_target_product_id": "doubao",
            "selected_target_sku_id": "ip_doubao",
            "target_selection": "matched_candidate_pool",
            "candidate_discovery_mode": "builtin_candidates",
            "candidate_pool_id": "internet_ai_assistant_v1",
            "candidate_pool_path": "data/snapshots/internet_ai_assistant_snapshot.json",
            "candidate_pool_name": "AI 助手内置候选池",
            "candidate_pool_source": "本地互联网产品快照候选池",
            "candidate_pool_load_message": "已自动加载 AI 助手内置候选池。",
            "candidate_gap_hint": "候选池不等于结论，仍需 Evidence、Analysis 和 QA 支撑。",
            "target_match_basis": "target_product_url",
            "target_match_confidence": "exact",
            "target_status": "target_matched",
            "candidate_count": 4,
            "selected_for_analysis_count": 4,
            "candidate_pool_loaded": True,
            "candidate_source_type": "builtin_candidate_pool",
            "candidates": [
                {
                    "product_id": "doubao",
                    "sku_id": "ip_doubao",
                    "name": "豆包",
                    "role": "target",
                    "status": "target_matched",
                },
                {
                    "product_id": "kimi",
                    "sku_id": "ip_kimi",
                    "name": "Kimi",
                    "role": "direct_competitor",
                    "status": "candidate_loaded",
                },
                {
                    "product_id": "deepseek",
                    "sku_id": "ip_deepseek",
                    "name": "DeepSeek",
                    "role": "direct_competitor",
                    "status": "candidate_loaded",
                },
                {
                    "product_id": "qianwen",
                    "sku_id": "ip_qianwen",
                    "name": "千问",
                    "role": "direct_competitor",
                    "status": "candidate_loaded",
                },
                {
                    "product_id": "yuanbao",
                    "sku_id": "ip_yuanbao",
                    "name": "腾讯元宝",
                    "role": "direct_competitor",
                    "status": "candidate_loaded",
                },
            ],
        },
    )


def _diff_sources(result: dict) -> list[str]:
    sources = []
    if result["metadata"]["collection_agent_repair"]["diffs"]:
        sources.append("collection_agent_repair")
    if (
        result["metadata"]["analysis_agent_recompute"]["diffs"]
        or result["metadata"]["analysis_agent_recompute"]["claim_diffs"]
    ):
        sources.append("analysis_agent_recompute")
    return sorted(sources)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
