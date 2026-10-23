from datetime import UTC, datetime

import pytest

from guardian.application.control_loop_evidence import (
    ControlLoopEvidenceService,
)
from guardian.domain.control_loop import (
    ControlLoopCycle,
    ControlLoopState,
)
from guardian.domain.evidence_analysis import (
    EvidenceAnalysisLevel,
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
        event_id="evidence-event-001",
        event_type=(
            ObservabilityEventType.HEALTH_SIGNAL_GENERATED
        ),
        resource_id="resource-001",
        metric="cpu_usage_percent",
        value=82.0,
        unit="percent",
        health_level=HealthSignalLevel.WARNING,
        observed_at=datetime.now(UTC),
        source="docker",
    )


def make_cycle(
    event: ObservabilityEvent,
) -> ControlLoopCycle:
    return ControlLoopCycle.from_observability_event(
        event
    )


def test_intake_and_analysis_moves_cycle_to_analyzing() -> None:
    event = make_event()
    cycle = make_cycle(event)

    service = ControlLoopEvidenceService()

    result = service.intake_and_analyze(
        cycle,
        event,
    )

    assert result.cycle.state == ControlLoopState.ANALYZING


def test_analysis_is_evidence_linked() -> None:
    event = make_event()
    cycle = make_cycle(event)

    service = ControlLoopEvidenceService()

    result = service.intake_and_analyze(
        cycle,
        event,
    )

    assert (
        result.analysis.source_event_id
        == event.event_id
    )
    assert (
        result.analysis.resource_id
        == event.resource_id
    )
    assert result.analysis.metric == event.metric


def test_warning_evidence_is_analyzed() -> None:
    event = make_event()
    cycle = make_cycle(event)

    service = ControlLoopEvidenceService()

    result = service.intake_and_analyze(
        cycle,
        event,
    )

    assert (
        result.analysis.level
        == EvidenceAnalysisLevel.WARNING
    )


def test_mismatched_event_id_is_rejected() -> None:
    event = make_event()

    cycle = make_cycle(event)

    mismatched_event = event.model_copy(
        update={
            "event_id": "different-event",
        }
    )

    service = ControlLoopEvidenceService()

    with pytest.raises(
        ValueError,
        match="source event",
    ):
        service.intake_and_analyze(
            cycle,
            mismatched_event,
        )


def test_mismatched_resource_is_rejected() -> None:
    event = make_event()
    cycle = make_cycle(event)

    mismatched_event = event.model_copy(
        update={
            "resource_id": "different-resource",
        }
    )

    service = ControlLoopEvidenceService()

    with pytest.raises(
        ValueError,
        match="resource",
    ):
        service.intake_and_analyze(
            cycle,
            mismatched_event,
        )


def test_mismatched_metric_is_rejected() -> None:
    event = make_event()
    cycle = make_cycle(event)

    mismatched_event = event.model_copy(
        update={
            "metric": "memory_usage_bytes",
        }
    )

    service = ControlLoopEvidenceService()

    with pytest.raises(
        ValueError,
        match="metric",
    ):
        service.intake_and_analyze(
            cycle,
            mismatched_event,
        )


def test_cycle_must_start_in_received_state() -> None:
    event = make_event()

    cycle = make_cycle(event).transition_to(
        ControlLoopState.ANALYZING
    )

    service = ControlLoopEvidenceService()

    with pytest.raises(
        ValueError,
        match="RECEIVED",
    ):
        service.intake_and_analyze(
            cycle,
            event,
        )


def test_original_cycle_is_not_modified() -> None:
    event = make_event()
    cycle = make_cycle(event)

    service = ControlLoopEvidenceService()

    result = service.intake_and_analyze(
        cycle,
        event,
    )

    assert cycle.state == ControlLoopState.RECEIVED
    assert result.cycle.state == ControlLoopState.ANALYZING