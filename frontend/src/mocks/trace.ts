import { createDevelopmentMockMeta } from "./development";
import type { TraceResponse } from "../types";

export const mockTraceFixture: TraceResponse = {
  mock_meta: createDevelopmentMockMeta("trace"),
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
      fixture_scope: "trace_page_contract"
    }
  },
  dag: {
    nodes: [
      {
        id: "orchestrator",
        label: "流程调度智能体",
        node_type: "agent",
        status: "succeeded",
        metadata: {
          display_name: "任务初始化"
        }
      },
      {
        id: "collection_agent",
        label: "采集智能体",
        node_type: "agent",
        status: "succeeded",
        metadata: {
          display_name: "快照采集"
        }
      },
      {
        id: "analysis_agent",
        label: "分析智能体",
        node_type: "agent",
        status: "succeeded",
        metadata: {
          display_name: "竞争分析"
        }
      },
      {
        id: "qa_agent",
        label: "质检智能体",
        node_type: "agent",
        status: "requires_revision",
        metadata: {
          display_name: "质检打回"
        }
      },
      {
        id: "writer_agent",
        label: "报告智能体",
        node_type: "agent",
        status: "pending",
        metadata: {
          display_name: "报告生成"
        }
      }
    ],
    edges: [
      {
        id: "dag_edge_collection",
        source: "orchestrator",
        target: "collection_agent",
        label: "开始采集",
        edge_type: "normal",
        metadata: {}
      },
      {
        id: "dag_edge_analysis",
        source: "collection_agent",
        target: "analysis_agent",
        label: "产物就绪",
        edge_type: "normal",
        metadata: {}
      },
      {
        id: "dag_edge_qa",
        source: "analysis_agent",
        target: "qa_agent",
        label: "进入质检",
        edge_type: "normal",
        metadata: {}
      },
      {
        id: "dag_edge_revision",
        source: "qa_agent",
        target: "collection_agent",
        label: "补齐证据",
        edge_type: "revision",
        metadata: {
          reason: "missing_access_time"
        }
      }
    ]
  },
  agent_run_logs: [
    {
      run_id: "run_collection_initial",
      task_id: "task_frontend_f03_mock",
      agent_name: "collection_agent",
      status: "succeeded",
      started_at: "2026-05-26T09:01:00+08:00",
      ended_at: "2026-05-26T09:01:20+08:00",
      input_summary: "读取前端开发样例快照。",
      output_summary: "生成产品、证据和评论洞察样例。"
    },
    {
      run_id: "run_analysis_initial",
      task_id: "task_frontend_f03_mock",
      agent_name: "analysis_agent",
      status: "succeeded",
      started_at: "2026-05-26T09:02:00+08:00",
      ended_at: "2026-05-26T09:02:40+08:00",
      input_summary: "消费产品和证据样例。",
      output_summary: "生成画像、Claim 和竞争边样例。"
    },
    {
      run_id: "run_qa_revision",
      task_id: "task_frontend_f03_mock",
      agent_name: "qa_agent",
      status: "requires_revision",
      started_at: "2026-05-26T09:03:00+08:00",
      ended_at: "2026-05-26T09:03:10+08:00",
      input_summary: "检查结论与证据绑定。",
      output_summary: "发现一条价格证据缺少访问时间。"
    }
  ],
  tool_call_logs: [
    {
      tool_call_id: "tool_snapshot_loader",
      task_id: "task_frontend_f03_mock",
      run_id: "run_collection_initial",
      tool_name: "snapshot_loader",
      arguments_summary: {
        source: "frontend_development_fixture",
        sku_count: 3
      },
      status: "succeeded",
      started_at: "2026-05-26T09:01:02+08:00",
      ended_at: "2026-05-26T09:01:08+08:00",
      duration_ms: 6000,
      error_message: null
    },
    {
      tool_call_id: "tool_qa_rules",
      task_id: "task_frontend_f03_mock",
      run_id: "run_qa_revision",
      tool_name: "qa_rules",
      arguments_summary: {
        claim_count: 2,
        evidence_count: 3,
        check_scope: "frontend_development_fixture"
      },
      status: "succeeded",
      started_at: "2026-05-26T09:03:02+08:00",
      ended_at: "2026-05-26T09:03:06+08:00",
      duration_ms: 4000,
      error_message: null
    }
  ],
  token_usage_logs: [
    {
      usage_id: "usage_collection_rule",
      task_id: "task_frontend_f03_mock",
      run_id: "run_collection_initial",
      agent_name: "collection_agent",
      model_name: "local_rule_flow",
      prompt_tokens: 0,
      completion_tokens: 0,
      total_tokens: 0,
      created_at: "2026-05-26T09:01:20+08:00"
    }
  ],
  review_tasks: [
    {
      review_task_id: "review_trace_missing_time",
      task_id: "task_frontend_f03_mock",
      check_name: "时效证据完整性",
      issue_code: "TIMELY_EVIDENCE_MISSING_ACCESS_TIME",
      severity: "warning",
      status: "open",
      target_type: "evidence",
      target_id: "ev_battle_alternative",
      message: "替代方案价格证据缺少访问时间。",
      required_action: "补齐访问时间；无法补齐时显示暂无可靠数据。",
      created_at: "2026-05-26T09:03:08+08:00",
      target_agent: "collection_agent",
      related_claim_ids: ["claim_battle_alternative"],
      evidence_ids: ["ev_battle_alternative"],
      resolved_at: null
    }
  ],
  agent_messages: [
    {
      message_id: "msg_trace_revision",
      task_id: "task_frontend_f03_mock",
      from_agent: "qa_agent",
      to_agent: "collection_agent",
      message_type: "revision_request",
      artifact_type: "claim_evidence_check",
      payload: {
        qa_status: "requires_revision",
        issue_codes: ["TIMELY_EVIDENCE_MISSING_ACCESS_TIME"],
        required_action: "补齐访问时间；无法补齐时显示暂无可靠数据。",
        target_ids: ["ev_battle_alternative"]
      },
      evidence_ids: ["ev_battle_alternative"],
      status: "requires_revision",
      created_at: "2026-05-26T09:03:09+08:00"
    }
  ],
  diffs: [
    {
      diff_id: "diff_trace_evidence_time",
      title: "价格证据访问时间",
      target_type: "evidence",
      target_id: "ev_battle_alternative",
      before: {
        access_time: null,
        risk_flags: ["missing_access_time"]
      },
      after: {
        access_time: "暂无可靠数据",
        risk_flags: ["unreliable_data"]
      },
      related_review_task_ids: ["review_trace_missing_time"]
    }
  ]
};
