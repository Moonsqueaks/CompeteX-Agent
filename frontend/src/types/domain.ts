export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonObject | JsonValue[];
export type JsonObject = { [key: string]: JsonValue };

export type IsoDateTime = string;

export type DataSourceMode = "demo_snapshot" | "snapshot_plus_live";

export type TaskStatus =
  | "created"
  | "collecting"
  | "analyzing"
  | "reviewing"
  | "writing"
  | "completed"
  | "failed"
  | "partial_failed"
  | "human_reviewing";

export type AgentName =
  | "orchestrator"
  | "collection_agent"
  | "analysis_agent"
  | "qa_agent"
  | "writer_agent"
  | "human";

export type AgentMessageType = "artifact_ready" | "revision_request" | "status_update" | "error";

export type AgentMessageStatus =
  | "pending"
  | "sent"
  | "processed"
  | "requires_revision"
  | "resolved"
  | "failed";

export type ProductRole =
  | "target"
  | "direct_competitor"
  | "alternative"
  | "channel_alternative"
  | "reference";

export type EvidenceSourceType =
  | "douyin_sku_snapshot"
  | "douyin_review_snapshot"
  | "user_research"
  | "manual_review"
  | "derived_artifact";

export type ConfidenceLevel = "low" | "medium" | "high" | "unknown";

export type RiskFlag =
  | "missing_evidence"
  | "missing_access_time"
  | "missing_screenshot"
  | "unsupported_inference"
  | "sensitive_claim"
  | "single_review_overgeneralized"
  | "conflicting_analysis"
  | "unreliable_data";

export type ClaimStatus = "accepted" | "rejected" | "needs_review" | "draft";

export type CompetitionType = "direct" | "alternative" | "channel" | "content_cooccurrence";

export type DecisionStage =
  | "information_reach"
  | "interest_formation"
  | "capability_understanding"
  | "trust_building"
  | "decision_completion";

export type ReviewSeverity = "info" | "warning" | "error" | "blocker";

export type ReviewStatus = "open" | "resolved" | "waived";

export type ReviewTargetType =
  | "task"
  | "product"
  | "evidence"
  | "claim"
  | "competition_edge"
  | "report";

export type RunStatus =
  | "started"
  | "running"
  | "succeeded"
  | "failed"
  | "requires_revision"
  | "skipped";

export type ToolCallStatus = "succeeded" | "failed" | "skipped";

export type MockFixtureName = "profile" | "battlefield" | "trace" | "report";

export type DevelopmentMockMeta = {
  data_kind: "development_mock";
  fixture_name: MockFixtureName;
  final_demo_data: false;
  generated_for: "frontend_f03";
  note: string;
  updated_at: IsoDateTime;
};

export type AnalysisTask = {
  task_id: string;
  target_product_name: string;
  category: string;
  subcategory: string;
  data_source_mode: DataSourceMode;
  status: TaskStatus;
  created_at: IsoDateTime;
  updated_at: IsoDateTime;
  target_product_url?: string | null;
  research_text?: string | null;
  metadata?: JsonObject;
};

export type Product = {
  product_id: string;
  task_id: string;
  name: string;
  category: string;
  subcategory: string;
  role: ProductRole;
  created_at: IsoDateTime;
  sku_id?: string | null;
  brand?: string | null;
  shop_name?: string | null;
  product_url?: string | null;
  evidence_ids: string[];
  tags: string[];
};

export type FeatureTree = {
  feature_tree_id: string;
  task_id: string;
  product_id: string;
  cleaning_capability: string[];
  odor_control: string[];
  safety_features: string[];
  smart_features: string[];
  maintenance_cost: string[];
  evidence_ids: string[];
  risk_flags: RiskFlag[];
};

export type PricingModel = {
  pricing_model_id: string;
  task_id: string;
  product_id: string;
  price_band: string;
  currency: "CNY";
  list_price: number | null;
  final_price: number | null;
  promotions: string[];
  bundle_description?: string | null;
  evidence_ids: string[];
  access_time?: IsoDateTime | null;
  risk_flags: RiskFlag[];
};

export type UserPersona = {
  persona_id: string;
  task_id: string;
  product_id: string;
  personas: string[];
  pain_points: string[];
  scenarios: string[];
  decision_factors: string[];
  evidence_ids: string[];
  is_inference: boolean;
  risk_flags: RiskFlag[];
};

export type Evidence = {
  evidence_id: string;
  task_id: string;
  source_type: EvidenceSourceType;
  content_summary: string;
  confidence_level: ConfidenceLevel;
  limitations: string;
  product_id?: string | null;
  source_url?: string | null;
  screenshot_path?: string | null;
  access_time?: IsoDateTime | null;
  metadata: JsonObject;
};

export type Claim = {
  claim_id: string;
  task_id: string;
  claim_type: string;
  content: string;
  evidence_ids: string[];
  confidence: number;
  is_inference: boolean;
  risk_flags: RiskFlag[];
  status: ClaimStatus;
  created_at: IsoDateTime;
};

export type CompetitionSlice = {
  price_band: string;
  persona: string;
  scenario: string;
};

export type ScoreBreakdown = {
  demand_substitutability: number;
  context_match: number;
  decision_stage_impact: number;
  evidence_confidence: number;
  market_signal_strength: number;
};

export type CompetitionEdge = {
  edge_id: string;
  task_id: string;
  target_product_id: string;
  competitor_product_id: string;
  competition_type: CompetitionType;
  slice: CompetitionSlice;
  decision_stages: DecisionStage[];
  edge_score: number;
  score_breakdown: ScoreBreakdown;
  claim_ids: string[];
  human_adjusted: boolean;
  risk_flags: RiskFlag[];
  created_at: IsoDateTime;
};

export type ReviewTask = {
  review_task_id: string;
  task_id: string;
  check_name: string;
  issue_code: string;
  severity: ReviewSeverity;
  status: ReviewStatus;
  target_type: ReviewTargetType;
  target_id: string;
  message: string;
  required_action: string;
  created_at: IsoDateTime;
  target_agent?: AgentName | null;
  related_claim_ids: string[];
  evidence_ids: string[];
  resolved_at?: IsoDateTime | null;
};

export type AgentMessage = {
  message_id: string;
  task_id: string;
  from_agent: AgentName;
  to_agent: AgentName;
  message_type: AgentMessageType;
  artifact_type: string;
  payload: JsonObject;
  evidence_ids: string[];
  status: AgentMessageStatus;
  created_at: IsoDateTime;
};

export type AgentRunLog = {
  run_id: string;
  task_id: string;
  agent_name: AgentName;
  status: RunStatus;
  started_at: IsoDateTime;
  ended_at?: IsoDateTime | null;
  input_summary?: string | null;
  output_summary?: string | null;
  error_message?: string | null;
};

export type ToolCallLog = {
  tool_call_id: string;
  task_id: string;
  run_id: string;
  tool_name: string;
  arguments_summary: JsonObject;
  status: ToolCallStatus;
  started_at: IsoDateTime;
  ended_at?: IsoDateTime | null;
  duration_ms?: number | null;
  error_message?: string | null;
};

export type TokenUsageLog = {
  usage_id: string;
  task_id: string;
  run_id: string;
  agent_name: AgentName;
  model_name: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  created_at: IsoDateTime;
};

export type GraphNode = {
  id: string;
  label: string;
  node_type: "product" | "agent" | "artifact";
  status?: TaskStatus | RunStatus | "pending";
  metadata: JsonObject;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  label: string;
  edge_type: string;
  metadata: JsonObject;
};

export type ProfileResponse = {
  mock_meta: DevelopmentMockMeta;
  task: AnalysisTask;
  target_product: Product;
  feature_tree: FeatureTree;
  pricing_model: PricingModel;
  user_persona: UserPersona;
  evidences: Evidence[];
  claims: Claim[];
  review_summary: {
    open_count: number;
    risk_flags: RiskFlag[];
    latest_review_task_ids: string[];
    human_feedback_enabled: boolean;
  };
};

export type BattlefieldResponse = {
  mock_meta: DevelopmentMockMeta;
  task: AnalysisTask;
  selected_slice: CompetitionSlice;
  available_slices: CompetitionSlice[];
  products: Product[];
  graph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  competition_edges: CompetitionEdge[];
  claims: Claim[];
  evidences: Evidence[];
  edge_explanations: Record<string, JsonObject>;
  qa_summary: {
    has_revision: boolean;
    review_tasks: ReviewTask[];
    diff_count: number;
  };
};

export type TraceDiff = {
  diff_id: string;
  title: string;
  target_type: ReviewTargetType;
  target_id: string;
  before: JsonObject;
  after: JsonObject;
  related_review_task_ids: string[];
};

export type TraceResponse = {
  mock_meta: DevelopmentMockMeta;
  task: AnalysisTask;
  dag: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  agent_run_logs: AgentRunLog[];
  tool_call_logs: ToolCallLog[];
  token_usage_logs: TokenUsageLog[];
  review_tasks: ReviewTask[];
  agent_messages: AgentMessage[];
  diffs: TraceDiff[];
};

export type ReportSection = {
  section_id: string;
  title: string;
  summary: string;
  claim_ids: string[];
  evidence_ids: string[];
  risk_flags: RiskFlag[];
};

export type ReportResponse = {
  mock_meta: DevelopmentMockMeta;
  task: AnalysisTask;
  report_id: string;
  report_status: "draft" | "ready" | "blocked";
  title: string;
  generated_at: IsoDateTime;
  sections: ReportSection[];
  claims: Claim[];
  evidence_index: Evidence[];
  qa_summary: {
    status: "passed" | "requires_revision";
    review_task_ids: string[];
    summary: string;
  };
  markdown_export: {
    available: boolean;
    reason?: string;
  };
};
