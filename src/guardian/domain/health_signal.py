from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class HealthSignalLevel(StrEnum):
    """
    Operational severity of a measured health signal.
    """

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


class HealthSignal(BaseModel):
    """
    Evidence-backed health signal derived from measured telemetry.

    A health signal describes the current operational condition
    represented by an observed metric. It is not a prediction,
    recommendation, or remediation action.
    """

    model_config = ConfigDict(extra="forbid")

    resource_id: str = Field(min_length=1)
    metric: str = Field(min_length=1)

    level: HealthSignalLevel

    value: float | None = None
    unit: str | None = None

    reason: str = Field(min_length=1)

    evidence_available: bool = True