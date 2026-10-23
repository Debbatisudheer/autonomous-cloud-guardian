from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.cost import CostCategory
from guardian.domain.cost_forecast import (
    CostForecastConfidence,
    CostForecastDirection,
)
from guardian.domain.cost_signal import (
    CostSignalSeverity,
    CostSignalType,
)


class CostRecommendationOutcome(StrEnum):
    NO_RECOMMENDATION = "no_recommendation"
    REVIEW = "review"
    OPTIMIZATION_RECOMMENDED = "optimization_recommended"


class CostRecommendationPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CostRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_id: str | None = None
    category: CostCategory | None = None
    currency: str = Field(min_length=1)

    signal_type: CostSignalType
    signal_severity: CostSignalSeverity

    forecast_direction: CostForecastDirection
    forecast_confidence: CostForecastConfidence

    current_amount: float = Field(ge=0)
    forecast_amount: float = Field(ge=0)

    outcome: CostRecommendationOutcome
    priority: CostRecommendationPriority

    evidence_available: bool
    observation_count: int = Field(ge=0)

    rationale: str

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )