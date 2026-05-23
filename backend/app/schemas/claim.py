from datetime import datetime

from pydantic import Field, model_validator

from app.schemas.common import ClaimStatus, RiskFlag, StrictBaseModel


class Claim(StrictBaseModel):
    claim_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    claim_type: str = Field(min_length=1)
    content: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    is_inference: bool = False
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    status: ClaimStatus = ClaimStatus.ACCEPTED
    created_at: datetime

    @model_validator(mode="after")
    def mark_missing_evidence(self) -> "Claim":
        if self.evidence_ids:
            return self
        if RiskFlag.MISSING_EVIDENCE not in self.risk_flags:
            self.risk_flags.append(RiskFlag.MISSING_EVIDENCE)
        object.__setattr__(self, "status", ClaimStatus.NEEDS_REVIEW)
        return self
