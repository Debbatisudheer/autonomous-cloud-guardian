from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PredictionConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PredictionDirection(StrEnum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    UNKNOWN = "unknown"


class PredictionResult(BaseModel):
    """
    Evidence-backed prediction derived from historical telemetry.

    A prediction does not constitute a decision or infrastructure
    action.
    """

    model_config = ConfigDict(extra="forbid")

    source_event_id: str = Field(min_length=1)

    resource_id: str = Field(min_length=1)

    metric: str = Field(min_length=1)

    current_value: float = Field(ge=0)

    predicted_value: float = Field(ge=0)

    direction: PredictionDirection

    confidence: PredictionConfidence

    sample_count: int = Field(ge=2)

    evidence_available: bool = True

    basis: str = Field(min_length=1)