from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
    TelemetrySource,
)


def test_telemetry_observation_accepts_valid_data() -> None:
    observed_at = datetime.now(UTC)

    observation = TelemetryObservation(
        resource_id="resource-1",
        metric=TelemetryMetric.CPU_USAGE_PERCENT,
        value=42.5,
        unit="percent",
        observed_at=observed_at,
        source=TelemetrySource.DOCKER,
    )

    assert observation.resource_id == "resource-1"
    assert observation.metric == TelemetryMetric.CPU_USAGE_PERCENT
    assert observation.value == 42.5
    assert observation.unit == "percent"
    assert observation.observed_at == observed_at
    assert observation.source == TelemetrySource.DOCKER


def test_telemetry_observation_defaults_are_valid() -> None:
    observation = TelemetryObservation(
        resource_id="resource-1",
        metric=TelemetryMetric.MEMORY_USAGE_BYTES,
        value=1024,
        unit="bytes",
    )

    assert observation.source == TelemetrySource.UNKNOWN
    assert observation.observed_at.tzinfo is not None
    assert observation.metadata == {}


def test_telemetry_observation_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        TelemetryObservation(
            resource_id="resource-1",
            metric=TelemetryMetric.CPU_USAGE_PERCENT,
            value=-1,
            unit="percent",
        )


def test_telemetry_observation_requires_resource_id() -> None:
    with pytest.raises(ValidationError):
        TelemetryObservation(
            resource_id="",
            metric=TelemetryMetric.CPU_USAGE_PERCENT,
            value=10,
            unit="percent",
        )


def test_telemetry_observation_requires_unit() -> None:
    with pytest.raises(ValidationError):
        TelemetryObservation(
            resource_id="resource-1",
            metric=TelemetryMetric.CPU_USAGE_PERCENT,
            value=10,
            unit="",
        )


def test_telemetry_metric_values_are_stable() -> None:
    assert TelemetryMetric.CPU_USAGE_PERCENT.value == (
        "cpu_usage_percent"
    )

    assert TelemetryMetric.MEMORY_USAGE_BYTES.value == (
        "memory_usage_bytes"
    )

    assert TelemetryMetric.MEMORY_USAGE_PERCENT.value == (
        "memory_usage_percent"
    )

    assert TelemetryMetric.NETWORK_RX_BYTES.value == (
        "network_rx_bytes"
    )

    assert TelemetryMetric.NETWORK_TX_BYTES.value == (
        "network_tx_bytes"
    )


def test_docker_is_supported_as_telemetry_source() -> None:
    observation = TelemetryObservation(
        resource_id="resource-1",
        metric=TelemetryMetric.CPU_USAGE_PERCENT,
        value=10,
        unit="percent",
        source=TelemetrySource.DOCKER,
    )

    assert observation.source == TelemetrySource.DOCKER


def test_metadata_can_store_evidence_context() -> None:
    observation = TelemetryObservation(
        resource_id="resource-1",
        metric=TelemetryMetric.CPU_USAGE_PERCENT,
        value=10,
        unit="percent",
        source=TelemetrySource.DOCKER,
        metadata={
            "container_name": "acg-postgres",
            "measurement": "docker_stats",
        },
    )

    assert observation.metadata["container_name"] == "acg-postgres"
    assert observation.metadata["measurement"] == "docker_stats"