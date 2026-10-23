from __future__ import annotations

from collections import defaultdict

from guardian.domain.telemetry import TelemetryMetric
from guardian.infrastructure.adapters.docker import (
    DockerInfrastructureAdapter,
)
from guardian.infrastructure.docker.telemetry import (
    DockerTelemetryCollector,
    DockerTelemetryError,
)


def main() -> None:
    print("=" * 72)
    print("PHASE 4.2 — REAL DOCKER TELEMETRY VALIDATION")
    print("=" * 72)

    # --------------------------------------------------------------
    # 1. REAL RESOURCE DISCOVERY
    # --------------------------------------------------------------

    adapter = DockerInfrastructureAdapter()

    resources = adapter.discover_resources()

    if not resources:
        raise RuntimeError(
            "No Docker resources were discovered."
        )

    print()
    print("[1] REAL DOCKER RESOURCES")
    print("-" * 72)

    for resource in resources:
        print(
            f"  {resource.name}: "
            f"status={resource.status.value}, "
            f"health={resource.health.value}"
        )

    # --------------------------------------------------------------
    # 2. REAL TELEMETRY COLLECTION
    # --------------------------------------------------------------

    collector = DockerTelemetryCollector()

    print()
    print("[2] REAL TELEMETRY COLLECTION")
    print("-" * 72)

    observations = collector.collect_all()

    if not observations:
        raise RuntimeError(
            "No real Docker telemetry was collected."
        )

    grouped: dict[str, list] = defaultdict(list)

    for observation in observations:
        grouped[observation.resource_id].append(
            observation
        )

    print(
        f"Telemetry observations collected: "
        f"{len(observations)}"
    )

    print(
        f"Containers with telemetry: "
        f"{len(grouped)}"
    )

    resource_names = {
        resource.id: resource.name
        for resource in resources
    }

    print()

    for resource_id, resource_observations in grouped.items():
        resource_name = resource_names.get(
            resource_id,
            resource_id,
        )

        print(f"  {resource_name}")

        for observation in resource_observations:
            print(
                f"    "
                f"{observation.metric.value}: "
                f"{observation.value:.4f} "
                f"{observation.unit}"
            )

    # --------------------------------------------------------------
    # 3. EVIDENCE VALIDATION
    # --------------------------------------------------------------

    print()
    print("[3] EVIDENCE VALIDATION")
    print("-" * 72)

    expected_metrics = {
        TelemetryMetric.CPU_USAGE_PERCENT,
        TelemetryMetric.MEMORY_USAGE_BYTES,
        TelemetryMetric.MEMORY_USAGE_PERCENT,
        TelemetryMetric.NETWORK_RX_BYTES,
        TelemetryMetric.NETWORK_TX_BYTES,
    }

    for observation in observations:
        if observation.source.value != "docker":
            raise RuntimeError(
                "Telemetry source is not Docker."
            )

        if not observation.resource_id:
            raise RuntimeError(
                "Telemetry observation has no resource ID."
            )

        if observation.value < 0:
            raise RuntimeError(
                "Telemetry observation contains a "
                "negative value."
            )

        if not observation.metadata.get(
            "container_name"
        ):
            raise RuntimeError(
                "Telemetry observation is missing "
                "container-name evidence."
            )

        if (
            observation.metadata.get("measurement")
            != "docker_stats"
        ):
            raise RuntimeError(
                "Telemetry observation does not identify "
                "docker_stats as its measurement source."
            )

    resource_metric_map: dict[
        str,
        set[TelemetryMetric],
    ] = defaultdict(set)

    for observation in observations:
        resource_metric_map[
            observation.resource_id
        ].add(observation.metric)

    for resource_id, metrics in resource_metric_map.items():
        print(
            f"  {resource_names.get(resource_id, resource_id)}: "
            f"{len(metrics)} metric types"
        )

        unexpected = metrics - expected_metrics

        if unexpected:
            raise RuntimeError(
                f"Unexpected telemetry metrics for "
                f"resource '{resource_id}': "
                f"{unexpected}"
            )

    print(
        f"Validated observations: {len(observations)}"
    )

    # --------------------------------------------------------------
    # 4. STOPPED RESOURCE EVIDENCE
    # --------------------------------------------------------------

    print()
    print("[4] STOPPED RESOURCE CHECK")
    print("-" * 72)

    stopped_resources = [
        resource
        for resource in resources
        if resource.status.value == "stopped"
    ]

    if not stopped_resources:
        print(
            "  No stopped resources were present "
            "during validation."
        )

    for resource in stopped_resources:
        telemetry_available = (
            resource.id in grouped
        )

        print(
            f"  {resource.name}: "
            f"telemetry_available="
            f"{telemetry_available}"
        )

        if telemetry_available:
            print(
                "    Docker supplied telemetry for "
                "this resource."
            )
        else:
            print(
                "    Docker supplied no runtime telemetry; "
                "no fabricated values were created."
            )

    # --------------------------------------------------------------
    # 5. FINAL RESULT
    # --------------------------------------------------------------

    print()
    print("=" * 72)
    print("PHASE 4.2 VALIDATION RESULT")
    print("=" * 72)

    print()
    print("REAL DOCKER DISCOVERY       : PASS")
    print("REAL TELEMETRY COLLECTION   : PASS")
    print("TELEMETRY SOURCE EVIDENCE   : PASS")
    print("NO FABRICATED VALUES        : PASS")

    print()
    print("PHASE 4.2 — COMPLETE: PASS")
    print("=" * 72)


if __name__ == "__main__":
    try:
        main()
    except DockerTelemetryError as exc:
        print()
        print("PHASE 4.2 — VALIDATION FAILED")
        print(f"Reason: {exc}")
        raise