from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from guardian.application.telemetry_query import (
    TelemetryQueryService,
)
from guardian.domain.telemetry import (
    TelemetryMetric,
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
        "PHASE 4.5 — REAL TELEMETRY QUERY & RETRIEVAL VALIDATION"
    )

    # ==================================================================
    # 1. Initialize storage
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
                "Telemetry source is not Docker."
            )

        if observation.value < 0:
            raise RuntimeError(
                "Telemetry contains a negative value."
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
    # 4. Create query service
    # ==================================================================

    print()
    print("[4] TELEMETRY QUERY SERVICE")
    print("-" * 72)

    query_service = TelemetryQueryService(
        storage=storage,
    )

    print("Query service               : PASS")

    # ==================================================================
    # 5. Recent query
    # ==================================================================

    print()
    print("[5] RECENT TELEMETRY QUERY")
    print("-" * 72)

    recent = query_service.get_recent(
        limit=len(observations),
    )

    if len(recent) < len(observations):
        raise RuntimeError(
            "Recent query did not return all "
            "newly persisted observations."
        )

    recent_resources = {
        observation.resource_id
        for observation in recent
    }

    if not resource_ids.issubset(
        recent_resources
    ):
        raise RuntimeError(
            "Recent query is missing telemetry resources."
        )

    print(
        "Records returned            : "
        f"{len(recent)}"
    )

    print(
        "Resources returned          : "
        f"{len(recent_resources)}"
    )

    print("Recent query                : PASS")

    # ==================================================================
    # 6. Resource query
    # ==================================================================

    print()
    print("[6] RESOURCE TELEMETRY QUERY")
    print("-" * 72)

    first_resource = min(resource_ids)

    resource_records = (
        query_service.get_for_resource(
            resource_id=first_resource,
            limit=100,
        )
    )

    if not resource_records:
        raise RuntimeError(
            "Resource query returned no telemetry."
        )

    if not all(
        observation.resource_id == first_resource
        for observation in resource_records
    ):
        raise RuntimeError(
            "Resource query returned telemetry "
            "from another resource."
        )

    print(
        "Resource queried            : "
        f"{first_resource}"
    )

    print(
        "Records returned            : "
        f"{len(resource_records)}"
    )

    print("Resource query              : PASS")

    # ==================================================================
    # 7. Resource + metric query
    # ==================================================================

    print()
    print("[7] RESOURCE + METRIC QUERY")
    print("-" * 72)

    target_observation = next(
        observation
        for observation in observations
        if observation.resource_id == first_resource
    )

    metric_records = (
        query_service.get_for_resource_and_metric(
            resource_id=first_resource,
            metric=target_observation.metric,
            limit=100,
        )
    )

    if not metric_records:
        raise RuntimeError(
            "Resource + metric query returned no telemetry."
        )

    if not all(
        observation.resource_id == first_resource
        and observation.metric == target_observation.metric
        for observation in metric_records
    ):
        raise RuntimeError(
            "Resource + metric query returned "
            "incorrect telemetry."
        )

    print(
        "Resource queried            : "
        f"{first_resource}"
    )

    print(
        "Metric queried              : "
        f"{target_observation.metric.value}"
    )

    print(
        "Records returned            : "
        f"{len(metric_records)}"
    )

    print("Resource + metric query     : PASS")

    # ==================================================================
    # 8. Time-range query
    # ==================================================================

    print()
    print("[8] TIME-RANGE QUERY")
    print("-" * 72)

    timestamps = [
        observation.observed_at
        for observation in observations
    ]

    earliest = min(timestamps)
    latest = max(timestamps)

    start = earliest - timedelta(
        minutes=1,
    )

    end = latest + timedelta(
        minutes=1,
    )

    time_records = query_service.get_between(
        start=start,
        end=end,
        limit=10000,
    )

    if len(time_records) < len(observations):
        raise RuntimeError(
            "Time-range query did not return "
            "all expected telemetry."
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
        "Records returned            : "
        f"{len(time_records)}"
    )

    print("Time-range query            : PASS")

    # ==================================================================
    # 9. Metric query across resources
    # ==================================================================

    print()
    print("[9] METRIC QUERY ACROSS RESOURCES")
    print("-" * 72)

    cpu_records = [
        observation
        for observation in observations
        if observation.metric
        == TelemetryMetric.CPU_USAGE_PERCENT
    ]

    if not cpu_records:
        raise RuntimeError(
            "No CPU telemetry exists in the "
            "real collection."
        )

    cpu_resource = cpu_records[0].resource_id

    cpu_query_records = (
        query_service.get_for_resource_and_metric(
            resource_id=cpu_resource,
            metric=TelemetryMetric.CPU_USAGE_PERCENT,
            limit=100,
        )
    )

    if not cpu_query_records:
        raise RuntimeError(
            "CPU metric query returned no telemetry."
        )

    if not all(
        observation.metric
        == TelemetryMetric.CPU_USAGE_PERCENT
        for observation in cpu_query_records
    ):
        raise RuntimeError(
            "CPU metric query returned another metric."
        )

    print(
        "Metric queried              : "
        "cpu_usage_percent"
    )

    print(
        "Resource queried            : "
        f"{cpu_resource}"
    )

    print(
        "Records returned            : "
        f"{len(cpu_query_records)}"
    )

    print("Metric query                : PASS")

    # ==================================================================
    # 10. Query evidence integrity
    # ==================================================================

    print()
    print("[10] QUERY EVIDENCE INTEGRITY")
    print("-" * 72)

    original_pairs = {
        (
            observation.resource_id,
            observation.metric.value,
            observation.value,
            observation.observed_at,
        )
        for observation in observations
    }

    queried_pairs = {
        (
            observation.resource_id,
            observation.metric.value,
            observation.value,
            observation.observed_at,
        )
        for observation in time_records
    }

    if not original_pairs.issubset(
        queried_pairs
    ):
        raise RuntimeError(
            "Query results do not preserve "
            "the collected telemetry evidence."
        )

    for observation in time_records:
        if observation.source.value != "docker":
            raise RuntimeError(
                "Query returned telemetry with "
                "an unexpected source."
            )

    print(
        "Original observations      : "
        f"{len(original_pairs)}"
    )

    print(
        "Matching queried records   : PASS"
    )

    print("Source integrity            : PASS")

    # ==================================================================
    # Final result
    # ==================================================================

    print()
    print("=" * 72)
    print("PHASE 4.5 VALIDATION RESULT")
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
        "QUERY SERVICE                : PASS"
    )

    print(
        "RECENT QUERY                 : PASS"
    )

    print(
        "RESOURCE QUERY               : PASS"
    )

    print(
        "RESOURCE + METRIC QUERY      : PASS"
    )

    print(
        "TIME-RANGE QUERY             : PASS"
    )

    print(
        "METRIC QUERY                 : PASS"
    )

    print(
        "QUERY EVIDENCE INTEGRITY     : PASS"
    )

    print()
    print(
        "PHASE 4.5 — COMPLETE: PASS"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()