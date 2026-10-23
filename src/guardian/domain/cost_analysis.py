from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.cost import CostCategory


class CostAnalysisLevel(StrEnum):
    UNKNOWN = "unknown"
    NORMAL = "normal"
    ELEVATED = "elevated"


class CostAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_id: str | None = None
    category: CostCategory | None = None
    currency: str = Field(min_length=1)

    count: int = Field(ge=0)
    total_amount: float = Field(ge=0)
    minimum_amount: float = Field(ge=0)
    maximum_amount: float = Field(ge=0)
    average_amount: float = Field(ge=0)

    latest_amount: float = Field(ge=0)
    latest_observed_at: datetime

    evidence_available: bool = False


class CostAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_id: str | None = None
    category: CostCategory | None = None
    currency: str = Field(min_length=1)

    level: CostAnalysisLevel
    total_amount: float = Field(ge=0)
    average_amount: float = Field(ge=0)
    latest_amount: float = Field(ge=0)

    observation_count: int = Field(ge=0)
    evidence_available: bool

    finding: str
    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )