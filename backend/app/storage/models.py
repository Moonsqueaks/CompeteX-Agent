from sqlalchemy import JSON, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.db import Base


class AnalysisTaskRecord(Base):
    __tablename__ = "analysis_tasks"

    task_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    target_product_name: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    subcategory: Mapped[str] = mapped_column(String(128), nullable=False)
    data_source_mode: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)
    target_product_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class ArtifactRecord(Base):
    __tablename__ = "artifact_json"
    __table_args__ = (
        UniqueConstraint("task_id", "artifact_type", "artifact_id", name="uq_artifact_identity"),
        Index("ix_artifact_task_type", "task_id", "artifact_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(128), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)


class TraceLogRecord(Base):
    __tablename__ = "trace_logs"
    __table_args__ = (
        UniqueConstraint("task_id", "log_type", "log_id", name="uq_trace_log_identity"),
        Index("ix_trace_logs_task_type", "task_id", "log_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(128), nullable=False)
    log_type: Mapped[str] = mapped_column(String(64), nullable=False)
    log_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)


class HumanFeedbackRecord(Base):
    __tablename__ = "human_feedback"
    __table_args__ = (Index("ix_human_feedback_task_id", "task_id"),)

    feedback_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
