from datetime import UTC, datetime

import pytest

from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
    TelemetrySource,
)
from guardian.infrastructure.postgres.telemetry_storage import (
    PostgreSQLTelemetryStorage,
)


def make_observation(
    resource_id: str = "container-123",
    metric: TelemetryMetric = TelemetryMetric.CPU_USAGE_PERCENT,
    value: float = 25.5,
) -> TelemetryObservation:
    return TelemetryObservation(
        resource_id=resource_id,
        metric=metric,
        value=value,
        unit="percent",
        observed_at=datetime.now(UTC),
        source=TelemetrySource.DOCKER,
        metadata={
            "container_name": "acg-test",
            "measurement": "docker_stats",
        },
    )


def test_storage_builds_default_dsn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ACG_POSTGRES_HOST",
        "localhost",
    )
    monkeypatch.setenv(
        "ACG_POSTGRES_PORT",
        "5433",
    )
    monkeypatch.setenv(
        "ACG_POSTGRES_DB",
        "guardian",
    )
    monkeypatch.setenv(
        "ACG_POSTGRES_USER",
        "postgres",
    )
    monkeypatch.setenv(
        "ACG_POSTGRES_PASSWORD",
        "postgres",
    )

    storage = PostgreSQLTelemetryStorage()

    assert "host=localhost" in storage._dsn
    assert "port=5433" in storage._dsn
    assert "dbname=guardian" in storage._dsn
    assert "user=postgres" in storage._dsn


def test_storage_accepts_explicit_dsn() -> None:
    dsn = (
        "host=test "
        "port=5432 "
        "dbname=test "
        "user=test "
        "password=test"
    )

    storage = PostgreSQLTelemetryStorage(
        dsn=dsn,
    )

    assert storage._dsn == dsn


def test_limit_validation_rejects_zero() -> None:
    with pytest.raises(ValueError):
        PostgreSQLTelemetryStorage._validate_limit(0)


def test_limit_validation_rejects_negative() -> None:
    with pytest.raises(ValueError):
        PostgreSQLTelemetryStorage._validate_limit(-1)


def test_limit_validation_accepts_positive() -> None:
    PostgreSQLTelemetryStorage._validate_limit(1)


def test_row_conversion_preserves_observation() -> None:
    observed_at = datetime.now(UTC)

    row = (
        "container-123",
        "cpu_usage_percent",
        42.5,
        "percent",
        observed_at,
        "docker",
        {
            "container_name": "acg-test",
            "measurement": "docker_stats",
        },
    )

    observation = (
        PostgreSQLTelemetryStorage._row_to_observation(
            row
        )
    )

    assert observation.resource_id == "container-123"
    assert observation.metric == (
        TelemetryMetric.CPU_USAGE_PERCENT
    )
    assert observation.value == 42.5
    assert observation.unit == "percent"
    assert observation.source == TelemetrySource.DOCKER
    assert observation.observed_at == observed_at
    assert observation.metadata["container_name"] == "acg-test"


def test_row_conversion_supports_all_metrics() -> None:
    for metric in TelemetryMetric:
        row = (
            "container-123",
            metric.value,
            10.0,
            "bytes",
            datetime.now(UTC),
            "docker",
            {},
        )

        observation = (
            PostgreSQLTelemetryStorage._row_to_observation(
                row
            )
        )

        assert observation.metric == metric


def test_get_between_requires_valid_range() -> None:
    storage = PostgreSQLTelemetryStorage()

    now = datetime.now(UTC)

    with pytest.raises(ValueError):
        storage.get_between(
            start=now,
            end=now,
        )


def test_empty_save_many_does_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = PostgreSQLTelemetryStorage(
        dsn="unused",
    )

    called = False

    def fake_connect() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(
        storage,
        "_connect",
        fake_connect,
    )

    storage.save_many([])

    assert called is False


def test_observation_factory_is_evidence_backed() -> None:
    observation = make_observation()

    assert observation.source == TelemetrySource.DOCKER
    assert observation.metadata["measurement"] == (
        "docker_stats"
    )
    assert observation.value == 25.5


def test_multiple_observations_have_distinct_metrics() -> None:
    observations = [
        make_observation(
            metric=TelemetryMetric.CPU_USAGE_PERCENT,
            value=10.0,
        ),
        make_observation(
            metric=TelemetryMetric.MEMORY_USAGE_BYTES,
            value=1000.0,
        ),
        make_observation(
            metric=TelemetryMetric.NETWORK_RX_BYTES,
            value=2000.0,
        ),
    ]

    assert len(observations) == 3
    assert {
        observation.metric
        for observation in observations
    } == {
        TelemetryMetric.CPU_USAGE_PERCENT,
        TelemetryMetric.MEMORY_USAGE_BYTES,
        TelemetryMetric.NETWORK_RX_BYTES,
    }