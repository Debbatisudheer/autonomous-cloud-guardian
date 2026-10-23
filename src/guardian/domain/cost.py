from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CostCategory(StrEnum):
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    UNKNOWN = "unknown"


class CostSource(StrEnum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    UNKNOWN = "unknown"


class CostObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_id: str = Field(min_length=1)
    amount: float = Field(ge=0)
    currency: str = Field(min_length=1)
    category: CostCategory = CostCategory.UNKNOWN
    source: CostSource = CostSource.UNKNOWN
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    billing_period_start: datetime | None = None
    billing_period_end: datetime | None = None
    evidence_available: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)