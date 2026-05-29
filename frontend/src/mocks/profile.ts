import { createDevelopmentMockMeta } from "./development";
import type { ProfileResponse } from "../types";

export const mockProfileFixture: ProfileResponse = {
  mock_meta: createDevelopmentMockMeta("profile"),
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
    research_text: null,
    metadata: {
      fixture_scope: "profile_page_contract"
    }
  },
  target_product: {
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
    evidence_ids: ["ev_profile_product", "ev_profile_review"],
    tags: ["自动清理", "封闭式", "开发样例"]
  },
  feature_tree: {
    feature_tree_id: "feature_frontend_target",
    task_id: "task_frontend_f03_mock",
    product_id: "prod_frontend_target",
    cleaning_capability: ["自动铲砂", "支持基础清洁记录"],
    odor_control: ["封闭仓体", "可替换除味模块"],
    safety_features: ["入口检测", "运行前状态确认"],
    smart_features: ["应用提醒", "耗材状态提示"],
    maintenance_cost: ["需要定期更换耗材", "清理频率依赖猫只数量"],
    evidence_ids: ["ev_profile_product"],
    risk_flags: []
  },
  pricing_model: {
    pricing_model_id: "pricing_frontend_target",
    task_id: "task_frontend_f03_mock",
    product_id: "prod_frontend_target",
    price_band: "1500-2000",
    currency: "CNY",
    list_price: 1899,
    final_price: 1699,
    promotions: ["开发样例满减", "开发样例赠品"],
    bundle_description: "主机与基础耗材套装",
    evidence_ids: ["ev_profile_product"],
    access_time: "2026-05-26T09:02:00+08:00",
    risk_flags: []
  },
  user_persona: {
    persona_id: "persona_frontend_target",
    task_id: "task_frontend_f03_mock",
    product_id: "prod_frontend_target",
    personas: ["多猫家庭", "工作日清洁时间有限的用户"],
    pain_points: ["清理频率高", "异味扩散", "需要确认运行安全"],
    scenarios: ["小户型客厅", "多猫共用猫砂区"],
    decision_factors: ["清洁稳定性", "耗材成本", "证据完整度"],
    evidence_ids: ["ev_profile_review"],
    is_inference: true,
    risk_flags: []
  },
  evidences: [
    {
      evidence_id: "ev_profile_product",
      task_id: "task_frontend_f03_mock",
      product_id: "prod_frontend_target",
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/target",
      screenshot_path: "data/screenshots/frontend-dev-target.png",
      access_time: "2026-05-26T09:02:00+08:00",
      content_summary: "开发样例商品页包含价格、基础功能卖点和套装信息。",
      confidence_level: "medium",
      limitations: "仅用于前端开发验证，非最终演示快照。",
      metadata: {
        fixture_source: "frontend_f03"
      }
    },
    {
      evidence_id: "ev_profile_review",
      task_id: "task_frontend_f03_mock",
      product_id: "prod_frontend_target",
      source_type: "douyin_review_snapshot",
      source_url: "https://example.invalid/frontend-dev/review",
      screenshot_path: "data/screenshots/frontend-dev-review.png",
      access_time: "2026-05-26T09:03:00+08:00",
      content_summary: "开发样例评论摘要提到清理省力和耗材成本关注。",
      confidence_level: "medium",
      limitations: "评论内容为前端开发样例，不代表真实用户结论。",
      metadata: {
        sample_size_label: "开发样例"
      }
    }
  ],
  claims: [
    {
      claim_id: "claim_profile_cleaning",
      task_id: "task_frontend_f03_mock",
      claim_type: "feature_summary",
      content: "目标产品的核心展示重点集中在自动清理、封闭除味和应用提醒。",
      evidence_ids: ["ev_profile_product"],
      confidence: 0.78,
      is_inference: false,
      risk_flags: [],
      status: "accepted",
      created_at: "2026-05-26T09:05:00+08:00"
    },
    {
      claim_id: "claim_profile_persona",
      task_id: "task_frontend_f03_mock",
      claim_type: "persona_inference",
      content: "推断目标人群更关注清洁负担、异味控制和日常维护成本。",
      evidence_ids: ["ev_profile_review"],
      confidence: 0.66,
      is_inference: true,
      risk_flags: [],
      status: "accepted",
      created_at: "2026-05-26T09:06:00+08:00"
    }
  ],
  review_summary: {
    open_count: 0,
    risk_flags: [],
    latest_review_task_ids: [],
    human_feedback_enabled: true
  }
};
