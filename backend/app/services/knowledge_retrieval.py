from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from app.schemas import KnowledgeArtifact, KnowledgeItem, KnowledgeSource
from app.schemas.common import ConfidenceLevel, JsonObject

KNOWLEDGE_ARTIFACT_TYPE = "knowledge_artifact"
LOCAL_KNOWLEDGE_SOURCE_ID = "src_local_auto_litter_box_framework_v1"


class KnowledgeRetrievalService:
    """Build auditable category knowledge artifacts for Writer prompts."""

    def retrieve_for_writer(
        self,
        *,
        state: Mapping[str, Any],
        report_items: Sequence[Mapping[str, Any]] = (),
        now: datetime | None = None,
    ) -> KnowledgeArtifact:
        generated_at = now or datetime.now(UTC)
        task = _mapping_value(state.get("task"))
        task_id = _string_value(task.get("task_id"), fallback="unknown_task")
        category = _string_value(task.get("category"), fallback="智能宠物硬件")
        subcategory = _string_value(task.get("subcategory"), fallback="自动猫砂盆")
        target_name = _string_value(task.get("target_product_name"), fallback="目标产品")
        focus_dimensions = _focus_dimensions(report_items)
        items = _local_category_items(focus_dimensions)

        return KnowledgeArtifact(
            knowledge_id=f"knowledge_{task_id}_writer_v1",
            task_id=task_id,
            category=category,
            subcategory=subcategory,
            generated_at=generated_at,
            retrieval_mode="local_static_category_framework",
            external_search_performed=False,
            query_context={
                "target_product_name": target_name,
                "focus_dimensions": focus_dimensions,
                "report_item_count": len(report_items),
                "retrieval_intent": (
                    "补充自动猫砂盆类目的通用决策维度和竞品分析框架，"
                    "用于帮助 Writer 组织报告推理。"
                ),
            },
            sources=[
                KnowledgeSource(
                    source_id=LOCAL_KNOWLEDGE_SOURCE_ID,
                    source_type="local_category_framework",
                    source_name="CompeteX MVP 自动猫砂盆类目分析框架",
                    source_url=None,
                    access_time=generated_at,
                    confidence_level=ConfidenceLevel.MEDIUM,
                    limitations=[
                        "该来源是本地通用分析框架，不代表实时行业数据。",
                        "不能作为具体 SKU 的价格、销量、认证、排名或真实评论依据。",
                    ],
                )
            ],
            items=items,
            limitations=[
                "本次未执行外部实时检索。",
                "知识项只能帮助组织分析维度，具体产品判断必须回到 "
                "Evidence、Claim 和 CompetitionEdge。",
                "涉及宠物安全、电器认证、销量、价格和排名时必须保持保守。",
            ],
            metadata={
                "version": "local_auto_litter_box_framework_v1",
                "future_external_retrieval": {
                    "required_fields": [
                        "source_url",
                        "access_time",
                        "confidence_level",
                        "limitations",
                    ],
                    "policy": "外部知识必须先保存为 KnowledgeArtifact，再允许 Writer 引用。",
                },
            },
        )


def compact_knowledge_for_llm(
    knowledge_artifacts: Sequence[KnowledgeArtifact | Mapping[str, Any]],
    *,
    max_items: int = 8,
) -> JsonObject:
    if not knowledge_artifacts:
        return {}

    artifact = KnowledgeArtifact.model_validate(knowledge_artifacts[-1])
    sources_by_id = {source.source_id: source for source in artifact.sources}
    return {
        "knowledge_id": artifact.knowledge_id,
        "retrieval_mode": artifact.retrieval_mode,
        "external_search_performed": artifact.external_search_performed,
        "use_as": "可审计的分析框架；不能当作具体 SKU 事实。",
        "query_context": artifact.query_context,
        "items": [
            {
                "title": item.title,
                "dimension": item.dimension,
                "content": item.content,
                "use_policy": item.use_policy,
                "source_names": [
                    sources_by_id[source_id].source_name
                    for source_id in item.source_ids
                    if source_id in sources_by_id
                ],
                "tags": item.tags,
            }
            for item in artifact.items[:max_items]
        ],
        "limitations": artifact.limitations,
    }


def _local_category_items(focus_dimensions: Sequence[str]) -> list[KnowledgeItem]:
    base_items = [
        _knowledge_item(
            "cleaning_burden",
            "清理负担是自动猫砂盆的首要比较轴",
            "清理负担",
            "用户通常不是单看是否自动，而是比较日常铲屎频率、清理动作数量、清洗难度和故障后的补救成本。",
            ["清理", "维护", "决策维度"],
        ),
        _knowledge_item(
            "odor_control",
            "除臭表现会影响家庭接受度",
            "除臭与封闭性",
            "自动猫砂盆的除臭表达需要区分封闭结构、清理频率、耗材和使用空间，不能只用“无异味”作确定承诺。",
            ["除臭", "家庭场景", "保守表达"],
        ),
        _knowledge_item(
            "capacity_multi_cat",
            "容量和多猫适配决定高频使用场景",
            "容量与多猫适配",
            "多猫或大空间用户更关注容量、连续使用稳定性、清理间隔和设备是否容易被频繁使用压垮。",
            ["容量", "多猫", "场景切片"],
        ),
        _knowledge_item(
            "safety_reliability",
            "安全可靠性必须保守处理",
            "安全与可靠性",
            "宠物电器类产品涉及传感器、卡猫风险、电器稳定性和售后保障；没有可靠证据时只能写需要复核。",
            ["安全", "认证", "风险"],
        ),
        _knowledge_item(
            "ownership_cost",
            "维护成本会改变用户对价格的判断",
            "维护成本",
            "用户会把到手价、耗材、清洗时间、故障风险和售后成本一起理解为长期使用成本。",
            ["价格", "耗材", "长期成本"],
        ),
        _knowledge_item(
            "message_clarity",
            "卖点表达应转成用户收益",
            "信息表达",
            "报告和商品表达都应把功能堆叠翻译成用户能理解的收益，例如更少清理、更低异味顾虑、更容易维护。",
            ["表达", "转化", "行动建议"],
        ),
        _knowledge_item(
            "competitive_frame",
            "竞品分析应围绕同一购买任务比较",
            "竞品分析框架",
            "判断竞品时优先看是否解决同一用户任务、是否出现在同一价格带或使用场景、是否影响同一决策阶段。",
            ["竞品框架", "切片", "决策链"],
        ),
    ]
    if not focus_dimensions:
        return base_items

    preferred: list[KnowledgeItem] = []
    deferred: list[KnowledgeItem] = []
    focus_text = " ".join(focus_dimensions)
    for item in base_items:
        if item.dimension in focus_text or any(tag in focus_text for tag in item.tags):
            preferred.append(item)
        else:
            deferred.append(item)
    return [*preferred, *deferred]


def _knowledge_item(
    item_id: str,
    title: str,
    dimension: str,
    content: str,
    tags: list[str],
) -> KnowledgeItem:
    return KnowledgeItem(
        item_id=f"knowledge_item_{item_id}",
        title=title,
        dimension=dimension,
        content=content,
        use_policy="只能作为分析框架，不得写成具体产品事实。",
        source_ids=[LOCAL_KNOWLEDGE_SOURCE_ID],
        tags=tags,
    )


def _focus_dimensions(report_items: Sequence[Mapping[str, Any]]) -> list[str]:
    dimensions: list[str] = []
    for item in report_items:
        for key in ("price_band", "persona", "scenario", "decision_stage", "recommendation"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                dimensions.append(value.strip())
        competitor = item.get("competitor")
        if isinstance(competitor, Mapping):
            name = competitor.get("name")
            if isinstance(name, str) and name.strip():
                dimensions.append(name.strip())
    return _dedupe(dimensions)[:12]


def _mapping_value(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_value(value: object, *, fallback: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else fallback


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
