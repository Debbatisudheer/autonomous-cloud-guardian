from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.health_signal import (
    HealthSignalLevel,
)


class ObservabilityEventType(StrEnum):
    """
    Types of events emitted by the observability pipeline.
    """

    TELEMETRY_OBSERVED = "telemetry_observed"
    HEALTH_SIGNAL_GENERATED = "health_signal_generated"


class ObservabilityEvent(BaseModel):
    """
    Evidence-backed event emitted by the observability pipeline.

    An observability event records something that has already
    happened or has already been measured.

    It is not a prediction, recommendation, or remediation command.
    """

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(
        default_factory=lambda: str(uuid4()),
        min_length=1,
    )

    event_type: ObservabilityEventType

    resource_id: str = Field(min_length=1)

    metric: str = Field(min_length=1)

    value: float = Field(ge=0)

    unit: str = Field(min_length=1)

    health_level: HealthSignalLevel

    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    source: str = Field(min_length=1)

    metadata: dict[str, str] = Field(
        default_factory=dict,
    )