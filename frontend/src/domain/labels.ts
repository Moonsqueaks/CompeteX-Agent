export const TASK_STATUS_LABELS: Record<string, string> = {
  analyzing: "分析中",
  collecting: "采集中",
  completed: "已完成",
  created: "已创建",
  failed: "失败",
  human_reviewing: "人工复核中",
  partial_failed: "部分失败",
  reviewing: "质检中",
  writing: "报告生成中"
};

export const ROUTE_STATUS_COPY: Record<string, string> = {
  "/": "任务输入就绪",
  "/overview": "总览数据就绪",
  "/profile": "画像数据就绪",
  "/battlefield": "图谱数据就绪",
  "/report": "报告数据就绪",
  "/trace": "追踪数据就绪"
};

export const WORKFLOW_STATUS_LABELS: Record<string, string> = {
  completed: "已完成",
  created: "已创建",
  failed: "失败",
  partial_failed: "部分失败",
  requires_revision: "需要修复",
  reviewing: "质检中",
  running: "运行中",
  succeeded: "成功",
  writing: "报告生成中"
};

export const AGENT_LABELS: Record<string, string> = {
  analysis_agent: "分析智能体",
  collection_agent: "采集智能体",
  human: "人工复核",
  orchestrator: "流程编排",
  qa_agent: "质检智能体",
  writer_agent: "报告智能体"
};

export const RUN_STATUS_LABELS: Record<string, string> = {
  failed: "失败",
  requires_revision: "需要打回",
  running: "运行中",
  skipped: "跳过",
  started: "已开始",
  succeeded: "成功"
};

export const TOOL_STATUS_LABELS: Record<string, string> = {
  failed: "失败",
  skipped: "跳过",
  succeeded: "成功"
};

export const REVIEW_SEVERITY_LABELS: Record<string, string> = {
  blocker: "阻断",
  error: "错误",
  info: "提示",
  warning: "警告"
};

export const REVIEW_STATUS_LABELS: Record<string, string> = {
  open: "未处理",
  resolved: "已解决",
  waived: "已豁免"
};

export const TRACE_TARGET_TYPE_LABELS: Record<string, string> = {
  claim: "结论",
  competition_edge: "竞争关系",
  evidence: "证据",
  feature_tree: "功能树",
  pricing_model: "价格模型",
  product: "产品",
  product_profile: "产品画像",
  report: "报告",
  task: "任务",
  user_persona: "用户人群"
};

export const TRACE_DIFF_STATUS_LABELS: Record<string, string> = {
  applied: "已应用",
  partial: "部分处理",
  recomputed: "已重算",
  repaired: "已修复",
  resolved: "已解决",
  updated: "已更新"
};

export const TRACE_NODE_STATUS_LABELS: Record<string, string> = {
  completed: "已完成",
  created: "已创建",
  failed: "失败",
  pending: "等待中",
  requires_revision: "需要打回",
  running: "运行中",
  skipped: "跳过",
  succeeded: "成功"
};

export const TRACE_TAB_LABELS: Record<string, string> = {
  agent_process: "智能体过程",
  diff_records: "差异记录",
  evidence_chain: "证据链",
  quality_records: "质检记录"
};

export const RISK_FLAG_LABELS: Record<string, string> = {
  conflicting_analysis: "分析冲突",
  missing_access_time: "缺少访问时间",
  missing_evidence: "缺少证据",
  missing_screenshot: "缺少截图",
  sensitive_claim: "敏感表达",
  single_review_overgeneralized: "单条评论过度概括",
  unreliable_data: "数据不可靠",
  unsupported_inference: "推断待补证"
};

export const TRACE_RISK_FLAG_LABELS: Record<string, string> = {
  ...RISK_FLAG_LABELS,
  unreliable_data: "数据不可依赖"
};

export const OVERVIEW_RELATIONSHIP_LABELS: Record<string, string> = {
  content_seeding_competition: "内容种草竞争",
  head_to_head: "正面竞争",
  low_price_interception: "低价拦截",
  scenario_substitute: "场景替代",
  trust_suppression: "信任压制"
};

export const OVERVIEW_THREAT_LABELS: Record<string, string> = {
  high_score_needs_review: "高分需复核",
  high_threat: "高威胁",
  low_threat: "低威胁",
  medium_threat: "中威胁"
};

export const OVERVIEW_ACTION_PRIORITY_LABELS: Record<string, string> = {
  p0_immediate: "P0 立即处理",
  p1_current_iteration: "P1 本轮优化",
  p2_follow_up_validation: "P2 后续验证"
};

export const OVERVIEW_RESPONSIBILITY_LABELS: Record<string, string> = {
  content_expression: "内容表达",
  evidence_research: "证据补研",
  pricing_strategy: "价格策略",
  product_feature: "产品功能"
};

export const OVERVIEW_THREAT_TAG_COLORS: Record<string, string> = {
  high_score_needs_review: "orange",
  high_threat: "red",
  low_threat: "green",
  medium_threat: "gold"
};

export const BATTLEFIELD_THREAT_TAG_COLORS: Record<string, string> = {
  high_score_needs_review: "orange",
  high_threat: "red",
  low_threat: "blue",
  medium_threat: "gold"
};

export const DISPLAY_STATUS_COLORS: Record<string, string> = {
  clear_judgment: "green",
  evidence_insufficient: "orange",
  needs_review: "orange",
  ready_for_initial_decision: "green",
  risk_blocked: "red",
  weak_signal: "blue"
};

export const COMPETITION_TYPE_LABELS: Record<string, string> = {
  alternative: "需求替代",
  channel: "渠道替代",
  channel_alternative: "渠道替代",
  content_cooccurrence: "内容共现",
  direct: "直接竞品",
  direct_competitor: "直接竞品",
  reference: "参考对象"
};

export const DECISION_STAGE_LABELS: Record<string, string> = {
  capability_understanding: "能力理解",
  decision_completion: "决策完成",
  information_reach: "信息触达",
  interest_formation: "兴趣形成",
  trust_building: "信任建立"
};

export const SCORE_BREAKDOWN_LABELS: Record<string, string> = {
  context_match: "场景匹配度",
  decision_stage_impact: "购买路径影响",
  demand_substitutability: "需求替代性",
  evidence_confidence: "证据支撑度",
  market_signal_strength: "市场信号强度"
};

export const SCORE_BREAKDOWN_DESCRIPTIONS: Record<string, string> = {
  context_match: "看这条关系是否匹配当前价格带、人群和使用场景。",
  decision_stage_impact: "看它会影响用户从了解、信任到下单的哪个关键阶段。",
  demand_substitutability: "看用户是否会把两款产品当成同一个需求下的二选一方案。",
  evidence_confidence: "看当前判断背后有多少可追溯证据，证据是否完整、可信。",
  market_signal_strength: "看商品页、评论和内容信号是否共同指向这条竞争关系。"
};

export const SOURCE_TYPE_LABELS: Record<string, string> = {
  derived_artifact: "派生分析产物",
  douyin_review_snapshot: "抖音评论快照",
  douyin_sku_snapshot: "抖音商品快照",
  ecommerce_page: "电商商品页",
  human_research: "用户研究材料",
  interview_note: "访谈材料",
  local_snapshot: "本地脱敏快照",
  manual_review: "人工复核",
  questionnaire: "问卷材料",
  repaired_snapshot: "补充后的本地快照",
  review_snapshot: "评论快照",
  user_research: "用户研究材料"
};

export const CLAIM_STATUS_LABELS: Record<string, string> = {
  accepted: "已采纳",
  draft: "草稿",
  needs_review: "需复核",
  rejected: "不采纳"
};

export const BATTLEFIELD_CLAIM_STATUS_LABELS: Record<string, string> = {
  accepted: "已采纳",
  needs_review: "需复核",
  rejected: "已拒绝"
};

export const EVIDENCE_CONFIDENCE_LABELS: Record<string, string> = {
  high: "高可信度",
  low: "低可信度",
  medium: "中等可信度"
};

export const CONFIDENCE_LABELS: Record<string, string> = {
  high: "高",
  low: "低",
  medium: "中",
  unknown: "未知"
};

export const CONFIDENCE_DETAIL_LABELS: Record<string, string> = {
  high: "高可信度",
  low: "低可信度，建议补充验证",
  medium: "中等可信度",
  unknown: "可信度未知"
};

export const ACCESS_TIME_STATUS_LABELS: Record<string, string> = {
  available: "访问时间已记录",
  missing: "缺少访问时间",
  unavailable: "暂无访问时间"
};

export const TECHNICAL_MODEL_LABELS: Record<string, string> = {
  local_rule_flow: "本地规则流程"
};

export const TOOL_NAME_LABELS: Record<string, string> = {
  analysis_recompute: "重新计算竞争关系",
  evidence_repair: "补齐证据材料",
  qa_rules: "执行 QA 规则检查",
  report_writer: "生成分析报告",
  snapshot_loader: "读取本地商品快照",
  word_report_export: "生成 Word 报告"
};

export const REPORT_FIELD_LABELS: Record<string, string> = {
  access_time: "访问时间",
  analysis_recompute: "分析智能体重算",
  basis_edge_id: "依据竞争关系",
  brand: "品牌",
  claim_ids: "分析判断",
  claims: "分析判断",
  collection_repair: "采集智能体修复",
  competitor: "竞品",
  competition_type: "竞争类型",
  confidence: "置信度",
  confidence_level: "置信度",
  content: "正文",
  content_summary: "内容摘要",
  decision_factors: "决策因素",
  decision_stage: "决策阶段",
  decision_stages: "决策阶段",
  edge_score: "竞争分",
  evidence_ids: "证据材料",
  final_price: "到手价",
  is_inference: "推断标识",
  limitations: "局限性",
  list_price: "标价",
  pain_points: "痛点",
  persona: "人群",
  personas: "目标人群",
  price_band: "价格带",
  product: "产品",
  product_url: "商品链接",
  qa_agent: "质检智能体",
  recommendation: "建议",
  review_task_count: "质检问题数",
  revision_message_count: "打回消息",
  risk_flags: "风险标记",
  scenario: "使用场景",
  score_breakdown: "评分拆解",
  shop_name: "店铺",
  slice: "分析场景",
  source_type: "来源类型",
  source_url: "来源链接",
  status: "状态",
  summary: "摘要",
  top_edge_score: "最高竞争分"
};

export const REPORT_SECTION_FALLBACK_TITLES: Record<string, string> = {
  analysis_process_appendix: "分析流程与系统能力附录",
  competitive_landscape_judgment: "竞争格局判断",
  conclusion_summary: "结论摘要",
  core_competitor_analysis: "核心竞品拆解",
  evidence_quality_appendix: "证据与质检附录",
  product_strategy_recommendations: "产品策略建议",
  target_opportunities_and_risks: "目标产品机会与风险",
  user_decision_chain_analysis: "用户决策链分析"
};

export const REPORT_SECTION_PREVIEW_LIMITS: Record<string, number> = {
  competitive_landscape_judgment: 3,
  core_competitor_analysis: 3,
  decision_chain_analysis: 3,
  dynamic_slice_analysis: 3,
  user_decision_chain_analysis: 3
};

export const DECISION_STAGE_REPORT_GUIDANCE: Record<string, { action: string; focus: string }> = {
  capability_understanding: {
    action: "把自动清理、容量、除臭、安全和维护成本讲成可比较的能力，而不是只堆卖点名称",
    focus: "用户是否真正理解这台机器解决什么问题、和其他候选产品差在哪里"
  },
  decision_completion: {
    action: "把价格、耗材、售后和使用风险交代清楚，降低用户在下单前的犹豫",
    focus: "用户是否有足够理由把目标产品加入最终候选，甚至直接完成购买"
  },
  information_reach: {
    action: "先让核心场景和主卖点被看见，再把用户带到更具体的能力比较中",
    focus: "用户最先看到哪些信息，以及这些信息能否把目标产品放进候选清单"
  },
  interest_formation: {
    action: "把最容易引发兴趣的省心体验和场景收益表达清楚，避免只停留在参数展示",
    focus: "用户是否因为某个具体使用场景产生继续了解的兴趣"
  },
  trust_building: {
    action: "补足截图、评论快照和保守表述，让安全、除臭等敏感卖点有证据边界",
    focus: "用户是否相信这些卖点可靠，而不是把它们当成未经验证的宣传"
  }
};

export const PROFILE_COMPARISON_SLOT_LABELS: Record<string, string> = {
  highest_threat_alternative: "最高威胁替代竞品",
  highest_threat_direct_competitor: "最高威胁直接竞品",
  target: "目标产品"
};

export const PROFILE_COMPARISON_EMPTY_LABELS: Record<string, string> = {
  highest_threat_alternative: "暂无可用于对比的替代竞品",
  highest_threat_direct_competitor: "暂无可用于对比的直接竞品",
  target: "暂无目标产品"
};

export const PROFILE_COMPARISON_STATUS_LABELS: Record<string, string> = {
  advantage: "优势",
  insufficient_evidence: "证据不足",
  parity: "持平",
  weakness: "短板"
};
