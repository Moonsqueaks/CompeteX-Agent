import { createDevelopmentMockMeta } from "./development";
import type { BattlefieldResponse } from "../types";

export const mockBattlefieldFixture: BattlefieldResponse = {
  mock_meta: createDevelopmentMockMeta("battlefield"),
  task: {
    task_id: "task_frontend_f03_mock",
    target_product_name: "开发样例自动猫砂盆 A",
    target_product_url: "https://example.invalid/frontend-dev/target",
    category: "智能宠物硬件",
    subcategory: "自动猫砂盆",
    data_source_mode: "demo_snapshot",
    status: "reviewing",
    created_at: "2026-05-26T09:00:00+08:00",
    updated_at: "2026-05-26T09:08:00+08:00",
    metadata: {
      fixture_scope: "battlefield_page_contract"
    }
  },
  selected_slice: {
    price_band: "1500-2000",
    persona: "多猫家庭",
    scenario: "重除臭"
  },
  available_slices: [
    {
      price_band: "1500-2000",
      persona: "多猫家庭",
      scenario: "重除臭"
    },
    {
      price_band: "1000-1500",
      persona: "预算敏感用户",
      scenario: "基础清洁"
    },
    {
      price_band: "2000以上",
      persona: "高便利需求用户",
      scenario: "远程看护"
    }
  ],
  products: [
    {
      product_id: "prod_frontend_target",
      task_id: "task_frontend_f03_mock",
      name: "开发样例自动猫砂盆 A",
      category: "智能宠物硬件",
      subcategory: "自动猫砂盆",
      role: "target",
      created_at: "2026-05-26T09:01:00+08:00",
      sku_id: "dev_sku_target",
      brand: "开发样例品牌",
      shop_name: "开发样例店铺",
      product_url: "https://example.invalid/frontend-dev/target",
      evidence_ids: ["ev_battle_target"],
      tags: ["目标", "自动清理"]
    },
    {
      product_id: "prod_frontend_direct",
      task_id: "task_frontend_f03_mock",
      name: "开发样例竞品 B",
      category: "智能宠物硬件",
      subcategory: "自动猫砂盆",
      role: "direct_competitor",
      created_at: "2026-05-26T09:01:30+08:00",
      sku_id: "dev_sku_direct",
      brand: "开发样例竞品品牌",
      shop_name: "开发样例竞品店铺",
      product_url: "https://example.invalid/frontend-dev/direct",
      evidence_ids: ["ev_battle_direct"],
      tags: ["直接竞品", "除味"]
    },
    {
      product_id: "prod_frontend_alternative",
      task_id: "task_frontend_f03_mock",
      name: "开发样例封闭猫砂盆 C",
      category: "智能宠物硬件",
      subcategory: "猫砂盆",
      role: "alternative",
      created_at: "2026-05-26T09:02:00+08:00",
      sku_id: "dev_sku_alternative",
      brand: "开发样例替代品牌",
      shop_name: "开发样例替代店铺",
      product_url: "https://example.invalid/frontend-dev/alternative",
      evidence_ids: ["ev_battle_alternative"],
      tags: ["需求替代", "低预算"]
    }
  ],
  graph: {
    nodes: [
      {
        id: "prod_frontend_target",
        label: "开发样例自动猫砂盆 A",
        node_type: "product",
        metadata: {
          role: "target",
          score_label: "目标产品"
        }
      },
      {
        id: "prod_frontend_direct",
        label: "开发样例竞品 B",
        node_type: "product",
        metadata: {
          role: "direct_competitor",
          score_label: "0.82"
        }
      },
      {
        id: "prod_frontend_alternative",
        label: "开发样例封闭猫砂盆 C",
        node_type: "product",
        metadata: {
          role: "alternative",
          score_label: "0.61"
        }
      }
    ],
    edges: [
      {
        id: "graph_edge_direct",
        source: "prod_frontend_target",
        target: "prod_frontend_direct",
        label: "直接竞争",
        edge_type: "direct",
        metadata: {
          edge_score: 0.82,
          risk_flags: []
        }
      },
      {
        id: "graph_edge_alternative",
        source: "prod_frontend_target",
        target: "prod_frontend_alternative",
        label: "需求替代",
        edge_type: "alternative",
        metadata: {
          edge_score: 0.61,
          risk_flags: ["missing_access_time"]
        }
      }
    ]
  },
  competition_edges: [
    {
      edge_id: "edge_frontend_direct",
      task_id: "task_frontend_f03_mock",
      target_product_id: "prod_frontend_target",
      competitor_product_id: "prod_frontend_direct",
      competition_type: "direct",
      slice: {
        price_band: "1500-2000",
        persona: "多猫家庭",
        scenario: "重除臭"
      },
      decision_stages: ["capability_understanding", "trust_building", "decision_completion"],
      edge_score: 0.82,
      score_breakdown: {
        demand_substitutability: 0.9,
        context_match: 0.86,
        decision_stage_impact: 0.8,
        evidence_confidence: 0.74,
        market_signal_strength: 0.72
      },
      claim_ids: ["claim_battle_direct"],
      human_adjusted: false,
      risk_flags: [],
      created_at: "2026-05-26T09:06:00+08:00"
    },
    {
      edge_id: "edge_frontend_alternative",
      task_id: "task_frontend_f03_mock",
      target_product_id: "prod_frontend_target",
      competitor_product_id: "prod_frontend_alternative",
      competition_type: "alternative",
      slice: {
        price_band: "1000-1500",
        persona: "预算敏感用户",
        scenario: "基础清洁"
      },
      decision_stages: ["interest_formation", "decision_completion"],
      edge_score: 0.61,
      score_breakdown: {
        demand_substitutability: 0.7,
        context_match: 0.68,
        decision_stage_impact: 0.58,
        evidence_confidence: 0.42,
        market_signal_strength: 0.6
      },
      claim_ids: ["claim_battle_alternative"],
      human_adjusted: false,
      risk_flags: ["missing_access_time"],
      created_at: "2026-05-26T09:06:30+08:00"
    }
  ],
  claims: [
    {
      claim_id: "claim_battle_direct",
      task_id: "task_frontend_f03_mock",
      claim_type: "competition_edge",
      content: "开发样例竞品 B 在同价位多猫家庭切片中形成直接竞争。",
      evidence_ids: ["ev_battle_target", "ev_battle_direct"],
      confidence: 0.82,
      is_inference: true,
      risk_flags: [],
      status: "accepted",
      created_at: "2026-05-26T09:05:00+08:00"
    },
    {
      claim_id: "claim_battle_alternative",
      task_id: "task_frontend_f03_mock",
      claim_type: "competition_edge",
      content: "开发样例封闭猫砂盆 C 是低预算切片中的需求替代方案，但价格证据需要复核。",
      evidence_ids: ["ev_battle_alternative"],
      confidence: 0.58,
      is_inference: true,
      risk_flags: ["missing_access_time"],
      status: "needs_review",
      created_at: "2026-05-26T09:05:30+08:00"
    }
  ],
  evidences: [
    {
      evidence_id: "ev_battle_target",
      task_id: "task_frontend_f03_mock",
      product_id: "prod_frontend_target",
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/target",
      screenshot_path: "data/screenshots/frontend-dev-target.png",
      access_time: "2026-05-26T09:02:00+08:00",
      content_summary: "目标产品开发样例证据包含价格带和核心卖点。",
      confidence_level: "medium",
      limitations: "仅用于竞争图谱组件开发。",
      metadata: {
        fixture_source: "frontend_f03"
      }
    },
    {
      evidence_id: "ev_battle_direct",
      task_id: "task_frontend_f03_mock",
      product_id: "prod_frontend_direct",
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/direct",
      screenshot_path: "data/screenshots/frontend-dev-direct.png",
      access_time: "2026-05-26T09:02:30+08:00",
      content_summary: "直接竞品开发样例证据包含除味能力与价格区间。",
      confidence_level: "medium",
      limitations: "非最终演示数据。",
      metadata: {
        fixture_source: "frontend_f03"
      }
    },
    {
      evidence_id: "ev_battle_alternative",
      task_id: "task_frontend_f03_mock",
      product_id: "prod_frontend_alternative",
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/alternative",
      screenshot_path: "data/screenshots/frontend-dev-alternative.png",
      access_time: null,
      content_summary: "替代方案开发样例证据缺少访问时间，用于展示风险标记。",
      confidence_level: "low",
      limitations: "缺少访问时间，仅可作为开发样例风险数据。",
      metadata: {
        missing_fields: ["source.access_time"]
      }
    }
  ],
  edge_explanations: {
    edge_frontend_direct: {
      summary: "直接竞品在需求替代性、场景匹配和决策影响上得分较高。",
      weights: {
        demand_substitutability: 0.3,
        context_match: 0.25,
        decision_stage_impact: 0.2,
        evidence_confidence: 0.15,
        market_signal_strength: 0.1
      }
    },
    edge_frontend_alternative: {
      summary: "替代方案价格吸引力较强，但证据时效字段缺失。",
      weights: {
        demand_substitutability: 0.3,
        context_match: 0.25,
        decision_stage_impact: 0.2,
        evidence_confidence: 0.15,
        market_signal_strength: 0.1
      }
    }
  },
  qa_summary: {
    has_revision: true,
    diff_count: 1,
    review_tasks: [
      {
        review_task_id: "review_battle_missing_time",
        task_id: "task_frontend_f03_mock",
        check_name: "时效证据完整性",
        issue_code: "TIMELY_EVIDENCE_MISSING_ACCESS_TIME",
        severity: "warning",
        status: "open",
        target_type: "evidence",
        target_id: "ev_battle_alternative",
        message: "替代方案价格证据缺少访问时间。",
        required_action: "补齐访问时间；无法补齐时显示暂无可靠数据。",
        created_at: "2026-05-26T09:07:00+08:00",
        target_agent: "collection_agent",
        related_claim_ids: ["claim_battle_alternative"],
        evidence_ids: ["ev_battle_alternative"],
        resolved_at: null
      }
    ]
  }
};
