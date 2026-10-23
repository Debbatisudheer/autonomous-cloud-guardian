from datetime import UTC, datetime

import pytest

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


def make_event() -> ObservabilityEvent:
    return ObservabilityEvent(
        event_id="orchestrator-event-001",
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


@pytest.fixture
def orchestrator() -> ControlLoopOrchestrator:
    return ControlLoopOrchestrator()


@pytest.fixture
def cycle(
    orchestrator: ControlLoopOrchestrator,
):
    return orchestrator.start(make_event())


def test_start_creates_received_cycle(
    orchestrator: ControlLoopOrchestrator,
) -> None:
    cycle = orchestrator.start(make_event())

    assert cycle.state == ControlLoopState.RECEIVED
    assert (
        cycle.source_event_id
        == "orchestrator-event-001"
    )


def test_advance_to_analysis(
    orchestrator: ControlLoopOrchestrator,
    cycle,
) -> None:
    result = orchestrator.advance_to_analysis(cycle)

    assert result.state == ControlLoopState.ANALYZING
    assert result.cycle_id == cycle.cycle_id


def test_advance_to_prediction(
    orchestrator: ControlLoopOrchestrator,
    cycle,
) -> None:
    result = orchestrator.advance_to_prediction(cycle)

    assert result.state == ControlLoopState.PREDICTING
    assert result.cycle_id == cycle.cycle_id


def test_advance_to_decision(
    orchestrator: ControlLoopOrchestrator,
    cycle,
) -> None:
    result = orchestrator.advance_to_decision(cycle)

    assert result.state == ControlLoopState.DECIDING
    assert result.cycle_id == cycle.cycle_id


def test_advance_to_action(
    orchestrator: ControlLoopOrchestrator,
    cycle,
) -> None:
    result = orchestrator.advance_to_action(cycle)

    assert result.state == ControlLoopState.ACTING
    assert result.cycle_id == cycle.cycle_id


def test_advance_to_verification(
    orchestrator: ControlLoopOrchestrator,
    cycle,
) -> None:
    result = orchestrator.advance_to_verification(
        cycle
    )

    assert result.state == ControlLoopState.VERIFYING
    assert result.cycle_id == cycle.cycle_id


def test_advance_to_learning(
    orchestrator: ControlLoopOrchestrator,
    cycle,
) -> None:
    result = orchestrator.advance_to_learning(cycle)

    assert result.state == ControlLoopState.LEARNING
    assert result.cycle_id == cycle.cycle_id


def test_complete_cycle(
    orchestrator: ControlLoopOrchestrator,
    cycle,
) -> None:
    result = orchestrator.complete(cycle)

    assert result.state == ControlLoopState.COMPLETED
    assert result.cycle_id == cycle.cycle_id


def test_fail_cycle(
    orchestrator: ControlLoopOrchestrator,
    cycle,
) -> None:
    result = orchestrator.fail(
        cycle,
        "Control-loop dependency unavailable.",
    )

    assert result.state == ControlLoopState.FAILED
    assert (
        result.failure_reason
        == "Control-loop dependency unavailable."
    )


def test_full_lifecycle_can_be_orchestrated(
    orchestrator: ControlLoopOrchestrator,
) -> None:
    cycle = orchestrator.start(make_event())

    cycle = orchestrator.advance_to_analysis(cycle)
    cycle = orchestrator.advance_to_prediction(cycle)
    cycle = orchestrator.advance_to_decision(cycle)
    cycle = orchestrator.advance_to_action(cycle)
    cycle = orchestrator.advance_to_verification(cycle)
    cycle = orchestrator.advance_to_learning(cycle)
    cycle = orchestrator.complete(cycle)

    assert cycle.state == ControlLoopState.COMPLETED


def test_orchestration_preserves_evidence_identity(
    orchestrator: ControlLoopOrchestrator,
) -> None:
    event = make_event()

    cycle = orchestrator.start(event)
    cycle = orchestrator.advance_to_analysis(cycle)
    cycle = orchestrator.advance_to_prediction(cycle)
    cycle = orchestrator.advance_to_decision(cycle)

    assert cycle.source_event_id == event.event_id
    assert cycle.resource_id == event.resource_id
    assert cycle.metric == event.metric


def test_orchestration_does_not_modify_original_cycle(
    orchestrator: ControlLoopOrchestrator,
) -> None:
    original = orchestrator.start(make_event())

    advanced = orchestrator.advance_to_analysis(
        original
    )

    assert original.state == ControlLoopState.RECEIVED
    assert advanced.state == ControlLoopState.ANALYZING
    assert original.cycle_id == advanced.cycle_id