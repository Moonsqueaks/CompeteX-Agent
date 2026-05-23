from typing import Any

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiResponse[DataT](BaseModel):
    data: DataT | None = None
    error: ApiError | None = None
    trace_id: str
