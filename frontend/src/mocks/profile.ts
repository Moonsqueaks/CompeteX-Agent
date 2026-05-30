import { createDevelopmentMockMeta } from "./development";
import type { ProfileFixture } from "../types";

export const mockProfileFixture: ProfileFixture = {
  mock_meta: createDevelopmentMockMeta("profile"),
  evidence_summaries: [
    {
      access_time: "2026-05-26T09:02:00+08:00",
      access_time_status: "available",
      confidence_level: "medium",
      content_summary: "商品页快照包含目标产品价格、自动清理、封闭除味和应用提醒卖点。",
      evidence_id: "ev_profile_target",
      limitations: "开发样例证据，不作为最终演示数据。",
      product_id: "prod_frontend_target",
      risk_flags: [],
      screenshot_path: "/assets/mock/target.png",
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/target"
    },
    {
      access_time: null,
      access_time_status: "missing",
      confidence_level: "low",
      content_summary: "替代竞品样例证据缺少访问时间，用于验证风险展示。",
      evidence_id: "ev_profile_alternative",
      limitations: "缺少访问时间，仅可谨慎参考。",
      product_id: "prod_frontend_alternative",
      risk_flags: ["missing_access_time"],
      screenshot_path: null,
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/alternative"
    }
  ],
  feature_tree: {
    cleaning_capability: ["自动铲砂", "基础清洁记录"],
    evidence_ids: ["ev_profile_target"],
    feature_tree_id: "feature_frontend_target",
    maintenance_cost: ["需要定期更换耗材", "清理频率依赖猫只数量"],
    odor_control: ["封闭仓体", "可替换除味模块"],
    product_id: "prod_frontend_target",
    risk_flags: [],
    safety_features: ["入口检测", "运行前状态确认"],
    smart_features: ["应用提醒", "耗材状态提示"],
    task_id: "task_frontend_f03_mock"
  },
  generated_at: "2026-05-26T09:10:00+08:00",
  horizontal_comparison: {
    compared_products: [
      {
        brand: "开发样例品牌",
        primary_image_path: "/assets/mock/target.png",
        product_id: "prod_frontend_target",
        product_name: "开发样例自动猫砂盆 A",
        product_url: "https://example.invalid/frontend-dev/target",
        slot: "target"
      },
      {
        brand: "开发竞品品牌",
        primary_image_path: null,
        product_id: "prod_frontend_direct",
        product_name: "开发样例竞品 B",
        product_url: "https://example.invalid/frontend-dev/direct",
        slot: "highest_threat_direct_competitor"
      },
      {
        brand: "开发替代品牌",
        primary_image_path: null,
        product_id: "prod_frontend_alternative",
        product_name: "开发样例封闭猫砂盆 C",
        product_url: "https://example.invalid/frontend-dev/alternative",
        slot: "highest_threat_alternative"
      }
    ],
    dimensions: [
      {
        dimension_key: "price_band",
        dimension_label: "价格带",
        evidence_ids: ["ev_profile_target", "ev_profile_alternative"],
        risk_flags: [],
        status_reason: "目标产品价格低于核心直接竞品，但替代方案证据缺少访问时间。",
        target_status: "advantage",
        trace_refs: ["trace:pricing"],
        values: [
          {
            evidence_ids: ["ev_profile_target"],
            product_id: "prod_frontend_target",
            value: "1500-2000"
          },
          {
            evidence_ids: ["ev_profile_target"],
            product_id: "prod_frontend_direct",
            value: "2000以上"
          },
          {
            evidence_ids: ["ev_profile_alternative"],
            product_id: "prod_frontend_alternative",
            value: "1000-1500"
          }
        ]
      },
      {
        dimension_key: "core_selling_points",
        dimension_label: "核心卖点",
        evidence_ids: ["ev_profile_target"],
        risk_flags: [],
        status_reason: "目标产品卖点完整，但信任证据仍需更清晰呈现。",
        target_status: "parity",
        trace_refs: ["trace:feature"],
        values: [
          {
            evidence_ids: ["ev_profile_target"],
            product_id: "prod_frontend_target",
            value: "自动清理、封闭除味"
          },
          {
            evidence_ids: ["ev_profile_target"],
            product_id: "prod_frontend_direct",
            value: "除味强化、售后承诺"
          },
          {
            evidence_ids: ["ev_profile_alternative"],
            product_id: "prod_frontend_alternative",
            value: "低价封闭除味"
          }
        ]
      }
    ],
    target_product_id: "prod_frontend_target"
  },
  metadata: {
    fixture_scope: "profile_page_v2_contract"
  },
  pricing_evidence: {
    access_time: "2026-05-26T09:02:00+08:00",
    access_time_status: "available",
    evidence_ids: ["ev_profile_target"],
    risk_flags: []
  },
  pricing_model: {
    access_time: "2026-05-26T09:02:00+08:00",
    bundle_description: "主机与基础耗材套装",
    currency: "CNY",
    evidence_ids: ["ev_profile_target"],
    final_price: 1699,
    list_price: 1899,
    price_band: "1500-2000",
    pricing_model_id: "pricing_frontend_target",
    product_id: "prod_frontend_target",
    promotions: ["开发样例满减", "开发样例赠品"],
    risk_flags: [],
    task_id: "task_frontend_f03_mock"
  },
  product: {
    brand: "开发样例品牌",
    category: "智能宠物硬件",
    created_at: "2026-05-26T09:01:00+08:00",
    evidence_ids: ["ev_profile_target"],
    name: "开发样例自动猫砂盆 A",
    primary_image_path: "/assets/mock/target.png",
    primary_image_source_path: "snapshot.main_image_url",
    primary_image_status: "available",
    primary_image_url: "https://example.invalid/assets/target.png",
    product_id: "prod_frontend_target",
    product_url: "https://example.invalid/frontend-dev/target",
    role: "target",
    shop_name: "开发样例店铺",
    sku_id: "dev_sku_target",
    subcategory: "自动猫砂盆",
    tags: ["自动清理", "封闭式", "开发样例"],
    task_id: "task_frontend_f03_mock"
  },
  profile_id: "profile_frontend_f03_mock",
  task_id: "task_frontend_f03_mock",
  user_persona: {
    decision_factors: ["清洁稳定性", "耗材成本", "证据完整度"],
    evidence_ids: ["ev_profile_target"],
    is_inference: true,
    pain_points: ["清理频率高", "异味扩散", "需要确认运行安全"],
    persona_id: "persona_frontend_target",
    personas: ["多猫家庭", "工作日清洁时间有限的用户"],
    product_id: "prod_frontend_target",
    risk_flags: [],
    scenarios: ["小户型客厅", "多猫共用猫砂区"],
    task_id: "task_frontend_f03_mock"
  }
};
