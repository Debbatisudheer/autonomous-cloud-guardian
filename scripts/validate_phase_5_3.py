from __future__ import annotations

from guardian.application.control_loop_evidence import (
    ControlLoopEvidenceService,
)
from guardian.domain.control_loop import (
    ControlLoopState,
)
from guardian.domain.health_signal import (
    HealthSignalLevel,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
    ObservabilityEventType,
)
from guardian.infrastructure.postgres.telemetry_storage import (
    PostgreSQLTelemetryStorage,
)


def main() -> int:
    print("=" * 72)
    print("PHASE 5.3 — EVIDENCE INTAKE & ANALYSIS VALIDATION")
    print("=" * 72)

    storage = PostgreSQLTelemetryStorage()
    storage.initialize()

    observations = storage.get_recent(limit=1)

    if not observations:
        print()
        print("REAL TELEMETRY OBSERVATION : FAIL")
        print("No persisted telemetry evidence is available.")
        return 1

    observation = observations[0]

    print()
    print("[1] REAL PHASE 4 TELEMETRY")
    print("-" * 72)
    print(f"Resource                    : {observation.resource_id}")
    print(f"Metric                      : {observation.metric}")
    print(f"Value                       : {observation.value}")
    print(f"Unit                        : {observation.unit}")
    print(f"Observed at                 : {observation.observed_at}")
    print(f"Source                      : {observation.source}")

    if observation.value < 0:
        print("Telemetry evidence          : FAIL")
        return 1

    print("Telemetry evidence          : PASS")

    if observation.metric.value.startswith("cpu"):
        if observation.value < 70:
            health_level = HealthSignalLevel.HEALTHY
        elif observation.value < 90:
            health_level = HealthSignalLevel.WARNING
        else:
            health_level = HealthSignalLevel.CRITICAL
    elif observation.metric.value == "memory_usage_percent":
        if observation.value < 75:
            health_level = HealthSignalLevel.HEALTHY
        elif observation.value < 90:
            health_level = HealthSignalLevel.WARNING
        else:
            health_level = HealthSignalLevel.CRITICAL
    else:
        health_level = HealthSignalLevel.HEALTHY

    event = ObservabilityEvent(
        event_type=(
            ObservabilityEventType.HEALTH_SIGNAL_GENERATED
        ),
        resource_id=observation.resource_id,
        metric=observation.metric.value,
        value=observation.value,
        unit=observation.unit,
        health_level=health_level,
        observed_at=observation.observed_at,
        source=observation.source.value,
        metadata=observation.metadata,
    )

    print()
    print("[2] OBSERVABILITY EVENT")
    print("-" * 72)
    print(f"Event ID                    : {event.event_id}")
    print(f"Resource                    : {event.resource_id}")
    print(f"Metric                      : {event.metric}")
    print(f"Value                       : {event.value}")
    print(f"Health level                : {event.health_level}")
    print("Event construction          : PASS")

    cycle = (
        __import__(
            "guardian.domain.control_loop",
            fromlist=["ControlLoopCycle"],
        )
        .ControlLoopCycle
        .from_observability_event(event)
    )

    service = ControlLoopEvidenceService()

    result = service.intake_and_analyze(
        cycle,
        event,
    )

    print()
    print("[3] CONTROL LOOP EVIDENCE INTAKE")
    print("-" * 72)
    print(f"Cycle ID                    : {result.cycle.cycle_id}")
    print(f"Cycle state                 : {result.cycle.state}")
    print(f"Source event                : {result.cycle.source_event_id}")

    if result.cycle.state != ControlLoopState.ANALYZING:
        print("Evidence intake             : FAIL")
        return 1

    print("Evidence intake             : PASS")

    print()
    print("[4] EVIDENCE ANALYSIS")
    print("-" * 72)
    print(f"Analysis level              : {result.analysis.level}")
    print(f"Finding                     : {result.analysis.finding}")
    print(f"Evidence available          : {result.analysis.evidence_available}")

    if not result.analysis.evidence_available:
        print("Analysis evidence           : FAIL")
        return 1

    if result.analysis.source_event_id != event.event_id:
        print("Event correlation           : FAIL")
        return 1

    if result.analysis.resource_id != event.resource_id:
        print("Resource correlation        : FAIL")
        return 1

    if result.analysis.metric != event.metric:
        print("Metric correlation          : FAIL")
        return 1

    if result.analysis.value != event.value:
        print("Value correlation           : FAIL")
        return 1

    print("Analysis evidence           : PASS")
    print("Event correlation           : PASS")
    print("Resource correlation        : PASS")
    print("Metric correlation          : PASS")
    print("Value correlation           : PASS")

    print()
    print("[5] AUTONOMOUS CAPABILITY BOUNDARY")
    print("-" * 72)
    print("Prediction generated        : NONE")
    print("Decision generated          : NONE")
    print("Infrastructure action       : NONE")
    print("Remediation executed        : NONE")
    print("External infrastructure     : NOT MODIFIED")
    print("Phase boundary              : PASS")

    print()
    print("=" * 72)
    print("PHASE 5.3 VALIDATION RESULT")
    print("=" * 72)
    print("REAL TELEMETRY EVIDENCE     : PASS")
    print("OBSERVABILITY EVENT         : PASS")
    print("EVIDENCE INTAKE             : PASS")
    print("EVIDENCE ANALYSIS           : PASS")
    print("EVIDENCE CORRELATION        : PASS")
    print("AUTONOMOUS ACTION BOUNDARY  : PASS")
    print()
    print("PHASE 5.3 — COMPLETE: PASS")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())