/**
 * This file is generated from the FastAPI OpenAPI schema.
 * Run `npm --prefix frontend run sync:types` after backend API contract changes.
 */
export type paths = {
  "/health": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Health Check */
    get: operations["health_check_health_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/tasks": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Create Task */
    post: operations["create_task_tasks_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/tasks/{task_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Task */
    get: operations["get_task_tasks__task_id__get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/tasks/{task_id}/battlefield": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Task Battlefield */
    get: operations["get_task_battlefield_tasks__task_id__battlefield_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/tasks/{task_id}/feedback": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Submit Task Feedback */
    post: operations["submit_task_feedback_tasks__task_id__feedback_post"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/tasks/{task_id}/profile": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Task Profile */
    get: operations["get_task_profile_tasks__task_id__profile_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/tasks/{task_id}/report": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Task Report */
    get: operations["get_task_report_tasks__task_id__report_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/tasks/{task_id}/report/markdown": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Export Task Report Markdown */
    get: operations["export_task_report_markdown_tasks__task_id__report_markdown_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/tasks/{task_id}/trace": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Task Trace */
    get: operations["get_task_trace_tasks__task_id__trace_get"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
};
export type webhooks = Record<string, never>;
export type components = {
  schemas: {
    /** AgentMessage */
    AgentMessage: {
      /** Artifact Type */
      artifact_type: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Evidence Ids */
      evidence_ids?: string[];
      from_agent: components["schemas"]["AgentName"];
      /** Message Id */
      message_id: string;
      message_type: components["schemas"]["AgentMessageType"];
      /** Payload */
      payload?: {
        [key: string]: unknown;
      };
      /** @default pending */
      status: components["schemas"]["AgentMessageStatus"];
      /** Task Id */
      task_id: string;
      to_agent: components["schemas"]["AgentName"];
    };
    /**
     * AgentMessageStatus
     * @enum {string}
     */
    AgentMessageStatus:
      | "pending"
      | "sent"
      | "processed"
      | "requires_revision"
      | "resolved"
      | "failed";
    /**
     * AgentMessageType
     * @enum {string}
     */
    AgentMessageType: "artifact_ready" | "revision_request" | "status_update" | "error";
    /**
     * AgentName
     * @enum {string}
     */
    AgentName:
      | "orchestrator"
      | "collection_agent"
      | "analysis_agent"
      | "qa_agent"
      | "writer_agent"
      | "human";
    /** AgentRunLog */
    AgentRunLog: {
      agent_name: components["schemas"]["AgentName"];
      /** Ended At */
      ended_at?: string | null;
      /** Error Message */
      error_message?: string | null;
      /** Input Summary */
      input_summary?: string | null;
      /** Output Summary */
      output_summary?: string | null;
      /** Run Id */
      run_id: string;
      /**
       * Started At
       * Format: date-time
       */
      started_at: string;
      status: components["schemas"]["RunStatus"];
      /** Task Id */
      task_id: string;
    };
    /** AnalysisTask */
    AnalysisTask: {
      /** Category */
      category: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** @default demo_snapshot */
      data_source_mode: components["schemas"]["DataSourceMode"];
      /** Metadata */
      metadata?: {
        [key: string]: unknown;
      };
      /** Research Text */
      research_text?: string | null;
      /** @default created */
      status: components["schemas"]["TaskStatus"];
      /** Subcategory */
      subcategory: string;
      /** Target Product Name */
      target_product_name: string;
      /** Target Product Url */
      target_product_url?: string | null;
      /** Task Id */
      task_id: string;
      /**
       * Updated At
       * Format: date-time
       */
      updated_at: string;
    };
    /** ApiError */
    ApiError: {
      /** Code */
      code: string;
      /** Details */
      details?: {
        [key: string]: unknown;
      };
      /** Message */
      message: string;
    };
    /** ApiResponse[BattlefieldData] */
    ApiResponse_BattlefieldData_: {
      data?: components["schemas"]["BattlefieldData"] | null;
      error?: components["schemas"]["ApiError"] | null;
      /** Trace Id */
      trace_id: string;
    };
    /** ApiResponse[HumanFeedbackCreateResponse] */
    ApiResponse_HumanFeedbackCreateResponse_: {
      data?: components["schemas"]["HumanFeedbackCreateResponse"] | null;
      error?: components["schemas"]["ApiError"] | null;
      /** Trace Id */
      trace_id: string;
    };
    /** ApiResponse[MarkdownReport] */
    ApiResponse_MarkdownReport_: {
      data?: components["schemas"]["MarkdownReport"] | null;
      error?: components["schemas"]["ApiError"] | null;
      /** Trace Id */
      trace_id: string;
    };
    /** ApiResponse[ProductProfileData] */
    ApiResponse_ProductProfileData_: {
      data?: components["schemas"]["ProductProfileData"] | null;
      error?: components["schemas"]["ApiError"] | null;
      /** Trace Id */
      trace_id: string;
    };
    /** ApiResponse[ReportData] */
    ApiResponse_ReportData_: {
      data?: components["schemas"]["ReportData"] | null;
      error?: components["schemas"]["ApiError"] | null;
      /** Trace Id */
      trace_id: string;
    };
    /** ApiResponse[TaskCreateResponse] */
    ApiResponse_TaskCreateResponse_: {
      data?: components["schemas"]["TaskCreateResponse"] | null;
      error?: components["schemas"]["ApiError"] | null;
      /** Trace Id */
      trace_id: string;
    };
    /** ApiResponse[TaskStatusResponse] */
    ApiResponse_TaskStatusResponse_: {
      data?: components["schemas"]["TaskStatusResponse"] | null;
      error?: components["schemas"]["ApiError"] | null;
      /** Trace Id */
      trace_id: string;
    };
    /** ApiResponse[TraceData] */
    ApiResponse_TraceData_: {
      data?: components["schemas"]["TraceData"] | null;
      error?: components["schemas"]["ApiError"] | null;
      /** Trace Id */
      trace_id: string;
    };
    /** BattlefieldClaimReference */
    BattlefieldClaimReference: {
      /** Claim Id */
      claim_id: string;
      /** Confidence */
      confidence: number;
      /** Content */
      content: string;
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Is Inference */
      is_inference: boolean;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Status */
      status: string;
    };
    /** BattlefieldData */
    BattlefieldData: {
      /** Available Slices */
      available_slices?: components["schemas"]["BattlefieldSliceOption"][];
      /** Battlefield Id */
      battlefield_id: string;
      /** Decision Chain */
      decision_chain?: components["schemas"]["BattlefieldDecisionChainStage"][];
      /** Evidence Cards */
      evidence_cards?: components["schemas"]["BattlefieldEvidenceCard"][];
      /**
       * Generated At
       * Format: date-time
       */
      generated_at: string;
      /** Graph Edges */
      graph_edges?: components["schemas"]["BattlefieldGraphEdge"][];
      /** Graph Nodes */
      graph_nodes?: components["schemas"]["BattlefieldGraphNode"][];
      /** Metadata */
      metadata?: {
        [key: string]: unknown;
      };
      qa_summary: components["schemas"]["BattlefieldQASummary"];
      /** Score Explanations */
      score_explanations?: components["schemas"]["BattlefieldScoreExplanation"][];
      selected_slice: components["schemas"]["BattlefieldSliceSelection"];
      /** Task Id */
      task_id: string;
    };
    /** BattlefieldDecisionChainStage */
    BattlefieldDecisionChainStage: {
      /** Average Edge Score */
      average_edge_score: number;
      /** Claim Ids */
      claim_ids?: string[];
      /** Edge Ids */
      edge_ids?: string[];
      /** Evidence Ids */
      evidence_ids?: string[];
      stage: components["schemas"]["DecisionStage"];
    };
    /** BattlefieldEvidenceCard */
    BattlefieldEvidenceCard: {
      /** Access Time */
      access_time?: string | null;
      /**
       * Access Time Status
       * @enum {string}
       */
      access_time_status: "available" | "missing";
      confidence_level: components["schemas"]["ConfidenceLevel"];
      /** Content Summary */
      content_summary: string;
      /** Evidence Id */
      evidence_id: string;
      /** Limitations */
      limitations: string;
      /** Product Id */
      product_id?: string | null;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Screenshot Path */
      screenshot_path?: string | null;
      source_type: components["schemas"]["EvidenceSourceType"];
      /** Source Url */
      source_url?: string | null;
    };
    /** BattlefieldGraphEdge */
    BattlefieldGraphEdge: {
      /** Claim Ids */
      claim_ids?: string[];
      /** Claim Refs */
      claim_refs?: components["schemas"]["BattlefieldClaimReference"][];
      competition_type: components["schemas"]["CompetitionType"];
      /** Competitor Product Id */
      competitor_product_id: string;
      /** Decision Stages */
      decision_stages: components["schemas"]["DecisionStage"][];
      /** Edge Id */
      edge_id: string;
      /** Edge Score */
      edge_score: number;
      /** Evidence Ids */
      evidence_ids?: string[];
      /**
       * Human Adjusted
       * @default false
       */
      human_adjusted: boolean;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /**
       * Risk Status
       * @default normal
       * @enum {string}
       */
      risk_status: "normal" | "at_risk";
      score_breakdown: components["schemas"]["ScoreBreakdown"];
      /** Score Explanations */
      score_explanations?: string[];
      slice: components["schemas"]["BattlefieldSliceSelection"];
      /** Source */
      source: string;
      /** Target */
      target: string;
      /** Target Product Id */
      target_product_id: string;
    };
    /** BattlefieldGraphNode */
    BattlefieldGraphNode: {
      /** Brand */
      brand?: string | null;
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Label */
      label: string;
      /** Node Id */
      node_id: string;
      /** Product Id */
      product_id: string;
      /** Product Url */
      product_url?: string | null;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      role: components["schemas"]["ProductRole"];
      /** Shop Name */
      shop_name?: string | null;
    };
    /** BattlefieldQASummary */
    BattlefieldQASummary: {
      /** Open Review Task Count */
      open_review_task_count: number;
      /**
       * Qa Status
       * @enum {string}
       */
      qa_status: "passed" | "needs_attention";
      /** Resolved Review Task Count */
      resolved_review_task_count: number;
      /** Review Task Count */
      review_task_count: number;
      /** Review Task Ids */
      review_task_ids?: string[];
      /** Revision Message Count */
      revision_message_count: number;
      /** Risk Claim Ids */
      risk_claim_ids?: string[];
      /** Risk Edge Ids */
      risk_edge_ids?: string[];
    };
    /** BattlefieldScoreExplanation */
    BattlefieldScoreExplanation: {
      /** Claim Ids */
      claim_ids?: string[];
      /** Edge Id */
      edge_id: string;
      /** Edge Score */
      edge_score: number;
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Explanations */
      explanations?: string[];
      score_breakdown: components["schemas"]["ScoreBreakdown"];
    };
    /** BattlefieldSliceOption */
    BattlefieldSliceOption: {
      /** Edge Count */
      edge_count: number;
      /** Persona */
      persona: string;
      /** Price Band */
      price_band: string;
      /** Scenario */
      scenario: string;
      /** Top Edge Score */
      top_edge_score: number;
    };
    /** BattlefieldSliceSelection */
    BattlefieldSliceSelection: {
      /** Persona */
      persona?: string | null;
      /** Price Band */
      price_band?: string | null;
      /** Scenario */
      scenario?: string | null;
    };
    /**
     * CompetitionType
     * @enum {string}
     */
    CompetitionType: "direct" | "alternative" | "channel" | "content_cooccurrence";
    /**
     * ConfidenceLevel
     * @enum {string}
     */
    ConfidenceLevel: "low" | "medium" | "high" | "unknown";
    /**
     * DataSourceMode
     * @enum {string}
     */
    DataSourceMode: "demo_snapshot" | "snapshot_plus_live";
    /**
     * DecisionStage
     * @enum {string}
     */
    DecisionStage:
      | "information_reach"
      | "interest_formation"
      | "capability_understanding"
      | "trust_building"
      | "decision_completion";
    /**
     * EvidenceSourceType
     * @enum {string}
     */
    EvidenceSourceType:
      | "douyin_sku_snapshot"
      | "douyin_review_snapshot"
      | "user_research"
      | "manual_review"
      | "derived_artifact";
    /** EvidenceSummary */
    EvidenceSummary: {
      /** Access Time */
      access_time?: string | null;
      /** Access Time Status */
      access_time_status: string;
      confidence_level: components["schemas"]["ConfidenceLevel"];
      /** Content Summary */
      content_summary: string;
      /** Evidence Id */
      evidence_id: string;
      /** Limitations */
      limitations: string;
      /** Product Id */
      product_id?: string | null;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Screenshot Path */
      screenshot_path?: string | null;
      source_type: components["schemas"]["EvidenceSourceType"];
      /** Source Url */
      source_url?: string | null;
    };
    /** FeatureTree */
    FeatureTree: {
      /** Cleaning Capability */
      cleaning_capability?: string[];
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Feature Tree Id */
      feature_tree_id: string;
      /** Maintenance Cost */
      maintenance_cost?: string[];
      /** Odor Control */
      odor_control?: string[];
      /** Product Id */
      product_id: string;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Safety Features */
      safety_features?: string[];
      /** Smart Features */
      smart_features?: string[];
      /** Task Id */
      task_id: string;
    };
    /**
     * FeedbackAction
     * @enum {string}
     */
    FeedbackAction:
      | "update_field"
      | "add_competitor"
      | "remove_competitor"
      | "mark_accepted"
      | "mark_rejected"
      | "mark_needs_review"
      | "add_note";
    /**
     * FeedbackTargetType
     * @enum {string}
     */
    FeedbackTargetType:
      | "product"
      | "feature_tree"
      | "pricing_model"
      | "user_persona"
      | "claim"
      | "evidence"
      | "competition_edge"
      | "slice";
    /** HTTPValidationError */
    HTTPValidationError: {
      /** Detail */
      detail?: components["schemas"]["ValidationError"][];
    };
    /** HumanFeedback */
    HumanFeedback: {
      action: components["schemas"]["FeedbackAction"];
      /** After Value */
      after_value?: {
        [key: string]: unknown;
      };
      /** Before Value */
      before_value?: {
        [key: string]: unknown;
      };
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Feedback Id */
      feedback_id: string;
      /** Reason */
      reason: string;
      /** Target Id */
      target_id: string;
      target_type: components["schemas"]["FeedbackTargetType"];
      /** Task Id */
      task_id: string;
    };
    /** HumanFeedbackCreateRequest */
    HumanFeedbackCreateRequest: {
      action: components["schemas"]["FeedbackAction"];
      /** After Value */
      after_value?: {
        [key: string]: unknown;
      };
      /** Reason */
      reason: string;
      /** Target Id */
      target_id: string;
      target_type: components["schemas"]["FeedbackTargetType"];
    };
    /** HumanFeedbackCreateResponse */
    HumanFeedbackCreateResponse: {
      /** Affected Artifact Ids */
      affected_artifact_ids?: string[];
      feedback: components["schemas"]["HumanFeedback"];
      /** Metadata */
      metadata?: {
        [key: string]: unknown;
      };
      /** Recompute Status */
      recompute_status: string;
      task_status: components["schemas"]["TaskStatus"];
    };
    /** MarkdownReport */
    MarkdownReport: {
      /** File Path */
      file_path: string;
      /**
       * Generated At
       * Format: date-time
       */
      generated_at: string;
      /** Markdown */
      markdown: string;
      /** Markdown Report Id */
      markdown_report_id: string;
      /** Metadata */
      metadata?: {
        [key: string]: unknown;
      };
      /** Report Id */
      report_id: string;
      /** Task Id */
      task_id: string;
    };
    /** PricingEvidenceSummary */
    PricingEvidenceSummary: {
      /** Access Time */
      access_time?: string | null;
      /** Access Time Status */
      access_time_status: string;
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
    };
    /** PricingModel */
    PricingModel: {
      /** Access Time */
      access_time?: string | null;
      /** Bundle Description */
      bundle_description?: string | null;
      /**
       * Currency
       * @default CNY
       */
      currency: string;
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Final Price */
      final_price?: number | null;
      /** List Price */
      list_price?: number | null;
      /** Price Band */
      price_band: string;
      /** Pricing Model Id */
      pricing_model_id: string;
      /** Product Id */
      product_id: string;
      /** Promotions */
      promotions?: string[];
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Task Id */
      task_id: string;
    };
    /** Product */
    Product: {
      /** Brand */
      brand?: string | null;
      /** Category */
      category: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Name */
      name: string;
      /** Product Id */
      product_id: string;
      /** Product Url */
      product_url?: string | null;
      role: components["schemas"]["ProductRole"];
      /** Shop Name */
      shop_name?: string | null;
      /** Sku Id */
      sku_id?: string | null;
      /** Subcategory */
      subcategory: string;
      /** Tags */
      tags?: string[];
      /** Task Id */
      task_id: string;
    };
    /** ProductProfileData */
    ProductProfileData: {
      /** Evidence Summaries */
      evidence_summaries?: components["schemas"]["EvidenceSummary"][];
      feature_tree: components["schemas"]["FeatureTree"];
      /**
       * Generated At
       * Format: date-time
       */
      generated_at: string;
      /** Metadata */
      metadata?: {
        [key: string]: unknown;
      };
      pricing_evidence: components["schemas"]["PricingEvidenceSummary"];
      pricing_model: components["schemas"]["PricingModel"];
      product: components["schemas"]["Product"];
      /** Profile Id */
      profile_id: string;
      /** Task Id */
      task_id: string;
      user_persona: components["schemas"]["UserPersona"];
    };
    /**
     * ProductRole
     * @enum {string}
     */
    ProductRole:
      | "target"
      | "direct_competitor"
      | "alternative"
      | "channel_alternative"
      | "reference";
    /** ReportData */
    ReportData: {
      competitor_findings: components["schemas"]["ReportSection"];
      decision_chain_analysis: components["schemas"]["ReportSection"];
      dynamic_slice_analysis: components["schemas"]["ReportSection"];
      evidence_index: components["schemas"]["ReportSection"];
      executive_summary: components["schemas"]["ReportSection"];
      /**
       * Generated At
       * Format: date-time
       */
      generated_at: string;
      product_profile: components["schemas"]["ReportSection"];
      qa_summary: components["schemas"]["ReportSection"];
      recommendations: components["schemas"]["ReportSection"];
      /** Report Id */
      report_id: string;
      /** Section Order */
      section_order: string[];
      /** Task Id */
      task_id: string;
      user_research_insights: components["schemas"]["ReportSection"];
    };
    /** ReportSection */
    ReportSection: {
      /** Claim Ids */
      claim_ids?: string[];
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Items */
      items?: {
        [key: string]: unknown;
      }[];
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Section Id */
      section_id: string;
      /** Summary */
      summary: string;
      /** Title */
      title: string;
    };
    /**
     * ReviewSeverity
     * @enum {string}
     */
    ReviewSeverity: "info" | "warning" | "error" | "blocker";
    /**
     * ReviewStatus
     * @enum {string}
     */
    ReviewStatus: "open" | "resolved" | "waived";
    /**
     * ReviewTargetType
     * @enum {string}
     */
    ReviewTargetType: "task" | "product" | "evidence" | "claim" | "competition_edge" | "report";
    /** ReviewTask */
    ReviewTask: {
      /** Check Name */
      check_name: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Issue Code */
      issue_code: string;
      /** Message */
      message: string;
      /** Related Claim Ids */
      related_claim_ids?: string[];
      /** Required Action */
      required_action: string;
      /** Resolved At */
      resolved_at?: string | null;
      /** Review Task Id */
      review_task_id: string;
      severity: components["schemas"]["ReviewSeverity"];
      /** @default open */
      status: components["schemas"]["ReviewStatus"];
      target_agent?: components["schemas"]["AgentName"] | null;
      /** Target Id */
      target_id: string;
      target_type: components["schemas"]["ReviewTargetType"];
      /** Task Id */
      task_id: string;
    };
    /**
     * RiskFlag
     * @enum {string}
     */
    RiskFlag:
      | "missing_evidence"
      | "missing_access_time"
      | "missing_screenshot"
      | "unsupported_inference"
      | "sensitive_claim"
      | "single_review_overgeneralized"
      | "conflicting_analysis"
      | "unreliable_data";
    /**
     * RunStatus
     * @enum {string}
     */
    RunStatus: "started" | "running" | "succeeded" | "failed" | "requires_revision" | "skipped";
    /** ScoreBreakdown */
    ScoreBreakdown: {
      /** Context Match */
      context_match: number;
      /** Decision Stage Impact */
      decision_stage_impact: number;
      /** Demand Substitutability */
      demand_substitutability: number;
      /** Evidence Confidence */
      evidence_confidence: number;
      /** Market Signal Strength */
      market_signal_strength: number;
    };
    /** TaskCreateRequest */
    TaskCreateRequest: {
      /** Category */
      category?: string | null;
      /** @default demo_snapshot */
      data_source_mode: components["schemas"]["DataSourceMode"];
      /** Research Text */
      research_text?: string | null;
      /** Subcategory */
      subcategory?: string | null;
      /** Target Product Name */
      target_product_name?: string | null;
      /** Target Product Url */
      target_product_url?: string | null;
    };
    /** TaskCreateResponse */
    TaskCreateResponse: {
      status: components["schemas"]["TaskStatus"];
      task: components["schemas"]["AnalysisTask"];
      /** Task Id */
      task_id: string;
    };
    /**
     * TaskStatus
     * @enum {string}
     */
    TaskStatus:
      | "created"
      | "collecting"
      | "analyzing"
      | "reviewing"
      | "writing"
      | "completed"
      | "failed"
      | "partial_failed"
      | "human_reviewing";
    /** TaskStatusResponse */
    TaskStatusResponse: {
      /** Category */
      category: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      data_source_mode: components["schemas"]["DataSourceMode"];
      status: components["schemas"]["TaskStatus"];
      /** Subcategory */
      subcategory: string;
      /** Target Product Name */
      target_product_name: string;
      /** Target Product Url */
      target_product_url?: string | null;
      /** Task Id */
      task_id: string;
      /**
       * Updated At
       * Format: date-time
       */
      updated_at: string;
    };
    /** TokenUsageLog */
    TokenUsageLog: {
      agent_name: components["schemas"]["AgentName"];
      /** Completion Tokens */
      completion_tokens: number;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** Model Name */
      model_name: string;
      /** Prompt Tokens */
      prompt_tokens: number;
      /** Run Id */
      run_id: string;
      /** Task Id */
      task_id: string;
      /** Total Tokens */
      total_tokens: number;
      /** Usage Id */
      usage_id: string;
    };
    /** ToolCallLog */
    ToolCallLog: {
      /** Arguments Summary */
      arguments_summary?: {
        [key: string]: unknown;
      };
      /** Duration Ms */
      duration_ms?: number | null;
      /** Ended At */
      ended_at?: string | null;
      /** Error Message */
      error_message?: string | null;
      /** Run Id */
      run_id: string;
      /**
       * Started At
       * Format: date-time
       */
      started_at: string;
      status: components["schemas"]["ToolCallStatus"];
      /** Task Id */
      task_id: string;
      /** Tool Call Id */
      tool_call_id: string;
      /** Tool Name */
      tool_name: string;
    };
    /**
     * ToolCallStatus
     * @enum {string}
     */
    ToolCallStatus: "succeeded" | "failed" | "skipped";
    /** TraceDagEdge */
    TraceDagEdge: {
      /** Condition */
      condition?: string | null;
      /** Edge Id */
      edge_id: string;
      /** Label */
      label: string;
      /** Source */
      source: string;
      /** Target */
      target: string;
    };
    /** TraceDagNode */
    TraceDagNode: {
      agent_name?: components["schemas"]["AgentName"] | null;
      /**
       * Current
       * @default false
       */
      current: boolean;
      /**
       * Failed
       * @default false
       */
      failed: boolean;
      /** Label */
      label: string;
      /** Node Id */
      node_id: string;
      /** Node Type */
      node_type: string;
      /** Run Ids */
      run_ids?: string[];
      /** Status */
      status: string;
      /**
       * Visible
       * @default true
       */
      visible: boolean;
    };
    /** TraceData */
    TraceData: {
      /** Agent Runs */
      agent_runs?: components["schemas"]["AgentRunLog"][];
      /** Dag Edges */
      dag_edges?: components["schemas"]["TraceDagEdge"][];
      /** Dag Nodes */
      dag_nodes?: components["schemas"]["TraceDagNode"][];
      /** Diffs */
      diffs?: components["schemas"]["TraceDiff"][];
      /**
       * Generated At
       * Format: date-time
       */
      generated_at: string;
      /** Metadata */
      metadata?: {
        [key: string]: unknown;
      };
      /** Prompt Previews */
      prompt_previews?: components["schemas"]["TracePromptPreview"][];
      /** Qa Reviews */
      qa_reviews?: components["schemas"]["ReviewTask"][];
      /** Revision Messages */
      revision_messages?: components["schemas"]["AgentMessage"][];
      /** Task Id */
      task_id: string;
      /** Task Status */
      task_status: string;
      /** Token Usage */
      token_usage?: components["schemas"]["TokenUsageLog"][];
      /** Tool Calls */
      tool_calls?: components["schemas"]["ToolCallLog"][];
      /** Trace View Id */
      trace_view_id: string;
      /** Workflow Status */
      workflow_status: string;
    };
    /** TraceDiff */
    TraceDiff: {
      /** After */
      after?: {
        [key: string]: unknown;
      };
      /** Before */
      before?: {
        [key: string]: unknown;
      };
      /** Diff Id */
      diff_id: string;
      /** Metadata */
      metadata?: {
        [key: string]: unknown;
      };
      /** Revision Message Ids */
      revision_message_ids?: string[];
      /** Source */
      source: string;
      /** Status */
      status: string;
      /** Target Id */
      target_id: string;
      /** Target Type */
      target_type: string;
    };
    /** TracePromptPreview */
    TracePromptPreview: {
      agent_name: components["schemas"]["AgentName"];
      /** Content Summary */
      content_summary: string;
      /**
       * Folded
       * @default true
       */
      folded: boolean;
      /** Preview Id */
      preview_id: string;
      /**
       * Redacted
       * @default true
       */
      redacted: boolean;
      /** Run Id */
      run_id: string;
      /** Title */
      title: string;
    };
    /** UserPersona */
    UserPersona: {
      /** Decision Factors */
      decision_factors?: string[];
      /** Evidence Ids */
      evidence_ids?: string[];
      /**
       * Is Inference
       * @default true
       */
      is_inference: boolean;
      /** Pain Points */
      pain_points?: string[];
      /** Persona Id */
      persona_id: string;
      /** Personas */
      personas?: string[];
      /** Product Id */
      product_id: string;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Scenarios */
      scenarios?: string[];
      /** Task Id */
      task_id: string;
    };
    /** ValidationError */
    ValidationError: {
      /** Context */
      ctx?: Record<string, never>;
      /** Input */
      input?: unknown;
      /** Location */
      loc: (string | number)[];
      /** Message */
      msg: string;
      /** Error Type */
      type: string;
    };
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
};
export type $defs = Record<string, never>;
export interface operations {
  health_check_health_get: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": unknown;
        };
      };
    };
  };
  create_task_tasks_post: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["TaskCreateRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ApiResponse_TaskCreateResponse_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  get_task_tasks__task_id__get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        task_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ApiResponse_TaskStatusResponse_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  get_task_battlefield_tasks__task_id__battlefield_get: {
    parameters: {
      query?: {
        persona?: string | null;
        price_band?: string | null;
        scenario?: string | null;
      };
      header?: never;
      path: {
        task_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ApiResponse_BattlefieldData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  submit_task_feedback_tasks__task_id__feedback_post: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        task_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["HumanFeedbackCreateRequest"];
      };
    };
    responses: {
      /** @description Successful Response */
      201: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ApiResponse_HumanFeedbackCreateResponse_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  get_task_profile_tasks__task_id__profile_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        task_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ApiResponse_ProductProfileData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  get_task_report_tasks__task_id__report_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        task_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ApiResponse_ReportData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  export_task_report_markdown_tasks__task_id__report_markdown_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        task_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ApiResponse_MarkdownReport_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
  get_task_trace_tasks__task_id__trace_get: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        task_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ApiResponse_TraceData_"];
        };
      };
      /** @description Validation Error */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["HTTPValidationError"];
        };
      };
    };
  };
}
