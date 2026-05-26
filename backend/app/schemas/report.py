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
    executive_summary: ReportSection
    product_profile: ReportSection
    competitor_findings: ReportSection
    dynamic_slice_analysis: ReportSection
    decision_chain_analysis: ReportSection
    user_research_insights: ReportSection
    recommendations: ReportSection
    qa_summary: ReportSection
    evidence_index: ReportSection


class MarkdownReport(StrictBaseModel):
    markdown_report_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    report_id: str = Field(min_length=1)
    generated_at: datetime
    markdown: str = Field(min_length=1)
    file_path: str = Field(min_length=1)
    metadata: JsonObject = Field(default_factory=dict)
