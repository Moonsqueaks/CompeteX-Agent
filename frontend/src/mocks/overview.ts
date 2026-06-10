import { createDevelopmentMockMeta } from "./development";
import type { OverviewFixture } from "../types";

export const mockOverviewFixture: OverviewFixture = {
  mock_meta: createDevelopmentMockMeta("overview"),
  action_recommendations: [
    {
      action_id: "action_frontend_evidence",
      description: "补齐缺失访问时间的价格证据，再决定是否把低价替代方案写入强竞争结论。",
      drilldown_refs: [
        {
          label: "查看质检记录",
          reference_type: "trace",
          route: "/trace?task_id=task_frontend_f03_mock&tab=quality_records",
          target_id: "quality_trace_missing_time"
        }
      ],
      evidence_ids: ["ev_trace_alternative"],
      expected_impact: "降低报告中无证据强判断的风险。",
      missing_reference_reason: null,
      priority: "p0_immediate",
      responsibility_type: "evidence_research",
      risk_flags: ["missing_access_time"],
      title: "先补齐价格时效证据",
      trace_refs: ["qa_agent:review_trace_missing_time"]
    }
  ],
  analysis_scope: {
    access_time_range: "2026-05-26",
    category: "智能宠物硬件",
    candidate_strategy: "snapshot_pool",
    data_source_label: "本地脱敏 SKU 快照",
    data_source_mode: "demo_snapshot",
    evidence_source_mode: "local_snapshot",
    evidence_count: 3,
    evidence_ids: ["ev_profile_target", "ev_profile_alternative", "ev_trace_alternative"],
    missing_fields: ["ev_trace_alternative.access_time"],
    platform_label: "抖音电商",
    platforms: ["douyin"],
    product_count: 3,
    scope_notice: "非实时全网数据，仅用于前端开发 fixture 契约验证。",
    sku_count: 3,
    snapshot_date: "2026-05-26",
    snapshot_version: "frontend_f03_mock",
    source_description: "本报告基于用户提供的脱敏 SKU 快照，不代表实时全网数据。",
    subcategory: "自动猫砂盆",
    task_id: "task_frontend_f03_mock"
  },
  current_slice: {
    persona: "多猫家庭",
    price_band: "1500-2000",
    scenario: "重除臭"
  },
  decision_usability: {
    evidence_ids: ["ev_profile_target", "ev_trace_alternative"],
    label: "建议谨慎决策",
    reason: "关键竞品方向可参考，但仍有一条价格证据缺少访问时间。",
    risk_flags: ["missing_access_time"],
    trace_refs: ["qa_agent:review_trace_missing_time"],
    value: "decision_with_caution"
  },
  drilldown_refs: [
    {
      label: "查看竞争图谱",
      reference_type: "battlefield",
      route: "/battlefield?task_id=task_frontend_f03_mock",
      target_id: "edge_frontend_direct"
    }
  ],
  generated_at: "2026-05-26T09:12:00+08:00",
  judgment_strength: {
    evidence_ids: ["ev_profile_target"],
    label: "倾向判断",
    reason: "直接竞品关系证据较完整，替代方案证据仍有局限。",
    risk_flags: ["missing_access_time"],
    trace_refs: ["analysis_agent:edge_frontend_direct"],
    value: "directional_judgment"
  },
  key_competitors: [
    {
      brand: "开发竞品品牌",
      competitor_type: "highest_threat_direct_competitor",
      drilldown_refs: [
        {
          label: "查看竞争关系",
          reference_type: "battlefield",
          route: "/battlefield?task_id=task_frontend_f03_mock&edge_id=edge_frontend_direct",
          target_id: "edge_frontend_direct"
        }
      ],
      evidence_credibility: {
        evidence_ids: ["ev_profile_target"],
        label: "可直接采纳",
        reason: "证据来自本地脱敏 SKU 快照并有访问时间。",
        risk_flags: [],
        trace_refs: ["evidence:ev_profile_target"],
        value: "directly_adoptable"
      },
      evidence_ids: ["ev_profile_target"],
      inclusion_reason: "同价位多猫家庭切片中竞争分最高。",
      missing_reference_reason: null,
      primary_image_path: null,
      product_id: "prod_frontend_direct",
      product_name: "开发样例竞品 B",
      relationship_label: "head_to_head",
      risk_flags: [],
      sku_id: "dev_sku_direct",
      threat_level: "high_threat",
      trace_refs: ["analysis_agent:edge_frontend_direct"]
    }
  ],
  metadata: {
    fixture_scope: "overview_page_v2_contract"
  },
  one_sentence_judgment: {
    content: "目标产品当前主要压力来自同价位直接竞品的信任表达，以及低预算替代方案的价格截流。",
    drilldown_refs: [
      {
        label: "查看依据",
        reference_type: "trace",
        route: "/trace?task_id=task_frontend_f03_mock&tab=evidence_chain",
        target_id: "chain_trace_direct_competitor"
      }
    ],
    evidence_ids: ["ev_profile_target"],
    missing_reference_reason: null,
    risk_flags: ["missing_access_time"],
    trace_refs: ["analysis_agent:edge_frontend_direct"]
  },
  opportunities: [
    {
      description: "强化详情页中安全检测和维护成本解释，减少信任建立阶段的疑虑。",
      drilldown_refs: [],
      evidence_ids: ["ev_profile_target"],
      finding_id: "opportunity_frontend_trust",
      finding_type: "expression_opportunity",
      missing_reference_reason: null,
      risk_flags: [],
      title: "信任表达可优化",
      trace_refs: ["analysis_agent:edge_frontend_direct"]
    }
  ],
  overview_id: "overview_frontend_f03_mock",
  risk_points: [
    {
      description: "替代方案价格证据缺少访问时间，不能直接作为强事实判断。",
      drilldown_refs: [
        {
          label: "查看质检",
          reference_type: "trace",
          route: "/trace?task_id=task_frontend_f03_mock&tab=quality_records",
          target_id: "quality_trace_missing_time"
        }
      ],
      evidence_ids: ["ev_trace_alternative"],
      finding_id: "risk_frontend_access_time",
      finding_type: "evidence_risk",
      missing_reference_reason: null,
      risk_flags: ["missing_access_time"],
      title: "证据时效需要补齐",
      trace_refs: ["qa_agent:review_trace_missing_time"]
    }
  ],
  status_reasons: ["直接竞品证据较完整", "替代方案仍有时效证据风险"],
  task_id: "task_frontend_f03_mock"
};
