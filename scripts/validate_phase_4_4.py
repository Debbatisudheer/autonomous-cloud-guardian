from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from guardian.application.telemetry_aggregation import (
    TelemetryAggregator,
)
from guardian.infrastructure.docker.telemetry import (
    DockerTelemetryCollector,
)
from guardian.infrastructure.postgres.telemetry_storage import (
    PostgreSQLTelemetryStorage,
)


def print_header(title: str) -> None:
    print("=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    print_header(
        "PHASE 4.4 — REAL TELEMETRY AGGREGATION VALIDATION"
    )

    # ==================================================================
    # 1. Initialize real PostgreSQL storage
    # ==================================================================

    print()
    print("[1] POSTGRESQL STORAGE INITIALIZATION")
    print("-" * 72)

    storage = PostgreSQLTelemetryStorage()

    storage.initialize()

    print("PostgreSQL connection       : PASS")
    print("Telemetry schema            : PASS")

    # ==================================================================
    # 2. Collect REAL Docker telemetry
    # ==================================================================

    print()
    print("[2] REAL DOCKER TELEMETRY COLLECTION")
    print("-" * 72)

    collector = DockerTelemetryCollector()

    observations = collector.collect_all()

    if not observations:
        raise RuntimeError(
            "No real Docker telemetry observations were collected."
        )

    print(
        "Real telemetry observations : "
        f"{len(observations)}"
    )

    resource_ids = {
        observation.resource_id
        for observation in observations
    }

    print(
        "Resources with telemetry   : "
        f"{len(resource_ids)}"
    )

    for observation in observations:
        if observation.source.value != "docker":
            raise RuntimeError(
                "Collected observation is not sourced from Docker."
            )

        if observation.value < 0:
            raise RuntimeError(
                "Collected telemetry contains a negative value."
            )

        if not observation.resource_id:
            raise RuntimeError(
                "Collected telemetry has no resource ID."
            )

        if not observation.unit:
            raise RuntimeError(
                "Collected telemetry has no unit."
            )

    print("Real telemetry evidence     : PASS")

    # ==================================================================
    # 3. Persist REAL telemetry
    # ==================================================================

    print()
    print("[3] POSTGRESQL TELEMETRY PERSISTENCE")
    print("-" * 72)

    storage.save_many(observations)

    print(
        "Persisted observations      : "
        f"{len(observations)}"
    )

    print("PostgreSQL persistence      : PASS")

    # ==================================================================
    # 4. Retrieve the exact telemetry time window
    # ==================================================================

    print()
    print("[4] STORED TELEMETRY RETRIEVAL")
    print("-" * 72)

    timestamps = [
        observation.observed_at
        for observation in observations
    ]

    earliest = min(timestamps)
    latest = max(timestamps)

    start = earliest - timedelta(
        minutes=1
    )

    end = latest + timedelta(
        minutes=1
    )

    stored_observations = storage.get_between(
        start=start,
        end=end,
        limit=10000,
    )

    if not stored_observations:
        raise RuntimeError(
            "No stored telemetry was retrieved."
        )

    stored_pairs = {
        (
            observation.resource_id,
            observation.metric.value,
            observation.value,
            observation.observed_at,
        )
        for observation in stored_observations
    }

    original_pairs = {
        (
            observation.resource_id,
            observation.metric.value,
            observation.value,
            observation.observed_at,
        )
        for observation in observations
    }

    if not original_pairs.issubset(
        stored_pairs
    ):
        raise RuntimeError(
            "Stored telemetry does not contain all "
            "newly collected observations."
        )

    print(
        "Stored observations       : "
        f"{len(stored_observations)}"
    )

    print("Stored telemetry evidence  : PASS")

    # ==================================================================
    # 5. Create aggregation engine
    # ==================================================================

    print()
    print("[5] TELEMETRY AGGREGATION ENGINE")
    print("-" * 72)

    aggregator = TelemetryAggregator()

    print("Aggregation engine          : PASS")

    # ==================================================================
    # 6. Resource + metric aggregation
    # ==================================================================

    print()
    print("[6] RESOURCE + METRIC AGGREGATION")
    print("-" * 72)

    aggregates = aggregator.aggregate(
        observations
    )

    if not aggregates:
        raise RuntimeError(
            "Aggregation returned no results."
        )

    expected_groups = {
        (
            observation.resource_id,
            observation.metric,
        )
        for observation in observations
    }

    actual_groups = {
        (
            aggregate.resource_id,
            aggregate.metric,
        )
        for aggregate in aggregates
    }

    if actual_groups != expected_groups:
        raise RuntimeError(
            "Aggregation groups do not match "
            "the collected telemetry."
        )

    for aggregate in aggregates:
        if aggregate.count <= 0:
            raise RuntimeError(
                "Aggregate count must be greater than zero."
            )

        if aggregate.minimum > aggregate.maximum:
            raise RuntimeError(
                "Aggregate minimum exceeds maximum."
            )

        if not (
            aggregate.minimum
            <= aggregate.average
            <= aggregate.maximum
        ):
            raise RuntimeError(
                "Aggregate average is outside "
                "the minimum/maximum range."
            )

        if not (
            aggregate.minimum
            <= aggregate.latest
            <= aggregate.maximum
        ):
            raise RuntimeError(
                "Aggregate latest value is outside "
                "the observed range."
            )

    print(
        "Aggregate groups           : "
        f"{len(aggregates)}"
    )

    print("Group integrity             : PASS")
    print("Statistics integrity        : PASS")

    # ==================================================================
    # 7. Print real aggregate evidence
    # ==================================================================

    print()
    print("[7] REAL AGGREGATE RESULTS")
    print("-" * 72)

    for aggregate in aggregates:
        print()
        print(
            f"  Resource: {aggregate.resource_id}"
        )

        print(
            f"  Metric:   {aggregate.metric.value}"
        )

        print(
            f"  Count:    {aggregate.count}"
        )

        print(
            f"  Minimum:  {aggregate.minimum:.4f}"
        )

        print(
            f"  Maximum:  {aggregate.maximum:.4f}"
        )

        print(
            f"  Average:  {aggregate.average:.4f}"
        )

        print(
            f"  Latest:   {aggregate.latest:.4f}"
        )

        print(
            "  Latest observed at: "
            f"{aggregate.latest_observed_at.isoformat()}"
        )

    print()
    print("Real aggregate evidence     : PASS")

    # ==================================================================
    # 8. Resource-specific aggregation
    # ==================================================================

    print()
    print("[8] RESOURCE-SPECIFIC AGGREGATION")
    print("-" * 72)

    first_resource = min(resource_ids)

    resource_aggregates = (
        aggregator.aggregate_for_resource(
            observations,
            first_resource,
        )
    )

    if not resource_aggregates:
        raise RuntimeError(
            "Resource-specific aggregation returned "
            "no results."
        )

    if not all(
        aggregate.resource_id == first_resource
        for aggregate in resource_aggregates
    ):
        raise RuntimeError(
            "Resource-specific aggregation contains "
            "another resource."
        )

    print(
        "Resource queried           : "
        f"{first_resource}"
    )

    print(
        "Aggregate groups            : "
        f"{len(resource_aggregates)}"
    )

    print("Resource aggregation        : PASS")

    # ==================================================================
    # 9. Metric-specific aggregation
    # ==================================================================

    print()
    print("[9] METRIC-SPECIFIC AGGREGATION")
    print("-" * 72)

    first_metric = observations[0].metric

    metric_aggregates = (
        aggregator.aggregate_for_metric(
            observations,
            first_metric,
        )
    )

    if not metric_aggregates:
        raise RuntimeError(
            "Metric-specific aggregation returned "
            "no results."
        )

    if not all(
        aggregate.metric == first_metric
        for aggregate in metric_aggregates
    ):
        raise RuntimeError(
            "Metric-specific aggregation contains "
            "another metric."
        )

    print(
        "Metric queried              : "
        f"{first_metric.value}"
    )

    print(
        "Aggregate groups            : "
        f"{len(metric_aggregates)}"
    )

    print("Metric aggregation          : PASS")

    # ==================================================================
    # 10. Time-window aggregation
    # ==================================================================

    print()
    print("[10] TIME-WINDOW AGGREGATION")
    print("-" * 72)

    window_aggregates = aggregator.aggregate_between(
        observations,
        start,
        end,
    )

    if not window_aggregates:
        raise RuntimeError(
            "Time-window aggregation returned "
            "no results."
        )

    window_groups = {
        (
            aggregate.resource_id,
            aggregate.metric,
        )
        for aggregate in window_aggregates
    }

    if window_groups != expected_groups:
        raise RuntimeError(
            "Time-window aggregation groups do not "
            "match the source telemetry."
        )

    print(
        "Window start                : "
        f"{start.isoformat()}"
    )

    print(
        "Window end                  : "
        f"{end.isoformat()}"
    )

    print(
        "Aggregate groups            : "
        f"{len(window_aggregates)}"
    )

    print("Time-window aggregation     : PASS")

    # ==================================================================
    # Final result
    # ==================================================================

    print()
    print("=" * 72)
    print("PHASE 4.4 VALIDATION RESULT")
    print("=" * 72)

    print(
        "POSTGRESQL CONNECTION        : PASS"
    )

    print(
        "REAL DOCKER TELEMETRY        : PASS"
    )

    print(
        "TELEMETRY PERSISTENCE        : PASS"
    )

    print(
        "STORED TELEMETRY RETRIEVAL   : PASS"
    )

    print(
        "AGGREGATION ENGINE           : PASS"
    )

    print(
        "RESOURCE + METRIC AGGREGATION: PASS"
    )

    print(
        "RESOURCE AGGREGATION         : PASS"
    )

    print(
        "METRIC AGGREGATION           : PASS"
    )

    print(
        "TIME-WINDOW AGGREGATION      : PASS"
    )

    print()
    print(
        "PHASE 4.4 — COMPLETE: PASS"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()