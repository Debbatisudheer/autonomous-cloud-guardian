from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.cost import CostCategory


class CostSignalType(StrEnum):
    HIGH_LATEST_COST = "high_latest_cost"
    RISING_COST = "rising_cost"
    COST_CONCENTRATION = "cost_concentration"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NO_OPTIMIZATION_SIGNAL = "no_optimization_signal"


class CostSignalSeverity(StrEnum):
    UNKNOWN = "unknown"
    INFO = "info"
    WARNING = "warning"


class CostOptimizationSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal_type: CostSignalType
    severity: CostSignalSeverity

    resource_id: str | None = None
    category: CostCategory | None = None
    currency: str = Field(min_length=1)

    current_amount: float = Field(ge=0)
    baseline_amount: float = Field(ge=0)

    evidence_available: bool
    observation_count: int = Field(ge=0)

    finding: str
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )