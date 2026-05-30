export const TERM_EXPLANATIONS = {
  context_match: {
    description: "竞品是否出现在相同价格、人群和场景中。",
    label: "上下文匹配度"
  },
  decision_stage_impact: {
    description: "它影响用户从了解、信任到下单的哪个环节。",
    label: "决策阶段影响力"
  },
  demand_substitutability: {
    description: "两件产品能满足同一需求的程度。",
    label: "需求替代性"
  },
  dynamic_slice: {
    description: "按价格、人群或场景切换同一份分析。",
    label: "动态切片"
  },
  evidence_confidence: {
    description: "支撑结论的证据是否完整、可追溯。",
    label: "证据置信度"
  },
  evidence_credibility: {
    description: "当前证据能否直接支撑页面上的说法。",
    label: "证据可信状态"
  },
  judgment_strength: {
    description: "结论从假设到明确判断的可靠程度。",
    label: "判断强度"
  },
  market_signal_strength: {
    description: "价格、卖点、评论等市场信号是否足够集中。",
    label: "市场信号强度"
  },
  quality_review: {
    description: "系统检查证据、结论和敏感表达是否可靠。",
    label: "质检"
  },
  threat_level: {
    description: "竞品对目标产品形成拦截的强弱。",
    label: "威胁等级"
  }
} as const;

export type TermKey = keyof typeof TERM_EXPLANATIONS;
