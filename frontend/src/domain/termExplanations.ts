export type TermExplanation = {
  name: string;
  professional: string;
  scenario: string;
};

export const TERM_DICTIONARY = {
  context_match: {
    name: "场景匹配度",
    professional: "评估竞品与目标产品在使用环境、目标人群和预算范围上的吻合度。",
    scenario: "业务思考：这两款产品是否在抢夺同一类预算和生活场景下的用户？"
  },
  decision_stage_impact: {
    name: "购买路径影响",
    professional: "反映该竞品在用户从了解到下单的哪个环节产生了最强的拦截作用。",
    scenario: "业务思考：它是在哪一步抢走用户的？是因为参数更好，还是因为评论更真实？"
  },
  demand_substitutability: {
    name: "需求替代性",
    professional: "衡量两款产品在核心功能与解决用户底层痛点上的重合程度。",
    scenario: "业务思考：如果用户买了这款竞品，是否意味着不再需要你的产品？"
  },
  dynamic_slice: {
    name: "动态切片",
    professional: "按价格带、人群或使用场景重新观察同一组竞品关系。",
    scenario: "业务思考：把同一张竞争地图切成不同沙盘，看看换预算或换人群后谁会突然变强。"
  },
  evidence_confidence: {
    name: "证据支撑度",
    professional: "衡量当前评分背后证据的完整性、可追溯性和时效性。",
    scenario: "业务思考：分数看起来高不高是一回事，更要看背后有没有足够可靠的截图、来源和访问时间。"
  },
  evidence_credibility: {
    name: "证据可信度",
    professional: "系统对底层数据完整性和时效性的评估。",
    scenario: "业务思考：高可信说明有确凿数据支撑；低可信说明大模型存在推测成分，建议人工核实。"
  },
  judgment_strength: {
    name: "判断强度",
    professional: "表示当前结论从初步假设到明确判断之间的可靠程度。",
    scenario: "业务思考：强判断适合进入策略会；弱判断更像待验证线索，先别急着拍板。"
  },
  market_signal_strength: {
    name: "市场信号强度",
    professional: "评估价格、评论、卖点和内容共现等市场信号是否集中指向同一竞争关系。",
    scenario: "业务思考：如果用户讨论、商品卖点和价格优势都指向它，就说明它不是偶然冒出来的对手。"
  },
  quality_review: {
    name: "QA 质检打回",
    professional: "多智能体架构中的独立审核机制，负责驳回缺乏证据或逻辑冲突的初步分析结论。",
    scenario: "业务思考：看到打回记录，说明系统刚刚自我纠正了一个可能误导业务判断的问题。"
  },
  threat_level: {
    name: "综合威胁等级",
    professional: "基于算法多维评分计算出的整体竞争威胁评级。",
    scenario: "业务思考：高威胁代表用户极易流失至该产品，需优先制定应对策略。"
  }
} satisfies Record<string, TermExplanation>;

export type TermKey = keyof typeof TERM_DICTIONARY;

export function isTermKey(value: string): value is TermKey {
  return Object.prototype.hasOwnProperty.call(TERM_DICTIONARY, value);
}
