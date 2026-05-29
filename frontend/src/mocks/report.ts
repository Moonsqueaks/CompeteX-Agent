import { createDevelopmentMockMeta } from "./development";
import type { ReportResponse } from "../types";

export const mockReportFixture: ReportResponse = {
  mock_meta: createDevelopmentMockMeta("report"),
  task: {
    task_id: "task_frontend_f03_mock",
    target_product_name: "开发样例自动猫砂盆 A",
    target_product_url: "https://example.invalid/frontend-dev/target",
    category: "智能宠物硬件",
    subcategory: "自动猫砂盆",
    data_source_mode: "demo_snapshot",
    status: "writing",
    created_at: "2026-05-26T09:00:00+08:00",
    updated_at: "2026-05-26T09:10:00+08:00",
    metadata: {
      fixture_scope: "report_page_contract"
    }
  },
  report_id: "report_frontend_f03_mock",
  report_status: "draft",
  title: "开发样例自动猫砂盆竞争关系分析",
  generated_at: "2026-05-26T09:10:00+08:00",
  sections: [
    {
      section_id: "section_executive_summary",
      title: "执行摘要",
      summary: "目标产品在自动清理和封闭除味上具备展示重点，竞争风险集中在同价位直接竞品。",
      claim_ids: ["claim_report_summary"],
      evidence_ids: ["ev_report_target"],
      risk_flags: []
    },
    {
      section_id: "section_profile",
      title: "目标产品画像",
      summary: "画像由开发样例商品页和评论摘要驱动，后续将切换为真实接口数据。",
      claim_ids: ["claim_report_profile"],
      evidence_ids: ["ev_report_target", "ev_report_review"],
      risk_flags: []
    },
    {
      section_id: "section_competitors",
      title: "竞品集合与召回逻辑",
      summary: "当前样例覆盖直接竞品和需求替代方案，用于验证报告列表结构。",
      claim_ids: ["claim_report_competitor"],
      evidence_ids: ["ev_report_competitor"],
      risk_flags: []
    },
    {
      section_id: "section_slices",
      title: "动态竞争切片分析",
      summary: "价格带、人群和场景切片会改变竞品排序与评分解释。",
      claim_ids: ["claim_report_slice"],
      evidence_ids: ["ev_report_target", "ev_report_competitor"],
      risk_flags: []
    },
    {
      section_id: "section_decision_chain",
      title: "决策链竞争优势与短板",
      summary: "直接竞品在信任建立和决策完成阶段更接近目标产品。",
      claim_ids: ["claim_report_decision"],
      evidence_ids: ["ev_report_competitor"],
      risk_flags: []
    },
    {
      section_id: "section_user_research",
      title: "用户研究洞察",
      summary: "开发样例仅展示结构，真实洞察需要来自脱敏问卷或访谈材料。",
      claim_ids: ["claim_report_research"],
      evidence_ids: ["ev_report_review"],
      risk_flags: []
    },
    {
      section_id: "section_actions",
      title: "可执行建议",
      summary: "建议围绕证据完整度、价格说明和维护成本表达做保守优化。",
      claim_ids: ["claim_report_action"],
      evidence_ids: ["ev_report_target"],
      risk_flags: []
    },
    {
      section_id: "section_qa",
      title: "质检审查摘要",
      summary: "一条开发样例证据缺少访问时间，需要在正式报告中保守展示。",
      claim_ids: ["claim_report_qa"],
      evidence_ids: ["ev_report_missing_time"],
      risk_flags: ["missing_access_time"]
    },
    {
      section_id: "section_evidence_index",
      title: "证据索引",
      summary: "列出报告引用的开发样例证据，后续由后端报告接口提供真实索引。",
      claim_ids: [],
      evidence_ids: ["ev_report_target", "ev_report_competitor", "ev_report_review"],
      risk_flags: []
    }
  ],
  claims: [
    {
      claim_id: "claim_report_summary",
      task_id: "task_frontend_f03_mock",
      claim_type: "report_summary",
      content: "开发样例报告认为直接竞品在同价位切片中竞争强度较高。",
      evidence_ids: ["ev_report_target", "ev_report_competitor"],
      confidence: 0.76,
      is_inference: true,
      risk_flags: [],
      status: "accepted",
      created_at: "2026-05-26T09:08:00+08:00"
    },
    {
      claim_id: "claim_report_profile",
      task_id: "task_frontend_f03_mock",
      claim_type: "profile_summary",
      content: "目标产品的展示重点包括自动清理、封闭除味和应用提醒。",
      evidence_ids: ["ev_report_target"],
      confidence: 0.8,
      is_inference: false,
      risk_flags: [],
      status: "accepted",
      created_at: "2026-05-26T09:08:10+08:00"
    },
    {
      claim_id: "claim_report_competitor",
      task_id: "task_frontend_f03_mock",
      claim_type: "competitor_set",
      content: "样例竞品集合包含直接竞品与需求替代方案。",
      evidence_ids: ["ev_report_competitor"],
      confidence: 0.74,
      is_inference: true,
      risk_flags: [],
      status: "accepted",
      created_at: "2026-05-26T09:08:20+08:00"
    },
    {
      claim_id: "claim_report_slice",
      task_id: "task_frontend_f03_mock",
      claim_type: "slice_analysis",
      content: "不同价格带和使用场景会改变竞争边排序。",
      evidence_ids: ["ev_report_target", "ev_report_competitor"],
      confidence: 0.7,
      is_inference: true,
      risk_flags: [],
      status: "accepted",
      created_at: "2026-05-26T09:08:30+08:00"
    },
    {
      claim_id: "claim_report_decision",
      task_id: "task_frontend_f03_mock",
      claim_type: "decision_chain",
      content: "直接竞品在能力理解和信任建立阶段更接近目标产品。",
      evidence_ids: ["ev_report_competitor"],
      confidence: 0.69,
      is_inference: true,
      risk_flags: [],
      status: "accepted",
      created_at: "2026-05-26T09:08:40+08:00"
    },
    {
      claim_id: "claim_report_research",
      task_id: "task_frontend_f03_mock",
      claim_type: "research_insight",
      content: "用户研究模块需要真实脱敏材料接入后再形成最终结论。",
      evidence_ids: ["ev_report_review"],
      confidence: 0.52,
      is_inference: true,
      risk_flags: [],
      status: "draft",
      created_at: "2026-05-26T09:08:50+08:00"
    },
    {
      claim_id: "claim_report_action",
      task_id: "task_frontend_f03_mock",
      claim_type: "action_recommendation",
      content: "报告建议优先补齐价格时效证据，再输出强竞争判断。",
      evidence_ids: ["ev_report_missing_time"],
      confidence: 0.62,
      is_inference: true,
      risk_flags: ["missing_access_time"],
      status: "needs_review",
      created_at: "2026-05-26T09:09:00+08:00"
    },
    {
      claim_id: "claim_report_qa",
      task_id: "task_frontend_f03_mock",
      claim_type: "qa_summary",
      content: "质检样例发现一条价格证据缺少访问时间。",
      evidence_ids: ["ev_report_missing_time"],
      confidence: 0.84,
      is_inference: false,
      risk_flags: ["missing_access_time"],
      status: "needs_review",
      created_at: "2026-05-26T09:09:10+08:00"
    }
  ],
  evidence_index: [
    {
      evidence_id: "ev_report_target",
      task_id: "task_frontend_f03_mock",
      product_id: "prod_frontend_target",
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/target",
      screenshot_path: "data/screenshots/frontend-dev-target.png",
      access_time: "2026-05-26T09:02:00+08:00",
      content_summary: "目标产品开发样例证据。",
      confidence_level: "medium",
      limitations: "前端开发样例，不作为最终演示数据。",
      metadata: {
        fixture_source: "frontend_f03"
      }
    },
    {
      evidence_id: "ev_report_competitor",
      task_id: "task_frontend_f03_mock",
      product_id: "prod_frontend_direct",
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/direct",
      screenshot_path: "data/screenshots/frontend-dev-direct.png",
      access_time: "2026-05-26T09:02:30+08:00",
      content_summary: "直接竞品开发样例证据。",
      confidence_level: "medium",
      limitations: "前端开发样例，不作为最终演示数据。",
      metadata: {
        fixture_source: "frontend_f03"
      }
    },
    {
      evidence_id: "ev_report_review",
      task_id: "task_frontend_f03_mock",
      product_id: "prod_frontend_target",
      source_type: "douyin_review_snapshot",
      source_url: "https://example.invalid/frontend-dev/review",
      screenshot_path: "data/screenshots/frontend-dev-review.png",
      access_time: "2026-05-26T09:03:00+08:00",
      content_summary: "评论摘要开发样例证据。",
      confidence_level: "medium",
      limitations: "不代表真实用户结论。",
      metadata: {
        fixture_source: "frontend_f03"
      }
    },
    {
      evidence_id: "ev_report_missing_time",
      task_id: "task_frontend_f03_mock",
      product_id: "prod_frontend_alternative",
      source_type: "douyin_sku_snapshot",
      source_url: "https://example.invalid/frontend-dev/alternative",
      screenshot_path: "data/screenshots/frontend-dev-alternative.png",
      access_time: null,
      content_summary: "缺少访问时间的开发样例证据。",
      confidence_level: "low",
      limitations: "缺少访问时间，需要保守展示。",
      metadata: {
        missing_fields: ["source.access_time"]
      }
    }
  ],
  qa_summary: {
    status: "requires_revision",
    review_task_ids: ["review_trace_missing_time"],
    summary: "开发样例报告保留一条需复核证据，用于验证风险展示。"
  },
  markdown_export: {
    available: false,
    reason: "等待后端 Markdown 报告导出接口完成。"
  }
};
