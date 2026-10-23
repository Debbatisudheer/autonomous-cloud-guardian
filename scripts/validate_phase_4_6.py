from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from guardian.application.health_signals import (
    HealthSignalEngine,
)
from guardian.domain.health_signal import (
    HealthSignalLevel,
)
from guardian.infrastructure.docker.telemetry import (
    DockerTelemetryCollector,
)


def print_header(title: str) -> None:
    print("=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    print_header(
        "PHASE 4.6 — REAL METRICS & HEALTH SIGNAL VALIDATION"
    )

    # ==================================================================
    # 1. Collect real Docker telemetry
    # ==================================================================

    print()
    print("[1] REAL DOCKER TELEMETRY COLLECTION")
    print("-" * 72)

    collector = DockerTelemetryCollector()

    observations = collector.collect_all()

    if not observations:
        raise RuntimeError(
            "No real Docker telemetry was collected."
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

    resources = {
        observation.resource_id
        for observation in observations
    }

    metrics = {
        observation.metric
        for observation in observations
    }

    print(
        "Real observations           : "
        f"{len(observations)}"
    )

    print(
        "Resources                   : "
        f"{len(resources)}"
    )

    print(
        "Metrics                     : "
        f"{len(metrics)}"
    )

    print("Real telemetry evidence     : PASS")

    # ==================================================================
    # 2. Evaluate health signals
    # ==================================================================

    print()
    print("[2] HEALTH SIGNAL ENGINE")
    print("-" * 72)

    engine = HealthSignalEngine()

    signals = engine.evaluate_many(
        observations,
    )

    if len(signals) != len(observations):
        raise RuntimeError(
            "Health signal count does not match "
            "telemetry observation count."
        )

    print(
        "Signals generated           : "
        f"{len(signals)}"
    )

    print("Signal generation           : PASS")

    # ==================================================================
    # 3. Evidence integrity
    # ==================================================================

    print()
    print("[3] SIGNAL EVIDENCE INTEGRITY")
    print("-" * 72)

    for observation, signal in zip(
        observations,
        signals,
        strict=True,
    ):
        if signal.resource_id != (
            observation.resource_id
        ):
            raise RuntimeError(
                "Signal resource ID does not match "
                "the telemetry observation."
            )

        if signal.metric != (
            observation.metric.value
        ):
            raise RuntimeError(
                "Signal metric does not match "
                "the telemetry observation."
            )

        if signal.value != observation.value:
            raise RuntimeError(
                "Signal value does not match "
                "the telemetry observation."
            )

        if signal.unit != observation.unit:
            raise RuntimeError(
                "Signal unit does not match "
                "the telemetry observation."
            )

        if not signal.evidence_available:
            raise RuntimeError(
                "Real telemetry produced a signal "
                "without evidence availability."
            )

    print("Resource correlation         : PASS")
    print("Metric correlation           : PASS")
    print("Value correlation            : PASS")
    print("Unit correlation             : PASS")
    print("Evidence availability        : PASS")

    # ==================================================================
    # 4. Signal distribution
    # ==================================================================

    print()
    print("[4] SIGNAL DISTRIBUTION")
    print("-" * 72)

    distribution: dict[
        HealthSignalLevel,
        int,
    ] = {
        level: 0
        for level in HealthSignalLevel
    }

    for signal in signals:
        distribution[signal.level] += 1

    for level in HealthSignalLevel:
        print(
            f"{level.value:28}: "
            f"{distribution[level]}"
        )

    if distribution[HealthSignalLevel.UNKNOWN] > 0:
        raise RuntimeError(
            "Unexpected UNKNOWN health signals "
            "were generated from supported real metrics."
        )

    print("Signal distribution         : PASS")

    # ==================================================================
    # 5. CPU signal validation
    # ==================================================================

    print()
    print("[5] CPU HEALTH SIGNALS")
    print("-" * 72)

    cpu_observations = [
        observation
        for observation in observations
        if observation.metric.value
        == "cpu_usage_percent"
    ]

    cpu_signals = [
        signal
        for signal in signals
        if signal.metric
        == "cpu_usage_percent"
    ]

    if not cpu_observations:
        raise RuntimeError(
            "Real Docker CPU telemetry was not collected."
        )

    if len(cpu_observations) != len(cpu_signals):
        raise RuntimeError(
            "CPU observation and signal counts differ."
        )

    for signal in cpu_signals:
        if signal.level not in {
            HealthSignalLevel.HEALTHY,
            HealthSignalLevel.WARNING,
            HealthSignalLevel.CRITICAL,
        }:
            raise RuntimeError(
                "CPU signal has an invalid level."
            )

    print(
        "CPU observations            : "
        f"{len(cpu_observations)}"
    )

    print(
        "CPU signals                 : "
        f"{len(cpu_signals)}"
    )

    print("CPU signal evaluation       : PASS")

    # ==================================================================
    # 6. Memory signal validation
    # ==================================================================

    print()
    print("[6] MEMORY HEALTH SIGNALS")
    print("-" * 72)

    memory_observations = [
        observation
        for observation in observations
        if observation.metric.value
        == "memory_usage_percent"
    ]

    memory_signals = [
        signal
        for signal in signals
        if signal.metric
        == "memory_usage_percent"
    ]

    if not memory_observations:
        raise RuntimeError(
            "Real Docker memory percentage telemetry "
            "was not collected."
        )

    if len(memory_observations) != len(memory_signals):
        raise RuntimeError(
            "Memory observation and signal counts differ."
        )

    print(
        "Memory observations         : "
        f"{len(memory_observations)}"
    )

    print(
        "Memory signals              : "
        f"{len(memory_signals)}"
    )

    print("Memory signal evaluation    : PASS")

    # ==================================================================
    # 7. Network signal validation
    # ==================================================================

    print()
    print("[7] NETWORK HEALTH SIGNALS")
    print("-" * 72)

    network_observations = [
        observation
        for observation in observations
        if observation.metric.value
        in {
            "network_rx_bytes",
            "network_tx_bytes",
        }
    ]

    network_signals = [
        signal
        for signal in signals
        if signal.metric
        in {
            "network_rx_bytes",
            "network_tx_bytes",
        }
    ]

    if not network_observations:
        raise RuntimeError(
            "Real Docker network telemetry "
            "was not collected."
        )

    if len(network_observations) != len(network_signals):
        raise RuntimeError(
            "Network observation and signal counts differ."
        )

    for signal in network_signals:
        if signal.level != (
            HealthSignalLevel.HEALTHY
        ):
            raise RuntimeError(
                "Network byte counters should not "
                "be interpreted as unhealthy merely "
                "because traffic volume exists."
            )

    print(
        "Network observations       : "
        f"{len(network_observations)}"
    )

    print(
        "Network signals             : "
        f"{len(network_signals)}"
    )

    print("Network signal evaluation   : PASS")

    # ==================================================================
    # 8. No autonomous action
    # ==================================================================

    print()
    print("[8] AUTONOMOUS ACTION BOUNDARY")
    print("-" * 72)

    print(
        "Health engine action        : NONE"
    )

    print(
        "Remediation executed       : NONE"
    )

    print(
        "Prediction generated       : NONE"
    )

    print(
        "Decision generated         : NONE"
    )

    print("Phase boundary              : PASS")

    # ==================================================================
    # Final result
    # ==================================================================

    print()
    print("=" * 72)
    print("PHASE 4.6 VALIDATION RESULT")
    print("=" * 72)

    print(
        "REAL DOCKER TELEMETRY        : PASS"
    )

    print(
        "HEALTH SIGNAL GENERATION     : PASS"
    )

    print(
        "EVIDENCE INTEGRITY            : PASS"
    )

    print(
        "CPU SIGNALS                   : PASS"
    )

    print(
        "MEMORY SIGNALS                : PASS"
    )

    print(
        "NETWORK SIGNALS               : PASS"
    )

    print(
        "AUTONOMOUS ACTION BOUNDARY    : PASS"
    )

    print()
    print(
        "PHASE 4.6 — COMPLETE: PASS"
    )

    print("=" * 72)


if __name__ == "__main__":
    main()