import { createDevelopmentMockMeta } from "./development";
import type { ReportFixture } from "../types";

const section = (
  section_id: string,
  title: string,
  summary: string,
  items: Record<string, unknown>[] = []
) => ({
  claim_ids: [`claim_${section_id}`],
  evidence_ids: ["ev_report_target"],
  items,
  risk_flags: [],
  section_id,
  summary,
  title
});

export const mockReportFixture: ReportFixture = {
  mock_meta: createDevelopmentMockMeta("report"),
  analysis_process_appendix: section(
    "analysis_process_appendix",
    "分析流程与系统能力附录",
    "记录采集、分析、质检和报告智能体的协作过程，以及 QA 打回后的证据补齐。"
  ),
  competitive_landscape_judgment: section(
    "competitive_landscape_judgment",
    "竞争格局判断",
    "目标产品面对直接竞品的信任表达压力，同时在低预算切片中存在替代方案截流风险。"
  ),
  conclusion_summary: section(
    "conclusion_summary",
    "结论摘要",
    "当前最大竞争压力来自同价位直接竞品的信任表达和低价替代方案的决策截流。",
    [
      {
        judgment_strength: "倾向判断",
        recommendation: "优先补齐价格时效证据，再强化详情页安全与维护成本解释。",
        responsibility_type: "商品详情页/内容表达"
      }
    ]
  ),
  core_competitor_analysis: section(
    "core_competitor_analysis",
    "核心竞品拆解",
    "开发样例竞品 B 是默认关键直接竞品，封闭猫砂盆 C 是低预算切片的需求替代对象。"
  ),
  evidence_quality_appendix: section(
    "evidence_quality_appendix",
    "证据与质检附录",
    "保留证据来源、访问时间、局限性和 QA 处理结果；缺少可靠证据时显示暂无可靠数据。",
    [
      {
        action_result: "访问时间已补齐，相关结论可进入复核。",
        check_item: "价格证据完整性",
        needs_attention: false
      }
    ]
  ),
  generated_at: "2026-05-26T09:20:00+08:00",
  product_strategy_recommendations: section(
    "product_strategy_recommendations",
    "产品策略建议",
    "建议将首要动作聚焦在证据补齐、信任表达和维护成本说明上。",
    [
      {
        priority: "P0 立即处理",
        recommendation: "补齐价格截图与访问时间，避免无证据强结论进入正式报告。",
        responsibility_type: "证据补齐/调研验证"
      }
    ]
  ),
  report_id: "report_frontend_f03_mock_v2",
  section_order: [
    "conclusion_summary",
    "competitive_landscape_judgment",
    "core_competitor_analysis",
    "user_decision_chain_analysis",
    "target_opportunities_and_risks",
    "product_strategy_recommendations",
    "evidence_quality_appendix",
    "analysis_process_appendix"
  ],
  target_opportunities_and_risks: section(
    "target_opportunities_and_risks",
    "目标产品机会与风险",
    "机会集中在清洁稳定性和除味表达，风险集中在证据时效与竞品信任背书。"
  ),
  task_id: "task_frontend_f03_mock",
  user_decision_chain_analysis: section(
    "user_decision_chain_analysis",
    "用户决策链分析",
    "直接竞品主要影响能力理解和信任建立，低价替代方案主要影响决策完成。"
  )
};
