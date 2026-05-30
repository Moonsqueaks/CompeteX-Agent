import { createDevelopmentMockMeta } from "./development";
import type { BattlefieldFixture } from "../types";

const scoreBreakdown = {
  context_match: 0.86,
  decision_stage_impact: 0.8,
  demand_substitutability: 0.9,
  evidence_confidence: 0.74,
  market_signal_strength: 0.72
};

const explanationSegment = (
  text: string,
  evidence_ids: string[],
  trace_refs: string[],
  is_analysis_suggestion = false
) => ({
  claim_ids: ["claim_battle_direct"],
  evidence_ids,
  is_analysis_suggestion,
  risk_flags: [],
  text,
  trace_refs
});

export const mockBattlefieldFixture: BattlefieldFixture = {
  mock_meta: createDevelopmentMockMeta("battlefield"),
  available_slices: [
    {
      edge_count: 2,
      persona: "多猫家庭",
      price_band: "1500-2000",
      scenario: "重除臭",
      top_edge_score: 0.82
    },
    {
      edge_count: 1,
      persona: "预算敏感用户",
      price_band: "1000-1500",
      scenario: "基础清洁",
      top_edge_score: 0.61
    },
    {
      edge_count: 1,
      persona: "高便利需求用户",
      price_band: "2000以上",
      scenario: "远程看护",
      top_edge_score: 0.58
    }
  ],
  battlefield_id: "battlefield_frontend_f03_mock_v2",
  decision_chain: [
    {
      average_edge_score: 0.74,
      claim_ids: ["claim_battle_direct"],
      edge_ids: ["edge_frontend_direct", "edge_frontend_alternative"],
      evidence_ids: ["ev_battle_target", "ev_battle_direct"],
      stage: "capability_understanding"
    },
    {
      average_edge_score: 0.82,
      claim_ids: ["claim_battle_direct"],
      edge_ids: ["edge_frontend_direct"],
      evidence_ids: ["ev_battle_direct"],
      stage: "trust_building"
    }
  ],
  evidence_cards: [
    {
      access_time: "2026-05-26T09:02:00+08:00",
      access_time_status: "available",
      confidence_level: "medium",
      content_summary: "目标产品开发样例证据包含价格带、自动清理和封闭除味卖点。",
      evidence_id: "ev_battle_target",
      limitations: "仅用于竞争图谱组件开发，不作为最终演示数据。",
      product_id: "prod_frontend_target",
      risk_flags: [],
      screenshot_path: "/assets/mock/target.png",
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/target"
    },
    {
      access_time: "2026-05-26T09:02:30+08:00",
      access_time_status: "available",
      confidence_level: "medium",
      content_summary: "直接竞品开发样例证据包含除味能力与价格区间。",
      evidence_id: "ev_battle_direct",
      limitations: "非最终演示数据。",
      product_id: "prod_frontend_direct",
      risk_flags: [],
      screenshot_path: null,
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/direct"
    },
    {
      access_time: null,
      access_time_status: "missing",
      confidence_level: "low",
      content_summary: "替代方案开发样例证据缺少访问时间，用于展示风险标记。",
      evidence_id: "ev_battle_alternative",
      limitations: "缺少访问时间，仅可作为开发样例风险数据。",
      product_id: "prod_frontend_alternative",
      risk_flags: ["missing_access_time"],
      screenshot_path: null,
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/alternative"
    }
  ],
  generated_at: "2026-05-26T09:12:00+08:00",
  graph_edges: [
    {
      claim_ids: ["claim_battle_direct"],
      claim_refs: [
        {
          claim_id: "claim_battle_direct",
          confidence: 0.82,
          content: "开发样例竞品 B 在同价位多猫家庭切片中形成直接竞争。",
          evidence_ids: ["ev_battle_target", "ev_battle_direct"],
          is_inference: true,
          risk_flags: [],
          status: "accepted"
        }
      ],
      competition_type: "direct",
      competitor_product_id: "prod_frontend_direct",
      decision_stages: ["capability_understanding", "trust_building", "decision_completion"],
      edge_id: "edge_frontend_direct",
      edge_score: 0.82,
      evidence_ids: ["ev_battle_target", "ev_battle_direct"],
      human_adjusted: false,
      risk_flags: [],
      risk_status: "normal",
      score_breakdown: scoreBreakdown,
      score_explanations: ["同价位、同人群、同除味诉求下需求替代强。"],
      slice: {
        persona: "多猫家庭",
        price_band: "1500-2000",
        scenario: "重除臭"
      },
      source: "prod_frontend_target",
      target: "prod_frontend_direct",
      target_product_id: "prod_frontend_target"
    },
    {
      claim_ids: ["claim_battle_alternative"],
      claim_refs: [
        {
          claim_id: "claim_battle_alternative",
          confidence: 0.58,
          content: "封闭猫砂盆 C 是低预算切片中的需求替代方案，但证据需要复核。",
          evidence_ids: ["ev_battle_alternative"],
          is_inference: true,
          risk_flags: ["missing_access_time"],
          status: "needs_review"
        }
      ],
      competition_type: "alternative",
      competitor_product_id: "prod_frontend_alternative",
      decision_stages: ["interest_formation", "decision_completion"],
      edge_id: "edge_frontend_alternative",
      edge_score: 0.61,
      evidence_ids: ["ev_battle_alternative"],
      human_adjusted: false,
      risk_flags: ["missing_access_time"],
      risk_status: "at_risk",
      score_breakdown: {
        context_match: 0.68,
        decision_stage_impact: 0.58,
        demand_substitutability: 0.7,
        evidence_confidence: 0.42,
        market_signal_strength: 0.6
      },
      score_explanations: ["价格吸引力较强，但访问时间缺失导致证据可信度降低。"],
      slice: {
        persona: "预算敏感用户",
        price_band: "1000-1500",
        scenario: "基础清洁"
      },
      source: "prod_frontend_target",
      target: "prod_frontend_alternative",
      target_product_id: "prod_frontend_target"
    }
  ],
  graph_nodes: [
    {
      brand: "开发样例品牌",
      evidence_ids: ["ev_battle_target"],
      label: "开发样例自动猫砂盆 A",
      node_id: "prod_frontend_target",
      primary_image_path: "/assets/mock/target.png",
      product_id: "prod_frontend_target",
      product_url: "https://example.invalid/frontend-dev/target",
      risk_flags: [],
      role: "target",
      shop_name: "开发样例店铺"
    },
    {
      brand: "开发竞品品牌",
      evidence_ids: ["ev_battle_direct"],
      label: "开发样例竞品 B",
      node_id: "prod_frontend_direct",
      primary_image_path: null,
      product_id: "prod_frontend_direct",
      product_url: "https://example.invalid/frontend-dev/direct",
      risk_flags: [],
      role: "direct_competitor",
      shop_name: "开发竞品店铺"
    },
    {
      brand: "开发替代品牌",
      evidence_ids: ["ev_battle_alternative"],
      label: "开发样例封闭猫砂盆 C",
      node_id: "prod_frontend_alternative",
      primary_image_path: null,
      product_id: "prod_frontend_alternative",
      product_url: "https://example.invalid/frontend-dev/alternative",
      risk_flags: ["missing_access_time"],
      role: "alternative",
      shop_name: "开发替代店铺"
    }
  ],
  key_relations: [
    {
      action_suggestion: "优先补强安全检测和维护成本表达，降低直接竞品的信任压制。",
      claim_ids: ["claim_battle_direct"],
      competitor_brand: "开发竞品品牌",
      competitor_primary_image_path: null,
      competitor_product_id: "prod_frontend_direct",
      competitor_product_name: "开发样例竞品 B",
      edge_id: "edge_frontend_direct",
      evidence_credibility: {
        evidence_ids: ["ev_battle_direct"],
        label: "可直接采纳",
        reason: "证据来自本地脱敏 SKU 快照，并包含访问时间。",
        risk_flags: [],
        trace_refs: ["evidence:ev_battle_direct"],
        value: "directly_adoptable"
      },
      evidence_ids: ["ev_battle_target", "ev_battle_direct"],
      four_part_explanation: {
        decision_stage_impact: explanationSegment(
          "主要影响能力理解、信任建立和最终决策。",
          ["ev_battle_direct"],
          ["analysis_agent:edge_frontend_direct"]
        ),
        response_suggestion: explanationSegment(
          "在详情页优先补足运行安全、维护成本和售后承诺表达。",
          ["ev_battle_target"],
          ["writer_agent:recommendation_direct"],
          true
        ),
        strength: explanationSegment(
          "竞争强度为高威胁，边分数 0.82。",
          ["ev_battle_target", "ev_battle_direct"],
          ["analysis_agent:score_edge_frontend_direct"]
        ),
        why_competitor: explanationSegment(
          "同价位、同人群、同除味诉求，需求替代关系明确。",
          ["ev_battle_target", "ev_battle_direct"],
          ["analysis_agent:edge_frontend_direct"]
        )
      },
      inclusion_reason: "同价位多猫家庭切片中竞争分最高，且证据链较完整。",
      is_default_visible: true,
      relationship_label: "head_to_head",
      relationship_label_explanation: "双方争夺同一价格带和重除味场景下的核心决策。",
      risk_flags: [],
      target_product_id: "prod_frontend_target",
      threat_level: "high_threat",
      trace_refs: ["analysis_agent:edge_frontend_direct"]
    },
    {
      action_suggestion: "先补齐替代方案价格访问时间，再决定是否写入强结论。",
      claim_ids: ["claim_battle_alternative"],
      competitor_brand: "开发替代品牌",
      competitor_primary_image_path: null,
      competitor_product_id: "prod_frontend_alternative",
      competitor_product_name: "开发样例封闭猫砂盆 C",
      edge_id: "edge_frontend_alternative",
      evidence_credibility: {
        evidence_ids: ["ev_battle_alternative"],
        label: "谨慎参考",
        reason: "价格证据缺少访问时间，QA 仍要求补齐。",
        risk_flags: ["missing_access_time"],
        trace_refs: ["qa_agent:review_battle_missing_time"],
        value: "cautious_reference"
      },
      evidence_ids: ["ev_battle_alternative"],
      four_part_explanation: {
        decision_stage_impact: explanationSegment(
          "主要影响预算敏感用户的兴趣形成和决策完成。",
          ["ev_battle_alternative"],
          ["analysis_agent:edge_frontend_alternative"]
        ),
        response_suggestion: explanationSegment(
          "不能把低价截流写成强事实；补齐证据前标记为推断。",
          ["ev_battle_alternative"],
          ["qa_agent:review_battle_missing_time"],
          true
        ),
        strength: explanationSegment(
          "竞争强度为中等，但证据可信度偏低。",
          ["ev_battle_alternative"],
          ["analysis_agent:score_edge_frontend_alternative"]
        ),
        why_competitor: explanationSegment(
          "价格吸引力可能截流低预算用户，但缺少时效证据。",
          ["ev_battle_alternative"],
          ["analysis_agent:edge_frontend_alternative"]
        )
      },
      inclusion_reason: "用于覆盖缺图和缺访问时间的开发 fixture 风险展示。",
      is_default_visible: true,
      relationship_label: "low_price_interception",
      relationship_label_explanation: "低价封闭方案可能在预算敏感切片截流目标产品。",
      risk_flags: ["missing_access_time"],
      target_product_id: "prod_frontend_target",
      threat_level: "medium_threat",
      trace_refs: [
        "analysis_agent:edge_frontend_alternative",
        "qa_agent:review_battle_missing_time"
      ]
    }
  ],
  metadata: {
    fixture_scope: "battlefield_page_v2_contract",
    final_demo_data: false
  },
  qa_summary: {
    open_review_task_count: 1,
    qa_status: "needs_attention",
    resolved_review_task_count: 0,
    review_task_count: 1,
    review_task_ids: ["review_battle_missing_time"],
    revision_message_count: 1,
    risk_claim_ids: ["claim_battle_alternative"],
    risk_edge_ids: ["edge_frontend_alternative"]
  },
  relation_filter: {
    can_expand_all: false,
    default_limit: 5,
    include_all_relations: false,
    total_relation_count: 2,
    visible_relation_count: 2
  },
  score_explanations: [
    {
      claim_ids: ["claim_battle_direct"],
      edge_id: "edge_frontend_direct",
      edge_score: 0.82,
      evidence_ids: ["ev_battle_target", "ev_battle_direct"],
      explanations: ["需求替代、场景匹配和决策影响均较高。"],
      score_breakdown: scoreBreakdown
    },
    {
      claim_ids: ["claim_battle_alternative"],
      edge_id: "edge_frontend_alternative",
      edge_score: 0.61,
      evidence_ids: ["ev_battle_alternative"],
      explanations: ["低价截流有可能成立，但证据时效不足。"],
      score_breakdown: {
        context_match: 0.68,
        decision_stage_impact: 0.58,
        demand_substitutability: 0.7,
        evidence_confidence: 0.42,
        market_signal_strength: 0.6
      }
    }
  ],
  selected_slice: {
    persona: "多猫家庭",
    price_band: "1500-2000",
    scenario: "重除臭"
  },
  task_id: "task_frontend_f03_mock"
};
