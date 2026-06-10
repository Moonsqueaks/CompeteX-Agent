import { isRecordValue } from "../utils/format";

export const INTERNET_AI_ASSISTANT_DOMAIN_KEY = "internet_ai_assistant";

export type DomainUiProfile = {
  categoryLabel: string;
  featureInsight: {
    cleaning: string;
    odor: string;
    safety: string;
    smart: string;
    maintenance: string;
  };
  featureTitles: {
    cleaning: string;
    odor: string;
    safety: string;
    smart: string;
    maintenance: string;
  };
  isInternetAiAssistant: boolean;
  productLinkLabel: string;
  productNameLabel: string;
  pricingCardTitle: string;
  pricingEvidenceLabel: string;
  pricingMetricLabel: string;
  sliceAxisLabel: string;
  sliceHint: string;
  slicePlaceholder: string;
  sliceSummaryLabel: string;
};

export const SMART_LITTER_BOX_UI_PROFILE: DomainUiProfile = {
  categoryLabel: "自动猫砂盆",
  featureInsight: {
    cleaning: "这部分判断目标产品能否减少日常铲屎和清理负担，是自动猫砂盆最核心的购买理由。",
    maintenance: "这部分用于判断长期使用是否省心，包括耗材、清洁频率、套装和后续复核成本。",
    odor: "这部分关注气味管理是否有明确证据支撑；如果没有可靠来源，页面会保守显示为待补证。",
    safety: "这部分涉及宠物安全和电器安全，必须有更谨慎的证据边界，不能把宣传语直接写成确定事实。",
    smart: "这部分说明产品是否能通过可视化、电动控制或自动化体验降低用户操作成本。"
  },
  featureTitles: {
    cleaning: "清洁能力",
    maintenance: "维护成本",
    odor: "除臭能力",
    safety: "安全能力",
    smart: "智能能力"
  },
  isInternetAiAssistant: false,
  pricingCardTitle: "价格与证据",
  pricingEvidenceLabel: "价格证据",
  pricingMetricLabel: "价格带",
  productLinkLabel: "商品链接",
  productNameLabel: "SKU 名称",
  sliceAxisLabel: "价格带",
  sliceHint: "按价格带、人群和使用场景刷新判断",
  slicePlaceholder: "全部价格带",
  sliceSummaryLabel: "价格带"
};

export const INTERNET_AI_ASSISTANT_UI_PROFILE: DomainUiProfile = {
  categoryLabel: "AI 助手",
  featureInsight: {
    cleaning: "这部分判断目标产品是否覆盖对话问答、搜索研究、文档处理等高频任务入口。",
    maintenance: "这部分用于判断订阅、API、企业版或迁移成本等商业化信息是否有可靠证据。",
    odor: "这部分关注内容创作、多模态、办公协作等扩展能力是否有官方公开页证据支撑。",
    safety: "这部分涉及隐私、安全、企业能力和使用边界，必须保守表达，不能写成绝对承诺。",
    smart: "这部分说明智能体、工作流、平台入口和生态整合是否能降低用户任务完成成本。"
  },
  featureTitles: {
    cleaning: "核心任务能力",
    maintenance: "商业化与迁移成本",
    odor: "创作与多模态能力",
    safety: "隐私安全与企业能力",
    smart: "智能体与生态入口"
  },
  isInternetAiAssistant: true,
  pricingCardTitle: "商业模式与证据",
  pricingEvidenceLabel: "商业模式证据",
  pricingMetricLabel: "商业模式/付费层",
  productLinkLabel: "产品入口",
  productNameLabel: "产品名称",
  sliceAxisLabel: "商业模式/付费层",
  sliceHint: "按商业模式、人群和使用场景刷新判断",
  slicePlaceholder: "全部付费层",
  sliceSummaryLabel: "商业模式"
};

export function domainUiProfileFromFields(fields: {
  category?: string | null;
  domainKey?: string | null;
  metadata?: unknown;
  productUrl?: string | null;
  subcategory?: string | null;
  tags?: string[] | null;
  textHints?: unknown[] | null;
}) {
  return isInternetAiAssistantDomain(fields)
    ? INTERNET_AI_ASSISTANT_UI_PROFILE
    : SMART_LITTER_BOX_UI_PROFILE;
}

export function isInternetAiAssistantDomain(fields: {
  category?: string | null;
  domainKey?: string | null;
  metadata?: unknown;
  productUrl?: string | null;
  subcategory?: string | null;
  tags?: string[] | null;
  textHints?: unknown[] | null;
}) {
  const metadataDomainKey = metadataString(fields.metadata, "domain_key");
  const text = [
    fields.domainKey,
    metadataDomainKey,
    fields.category,
    fields.subcategory,
    fields.productUrl,
    ...(fields.tags ?? []),
    ...flattenDomainHints(fields.textHints ?? []),
    ...flattenDomainHints(fields.metadata)
  ]
    .filter((item): item is string => typeof item === "string" && item.length > 0)
    .join(" ")
    .toLowerCase();

  return (
    text.includes(INTERNET_AI_ASSISTANT_DOMAIN_KEY) ||
    text.includes("ai 助手") ||
    text.includes("ai_assistant") ||
    text.includes("互联网产品") ||
    text.includes("doubao.com") ||
    text.includes("kimi.com") ||
    text.includes("deepseek.com") ||
    text.includes("qianwen.com") ||
    text.includes("yuanbao.tencent.com") ||
    text.includes("freemium") ||
    text.includes("api/开发者") ||
    text.includes("开发者付费") ||
    text.includes("订阅") ||
    text.includes("会员") ||
    text.includes("企业版")
  );
}

export function metadataString(metadata: unknown, key: string) {
  if (!isRecordValue(metadata)) {
    return null;
  }
  const value = metadata[key];
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function flattenDomainHints(value: unknown): string[] {
  if (typeof value === "string") {
    return [value];
  }

  if (Array.isArray(value)) {
    return value.flatMap(flattenDomainHints);
  }

  if (isRecordValue(value)) {
    return Object.values(value).flatMap(flattenDomainHints);
  }

  return [];
}
