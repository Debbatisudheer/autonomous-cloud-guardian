from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from guardian.application.observability_event_pipeline import (
    ObservabilityEventPipeline,
)
from guardian.application.observability_event_publisher import (
    ObservabilityEventPublisher,
)
from guardian.domain.health_signal import (
    HealthSignal,
    HealthSignalLevel,
)
from guardian.domain.observability_event import (
    ObservabilityEventType,
)
from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
    TelemetrySource,
)


def make_observation() -> TelemetryObservation:
    return TelemetryObservation(
        resource_id="resource-a",
        metric=TelemetryMetric.CPU_USAGE_PERCENT,
        value=42.0,
        unit="percent",
        observed_at=datetime.now(UTC),
        source=TelemetrySource.DOCKER,
        metadata={
            "container_name": "test-container",
        },
    )


def make_signal() -> HealthSignal:
    return HealthSignal(
        resource_id="resource-a",
        metric="cpu_usage_percent",
        level=HealthSignalLevel.HEALTHY,
        value=42.0,
        unit="percent",
        reason="CPU usage is below the warning threshold.",
        evidence_available=True,
    )


def create_pipeline() -> tuple[
    ObservabilityEventPipeline,
    Mock,
]:
    publisher = Mock(
        spec=ObservabilityEventPublisher,
    )

    pipeline = ObservabilityEventPipeline(
        publisher=publisher,
    )

    return pipeline, publisher


def test_create_telemetry_event_preserves_evidence() -> None:
    pipeline, _ = create_pipeline()

    observation = make_observation()

    event = pipeline.create_telemetry_event(
        observation,
    )

    assert (
        event.event_type
        == ObservabilityEventType.TELEMETRY_OBSERVED
    )

    assert event.resource_id == (
        observation.resource_id
    )

    assert event.metric == (
        observation.metric.value
    )

    assert event.value == observation.value
    assert event.unit == observation.unit
    assert event.observed_at == (
        observation.observed_at
    )

    assert event.source == "docker"

    assert event.metadata == {
        "container_name": "test-container",
    }


def test_publish_telemetry_publishes_event() -> None:
    pipeline, publisher = create_pipeline()

    observation = make_observation()

    event = pipeline.publish_telemetry(
        observation,
    )

    assert (
        event.event_type
        == ObservabilityEventType.TELEMETRY_OBSERVED
    )

    publisher.publish.assert_called_once_with(
        event,
    )


def test_create_health_event_preserves_signal() -> None:
    pipeline, _ = create_pipeline()

    signal = make_signal()

    event = pipeline.create_health_event(
        signal,
    )

    assert (
        event.event_type
        == ObservabilityEventType.HEALTH_SIGNAL_GENERATED
    )

    assert event.resource_id == signal.resource_id
    assert event.metric == signal.metric
    assert event.value == signal.value
    assert event.unit == signal.unit
    assert event.health_level == signal.level
    assert event.source == "health_signal_engine"

    assert event.metadata == {
        "reason": signal.reason,
    }


def test_publish_health_signal_publishes_event() -> None:
    pipeline, publisher = create_pipeline()

    signal = make_signal()

    event = pipeline.publish_health_signal(
        signal,
    )

    assert (
        event.event_type
        == ObservabilityEventType.HEALTH_SIGNAL_GENERATED
    )

    publisher.publish.assert_called_once_with(
        event,
    )


def test_publish_health_signals_publishes_all_events() -> None:
    pipeline, publisher = create_pipeline()

    signals = [
        make_signal(),
        HealthSignal(
            resource_id="resource-b",
            metric="memory_usage_percent",
            level=HealthSignalLevel.WARNING,
            value=80.0,
            unit="percent",
            reason=(
                "Memory usage is at or above "
                "the warning threshold of 75.0%."
            ),
            evidence_available=True,
        ),
    ]

    events = pipeline.publish_health_signals(
        signals,
    )

    assert len(events) == 2

    publisher.publish_many.assert_called_once_with(
        events,
    )


def test_health_event_requires_value() -> None:
    pipeline, publisher = create_pipeline()

    signal = HealthSignal(
        resource_id="resource-a",
        metric="cpu_usage_percent",
        level=HealthSignalLevel.UNKNOWN,
        value=None,
        unit="percent",
        reason="No evidence available.",
        evidence_available=False,
    )

    with pytest.raises(
        ValueError,
        match="Health signal must contain a value",
    ):
        pipeline.create_health_event(
            signal,
        )

    publisher.publish.assert_not_called()


def test_health_event_requires_unit() -> None:
    pipeline, publisher = create_pipeline()

    signal = HealthSignal(
        resource_id="resource-a",
        metric="cpu_usage_percent",
        level=HealthSignalLevel.UNKNOWN,
        value=10.0,
        unit=None,
        reason="Missing unit.",
        evidence_available=False,
    )

    with pytest.raises(
        ValueError,
        match="Health signal must contain a unit",
    ):
        pipeline.create_health_event(
            signal,
        )

    publisher.publish.assert_not_called()