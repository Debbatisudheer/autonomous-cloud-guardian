from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TelemetryMetric(StrEnum):
    """
    Supported infrastructure telemetry metrics.
    """

    CPU_USAGE_PERCENT = "cpu_usage_percent"
    MEMORY_USAGE_BYTES = "memory_usage_bytes"
    MEMORY_USAGE_PERCENT = "memory_usage_percent"
    NETWORK_RX_BYTES = "network_rx_bytes"
    NETWORK_TX_BYTES = "network_tx_bytes"


class TelemetrySource(StrEnum):
    """
    Source from which telemetry evidence was obtained.
    """

    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    AWS = "aws"
    UNKNOWN = "unknown"


class TelemetryObservation(BaseModel):
    """
    Evidence-backed observation of an infrastructure metric.

    A telemetry observation represents a measured value at a specific
    point in time. It does not represent a prediction or interpretation.
    """

    model_config = ConfigDict(extra="forbid")

    resource_id: str = Field(min_length=1)
    metric: TelemetryMetric
    value: float = Field(ge=0)
    unit: str = Field(min_length=1)

    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    source: TelemetrySource = TelemetrySource.UNKNOWN

    metadata: dict[str, str] = Field(default_factory=dict)