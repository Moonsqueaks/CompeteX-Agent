from datetime import datetime

from pydantic import Field

from app.schemas.common import JsonObject, RiskFlag, StrictBaseModel


class ReportSection(StrictBaseModel):
    section_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    items: list[JsonObject] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)


class ReportData(StrictBaseModel):
    report_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    generated_at: datetime
    section_order: list[str] = Field(min_length=1)
    conclusion_summary: ReportSection
    competitive_landscape_judgment: ReportSection
    core_competitor_analysis: ReportSection
    user_decision_chain_analysis: ReportSection
    target_opportunities_and_risks: ReportSection
    product_strategy_recommendations: ReportSection
    evidence_quality_appendix: ReportSection
    analysis_process_appendix: ReportSection
    narrative_report: JsonObject = Field(default_factory=dict)
    executive_summary: ReportSection | None = None
    product_profile: ReportSection | None = None
    competitor_findings: ReportSection | None = None
    dynamic_slice_analysis: ReportSection | None = None
    decision_chain_analysis: ReportSection | None = None
    user_research_insights: ReportSection | None = None
    recommendations: ReportSection | None = None
    qa_summary: ReportSection | None = None
    evidence_index: ReportSection | None = None


class MarkdownReport(StrictBaseModel):
    markdown_report_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    report_id: str = Field(min_length=1)
    generated_at: datetime
    markdown: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    metadata: JsonObject = Field(default_factory=dict)


class RelationshipGraphImage(StrictBaseModel):
    graph_image_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    report_id: str = Field(min_length=1)
    generated_at: datetime
    file_path: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    byte_size: int = Field(ge=0)
    metadata: JsonObject = Field(default_factory=dict)


class WordReport(StrictBaseModel):
    word_report_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    report_id: str = Field(min_length=1)
    generated_at: datetime
    file_path: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    byte_size: int = Field(ge=0)
    metadata: JsonObject = Field(default_factory=dict)
