from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.schemas import AnalysisTask, HumanFeedback, TaskStatus
from app.storage.models import (
    AnalysisTaskRecord,
    ArtifactRecord,
    HumanFeedbackRecord,
    TraceLogRecord,
)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _dump_model(payload: BaseModel | dict) -> dict:
    if isinstance(payload, BaseModel):
        return payload.model_dump(mode="json")
    return dict(payload)


def _load_model(model_type: type[BaseModel], payload: dict) -> BaseModel:
    return model_type.model_validate(payload)


class TaskRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, task: AnalysisTask) -> AnalysisTask:
        payload = task.model_dump(mode="json")
        record = AnalysisTaskRecord(
            task_id=payload["task_id"],
            target_product_name=payload["target_product_name"],
            target_product_url=payload.get("target_product_url"),
            category=payload["category"],
            subcategory=payload["subcategory"],
            data_source_mode=payload["data_source_mode"],
            status=payload["status"],
            research_text=payload.get("research_text"),
            metadata_json=payload.get("metadata", {}),
            created_at=payload["created_at"],
            updated_at=payload["updated_at"],
        )
        self.session.add(record)
        self.session.commit()
        return self._to_schema(record)

    def get(self, task_id: str) -> AnalysisTask | None:
        record = self.session.get(AnalysisTaskRecord, task_id)
        if record is None:
            return None
        return self._to_schema(record)

    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        updated_at: datetime | None = None,
    ) -> AnalysisTask | None:
        record = self.session.get(AnalysisTaskRecord, task_id)
        if record is None:
            return None

        record.status = status.value
        record.updated_at = (updated_at or datetime.now(UTC)).isoformat()
        self.session.commit()
        return self._to_schema(record)

    def update_metadata(
        self,
        task_id: str,
        metadata: dict,
        updated_at: datetime | None = None,
    ) -> AnalysisTask | None:
        record = self.session.get(AnalysisTaskRecord, task_id)
        if record is None:
            return None

        record.metadata_json = dict(metadata)
        record.updated_at = (updated_at or datetime.now(UTC)).isoformat()
        self.session.commit()
        return self._to_schema(record)

    def _to_schema(self, record: AnalysisTaskRecord) -> AnalysisTask:
        return AnalysisTask.model_validate(
            {
                "task_id": record.task_id,
                "target_product_name": record.target_product_name,
                "target_product_url": record.target_product_url,
                "category": record.category,
                "subcategory": record.subcategory,
                "data_source_mode": record.data_source_mode,
                "status": record.status,
                "research_text": record.research_text,
                "metadata": record.metadata_json,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
            }
        )


class ArtifactRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, artifact_type: str, artifact_id: str, payload: BaseModel | dict) -> None:
        dumped = _dump_model(payload)
        task_id = dumped["task_id"]
        existing = self._find_record(task_id, artifact_type, artifact_id)
        now = _utc_now_iso()

        if existing is None:
            existing = ArtifactRecord(
                task_id=task_id,
                artifact_type=artifact_type,
                artifact_id=artifact_id,
                payload=dumped,
                created_at=now,
                updated_at=now,
            )
            self.session.add(existing)
        else:
            existing.payload = dumped
            existing.updated_at = now
        self.session.commit()

    def get(
        self,
        task_id: str,
        artifact_type: str,
        artifact_id: str,
        model_type: type[BaseModel] | None = None,
    ) -> BaseModel | dict | None:
        record = self._find_record(task_id, artifact_type, artifact_id)
        if record is None:
            return None
        if model_type is None:
            return record.payload
        return _load_model(model_type, record.payload)

    def list_by_task(
        self,
        task_id: str,
        artifact_type: str | None = None,
        model_type: type[BaseModel] | None = None,
    ) -> list[BaseModel] | list[dict]:
        statement = select(ArtifactRecord).where(ArtifactRecord.task_id == task_id)
        if artifact_type is not None:
            statement = statement.where(ArtifactRecord.artifact_type == artifact_type)
        statement = statement.order_by(ArtifactRecord.id)

        records = self.session.scalars(statement).all()
        if model_type is None:
            return [record.payload for record in records]
        return [_load_model(model_type, record.payload) for record in records]

    def _find_record(
        self,
        task_id: str,
        artifact_type: str,
        artifact_id: str,
    ) -> ArtifactRecord | None:
        statement = select(ArtifactRecord).where(
            ArtifactRecord.task_id == task_id,
            ArtifactRecord.artifact_type == artifact_type,
            ArtifactRecord.artifact_id == artifact_id,
        )
        return self.session.scalars(statement).first()


class TraceLogRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, log_type: str, log_id: str, payload: BaseModel | dict) -> None:
        dumped = _dump_model(payload)
        task_id = dumped["task_id"]
        existing = self._find_record(task_id, log_type, log_id)

        if existing is None:
            existing = TraceLogRecord(
                task_id=task_id,
                log_type=log_type,
                log_id=log_id,
                payload=dumped,
                created_at=_utc_now_iso(),
            )
            self.session.add(existing)
        else:
            existing.payload = dumped
        self.session.commit()

    def list_by_task(
        self,
        task_id: str,
        log_type: str | None = None,
        model_type: type[BaseModel] | None = None,
    ) -> list[BaseModel] | list[dict]:
        statement = select(TraceLogRecord).where(TraceLogRecord.task_id == task_id)
        if log_type is not None:
            statement = statement.where(TraceLogRecord.log_type == log_type)
        statement = statement.order_by(TraceLogRecord.id)

        records = self.session.scalars(statement).all()
        if model_type is None:
            return [
                {"log_type": record.log_type, "log_id": record.log_id, "payload": record.payload}
                for record in records
            ]
        return [_load_model(model_type, record.payload) for record in records]

    def _find_record(self, task_id: str, log_type: str, log_id: str) -> TraceLogRecord | None:
        statement = select(TraceLogRecord).where(
            TraceLogRecord.task_id == task_id,
            TraceLogRecord.log_type == log_type,
            TraceLogRecord.log_id == log_id,
        )
        return self.session.scalars(statement).first()


class HumanFeedbackRepository:
    def __init__(self, session: Session):
        self.session = session

    def save(self, feedback: HumanFeedback) -> HumanFeedback:
        payload = feedback.model_dump(mode="json")
        existing = self.session.get(HumanFeedbackRecord, feedback.feedback_id)

        if existing is None:
            existing = HumanFeedbackRecord(
                feedback_id=payload["feedback_id"],
                task_id=payload["task_id"],
                target_type=payload["target_type"],
                target_id=payload["target_id"],
                action=payload["action"],
                payload=payload,
                created_at=payload["created_at"],
            )
            self.session.add(existing)
        else:
            existing.target_type = payload["target_type"]
            existing.target_id = payload["target_id"]
            existing.action = payload["action"]
            existing.payload = payload
            existing.created_at = payload["created_at"]
        self.session.commit()
        return self._to_schema(existing)

    def get(self, feedback_id: str) -> HumanFeedback | None:
        record = self.session.get(HumanFeedbackRecord, feedback_id)
        if record is None:
            return None
        return self._to_schema(record)

    def list_by_task(self, task_id: str) -> list[HumanFeedback]:
        statement = (
            select(HumanFeedbackRecord)
            .where(HumanFeedbackRecord.task_id == task_id)
            .order_by(HumanFeedbackRecord.created_at)
        )
        return [self._to_schema(record) for record in self.session.scalars(statement).all()]

    def _to_schema(self, record: HumanFeedbackRecord) -> HumanFeedback:
        return HumanFeedback.model_validate(record.payload)
