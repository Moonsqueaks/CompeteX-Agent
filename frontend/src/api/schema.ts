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
  "/tasks/{task_id}/overview": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Get Task Overview */
    get: operations["get_task_overview_tasks__task_id__overview_get"];
    put?: never;
    post?: never;
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
  "/tasks/{task_id}/report/docx": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Export Task Report Docx */
    get: operations["export_task_report_docx_tasks__task_id__report_docx_get"];
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
  "/tasks/{task_id}/report/regenerate": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** Regenerate Task Report */
    post: operations["regenerate_task_report_tasks__task_id__report_regenerate_post"];
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
    /**
     * ActionPriority
     * @enum {string}
     */
    ActionPriority: "p0_immediate" | "p1_current_iteration" | "p2_follow_up_validation";
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
    /** AnalysisScopeSummary */
    AnalysisScopeSummary: {
      /** Access Time Range */
      access_time_range: string;
      /** @default snapshot_pool */
      candidate_strategy: components["schemas"]["CandidateStrategy"];
      /** Category */
      category: string;
      /** Data Source Label */
      data_source_label: string;
      data_source_mode: components["schemas"]["DataSourceMode"];
      /** Evidence Count */
      evidence_count: number;
      /** Evidence Ids */
      evidence_ids?: string[];
      /** @default local_snapshot */
      evidence_source_mode: components["schemas"]["EvidenceSourceMode"];
      /** Missing Fields */
      missing_fields?: string[];
      /** Platform Label */
      platform_label: string;
      /** Platforms */
      platforms?: string[];
      /** Product Count */
      product_count: number;
      /** Scope Notice */
      scope_notice: string;
      /** Sku Count */
      sku_count: number;
      /** Snapshot Date */
      snapshot_date: string;
      /** Snapshot Version */
      snapshot_version?: string | null;
      /** Source Description */
      source_description: string;
      /** Subcategory */
      subcategory: string;
      /** Task Id */
      task_id: string;
    };
    /** AnalysisTask */
    AnalysisTask: {
      /** @default snapshot_pool */
      candidate_strategy: components["schemas"]["CandidateStrategy"];
      /** Category */
      category: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      /** @default demo_snapshot */
      data_source_mode: components["schemas"]["DataSourceMode"];
      /** @default local_snapshot */
      evidence_source_mode: components["schemas"]["EvidenceSourceMode"];
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
    /** ApiResponse[OverviewData] */
    ApiResponse_OverviewData_: {
      data?: components["schemas"]["OverviewData"] | null;
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
      /** Key Relations */
      key_relations?: components["schemas"]["BattlefieldKeyRelation"][];
      /** Metadata */
      metadata?: {
        [key: string]: unknown;
      };
      qa_summary: components["schemas"]["BattlefieldQASummary"];
      relation_filter?: components["schemas"]["BattlefieldRelationFilter"] | null;
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
      /** Missing Fields */
      missing_fields?: string[];
      /** Missing Reason */
      missing_reason?: string | null;
      /** Pricing Note */
      pricing_note?: string | null;
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
    /** BattlefieldExplanationSegment */
    BattlefieldExplanationSegment: {
      /** Claim Ids */
      claim_ids?: string[];
      /** Evidence Ids */
      evidence_ids?: string[];
      /**
       * Is Analysis Suggestion
       * @default false
       */
      is_analysis_suggestion: boolean;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Text */
      text: string;
      /** Trace Refs */
      trace_refs?: string[];
    };
    /** BattlefieldFourPartExplanation */
    BattlefieldFourPartExplanation: {
      decision_stage_impact: components["schemas"]["BattlefieldExplanationSegment"];
      response_suggestion: components["schemas"]["BattlefieldExplanationSegment"];
      strength: components["schemas"]["BattlefieldExplanationSegment"];
      why_competitor: components["schemas"]["BattlefieldExplanationSegment"];
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
      /** Primary Image Path */
      primary_image_path?: string | null;
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
    /** BattlefieldKeyRelation */
    BattlefieldKeyRelation: {
      /** Action Suggestion */
      action_suggestion: string;
      /** Claim Ids */
      claim_ids?: string[];
      /** Competitor Brand */
      competitor_brand?: string | null;
      /** Competitor Primary Image Path */
      competitor_primary_image_path?: string | null;
      /** Competitor Product Id */
      competitor_product_id: string;
      /** Competitor Product Name */
      competitor_product_name: string;
      /** Edge Id */
      edge_id: string;
      evidence_credibility: components["schemas"]["DisplayStatus"];
      /** Evidence Ids */
      evidence_ids?: string[];
      four_part_explanation: components["schemas"]["BattlefieldFourPartExplanation"];
      /** Inclusion Reason */
      inclusion_reason: string;
      /**
       * Is Default Visible
       * @default true
       */
      is_default_visible: boolean;
      relationship_label: components["schemas"]["PMRelationshipLabel"];
      /** Relationship Label Explanation */
      relationship_label_explanation: string;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Target Product Id */
      target_product_id: string;
      threat_level: components["schemas"]["ThreatLevel"];
      /** Trace Refs */
      trace_refs?: string[];
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
    /** BattlefieldRelationFilter */
    BattlefieldRelationFilter: {
      /**
       * Can Expand All
       * @default false
       */
      can_expand_all: boolean;
      /**
       * Default Limit
       * @default 5
       */
      default_limit: number;
      /**
       * Include All Relations
       * @default false
       */
      include_all_relations: boolean;
      /** Total Relation Count */
      total_relation_count: number;
      /** Visible Relation Count */
      visible_relation_count: number;
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
     * CandidateStrategy
     * @enum {string}
     */
    CandidateStrategy: "snapshot_pool" | "builtin_candidates";
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
    DataSourceMode: "demo_snapshot" | "snapshot_plus_live" | "builtin_candidates";
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
     * DecisionUsabilityStatus
     * @enum {string}
     */
    DecisionUsabilityStatus:
      | "ready_for_initial_decision"
      | "decision_with_caution"
      | "directional_reference_only";
    /** DisplayStatus */
    DisplayStatus: {
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Label */
      label: string;
      /** Reason */
      reason: string;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Trace Refs */
      trace_refs?: string[];
      value: components["schemas"]["DisplayStatusValue"];
    };
    DisplayStatusValue:
      | components["schemas"]["JudgmentStrength"]
      | components["schemas"]["DecisionUsabilityStatus"]
      | components["schemas"]["EvidenceCredibilityStatus"]
      | components["schemas"]["ThreatLevel"]
      | components["schemas"]["PMRelationshipLabel"]
      | components["schemas"]["ActionPriority"]
      | components["schemas"]["ResponsibilityType"];
    /**
     * EvidenceCredibilityStatus
     * @enum {string}
     */
    EvidenceCredibilityStatus:
      | "directly_adoptable"
      | "cautious_reference"
      | "insufficient_evidence";
    /**
     * EvidenceSourceMode
     * @enum {string}
     */
    EvidenceSourceMode: "local_snapshot" | "snapshot_plus_known_public_page";
    /**
     * EvidenceSourceType
     * @enum {string}
     */
    EvidenceSourceType:
      | "douyin_sku_snapshot"
      | "douyin_review_snapshot"
      | "user_research"
      | "manual_review"
      | "derived_artifact"
      | "public_product_page"
      | "public_brand_page"
      | "official_product_page"
      | "official_help_doc"
      | "app_store_page"
      | "official_release_note";
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
      /** Missing Fields */
      missing_fields?: string[];
      /** Missing Reason */
      missing_reason?: string | null;
      /** Pricing Note */
      pricing_note?: string | null;
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
      | "battlecard"
      | "gap_matrix_item"
      | "opportunity_item"
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
    /**
     * JudgmentStrength
     * @enum {string}
     */
    JudgmentStrength: "clear_judgment" | "directional_judgment" | "hypothesis_only";
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
    /** OverviewActionRecommendation */
    OverviewActionRecommendation: {
      /** Action Id */
      action_id: string;
      /** Description */
      description: string;
      /** Drilldown Refs */
      drilldown_refs?: components["schemas"]["OverviewDrilldownReference"][];
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Expected Impact */
      expected_impact?: string | null;
      /** Missing Reference Reason */
      missing_reference_reason?: string | null;
      priority: components["schemas"]["ActionPriority"];
      responsibility_type: components["schemas"]["ResponsibilityType"];
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Title */
      title: string;
      /** Trace Refs */
      trace_refs?: string[];
    };
    /** OverviewConclusion */
    OverviewConclusion: {
      /** Content */
      content: string;
      /** Drilldown Refs */
      drilldown_refs?: components["schemas"]["OverviewDrilldownReference"][];
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Missing Reference Reason */
      missing_reference_reason?: string | null;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Trace Refs */
      trace_refs?: string[];
    };
    /** OverviewData */
    OverviewData: {
      /** Action Recommendations */
      action_recommendations?: components["schemas"]["OverviewActionRecommendation"][];
      analysis_scope: components["schemas"]["AnalysisScopeSummary"];
      current_slice?: components["schemas"]["BattlefieldSliceSelection"];
      decision_usability: components["schemas"]["DisplayStatus"];
      /** Drilldown Refs */
      drilldown_refs?: components["schemas"]["OverviewDrilldownReference"][];
      /**
       * Generated At
       * Format: date-time
       */
      generated_at: string;
      judgment_strength: components["schemas"]["DisplayStatus"];
      /** Key Competitors */
      key_competitors?: components["schemas"]["OverviewKeyCompetitor"][];
      /** Metadata */
      metadata?: {
        [key: string]: unknown;
      };
      one_sentence_judgment: components["schemas"]["OverviewConclusion"];
      /** Opportunities */
      opportunities?: components["schemas"]["OverviewFinding"][];
      /** Overview Id */
      overview_id: string;
      /** Risk Points */
      risk_points?: components["schemas"]["OverviewFinding"][];
      /** Status Reasons */
      status_reasons?: string[];
      /** Task Id */
      task_id: string;
    };
    /** OverviewDrilldownReference */
    OverviewDrilldownReference: {
      /** Label */
      label: string;
      reference_type: components["schemas"]["OverviewDrilldownType"];
      /** Route */
      route: string;
      /** Target Id */
      target_id: string;
    };
    /**
     * OverviewDrilldownType
     * @enum {string}
     */
    OverviewDrilldownType: "battlefield" | "profile" | "report" | "trace" | "evidence";
    /** OverviewFinding */
    OverviewFinding: {
      /** Description */
      description: string;
      /** Drilldown Refs */
      drilldown_refs?: components["schemas"]["OverviewDrilldownReference"][];
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Finding Id */
      finding_id: string;
      finding_type: components["schemas"]["OverviewFindingType"];
      /** Missing Reference Reason */
      missing_reference_reason?: string | null;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Title */
      title: string;
      /** Trace Refs */
      trace_refs?: string[];
    };
    /**
     * OverviewFindingType
     * @enum {string}
     */
    OverviewFindingType:
      | "product_opportunity"
      | "expression_opportunity"
      | "evidence_risk"
      | "competition_risk"
      | "expression_risk"
      | "compliance_risk";
    /** OverviewKeyCompetitor */
    OverviewKeyCompetitor: {
      /** Brand */
      brand?: string | null;
      competitor_type: components["schemas"]["OverviewKeyCompetitorType"];
      /** Drilldown Refs */
      drilldown_refs?: components["schemas"]["OverviewDrilldownReference"][];
      evidence_credibility: components["schemas"]["DisplayStatus"];
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Inclusion Reason */
      inclusion_reason: string;
      /** Missing Reference Reason */
      missing_reference_reason?: string | null;
      /** Primary Image Path */
      primary_image_path?: string | null;
      /** Product Id */
      product_id: string;
      /** Product Name */
      product_name: string;
      relationship_label: components["schemas"]["PMRelationshipLabel"];
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Sku Id */
      sku_id?: string | null;
      threat_level: components["schemas"]["ThreatLevel"];
      /** Trace Refs */
      trace_refs?: string[];
    };
    /**
     * OverviewKeyCompetitorType
     * @enum {string}
     */
    OverviewKeyCompetitorType:
      | "highest_threat_direct_competitor"
      | "highest_threat_alternative"
      | "high_score_needs_review";
    /**
     * PMRelationshipLabel
     * @enum {string}
     */
    PMRelationshipLabel:
      | "head_to_head"
      | "low_price_interception"
      | "scenario_substitute"
      | "trust_suppression"
      | "content_seeding_competition";
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
      /** Primary Image Path */
      primary_image_path?: string | null;
      /** Primary Image Source Path */
      primary_image_source_path?: string | null;
      /** @default missing */
      primary_image_status: components["schemas"]["ProductImageStatus"];
      /** Primary Image Url */
      primary_image_url?: string | null;
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
    /**
     * ProductImageStatus
     * @enum {string}
     */
    ProductImageStatus: "available" | "missing";
    /** ProductProfileComparison */
    ProductProfileComparison: {
      /** Compared Products */
      compared_products?: components["schemas"]["ProfileComparisonProduct"][];
      /** Dimensions */
      dimensions?: components["schemas"]["ProfileComparisonDimension"][];
      /** Target Product Id */
      target_product_id: string;
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
      horizontal_comparison?: components["schemas"]["ProductProfileComparison"] | null;
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
    /** ProfileComparisonDimension */
    ProfileComparisonDimension: {
      dimension_key: components["schemas"]["ProfileComparisonDimensionKey"];
      /** Dimension Label */
      dimension_label: string;
      /** Evidence Ids */
      evidence_ids: string[];
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Status Reason */
      status_reason: string;
      target_status: components["schemas"]["TargetComparisonStatus"];
      /** Trace Refs */
      trace_refs?: string[];
      /** Values */
      values?: components["schemas"]["ProfileComparisonValue"][];
    };
    /**
     * ProfileComparisonDimensionKey
     * @enum {string}
     */
    ProfileComparisonDimensionKey:
      | "price_band"
      | "core_selling_points"
      | "persona"
      | "scenario"
      | "evidence_credibility";
    /** ProfileComparisonProduct */
    ProfileComparisonProduct: {
      /** Brand */
      brand?: string | null;
      /** Primary Image Path */
      primary_image_path?: string | null;
      /** Product Id */
      product_id: string;
      /** Product Name */
      product_name: string;
      /** Product Url */
      product_url?: string | null;
      slot: components["schemas"]["ProfileComparisonSlot"];
    };
    /**
     * ProfileComparisonSlot
     * @enum {string}
     */
    ProfileComparisonSlot:
      | "target"
      | "highest_threat_direct_competitor"
      | "highest_threat_alternative";
    /** ProfileComparisonValue */
    ProfileComparisonValue: {
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Product Id */
      product_id: string;
      /** Value */
      value: string;
    };
    /** ReportData */
    ReportData: {
      analysis_process_appendix: components["schemas"]["ReportSection"];
      competitive_landscape_judgment: components["schemas"]["ReportSection"];
      competitor_findings?: components["schemas"]["ReportSection"] | null;
      conclusion_summary: components["schemas"]["ReportSection"];
      core_competitor_analysis: components["schemas"]["ReportSection"];
      decision_chain_analysis?: components["schemas"]["ReportSection"] | null;
      dynamic_slice_analysis?: components["schemas"]["ReportSection"] | null;
      evidence_index?: components["schemas"]["ReportSection"] | null;
      evidence_quality_appendix: components["schemas"]["ReportSection"];
      executive_summary?: components["schemas"]["ReportSection"] | null;
      /**
       * Generated At
       * Format: date-time
       */
      generated_at: string;
      /** Narrative Report */
      narrative_report?: {
        [key: string]: unknown;
      };
      product_profile?: components["schemas"]["ReportSection"] | null;
      product_strategy_recommendations: components["schemas"]["ReportSection"];
      qa_summary?: components["schemas"]["ReportSection"] | null;
      recommendations?: components["schemas"]["ReportSection"] | null;
      /** Report Id */
      report_id: string;
      /** Section Order */
      section_order: string[];
      target_opportunities_and_risks: components["schemas"]["ReportSection"];
      /** Task Id */
      task_id: string;
      user_decision_chain_analysis: components["schemas"]["ReportSection"];
      user_research_insights?: components["schemas"]["ReportSection"] | null;
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
     * ResponsibilityType
     * @enum {string}
     */
    ResponsibilityType:
      | "product_feature"
      | "content_expression"
      | "pricing_strategy"
      | "evidence_research";
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
    /**
     * TargetComparisonStatus
     * @enum {string}
     */
    TargetComparisonStatus: "advantage" | "parity" | "weakness" | "insufficient_evidence";
    /** TaskCreateRequest */
    TaskCreateRequest: {
      /** @default snapshot_pool */
      candidate_strategy: components["schemas"]["CandidateStrategy"];
      /** Category */
      category?: string | null;
      data_source_mode?: components["schemas"]["DataSourceMode"] | null;
      /** @default local_snapshot */
      evidence_source_mode: components["schemas"]["EvidenceSourceMode"];
      /** Research Text */
      research_text?: string | null;
      /** Subcategory */
      subcategory?: string | null;
      /** Target Product Name */
      target_product_name?: string | null;
      /** Target Product Url */
      target_product_url: string;
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
      candidate_strategy: components["schemas"]["CandidateStrategy"];
      /** Category */
      category: string;
      /**
       * Created At
       * Format: date-time
       */
      created_at: string;
      data_source_mode: components["schemas"]["DataSourceMode"];
      evidence_source_mode: components["schemas"]["EvidenceSourceMode"];
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
    /**
     * ThreatLevel
     * @enum {string}
     */
    ThreatLevel: "high_threat" | "medium_threat" | "low_threat" | "high_score_needs_review";
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
      /** Drilldown Targets */
      drilldown_targets?: components["schemas"]["TraceDrilldownTarget"][];
      /** Evidence Chains */
      evidence_chains?: components["schemas"]["TraceEvidenceChain"][];
      /**
       * Generated At
       * Format: date-time
       */
      generated_at: string;
      /** Metadata */
      metadata?: {
        [key: string]: unknown;
      };
      process_view?: components["schemas"]["TraceProcessView"] | null;
      /** Prompt Previews */
      prompt_previews?: components["schemas"]["TracePromptPreview"][];
      /** Qa Reviews */
      qa_reviews?: components["schemas"]["ReviewTask"][];
      /** Quality Records */
      quality_records?: components["schemas"]["TraceQualityRecord"][];
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
      /**
       * Business Impact
       * @default ��¼�˷��������еĽṹ���仯�����ϱ��ǰ�������ж�ҵ��Ӱ�졣
       */
      business_impact: string;
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
    /** TraceDrilldownTarget */
    TraceDrilldownTarget: {
      /** Label */
      label: string;
      /** Query */
      query?: {
        [key: string]: unknown;
      };
      /** Tab */
      tab: string;
      /** Target Id */
      target_id: string;
    };
    /** TraceEvidenceChain */
    TraceEvidenceChain: {
      /** Chain Id */
      chain_id: string;
      /** Claim Content */
      claim_content: string;
      /** Claim Id */
      claim_id: string;
      /** Claim Status */
      claim_status: string;
      /** Confidence */
      confidence: number;
      /** Evidence Items */
      evidence_items?: components["schemas"]["TraceEvidenceItem"][];
      /** Is Inference */
      is_inference: boolean;
      /** Navigation */
      navigation?: {
        [key: string]: unknown;
      };
      /** Report Section Ids */
      report_section_ids?: string[];
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      /** Trace Refs */
      trace_refs?: string[];
    };
    /** TraceEvidenceItem */
    TraceEvidenceItem: {
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
      /** Navigation */
      navigation?: {
        [key: string]: unknown;
      };
      /** Product Id */
      product_id?: string | null;
      /** Risk Flags */
      risk_flags?: components["schemas"]["RiskFlag"][];
      source_type: components["schemas"]["EvidenceSourceType"];
      /** Source Url */
      source_url?: string | null;
    };
    /** TraceProcessView */
    TraceProcessView: {
      /** Agent Run Count */
      agent_run_count: number;
      /** Dag Node Count */
      dag_node_count: number;
      /**
       * Default Tab
       * @default evidence_chain
       */
      default_tab: string;
      /** Prompt Preview Count */
      prompt_preview_count: number;
      /**
       * Technical Details Folded
       * @default true
       */
      technical_details_folded: boolean;
      /** Token Usage Count */
      token_usage_count: number;
      /** Tool Call Count */
      tool_call_count: number;
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
    /** TraceQualityRecord */
    TraceQualityRecord: {
      /** Action Result */
      action_result: string;
      /** Check Item */
      check_item: string;
      /** Evidence Ids */
      evidence_ids?: string[];
      /** Issue Code */
      issue_code: string;
      /** Issue Summary */
      issue_summary: string;
      /** Navigation */
      navigation?: {
        [key: string]: unknown;
      };
      /** Needs Attention */
      needs_attention: boolean;
      /** Quality Record Id */
      quality_record_id: string;
      /** Related Claim Ids */
      related_claim_ids?: string[];
      /** Required Action */
      required_action: string;
      /** Resolved */
      resolved: boolean;
      /** Review Task Id */
      review_task_id: string;
      severity: components["schemas"]["ReviewSeverity"];
      status: components["schemas"]["ReviewStatus"];
      target_agent?: components["schemas"]["AgentName"] | null;
      /** Target Id */
      target_id: string;
      target_type: components["schemas"]["ReviewTargetType"];
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
        include_all_relations?: boolean;
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
  get_task_overview_tasks__task_id__overview_get: {
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
          "application/json": components["schemas"]["ApiResponse_OverviewData_"];
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
  export_task_report_docx_tasks__task_id__report_docx_get: {
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
      /** @description Word .docx report download. */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document": unknown;
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
  regenerate_task_report_tasks__task_id__report_regenerate_post: {
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
