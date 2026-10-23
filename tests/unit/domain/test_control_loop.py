from datetime import UTC, datetime

import pytest

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


def make_event() -> ObservabilityEvent:
    return ObservabilityEvent(
        event_id="event-001",
        event_type=(
            ObservabilityEventType.HEALTH_SIGNAL_GENERATED
        ),
        resource_id="resource-001",
        metric="cpu_usage_percent",
        value=25.0,
        unit="percent",
        health_level=HealthSignalLevel.HEALTHY,
        observed_at=datetime.now(UTC),
        source="docker",
    )


def test_cycle_starts_in_received_state() -> None:
    event = make_event()

    cycle = ControlLoopCycle.from_observability_event(
        event
    )

    assert cycle.state == ControlLoopState.RECEIVED
    assert cycle.source_event_id == event.event_id
    assert cycle.resource_id == event.resource_id
    assert cycle.metric == event.metric
    assert cycle.cycle_id


def test_cycle_has_unique_identity() -> None:
    event = make_event()

    first = ControlLoopCycle.from_observability_event(
        event
    )
    second = ControlLoopCycle.from_observability_event(
        event
    )

    assert first.cycle_id != second.cycle_id


def test_cycle_transition_changes_only_lifecycle_state() -> None:
    event = make_event()

    cycle = ControlLoopCycle.from_observability_event(
        event
    )

    analyzing = cycle.transition_to(
        ControlLoopState.ANALYZING
    )

    assert analyzing.cycle_id == cycle.cycle_id
    assert analyzing.source_event_id == cycle.source_event_id
    assert analyzing.resource_id == cycle.resource_id
    assert analyzing.metric == cycle.metric
    assert analyzing.state == ControlLoopState.ANALYZING


@pytest.mark.parametrize(
    "state",
    [
        ControlLoopState.ANALYZING,
        ControlLoopState.PREDICTING,
        ControlLoopState.DECIDING,
        ControlLoopState.ACTING,
        ControlLoopState.VERIFYING,
        ControlLoopState.LEARNING,
        ControlLoopState.COMPLETED,
    ],
)
def test_all_control_loop_states_are_representable(
    state: ControlLoopState,
) -> None:
    event = make_event()

    cycle = ControlLoopCycle.from_observability_event(
        event
    )

    transitioned = cycle.transition_to(state)

    assert transitioned.state == state


def test_failure_requires_reason() -> None:
    event = make_event()

    cycle = ControlLoopCycle.from_observability_event(
        event
    )

    with pytest.raises(ValueError, match="Failure reason"):
        cycle.fail("   ")


def test_failure_records_explicit_reason() -> None:
    event = make_event()

    cycle = ControlLoopCycle.from_observability_event(
        event
    )

    failed = cycle.fail(
        "Required control-loop input was unavailable."
    )

    assert failed.state == ControlLoopState.FAILED
    assert (
        failed.failure_reason
        == "Required control-loop input was unavailable."
    )


def test_cycle_does_not_change_source_event_identity() -> None:
    event = make_event()

    cycle = ControlLoopCycle.from_observability_event(
        event
    )

    completed = cycle.transition_to(
        ControlLoopState.COMPLETED
    )

    assert completed.source_event_id == "event-001"
    assert completed.resource_id == "resource-001"
    assert completed.metric == "cpu_usage_percent"