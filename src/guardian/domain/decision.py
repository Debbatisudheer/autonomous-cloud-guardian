from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.prediction import (
    PredictionConfidence,
    PredictionDirection,
)


class DecisionOutcome(StrEnum):
    NO_ACTION = "no_action"
    MONITOR = "monitor"
    ACTION_RECOMMENDED = "action_recommended"


class DecisionPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DecisionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_event_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    metric: str = Field(min_length=1)

    current_value: float = Field(ge=0)
    predicted_value: float = Field(ge=0)

    prediction_direction: PredictionDirection
    prediction_confidence: PredictionConfidence

    outcome: DecisionOutcome
    priority: DecisionPriority

    evidence_available: bool = True
    rationale: str = Field(min_length=1)