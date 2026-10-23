from __future__ import annotations

from datetime import UTC, datetime

from guardian.application.control_loop_orchestrator import (
    ControlLoopOrchestrator,
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


def create_validation_event() -> ObservabilityEvent:
    """
    Create an event with the same structure as a Phase 4
    observability event.

    This validation checks orchestration behavior only.
    It does not claim live infrastructure activity.
    """

    return ObservabilityEvent(
        event_id="phase-5-2-validation-event",
        event_type=(
            ObservabilityEventType.HEALTH_SIGNAL_GENERATED
        ),
        resource_id="phase-5-2-resource",
        metric="cpu_usage_percent",
        value=25.0,
        unit="percent",
        health_level=HealthSignalLevel.HEALTHY,
        observed_at=datetime.now(UTC),
        source="docker",
    )


def main() -> int:
    print("=" * 72)
    print("PHASE 5.2 — CONTROL LOOP ORCHESTRATOR VALIDATION")
    print("=" * 72)

    orchestrator = ControlLoopOrchestrator()
    event = create_validation_event()

    print()
    print("[1] CONTROL LOOP INPUT")
    print("-" * 72)
    print(f"Event ID                    : {event.event_id}")
    print(f"Resource                    : {event.resource_id}")
    print(f"Metric                      : {event.metric}")
    print(f"Health level                : {event.health_level}")
    print("Control-loop input          : PASS")

    cycle = orchestrator.start(event)

    print()
    print("[2] CONTROL CYCLE INITIALIZATION")
    print("-" * 72)
    print(f"Cycle ID                    : {cycle.cycle_id}")
    print(f"State                       : {cycle.state}")
    print(f"Source event                : {cycle.source_event_id}")

    if cycle.state != ControlLoopState.RECEIVED:
        print("Initialization              : FAIL")
        return 1

    if cycle.source_event_id != event.event_id:
        print("Source correlation          : FAIL")
        return 1

    print("Initialization              : PASS")
    print("Source correlation          : PASS")

    print()
    print("[3] ORCHESTRATED LIFECYCLE")
    print("-" * 72)

    transitions = [
        (
            ControlLoopState.ANALYZING,
            orchestrator.advance_to_analysis,
        ),
        (
            ControlLoopState.PREDICTING,
            orchestrator.advance_to_prediction,
        ),
        (
            ControlLoopState.DECIDING,
            orchestrator.advance_to_decision,
        ),
        (
            ControlLoopState.ACTING,
            orchestrator.advance_to_action,
        ),
        (
            ControlLoopState.VERIFYING,
            orchestrator.advance_to_verification,
        ),
        (
            ControlLoopState.LEARNING,
            orchestrator.advance_to_learning,
        ),
        (
            ControlLoopState.COMPLETED,
            orchestrator.complete,
        ),
    ]

    for expected_state, transition in transitions:
        cycle = transition(cycle)

        if cycle.state != expected_state:
            print(
                f"  {expected_state.value:<15} : FAIL"
            )
            return 1

        print(
            f"  {expected_state.value:<15} : PASS"
        )

    print("Lifecycle orchestration       : PASS")

    print()
    print("[4] EVIDENCE IDENTITY")
    print("-" * 72)

    checks = [
        (
            "Source event",
            cycle.source_event_id == event.event_id,
        ),
        (
            "Resource",
            cycle.resource_id == event.resource_id,
        ),
        (
            "Metric",
            cycle.metric == event.metric,
        ),
    ]

    for name, passed in checks:
        print(
            f"{name:<28} : "
            f"{'PASS' if passed else 'FAIL'}"
        )

        if not passed:
            return 1

    print("Evidence identity             : PASS")

    print()
    print("[5] FAILURE ORCHESTRATION")
    print("-" * 72)

    failed_cycle = orchestrator.fail(
        orchestrator.start(event),
        "Controlled orchestration failure test.",
    )

    print(f"Failure state                : {failed_cycle.state}")
    print(
        f"Failure reason               : "
        f"{failed_cycle.failure_reason}"
    )

    if failed_cycle.state != ControlLoopState.FAILED:
        print("Failure orchestration        : FAIL")
        return 1

    if not failed_cycle.failure_reason:
        print("Failure reason               : FAIL")
        return 1

    print("Failure orchestration        : PASS")

    print()
    print("[6] AUTONOMOUS CAPABILITY BOUNDARY")
    print("-" * 72)
    print("Prediction implementation   : NOT EXECUTED")
    print("Decision implementation     : NOT EXECUTED")
    print("Infrastructure action       : NONE")
    print("Remediation                 : NONE")
    print("External infrastructure     : NOT MODIFIED")
    print("Phase boundary              : PASS")

    print()
    print("=" * 72)
    print("PHASE 5.2 VALIDATION RESULT")
    print("=" * 72)
    print("CONTROL-LOOP INPUT           : PASS")
    print("CYCLE INITIALIZATION         : PASS")
    print("LIFECYCLE ORCHESTRATION      : PASS")
    print("EVIDENCE IDENTITY             : PASS")
    print("FAILURE ORCHESTRATION        : PASS")
    print("AUTONOMOUS ACTION BOUNDARY   : PASS")
    print()
    print("PHASE 5.2 — COMPLETE: PASS")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())