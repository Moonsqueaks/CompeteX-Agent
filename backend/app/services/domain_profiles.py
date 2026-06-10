from dataclasses import dataclass
from pathlib import Path

from app.schemas.common import JsonObject

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SMART_LITTER_BOX_DOMAIN = "smart_litter_box"
INTERNET_AI_ASSISTANT_DOMAIN = "internet_ai_assistant"


@dataclass(frozen=True)
class CandidatePoolProfile:
    pool_id: str
    pool_type: str
    snapshot_path: Path
    target_match_fields: tuple[str, ...]
    candidate_roles: tuple[str, ...]
    display_name: str
    source_description: str
    load_message: str
    gap_hint: str


@dataclass(frozen=True)
class DomainProfile:
    domain_key: str
    category: str
    subcategory: str
    snapshot_path: Path
    default_target_id: str
    target_url_required: bool
    feature_axes: tuple[str, ...]
    slice_axes: tuple[str, ...]
    decision_stages: tuple[str, ...]
    qa_terms: tuple[str, ...]
    report_template: tuple[str, ...]
    candidate_pool: CandidatePoolProfile


class DomainProfileError(Exception):
    def __init__(self, code: str, message: str, details: JsonObject | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


SMART_LITTER_BOX_PROFILE = DomainProfile(
    domain_key=SMART_LITTER_BOX_DOMAIN,
    category="smart_pet_hardware",
    subcategory="automatic_litter_box",
    snapshot_path=PROJECT_ROOT / "data" / "snapshots" / "demo_sku_snapshot.json",
    default_target_id="sku_02",
    target_url_required=True,
    feature_axes=(
        "自动清理",
        "除臭控味",
        "安全防护",
        "智能体验",
        "维护成本",
    ),
    slice_axes=("价格带", "用户人群", "使用场景"),
    decision_stages=("信息触达", "兴趣形成", "能力理解", "信任建立", "决策完成"),
    qa_terms=("价格", "访问时间", "截图", "认证", "宠物安全"),
    report_template=(
        "执行摘要",
        "竞争格局",
        "核心竞品 Battlecard",
        "差距矩阵",
        "机会地图",
        "Evidence 索引",
    ),
    candidate_pool=CandidatePoolProfile(
        pool_id="smart_litter_box_v1",
        pool_type="snapshot",
        snapshot_path=PROJECT_ROOT / "data" / "snapshots" / "demo_sku_snapshot.json",
        target_match_fields=("source_url", "sku_id", "product_name"),
        candidate_roles=(
            "target",
            "direct_competitor",
            "alternative",
            "channel_alternative",
            "reference",
        ),
        display_name="自动猫砂盆本地候选池",
        source_description="本地脱敏 SKU 快照",
        load_message="已自动加载猫砂盆内置候选池",
        gap_hint="价格访问时间、截图、认证和评论聚类证据可能需要补充。",
    ),
)

INTERNET_AI_ASSISTANT_PROFILE = DomainProfile(
    domain_key=INTERNET_AI_ASSISTANT_DOMAIN,
    category="互联网产品",
    subcategory="AI 助手",
    snapshot_path=PROJECT_ROOT / "data" / "snapshots" / "internet_ai_assistant_snapshot.json",
    default_target_id="doubao",
    target_url_required=True,
    feature_axes=(
        "对话问答",
        "搜索与深度研究",
        "文档处理",
        "内容创作",
        "编程与推理",
        "多模态能力",
        "智能体/工作流",
        "生态与分发入口",
        "隐私、安全与企业能力",
    ),
    slice_axes=("商业模式/付费层", "用户人群", "使用场景"),
    decision_stages=("认知", "试用", "留存", "付费", "生态迁移"),
    qa_terms=("定价", "访问时间", "截图", "应用商店", "登录后功能", "隐私"),
    report_template=(
        "执行摘要",
        "AI 助手竞争格局",
        "核心竞品 Battlecard",
        "能力差距矩阵",
        "机会地图",
        "Evidence 索引",
    ),
    candidate_pool=CandidatePoolProfile(
        pool_id="internet_ai_assistant_v1",
        pool_type="snapshot",
        snapshot_path=PROJECT_ROOT
        / "data"
        / "snapshots"
        / "internet_ai_assistant_snapshot.json",
        target_match_fields=("official_url", "official_urls", "product_id", "product_name"),
        candidate_roles=("target", "direct_competitor", "alternative", "reference"),
        display_name="AI 助手本地候选池",
        source_description="官方公开页快照",
        load_message="已自动加载 AI 助手内置候选池",
        gap_hint="定价、应用商店、登录后功能和关键截图证据可能需要补充。",
    ),
)

DOMAIN_PROFILES = {
    SMART_LITTER_BOX_PROFILE.domain_key: SMART_LITTER_BOX_PROFILE,
    INTERNET_AI_ASSISTANT_PROFILE.domain_key: INTERNET_AI_ASSISTANT_PROFILE,
}


def get_domain_profile(domain_key: str) -> DomainProfile:
    normalized = _normalize_domain_key(domain_key)
    profile = DOMAIN_PROFILES.get(normalized)
    if profile is None:
        raise DomainProfileError(
            code="UNKNOWN_DOMAIN",
            message="Unsupported analysis domain.",
            details={"domain_key": domain_key},
        )
    return profile


def infer_domain_key(
    category: str | None,
    subcategory: str | None,
    target_product_url: str | None = None,
    target_product_name: str | None = None,
) -> str:
    category_text = _normalize_text(category)
    subcategory_text = _normalize_text(subcategory)
    target_url = _normalize_text(target_product_url).lower()
    target_name = _normalize_text(target_product_name).lower()
    if category_text in {"互联网产品", "internet_product"} or subcategory_text in {
        "AI 助手",
        "ai_assistant",
        "internet_ai_assistant",
    }:
        return INTERNET_AI_ASSISTANT_DOMAIN
    if any(
        marker in target_url
        for marker in (
            "doubao.com",
            "kimi.com",
            "deepseek.com",
            "qianwen.com",
            "yuanbao.tencent.com",
        )
    ) or target_name in {
        "doubao",
        "豆包",
        "kimi",
        "deepseek",
        "qianwen",
        "千问",
        "通义千问",
        "yuanbao",
        "腾讯元宝",
    }:
        return INTERNET_AI_ASSISTANT_DOMAIN
    if category_text in {"smart_pet_hardware", "智能宠物硬件"} or subcategory_text in {
        "automatic_litter_box",
        "自动猫砂盆",
    }:
        return SMART_LITTER_BOX_DOMAIN
    return SMART_LITTER_BOX_DOMAIN


def profile_payload(profile: DomainProfile) -> JsonObject:
    return {
        "domain_key": profile.domain_key,
        "category": profile.category,
        "subcategory": profile.subcategory,
        "snapshot_path": _project_relative(profile.snapshot_path),
        "default_target_id": profile.default_target_id,
        "target_url_required": profile.target_url_required,
        "feature_axes": list(profile.feature_axes),
        "slice_axes": list(profile.slice_axes),
        "decision_stages": list(profile.decision_stages),
        "qa_terms": list(profile.qa_terms),
        "report_template": list(profile.report_template),
        "candidate_pool": candidate_pool_payload(profile.candidate_pool),
    }


def candidate_pool_payload(candidate_pool: CandidatePoolProfile) -> JsonObject:
    return {
        "pool_id": candidate_pool.pool_id,
        "pool_type": candidate_pool.pool_type,
        "snapshot_path": _project_relative(candidate_pool.snapshot_path),
        "target_match_fields": list(candidate_pool.target_match_fields),
        "candidate_roles": list(candidate_pool.candidate_roles),
        "display_name": candidate_pool.display_name,
        "source_description": candidate_pool.source_description,
        "load_message": candidate_pool.load_message,
        "gap_hint": candidate_pool.gap_hint,
    }


def _normalize_domain_key(domain_key: str) -> str:
    return domain_key.strip().lower()


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def _project_relative(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()
