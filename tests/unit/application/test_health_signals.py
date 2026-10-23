from datetime import UTC, datetime

import pytest

from guardian.application.health_signals import (
    HealthSignalEngine,
)
from guardian.domain.health_signal import (
    HealthSignalLevel,
)
from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
    TelemetrySource,
)


def make_observation(
    metric: TelemetryMetric,
    value: float,
    unit: str = "percent",
) -> TelemetryObservation:
    return TelemetryObservation(
        resource_id="resource-a",
        metric=metric,
        value=value,
        unit=unit,
        observed_at=datetime.now(UTC),
        source=TelemetrySource.DOCKER,
    )


def test_cpu_below_warning_is_healthy() -> None:
    engine = HealthSignalEngine()

    signal = engine.evaluate(
        make_observation(
            TelemetryMetric.CPU_USAGE_PERCENT,
            50.0,
        )
    )

    assert signal.level == HealthSignalLevel.HEALTHY
    assert signal.value == 50.0
    assert signal.evidence_available is True


def test_cpu_warning_threshold() -> None:
    engine = HealthSignalEngine()

    signal = engine.evaluate(
        make_observation(
            TelemetryMetric.CPU_USAGE_PERCENT,
            70.0,
        )
    )

    assert signal.level == HealthSignalLevel.WARNING


def test_cpu_critical_threshold() -> None:
    engine = HealthSignalEngine()

    signal = engine.evaluate(
        make_observation(
            TelemetryMetric.CPU_USAGE_PERCENT,
            90.0,
        )
    )

    assert signal.level == HealthSignalLevel.CRITICAL


def test_memory_below_warning_is_healthy() -> None:
    engine = HealthSignalEngine()

    signal = engine.evaluate(
        make_observation(
            TelemetryMetric.MEMORY_USAGE_PERCENT,
            60.0,
        )
    )

    assert signal.level == HealthSignalLevel.HEALTHY


def test_memory_warning_threshold() -> None:
    engine = HealthSignalEngine()

    signal = engine.evaluate(
        make_observation(
            TelemetryMetric.MEMORY_USAGE_PERCENT,
            75.0,
        )
    )

    assert signal.level == HealthSignalLevel.WARNING


def test_memory_critical_threshold() -> None:
    engine = HealthSignalEngine()

    signal = engine.evaluate(
        make_observation(
            TelemetryMetric.MEMORY_USAGE_PERCENT,
            90.0,
        )
    )

    assert signal.level == HealthSignalLevel.CRITICAL


def test_memory_bytes_are_measured_as_healthy() -> None:
    engine = HealthSignalEngine()

    signal = engine.evaluate(
        make_observation(
            TelemetryMetric.MEMORY_USAGE_BYTES,
            1048576.0,
            unit="bytes",
        )
    )

    assert signal.level == HealthSignalLevel.HEALTHY
    assert signal.value == 1048576.0


@pytest.mark.parametrize(
    "metric",
    [
        TelemetryMetric.NETWORK_RX_BYTES,
        TelemetryMetric.NETWORK_TX_BYTES,
    ],
)
def test_network_bytes_are_not_treated_as_failure(
    metric: TelemetryMetric,
) -> None:
    engine = HealthSignalEngine()

    signal = engine.evaluate(
        make_observation(
            metric,
            12345.0,
            unit="bytes",
        )
    )

    assert signal.level == HealthSignalLevel.HEALTHY
    assert signal.evidence_available is True


def test_evaluate_many() -> None:
    engine = HealthSignalEngine()

    observations = [
        make_observation(
            TelemetryMetric.CPU_USAGE_PERCENT,
            40.0,
        ),
        make_observation(
            TelemetryMetric.MEMORY_USAGE_PERCENT,
            80.0,
        ),
    ]

    signals = engine.evaluate_many(
        observations,
    )

    assert len(signals) == 2

    assert (
        signals[0].level
        == HealthSignalLevel.HEALTHY
    )

    assert (
        signals[1].level
        == HealthSignalLevel.WARNING
    )