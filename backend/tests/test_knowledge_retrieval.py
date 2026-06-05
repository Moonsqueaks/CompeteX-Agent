from datetime import UTC, datetime

from app.services.knowledge_retrieval import (
    KnowledgeRetrievalService,
    compact_knowledge_for_llm,
)

NOW = datetime(2026, 6, 5, 3, 0, tzinfo=UTC)


def test_knowledge_retrieval_builds_auditable_local_artifact() -> None:
    artifact = KnowledgeRetrievalService().retrieve_for_writer(
        state={
            "task": {
                "task_id": "task_knowledge",
                "target_product_name": "小佩自动猫砂盆 MAX PRO 2",
                "category": "智能宠物硬件",
                "subcategory": "自动猫砂盆",
            }
        },
        report_items=[
            {
                "scenario": "除臭控味",
                "persona": "多猫家庭",
                "recommendation": "优先解释维护成本",
            }
        ],
        now=NOW,
    )

    assert artifact.knowledge_id == "knowledge_task_knowledge_writer_v1"
    assert artifact.retrieval_mode == "local_static_category_framework"
    assert artifact.external_search_performed is False
    assert artifact.sources[0].source_type == "local_category_framework"
    assert artifact.sources[0].access_time == NOW
    assert artifact.items
    assert any(item.dimension == "除臭与封闭性" for item in artifact.items)
    assert "具体产品事实" in artifact.items[0].use_policy
    assert "本次未执行外部实时检索。" in artifact.limitations


def test_compact_knowledge_for_llm_keeps_source_and_boundary() -> None:
    artifact = KnowledgeRetrievalService().retrieve_for_writer(
        state={"task": {"task_id": "task_compact"}},
        report_items=[],
        now=NOW,
    )

    compact = compact_knowledge_for_llm([artifact], max_items=2)

    assert compact["knowledge_id"] == "knowledge_task_compact_writer_v1"
    assert compact["external_search_performed"] is False
    assert compact["use_as"] == "可审计的分析框架；不能当作具体 SKU 事实。"
    assert len(compact["items"]) == 2
    assert compact["items"][0]["source_names"] == ["CompeteX MVP 自动猫砂盆类目分析框架"]
    assert "本次未执行外部实时检索。" in compact["limitations"]
