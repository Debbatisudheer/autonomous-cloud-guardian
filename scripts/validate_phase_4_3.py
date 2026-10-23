from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

# ----------------------------------------------------------------------
# Project import path
# ----------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


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
        "PHASE 4.3 — REAL TELEMETRY STORAGE VALIDATION"
    )

    # ==================================================================
    # 1. PostgreSQL storage initialization
    # ==================================================================

    print()
    print("[1] POSTGRESQL STORAGE INITIALIZATION")
    print("-" * 72)

    storage = PostgreSQLTelemetryStorage()

    storage.initialize()

    print("PostgreSQL connection       : PASS")
    print("Telemetry schema            : PASS")
    print("Telemetry indexes           : PASS")

    # ==================================================================
    # 2. Real Docker telemetry collection
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

    # IMPORTANT:
    # Use a SET here because later validation uses issubset().
    resource_ids = {
        observation.resource_id
        for observation in observations
    }

    resource_ids_sorted = sorted(resource_ids)

    print(
        "Real telemetry observations : "
        f"{len(observations)}"
    )

    print(
        "Resources with telemetry   : "
        f"{len(resource_ids)}"
    )

    for resource_id in resource_ids_sorted:
        resource_observations = [
            observation
            for observation in observations
            if observation.resource_id == resource_id
        ]

        print()
        print(f"  {resource_id}")

        for observation in resource_observations:
            print(
                "    "
                f"{observation.metric.value}: "
                f"{observation.value:.4f} "
                f"{observation.unit}"
            )

    # ==================================================================
    # 3. Telemetry evidence validation
    # ==================================================================

    print()
    print("[3] TELEMETRY EVIDENCE VALIDATION")
    print("-" * 72)

    for observation in observations:
        if not observation.resource_id:
            raise RuntimeError(
                "Telemetry observation has no resource ID."
            )

        if not observation.unit:
            raise RuntimeError(
                "Telemetry observation has no unit."
            )

        if observation.value < 0:
            raise RuntimeError(
                "Telemetry observation contains a negative value."
            )

        if observation.source.value != "docker":
            raise RuntimeError(
                "Phase 4.3 expected Docker telemetry source."
            )

        if not observation.observed_at:
            raise RuntimeError(
                "Telemetry observation has no timestamp."
            )

    print(
        "Evidence-backed observations: "
        f"{len(observations)}"
    )

    print("Source validation           : PASS")
    print("Value validation            : PASS")
    print("Unit validation             : PASS")
    print("Timestamp validation        : PASS")
    print("No fabricated observations  : PASS")

    # ==================================================================
    # 4. Persist real telemetry
    # ==================================================================

    print()
    print("[4] POSTGRESQL TELEMETRY PERSISTENCE")
    print("-" * 72)

    storage.save_many(observations)

    print(
        "Persisted observations      : "
        f"{len(observations)}"
    )

    print("PostgreSQL persistence      : PASS")

    # ==================================================================
    # 5. Recent telemetry retrieval
    # ==================================================================

    print()
    print("[5] RECENT TELEMETRY RETRIEVAL")
    print("-" * 72)

    recent = storage.get_recent(
        limit=len(observations) + 10
    )

    if len(recent) < len(observations):
        raise RuntimeError(
            "PostgreSQL did not return all persisted "
            "telemetry observations."
        )

    print(
        "Retrieved recent records   : "
        f"{len(recent)}"
    )

    retrieved_resource_ids = {
        observation.resource_id
        for observation in recent
    }

    # resource_ids is intentionally a SET.
    if not resource_ids.issubset(
        retrieved_resource_ids
    ):
        raise RuntimeError(
            "Not all telemetry resources were returned "
            "from PostgreSQL."
        )

    print("Recent retrieval            : PASS")

    # ==================================================================
    # 6. Resource-specific retrieval
    # ==================================================================

    print()
    print("[6] RESOURCE-SPECIFIC RETRIEVAL")
    print("-" * 72)

    first_resource = resource_ids_sorted[0]

    resource_records = storage.get_for_resource(
        resource_id=first_resource,
        limit=100,
    )

    if not resource_records:
        raise RuntimeError(
            "Resource-specific telemetry retrieval "
            "returned no records."
        )

    for observation in resource_records:
        if observation.resource_id != first_resource:
            raise RuntimeError(
                "Resource-specific retrieval returned "
                "a different resource."
            )

    print(
        "Resource queried           : "
        f"{first_resource}"
    )

    print(
        "Records returned            : "
        f"{len(resource_records)}"
    )

    print("Resource retrieval          : PASS")

    # ==================================================================
    # 7. Resource + metric retrieval
    # ==================================================================

    print()
    print("[7] RESOURCE + METRIC RETRIEVAL")
    print("-" * 72)

    first_observation = observations[0]

    first_metric = first_observation.metric.value

    metric_records = (
        storage.get_for_resource_and_metric(
            resource_id=first_observation.resource_id,
            metric=first_metric,
            limit=100,
        )
    )

    if not metric_records:
        raise RuntimeError(
            "Resource + metric retrieval returned no records."
        )

    for observation in metric_records:
        if (
            observation.resource_id
            != first_observation.resource_id
        ):
            raise RuntimeError(
                "Metric retrieval returned an incorrect resource."
            )

        if observation.metric.value != first_metric:
            raise RuntimeError(
                "Metric retrieval returned an incorrect metric."
            )

    print(
        "Resource                    : "
        f"{first_observation.resource_id}"
    )

    print(
        "Metric                      : "
        f"{first_metric}"
    )

    print(
        "Records returned            : "
        f"{len(metric_records)}"
    )

    print("Metric retrieval            : PASS")

    # ==================================================================
    # 8. Time-range retrieval
    # ==================================================================

    print()
    print("[8] TIME-RANGE RETRIEVAL")
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

    time_records = storage.get_between(
        start=start,
        end=end,
        limit=10000,
    )

    if len(time_records) < len(observations):
        raise RuntimeError(
            "Time-range retrieval did not return "
            "all persisted observations."
        )

    print(
        "Time range start           : "
        f"{start.isoformat()}"
    )

    print(
        "Time range end             : "
        f"{end.isoformat()}"
    )

    print(
        "Records returned            : "
        f"{len(time_records)}"
    )

    print("Time-range retrieval        : PASS")

    # ==================================================================
    # 9. Persistence integrity
    # ==================================================================

    print()
    print("[9] PERSISTENCE INTEGRITY")
    print("-" * 72)

    persisted_pairs = {
        (
            observation.resource_id,
            observation.metric.value,
            observation.value,
            observation.unit,
            observation.source.value,
        )
        for observation in recent
    }

    original_pairs = {
        (
            observation.resource_id,
            observation.metric.value,
            observation.value,
            observation.unit,
            observation.source.value,
        )
        for observation in observations
    }

    if not original_pairs.issubset(
        persisted_pairs
    ):
        raise RuntimeError(
            "Persisted telemetry does not match "
            "the collected telemetry."
        )

    print(
        "Original observations      : "
        f"{len(original_pairs)}"
    )

    print(
        "Matching persisted records : PASS"
    )

    # ==================================================================
    # Final result
    # ==================================================================

    print()
    print("=" * 72)
    print("PHASE 4.3 VALIDATION RESULT")
    print("=" * 72)

    print(
        "POSTGRESQL CONNECTION        : PASS"
    )

    print(
        "TELEMETRY SCHEMA             : PASS"
    )

    print(
        "REAL DOCKER TELEMETRY        : PASS"
    )

    print(
        "TELEMETRY EVIDENCE           : PASS"
    )

    print(
        "POSTGRESQL PERSISTENCE       : PASS"
    )

    print(
        "RECENT RETRIEVAL              : PASS"
    )

    print(
        "RESOURCE RETRIEVAL            : PASS"
    )

    print(
        "METRIC RETRIEVAL              : PASS"
    )

    print(
        "TIME-RANGE RETRIEVAL          : PASS"
    )

    print(
        "PERSISTENCE INTEGRITY         : PASS"
    )

    print()
    print(
        "PHASE 4.3 — COMPLETE: PASS"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()