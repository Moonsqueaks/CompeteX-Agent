export type MetricExplanation = {
  name: string;
  source: string;
  scale: string;
  businessUse: string;
};

export const METRIC_DICTIONARY = {
  analysis_scope_counts: {
    name: "分析范围数量",
    source: "来自本次任务读取并通过 Schema 校验的产品、SKU 和 Evidence 计数。",
    scale: "数量越多通常代表覆盖面更广，但不等于结论一定更准；仍要结合证据可信度和 QA 状态判断。",
    businessUse: "业务解读：这是本轮分析的样本边界，用来判断报告是在少量线索上做判断，还是覆盖了足够多的竞品和证据。"
  },
  claim_confidence: {
    name: "结论置信度",
    source: "由 Analysis/QA 链路根据证据数量、证据完整性、是否推断和风险标记综合给出，取值为 0 到 1。",
    scale: "0.80-1.00 通常可视为明确判断；0.60-0.79 为较强线索，建议持续观察；低于 0.60 属于弱判断或待复核线索。",
    businessUse: "业务解读：0.82 代表这条结论已有较强证据支撑，但仍不是事实本身；涉及价格、认证或安全表达时仍建议人工复核。"
  },
  decision_stage_average_score: {
    name: "决策阶段平均分",
    source: "把影响同一购买阶段的竞争边得分进行平均，反映该阶段被竞品拦截的强弱。",
    scale: "0.80-1.00 表示强拦截；0.60-0.79 表示明显影响；0.40-0.59 表示中等影响；低于 0.40 表示当前证据下影响较弱。",
    businessUse: "业务解读：分数越高，越说明用户在该购买阶段更容易被竞品说服，需要优先补卖点、证据或转化策略。"
  },
  edge_score: {
    name: "综合竞争得分",
    source: "按评分公式计算：需求替代性 30% + 场景匹配度 25% + 购买路径影响 20% + 证据支撑度 15% + 市场信号强度 10%。",
    scale: "0.80-1.00 为致命威胁，0.60-0.79 为高度警惕，低于 0.60 为低度威胁或暂不优先。",
    businessUse: "业务解读：它表示当前切片下这条竞品关系的优先级，不是销量或市场份额。分数高时应优先查看拆解维度和底层证据。"
  },
  evidence_confidence_level: {
    name: "证据可信等级",
    source: "由 Evidence 的来源类型、访问时间、截图/链接完整性、局限性和风险标记共同决定。",
    scale: "高可信表示证据较完整；中等可信表示可参考但仍有边界；低可信表示缺字段、旧快照或推断成分较多。",
    businessUse: "业务解读：证据可信等级用于判断这条材料能不能支撑业务决策。低可信并不等于无效，但不适合单独作为拍板依据。"
  },
  metric_count: {
    name: "记录数量",
    source: "来自当前任务的结构化 Artifact 或 Trace 记录计数，例如 DAG 节点、运行记录、质检记录和证据条数。",
    scale: "数量用于说明覆盖范围和过程复杂度，不直接代表质量。0 表示当前没有相关记录或该模块尚未产出。",
    businessUse: "业务解读：这类数字用于判断本次分析是否有足够过程和材料可追溯，遇到异常时也方便定位缺口。"
  },
  qa_review_counts: {
    name: "QA 质检计数",
    source: "来自 QA Agent 生成的 ReviewTask、打回消息、开放问题和已解决问题数量。",
    scale: "开放问题越多，说明仍有证据缺口或逻辑风险；已解决问题表示系统已经完成一次自我修正闭环。",
    businessUse: "业务解读：不要只看是否有质检问题，更要看问题是否已解决。已解决的打回记录反而说明报告经过了纠偏。"
  },
  score_breakdown_value: {
    name: "评分维度值",
    source: "来自 CompetitionEdge.score_breakdown 的单项得分，每个维度取值为 0 到 1。",
    scale: "0.80-1.00 很强，0.60-0.79 较强，0.40-0.59 中等，低于 0.40 较弱。",
    businessUse: "业务解读：综合得分高时，用这些维度看具体输在哪里；比如需求替代性高代表用户可能真的会二选一。"
  },
  threat_rating: {
    name: "威胁评级区间",
    source: "由综合竞争得分映射而来，不额外改变评分公式。",
    scale: ">=0.80 为致命威胁；0.60-0.79 为高度警惕；<0.60 为低度威胁。",
    businessUse: "业务解读：评级是为了帮新手快速排序优先级。先处理高威胁，再看中低威胁是否需要观察或补证。"
  },
  token_usage: {
    name: "模型计量占比",
    source: "来自 Trace 中记录的 prompt_tokens、completion_tokens 和 total_tokens。",
    scale: "输入计量表示送入模型的上下文，输出计量表示模型生成内容，合计是两者之和；进度条展示它们在本次调用中的占比。",
    businessUse: "业务解读：它主要用于排查模型调用成本和上下文规模，不代表分析质量。输入过高可能说明上下文太长，输出过高可能说明报告生成较重。"
  }
} satisfies Record<string, MetricExplanation>;

export type MetricKey = keyof typeof METRIC_DICTIONARY;
