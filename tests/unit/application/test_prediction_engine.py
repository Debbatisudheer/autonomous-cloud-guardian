from datetime import UTC, datetime, timedelta

import pytest

from guardian.application.prediction_engine import (
    PredictionEngine,
)
from guardian.domain.prediction import (
    PredictionConfidence,
    PredictionDirection,
)
from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
    TelemetrySource,
)


def make_observation(
    value: float,
    seconds: int,
) -> TelemetryObservation:
    return TelemetryObservation(
        resource_id="resource-001",
        metric=TelemetryMetric.CPU_USAGE_PERCENT,
        value=value,
        unit="percent",
        observed_at=(
            datetime.now(UTC)
            + timedelta(seconds=seconds)
        ),
        source=TelemetrySource.DOCKER,
    )


def test_increasing_series_produces_increasing_prediction() -> None:
    engine = PredictionEngine()

    observations = [
        make_observation(40.0, 0),
        make_observation(50.0, 1),
        make_observation(60.0, 2),
        make_observation(70.0, 3),
        make_observation(80.0, 4),
    ]

    result = engine.predict(
        observations,
        "event-001",
    )

    assert result.direction == PredictionDirection.INCREASING
    assert result.predicted_value == pytest.approx(90.0)
    assert result.confidence == PredictionConfidence.HIGH
    assert result.sample_count == 5


def test_decreasing_series_produces_decreasing_prediction() -> None:
    engine = PredictionEngine()

    observations = [
        make_observation(80.0, 0),
        make_observation(70.0, 1),
        make_observation(60.0, 2),
    ]

    result = engine.predict(
        observations,
        "event-002",
    )

    assert result.direction == PredictionDirection.DECREASING
    assert result.predicted_value == pytest.approx(50.0)


def test_stable_series_is_classified_as_stable() -> None:
    engine = PredictionEngine()

    observations = [
        make_observation(50.0, 0),
        make_observation(50.0, 1),
        make_observation(50.0, 2),
    ]

    result = engine.predict(
        observations,
        "event-003",
    )

    assert result.direction == PredictionDirection.STABLE
    assert result.predicted_value == pytest.approx(50.0)


def test_two_samples_have_low_confidence() -> None:
    engine = PredictionEngine()

    observations = [
        make_observation(40.0, 0),
        make_observation(50.0, 1),
    ]

    result = engine.predict(
        observations,
        "event-004",
    )

    assert result.confidence == PredictionConfidence.LOW


def test_three_samples_have_medium_confidence() -> None:
    engine = PredictionEngine()

    observations = [
        make_observation(40.0, 0),
        make_observation(50.0, 1),
        make_observation(60.0, 2),
    ]

    result = engine.predict(
        observations,
        "event-005",
    )

    assert result.confidence == PredictionConfidence.MEDIUM


def test_prediction_requires_two_samples() -> None:
    engine = PredictionEngine()

    with pytest.raises(
        ValueError,
        match="At least two",
    ):
        engine.predict(
            [make_observation(50.0, 0)],
            "event-006",
        )


def test_mixed_resources_are_rejected() -> None:
    engine = PredictionEngine()

    first = make_observation(40.0, 0)
    second = make_observation(50.0, 1).model_copy(
        update={
            "resource_id": "resource-002",
        }
    )

    with pytest.raises(
        ValueError,
        match="same resource",
    ):
        engine.predict(
            [first, second],
            "event-007",
        )


def test_mixed_metrics_are_rejected() -> None:
    engine = PredictionEngine()

    first = make_observation(40.0, 0)
    second = make_observation(50.0, 1).model_copy(
        update={
            "metric": TelemetryMetric.MEMORY_USAGE_BYTES,
        }
    )

    with pytest.raises(
        ValueError,
        match="same metric",
    ):
        engine.predict(
            [first, second],
            "event-008",
        )


def test_prediction_preserves_evidence_identity() -> None:
    engine = PredictionEngine()

    observations = [
        make_observation(40.0, 0),
        make_observation(50.0, 1),
    ]

    result = engine.predict(
        observations,
        "event-009",
    )

    assert result.source_event_id == "event-009"
    assert result.resource_id == "resource-001"
    assert result.metric == "cpu_usage_percent"
    assert result.current_value == 50.0
    assert result.evidence_available is True