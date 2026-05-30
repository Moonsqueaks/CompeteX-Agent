import { createDevelopmentMockMeta } from "./development";
import type { TraceFixture } from "../types";

export const mockTraceFixture: TraceFixture = {
  mock_meta: createDevelopmentMockMeta("trace"),
  agent_runs: [
    {
      agent_name: "collection_agent",
      ended_at: "2026-05-26T09:01:20+08:00",
      input_summary: "读取前端开发样例快照。",
      output_summary: "生成产品、证据和评论洞察样例。",
      run_id: "run_collection_initial",
      started_at: "2026-05-26T09:01:00+08:00",
      status: "succeeded",
      task_id: "task_frontend_f03_mock"
    },
    {
      agent_name: "analysis_agent",
      ended_at: "2026-05-26T09:02:40+08:00",
      input_summary: "消费产品和证据样例。",
      output_summary: "生成画像、结论和竞争关系样例。",
      run_id: "run_analysis_initial",
      started_at: "2026-05-26T09:02:00+08:00",
      status: "succeeded",
      task_id: "task_frontend_f03_mock"
    },
    {
      agent_name: "qa_agent",
      ended_at: "2026-05-26T09:03:10+08:00",
      input_summary: "检查结论与证据绑定。",
      output_summary: "发现一条价格证据缺少访问时间。",
      run_id: "run_qa_revision",
      started_at: "2026-05-26T09:03:00+08:00",
      status: "requires_revision",
      task_id: "task_frontend_f03_mock"
    }
  ],
  dag_edges: [
    {
      condition: null,
      edge_id: "dag_edge_collection_analysis",
      label: "采集 → 分析",
      source: "collection_agent",
      target: "analysis_agent"
    },
    {
      condition: null,
      edge_id: "dag_edge_analysis_qa",
      label: "分析 → 质检",
      source: "analysis_agent",
      target: "qa_agent"
    },
    {
      condition: "revision_collection",
      edge_id: "dag_edge_revision",
      label: "质检打回采集",
      source: "qa_agent",
      target: "collection_agent"
    }
  ],
  dag_nodes: [
    {
      agent_name: "collection_agent",
      current: false,
      failed: false,
      label: "采集智能体",
      node_id: "collection_agent",
      node_type: "agent",
      run_ids: ["run_collection_initial"],
      status: "succeeded",
      visible: true
    },
    {
      agent_name: "analysis_agent",
      current: false,
      failed: false,
      label: "分析智能体",
      node_id: "analysis_agent",
      node_type: "agent",
      run_ids: ["run_analysis_initial"],
      status: "succeeded",
      visible: true
    },
    {
      agent_name: "qa_agent",
      current: true,
      failed: false,
      label: "质检智能体",
      node_id: "qa_agent",
      node_type: "agent",
      run_ids: ["run_qa_revision"],
      status: "requires_revision",
      visible: true
    },
    {
      agent_name: "writer_agent",
      current: false,
      failed: false,
      label: "报告智能体",
      node_id: "writer_agent",
      node_type: "agent",
      run_ids: [],
      status: "skipped",
      visible: true
    }
  ],
  diffs: [
    {
      after: {
        access_time: "暂无可靠数据",
        risk_flags: ["unreliable_data"]
      },
      before: {
        access_time: null,
        risk_flags: ["missing_access_time"]
      },
      business_impact: "缺少访问时间的价格证据被降级，相关结论只能谨慎参考。",
      diff_id: "diff_trace_evidence_time",
      metadata: {
        fixture_source: "frontend_f03"
      },
      revision_message_ids: ["msg_trace_revision"],
      source: "collection_agent_repair",
      status: "partial",
      target_id: "ev_trace_alternative",
      target_type: "evidence"
    }
  ],
  evidence_chains: [
    {
      chain_id: "chain_trace_direct_competitor",
      claim_content: "开发样例竞品 B 在同价位多猫家庭切片中形成直接竞争。",
      claim_id: "claim_trace_direct_competitor",
      claim_status: "accepted",
      confidence: 0.82,
      evidence_items: [
        {
          access_time_status: "available",
          confidence_level: "medium",
          content_summary: "商品页快照显示竞品价格与除臭卖点。",
          evidence_id: "ev_trace_direct",
          limitations: "开发样例证据，不作为最终演示数据。",
          product_id: "prod_frontend_direct",
          risk_flags: [],
          source_type: "douyin_sku_snapshot",
          source_url: "https://example.invalid/frontend-dev/direct"
        }
      ],
      is_inference: true,
      navigation: {
        trace_tab: "evidence_chain"
      },
      report_section_ids: ["core_competitor_analysis"],
      risk_flags: [],
      trace_refs: ["analysis_agent:edge_frontend_direct"]
    }
  ],
  generated_at: "2026-05-26T09:08:00+08:00",
  metadata: {
    fixture_scope: "trace_page_v2_contract"
  },
  process_view: {
    agent_run_count: 3,
    dag_node_count: 4,
    default_tab: "evidence_chain",
    prompt_preview_count: 1,
    technical_details_folded: true,
    token_usage_count: 1,
    tool_call_count: 2
  },
  prompt_previews: [
    {
      agent_name: "collection_agent",
      content_summary: "仅展示脱敏后的采集提示摘要，默认折叠。",
      folded: true,
      preview_id: "prompt_collection_fixture",
      redacted: true,
      run_id: "run_collection_initial",
      title: "Collection prompt"
    }
  ],
  qa_reviews: [
    {
      check_name: "时效证据完整性",
      created_at: "2026-05-26T09:03:08+08:00",
      evidence_ids: ["ev_trace_alternative"],
      issue_code: "TIMELY_EVIDENCE_MISSING_ACCESS_TIME",
      message: "替代方案价格证据缺少访问时间。",
      related_claim_ids: ["claim_trace_direct_competitor"],
      required_action: "补齐访问时间；无法补齐时显示暂无可靠数据。",
      resolved_at: null,
      review_task_id: "review_trace_missing_time",
      severity: "warning",
      status: "open",
      target_agent: "collection_agent",
      target_id: "ev_trace_alternative",
      target_type: "evidence",
      task_id: "task_frontend_f03_mock"
    }
  ],
  quality_records: [
    {
      action_result: "无法补齐访问时间，已将相关证据降级为谨慎参考。",
      check_item: "时效证据完整性",
      evidence_ids: ["ev_trace_alternative"],
      issue_code: "TIMELY_EVIDENCE_MISSING_ACCESS_TIME",
      issue_summary: "替代方案价格证据缺少访问时间。",
      needs_attention: true,
      quality_record_id: "quality_trace_missing_time",
      related_claim_ids: ["claim_trace_direct_competitor"],
      required_action: "补齐访问时间；无法补齐时显示暂无可靠数据。",
      resolved: false,
      review_task_id: "review_trace_missing_time",
      severity: "warning",
      status: "open",
      target_agent: "collection_agent",
      target_id: "ev_trace_alternative",
      target_type: "evidence"
    }
  ],
  revision_messages: [
    {
      artifact_type: "claim_evidence_check",
      created_at: "2026-05-26T09:03:09+08:00",
      evidence_ids: ["ev_trace_alternative"],
      from_agent: "qa_agent",
      message_id: "msg_trace_revision",
      message_type: "revision_request",
      payload: {
        issue_codes: ["TIMELY_EVIDENCE_MISSING_ACCESS_TIME"],
        required_action: "补齐访问时间；无法补齐时显示暂无可靠数据。",
        target_ids: ["ev_trace_alternative"]
      },
      status: "requires_revision",
      task_id: "task_frontend_f03_mock",
      to_agent: "collection_agent"
    }
  ],
  task_id: "task_frontend_f03_mock",
  task_status: "reviewing",
  token_usage: [
    {
      agent_name: "collection_agent",
      completion_tokens: 0,
      created_at: "2026-05-26T09:01:20+08:00",
      model_name: "local_rule_flow",
      prompt_tokens: 0,
      run_id: "run_collection_initial",
      task_id: "task_frontend_f03_mock",
      total_tokens: 0,
      usage_id: "usage_collection_rule"
    }
  ],
  tool_calls: [
    {
      arguments_summary: {
        source: "frontend_development_fixture",
        sku_count: 3
      },
      duration_ms: 6000,
      ended_at: "2026-05-26T09:01:08+08:00",
      error_message: null,
      run_id: "run_collection_initial",
      started_at: "2026-05-26T09:01:02+08:00",
      status: "succeeded",
      task_id: "task_frontend_f03_mock",
      tool_call_id: "tool_snapshot_loader",
      tool_name: "snapshot_loader"
    },
    {
      arguments_summary: {
        check_scope: "frontend_development_fixture"
      },
      duration_ms: 4000,
      ended_at: "2026-05-26T09:03:06+08:00",
      error_message: null,
      run_id: "run_qa_revision",
      started_at: "2026-05-26T09:03:02+08:00",
      status: "succeeded",
      task_id: "task_frontend_f03_mock",
      tool_call_id: "tool_qa_rules",
      tool_name: "qa_rules"
    }
  ],
  trace_view_id: "trace_frontend_f03_mock_v2",
  workflow_status: "requires_revision"
};
