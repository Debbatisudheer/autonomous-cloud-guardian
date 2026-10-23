from datetime import UTC, datetime, timedelta

from guardian.application.telemetry_aggregation import (
    TelemetryAggregator,
)
from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
    TelemetrySource,
)


def make_observation(
    resource_id: str,
    metric: TelemetryMetric,
    value: float,
    observed_at: datetime,
) -> TelemetryObservation:
    return TelemetryObservation(
        resource_id=resource_id,
        metric=metric,
        value=value,
        unit=(
            "percent"
            if metric
            in {
                TelemetryMetric.CPU_USAGE_PERCENT,
                TelemetryMetric.MEMORY_USAGE_PERCENT,
            }
            else "bytes"
        ),
        observed_at=observed_at,
        source=TelemetrySource.DOCKER,
    )


def test_aggregate_calculates_statistics() -> None:
    base_time = datetime(
        2026,
        10,
        23,
        8,
        0,
        tzinfo=UTC,
    )

    observations = [
        make_observation(
            "resource-a",
            TelemetryMetric.CPU_USAGE_PERCENT,
            10.0,
            base_time,
        ),
        make_observation(
            "resource-a",
            TelemetryMetric.CPU_USAGE_PERCENT,
            20.0,
            base_time + timedelta(seconds=10),
        ),
        make_observation(
            "resource-a",
            TelemetryMetric.CPU_USAGE_PERCENT,
            30.0,
            base_time + timedelta(seconds=20),
        ),
    ]

    aggregator = TelemetryAggregator()

    result = aggregator.aggregate(observations)

    assert len(result) == 1

    aggregate = result[0]

    assert aggregate.resource_id == "resource-a"
    assert aggregate.metric == TelemetryMetric.CPU_USAGE_PERCENT

    assert aggregate.count == 3
    assert aggregate.minimum == 10.0
    assert aggregate.maximum == 30.0
    assert aggregate.average == 20.0

    assert aggregate.latest == 30.0

    assert aggregate.latest_observed_at == (
        base_time + timedelta(seconds=20)
    )


def test_aggregate_groups_multiple_metrics() -> None:
    timestamp = datetime(
        2026,
        10,
        23,
        8,
        0,
        tzinfo=UTC,
    )

    observations = [
        make_observation(
            "resource-a",
            TelemetryMetric.CPU_USAGE_PERCENT,
            10.0,
            timestamp,
        ),
        make_observation(
            "resource-a",
            TelemetryMetric.MEMORY_USAGE_PERCENT,
            25.0,
            timestamp,
        ),
    ]

    aggregator = TelemetryAggregator()

    result = aggregator.aggregate(observations)

    assert len(result) == 2

    metrics = {
        aggregate.metric
        for aggregate in result
    }

    assert metrics == {
        TelemetryMetric.CPU_USAGE_PERCENT,
        TelemetryMetric.MEMORY_USAGE_PERCENT,
    }


def test_aggregate_groups_multiple_resources() -> None:
    timestamp = datetime(
        2026,
        10,
        23,
        8,
        0,
        tzinfo=UTC,
    )

    observations = [
        make_observation(
            "resource-a",
            TelemetryMetric.CPU_USAGE_PERCENT,
            10.0,
            timestamp,
        ),
        make_observation(
            "resource-b",
            TelemetryMetric.CPU_USAGE_PERCENT,
            50.0,
            timestamp,
        ),
    ]

    aggregator = TelemetryAggregator()

    result = aggregator.aggregate(observations)

    assert len(result) == 2

    resources = {
        aggregate.resource_id
        for aggregate in result
    }

    assert resources == {
        "resource-a",
        "resource-b",
    }


def test_aggregate_for_resource_filters_correctly() -> None:
    timestamp = datetime(
        2026,
        10,
        23,
        8,
        0,
        tzinfo=UTC,
    )

    observations = [
        make_observation(
            "resource-a",
            TelemetryMetric.CPU_USAGE_PERCENT,
            10.0,
            timestamp,
        ),
        make_observation(
            "resource-a",
            TelemetryMetric.MEMORY_USAGE_PERCENT,
            20.0,
            timestamp,
        ),
        make_observation(
            "resource-b",
            TelemetryMetric.CPU_USAGE_PERCENT,
            50.0,
            timestamp,
        ),
    ]

    aggregator = TelemetryAggregator()

    result = aggregator.aggregate_for_resource(
        observations,
        "resource-a",
    )

    assert len(result) == 2

    assert all(
        aggregate.resource_id == "resource-a"
        for aggregate in result
    )


def test_aggregate_for_metric_filters_correctly() -> None:
    timestamp = datetime(
        2026,
        10,
        23,
        8,
        0,
        tzinfo=UTC,
    )

    observations = [
        make_observation(
            "resource-a",
            TelemetryMetric.CPU_USAGE_PERCENT,
            10.0,
            timestamp,
        ),
        make_observation(
            "resource-b",
            TelemetryMetric.CPU_USAGE_PERCENT,
            20.0,
            timestamp,
        ),
        make_observation(
            "resource-a",
            TelemetryMetric.MEMORY_USAGE_PERCENT,
            30.0,
            timestamp,
        ),
    ]

    aggregator = TelemetryAggregator()

    result = aggregator.aggregate_for_metric(
        observations,
        TelemetryMetric.CPU_USAGE_PERCENT,
    )

    assert len(result) == 2

    assert all(
        aggregate.metric
        == TelemetryMetric.CPU_USAGE_PERCENT
        for aggregate in result
    )


def test_aggregate_between_filters_time_window() -> None:
    base_time = datetime(
        2026,
        10,
        23,
        8,
        0,
        tzinfo=UTC,
    )

    observations = [
        make_observation(
            "resource-a",
            TelemetryMetric.CPU_USAGE_PERCENT,
            10.0,
            base_time,
        ),
        make_observation(
            "resource-a",
            TelemetryMetric.CPU_USAGE_PERCENT,
            20.0,
            base_time + timedelta(minutes=1),
        ),
        make_observation(
            "resource-a",
            TelemetryMetric.CPU_USAGE_PERCENT,
            30.0,
            base_time + timedelta(minutes=2),
        ),
    ]

    aggregator = TelemetryAggregator()

    result = aggregator.aggregate_between(
        observations,
        base_time + timedelta(seconds=30),
        base_time + timedelta(minutes=1, seconds=30),
    )

    assert len(result) == 1

    aggregate = result[0]

    assert aggregate.count == 1
    assert aggregate.minimum == 20.0
    assert aggregate.maximum == 20.0
    assert aggregate.average == 20.0
    assert aggregate.latest == 20.0


def test_empty_observations_return_empty_result() -> None:
    aggregator = TelemetryAggregator()

    result = aggregator.aggregate([])

    assert result == []


def test_invalid_time_window_raises_error() -> None:
    aggregator = TelemetryAggregator()

    start = datetime(
        2026,
        10,
        23,
        9,
        0,
        tzinfo=UTC,
    )

    end = datetime(
        2026,
        10,
        23,
        8,
        0,
        tzinfo=UTC,
    )

    try:
        aggregator.aggregate_between(
            [],
            start,
            end,
        )
    except ValueError as exc:
        assert (
            str(exc)
            == "Aggregation end time must not be before start time."
        )
    else:
        raise AssertionError(
            "Expected ValueError was not raised."
        )