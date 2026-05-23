from datetime import datetime

from pydantic import Field

from app.schemas.common import (
    AgentMessageStatus,
    AgentMessageType,
    AgentName,
    JsonObject,
    StrictBaseModel,
)


class AgentMessage(StrictBaseModel):
    message_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    from_agent: AgentName
    to_agent: AgentName
    message_type: AgentMessageType
    artifact_type: str = Field(min_length=1)
    payload: JsonObject = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)
    status: AgentMessageStatus = AgentMessageStatus.PENDING
    created_at: datetime
