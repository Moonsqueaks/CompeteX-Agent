from datetime import datetime

from pydantic import Field, field_validator, model_validator

from app.schemas.common import (
    CandidateStrategy,
    DataSourceMode,
    EvidenceSourceMode,
    JsonObject,
    StrictBaseModel,
    TaskStatus,
)


def split_data_source_mode(
    data_source_mode: DataSourceMode | str | None,
) -> tuple[EvidenceSourceMode, CandidateStrategy]:
    if data_source_mode == DataSourceMode.SNAPSHOT_PLUS_LIVE.value:
        return (
            EvidenceSourceMode.SNAPSHOT_PLUS_KNOWN_PUBLIC_PAGE,
            CandidateStrategy.SNAPSHOT_POOL,
        )
    if data_source_mode == DataSourceMode.BUILTIN_CANDIDATES.value:
        return EvidenceSourceMode.LOCAL_SNAPSHOT, CandidateStrategy.BUILTIN_CANDIDATES
    return EvidenceSourceMode.LOCAL_SNAPSHOT, CandidateStrategy.SNAPSHOT_POOL


def combine_modes(
    evidence_source_mode: EvidenceSourceMode | str | None,
    candidate_strategy: CandidateStrategy | str | None,
) -> DataSourceMode:
    if evidence_source_mode == EvidenceSourceMode.SNAPSHOT_PLUS_KNOWN_PUBLIC_PAGE.value:
        return DataSourceMode.SNAPSHOT_PLUS_LIVE
    if candidate_strategy == CandidateStrategy.BUILTIN_CANDIDATES.value:
        return DataSourceMode.BUILTIN_CANDIDATES
    return DataSourceMode.DEMO_SNAPSHOT


class AnalysisTask(StrictBaseModel):
    task_id: str = Field(min_length=1)
    target_product_name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    subcategory: str = Field(min_length=1)
    data_source_mode: DataSourceMode = DataSourceMode.DEMO_SNAPSHOT
    evidence_source_mode: EvidenceSourceMode = EvidenceSourceMode.LOCAL_SNAPSHOT
    candidate_strategy: CandidateStrategy = CandidateStrategy.SNAPSHOT_POOL
    status: TaskStatus = TaskStatus.CREATED
    created_at: datetime
    updated_at: datetime
    target_product_url: str | None = None
    research_text: str | None = None
    metadata: JsonObject = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def derive_split_modes(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        evidence_source_mode = normalized.get("evidence_source_mode")
        candidate_strategy = normalized.get("candidate_strategy")
        data_source_mode = normalized.get("data_source_mode")
        if evidence_source_mode is None or candidate_strategy is None:
            legacy_evidence_source_mode, legacy_candidate_strategy = split_data_source_mode(
                data_source_mode
            )
            if evidence_source_mode is None:
                normalized["evidence_source_mode"] = legacy_evidence_source_mode
            if candidate_strategy is None:
                normalized["candidate_strategy"] = legacy_candidate_strategy
        normalized["data_source_mode"] = combine_modes(
            normalized.get("evidence_source_mode"),
            normalized.get("candidate_strategy"),
        )
        return normalized


class TaskCreateRequest(StrictBaseModel):
    target_product_name: str | None = None
    target_product_url: str = Field(min_length=1)
    category: str | None = None
    subcategory: str | None = None
    data_source_mode: DataSourceMode | None = None
    evidence_source_mode: EvidenceSourceMode = EvidenceSourceMode.LOCAL_SNAPSHOT
    candidate_strategy: CandidateStrategy = CandidateStrategy.SNAPSHOT_POOL
    research_text: str | None = None

    @model_validator(mode="before")
    @classmethod
    def derive_split_modes(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        evidence_source_mode = normalized.get("evidence_source_mode")
        candidate_strategy = normalized.get("candidate_strategy")
        data_source_mode = normalized.get("data_source_mode")
        if data_source_mode is not None and (
            evidence_source_mode is None or candidate_strategy is None
        ):
            legacy_evidence_source_mode, legacy_candidate_strategy = split_data_source_mode(
                data_source_mode
            )
            if evidence_source_mode is None:
                normalized["evidence_source_mode"] = legacy_evidence_source_mode
            if candidate_strategy is None:
                normalized["candidate_strategy"] = legacy_candidate_strategy
        normalized["data_source_mode"] = combine_modes(
            normalized.get("evidence_source_mode"),
            normalized.get("candidate_strategy"),
        )
        return normalized

    @field_validator("category", "subcategory")
    @classmethod
    def reject_blank_required_context(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank.")
        return stripped

    @field_validator("target_product_name", "research_text")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("target_product_url")
    @classmethod
    def reject_blank_target_product_url(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank.")
        return stripped


class TaskCreateResponse(StrictBaseModel):
    task_id: str = Field(min_length=1)
    status: TaskStatus
    task: AnalysisTask


class TaskStatusResponse(StrictBaseModel):
    task_id: str = Field(min_length=1)
    target_product_name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    subcategory: str = Field(min_length=1)
    data_source_mode: DataSourceMode
    evidence_source_mode: EvidenceSourceMode
    candidate_strategy: CandidateStrategy
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    target_product_url: str | None = None

    @classmethod
    def from_task(cls, task: AnalysisTask) -> "TaskStatusResponse":
        return cls(
            task_id=task.task_id,
            target_product_name=task.target_product_name,
            target_product_url=task.target_product_url,
            category=task.category,
            subcategory=task.subcategory,
            data_source_mode=task.data_source_mode,
            evidence_source_mode=task.evidence_source_mode,
            candidate_strategy=task.candidate_strategy,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
