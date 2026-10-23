from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.cost import CostCategory


class CostForecastDirection(StrEnum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    UNKNOWN = "unknown"


class CostForecastConfidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CostForecast(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_id: str
    category: CostCategory
    currency: str = Field(min_length=1)

    current_amount: float = Field(ge=0)
    forecast_amount: float = Field(ge=0)

    direction: CostForecastDirection
    confidence: CostForecastConfidence

    sample_count: int = Field(ge=2)
    evidence_available: bool

    latest_observed_at: datetime
    forecast_for: datetime

    basis: str
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )