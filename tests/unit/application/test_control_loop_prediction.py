from datetime import UTC, datetime, timedelta

import pytest

from guardian.application.control_loop_prediction import (
    ControlLoopPredictionService,
)
from guardian.domain.control_loop import (
    ControlLoopCycle,
    ControlLoopState,
)
from guardian.domain.health_signal import (
    HealthSignalLevel,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
    ObservabilityEventType,
)
from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
    TelemetrySource,
)


def make_event() -> ObservabilityEvent:
    return ObservabilityEvent(
        event_id="prediction-event-001",
        event_type=(
            ObservabilityEventType.HEALTH_SIGNAL_GENERATED
        ),
        resource_id="resource-001",
        metric="cpu_usage_percent",
        value=70.0,
        unit="percent",
        health_level=HealthSignalLevel.WARNING,
        observed_at=datetime.now(UTC),
        source="docker",
    )


def make_observations() -> list[TelemetryObservation]:
    base = datetime.now(UTC)

    return [
        TelemetryObservation(
            resource_id="resource-001",
            metric=TelemetryMetric.CPU_USAGE_PERCENT,
            value=value,
            unit="percent",
            observed_at=base + timedelta(seconds=index),
            source=TelemetrySource.DOCKER,
        )
        for index, value in enumerate(
            [40.0, 50.0, 60.0, 70.0, 80.0]
        )
    ]


def make_cycle() -> ControlLoopCycle:
    return ControlLoopCycle.from_observability_event(
        make_event()
    ).transition_to(
        ControlLoopState.ANALYZING
    )


def test_prediction_moves_cycle_to_predicting() -> None:
    service = ControlLoopPredictionService()

    result = service.predict(
        make_cycle(),
        make_observations(),
    )

    assert result.cycle.state == ControlLoopState.PREDICTING


def test_prediction_is_attached_to_cycle_evidence() -> None:
    service = ControlLoopPredictionService()

    result = service.predict(
        make_cycle(),
        make_observations(),
    )

    assert (
        result.prediction.source_event_id
        == "prediction-event-001"
    )
    assert (
        result.prediction.resource_id
        == "resource-001"
    )
    assert (
        result.prediction.metric
        == "cpu_usage_percent"
    )


def test_prediction_requires_analysis_state() -> None:
    service = ControlLoopPredictionService()

    cycle = ControlLoopCycle.from_observability_event(
        make_event()
    )

    with pytest.raises(
        ValueError,
        match="ANALYZING",
    ):
        service.predict(
            cycle,
            make_observations(),
        )


def test_prediction_requires_evidence() -> None:
    service = ControlLoopPredictionService()

    with pytest.raises(
        ValueError,
        match="telemetry evidence",
    ):
        service.predict(
            make_cycle(),
            [],
        )


def test_prediction_rejects_wrong_resource() -> None:
    service = ControlLoopPredictionService()

    observations = make_observations()

    observations[0] = observations[0].model_copy(
        update={
            "resource_id": "different-resource",
        }
    )

    with pytest.raises(
        ValueError,
        match="resource",
    ):
        service.predict(
            make_cycle(),
            observations,
        )


def test_prediction_rejects_wrong_metric() -> None:
    service = ControlLoopPredictionService()

    observations = make_observations()

    observations[0] = observations[0].model_copy(
        update={
            "metric": TelemetryMetric.MEMORY_USAGE_BYTES,
        }
    )

    with pytest.raises(
        ValueError,
        match="metric",
    ):
        service.predict(
            make_cycle(),
            observations,
        )


def test_prediction_does_not_modify_original_cycle() -> None:
    service = ControlLoopPredictionService()

    cycle = make_cycle()

    result = service.predict(
        cycle,
        make_observations(),
    )

    assert cycle.state == ControlLoopState.ANALYZING
    assert result.cycle.state == ControlLoopState.PREDICTING
    assert cycle.cycle_id == result.cycle.cycle_id