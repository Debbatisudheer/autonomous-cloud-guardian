from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.security import (
    SecuritySeverity,
)


class SecurityRiskSignalType(StrEnum):
    UNKNOWN_SECURITY_RISK = "unknown_security_risk"
    INFORMATIONAL_SECURITY_SIGNAL = (
        "informational_security_signal"
    )
    ELEVATED_SECURITY_RISK = "elevated_security_risk"
    HIGH_SECURITY_RISK = "high_security_risk"
    CRITICAL_SECURITY_RISK = "critical_security_risk"


class SecurityRiskSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_id: str = Field(min_length=1)

    finding_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    resource_id: str | None = None

    signal_type: SecurityRiskSignalType
    severity: SecuritySeverity

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)

    evidence_available: bool

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    metadata: dict[str, str] = Field(
        default_factory=dict
    )