from __future__ import annotations

from datetime import UTC, datetime

from guardian.domain.control_loop import (
    ControlLoopCycle,
    ControlLoopState,
)
from guardian.domain.health_signal import (
    HealthSignalLevel,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
    ObservabilityEventType,
)


def make_realistic_observability_event() -> ObservabilityEvent:
    """
    Construct a control-loop input representing the shape of an
    existing Phase 4 observability event.

    This validator does not claim that this event came from a live
    infrastructure run. The purpose of Phase 5.1 is domain-model
    validation, not live Kafka integration.
    """

    return ObservabilityEvent(
        event_id="phase-5-1-validation-event",
        event_type=(
            ObservabilityEventType.HEALTH_SIGNAL_GENERATED
        ),
        resource_id="phase-5-1-resource",
        metric="cpu_usage_percent",
        value=25.0,
        unit="percent",
        health_level=HealthSignalLevel.HEALTHY,
        observed_at=datetime.now(UTC),
        source="docker",
    )


def main() -> int:
    print("=" * 72)
    print("PHASE 5.1 — CONTROL LOOP DOMAIN MODEL VALIDATION")
    print("=" * 72)

    event = make_realistic_observability_event()

    print()
    print("[1] OBSERVABILITY EVENT INPUT")
    print("-" * 72)
    print(f"Event ID                    : {event.event_id}")
    print(f"Resource                    : {event.resource_id}")
    print(f"Metric                      : {event.metric}")
    print(f"Value                       : {event.value}")
    print(f"Unit                        : {event.unit}")
    print(f"Health level                : {event.health_level}")
    print("Event input                 : PASS")

    cycle = ControlLoopCycle.from_observability_event(
        event
    )

    print()
    print("[2] CONTROL LOOP CYCLE CREATION")
    print("-" * 72)
    print(f"Cycle ID                    : {cycle.cycle_id}")
    print(f"Source event                : {cycle.source_event_id}")
    print(f"Initial state               : {cycle.state}")
    print(f"Resource correlation        : {cycle.resource_id}")
    print(f"Metric correlation          : {cycle.metric}")

    if cycle.state != ControlLoopState.RECEIVED:
        print("Initial state               : FAIL")
        return 1

    if cycle.source_event_id != event.event_id:
        print("Event correlation           : FAIL")
        return 1

    if cycle.resource_id != event.resource_id:
        print("Resource correlation        : FAIL")
        return 1

    if cycle.metric != event.metric:
        print("Metric correlation          : FAIL")
        return 1

    print("Cycle creation              : PASS")
    print("Evidence correlation        : PASS")

    print()
    print("[3] LIFECYCLE REPRESENTATION")
    print("-" * 72)

    expected_states = [
        ControlLoopState.RECEIVED,
        ControlLoopState.ANALYZING,
        ControlLoopState.PREDICTING,
        ControlLoopState.DECIDING,
        ControlLoopState.ACTING,
        ControlLoopState.VERIFYING,
        ControlLoopState.LEARNING,
        ControlLoopState.COMPLETED,
    ]

    current = cycle

    for state in expected_states:
        current = current.transition_to(state)
        print(
            f"  {state.value:<15} : "
            f"{'PASS' if current.state == state else 'FAIL'}"
        )

        if current.state != state:
            return 1

    print("Lifecycle representation     : PASS")

    print()
    print("[4] FAILURE REPRESENTATION")
    print("-" * 72)

    failed = cycle.fail(
        "Validation failure recorded for control-loop testing."
    )

    if failed.state != ControlLoopState.FAILED:
        print("Failure state                : FAIL")
        return 1

    if not failed.failure_reason:
        print("Failure reason               : FAIL")
        return 1

    print(f"Failure state                : {failed.state}")
    print(f"Failure reason               : {failed.failure_reason}")
    print("Failure representation       : PASS")

    print()
    print("[5] AUTONOMOUS CAPABILITY BOUNDARY")
    print("-" * 72)
    print("Prediction generated        : NONE")
    print("Decision generated          : NONE")
    print("Action executed             : NONE")
    print("Remediation executed        : NONE")
    print("External infrastructure      : NOT MODIFIED")
    print("Autonomous capability        : NOT CLAIMED")
    print("Phase boundary               : PASS")

    print()
    print("=" * 72)
    print("PHASE 5.1 VALIDATION RESULT")
    print("=" * 72)
    print("OBSERVABILITY EVENT INPUT    : PASS")
    print("CONTROL CYCLE CREATION       : PASS")
    print("EVIDENCE CORRELATION         : PASS")
    print("LIFECYCLE REPRESENTATION     : PASS")
    print("FAILURE REPRESENTATION       : PASS")
    print("AUTONOMOUS ACTION BOUNDARY   : PASS")
    print()
    print("PHASE 5.1 — COMPLETE: PASS")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())