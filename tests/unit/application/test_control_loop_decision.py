import pytest

from guardian.application.control_loop_decision import (
    ControlLoopDecisionService,
)
from guardian.domain.control_loop import (
    ControlLoopCycle,
    ControlLoopState,
)
from guardian.domain.evidence_analysis import (
    EvidenceAnalysis,
    EvidenceAnalysisLevel,
)
from guardian.domain.prediction import (
    PredictionConfidence,
    PredictionDirection,
    PredictionResult,
)


def make_cycle() -> ControlLoopCycle:
    return ControlLoopCycle(
        source_event_id="event-1",
        resource_id="resource-1",
        metric="network_tx_bytes",
        state=ControlLoopState.PREDICTING,
    )


def make_analysis() -> EvidenceAnalysis:
    return EvidenceAnalysis(
        source_event_id="event-1",
        resource_id="resource-1",
        metric="network_tx_bytes",
        level=EvidenceAnalysisLevel.NORMAL,
        value=100.0,
        unit="bytes",
        evidence_available=True,
        finding="Real telemetry evidence.",
    )


def make_prediction() -> PredictionResult:
    return PredictionResult(
        source_event_id="event-1",
        resource_id="resource-1",
        metric="network_tx_bytes",
        current_value=100.0,
        predicted_value=120.0,
        direction=PredictionDirection.INCREASING,
        confidence=PredictionConfidence.HIGH,
        sample_count=7,
        evidence_available=True,
        basis=(
            "Projection derived from 7 ordered "
            "historical telemetry observations."
        ),
    )


def test_decision_transitions_cycle_to_deciding() -> None:
    service = ControlLoopDecisionService()

    result = service.decide(
        make_cycle(),
        make_analysis(),
        make_prediction(),
    )

    assert result.cycle.state == ControlLoopState.DECIDING
    assert result.decision.evidence_available is True


def test_decision_requires_predicting_state() -> None:
    service = ControlLoopDecisionService()

    cycle = make_cycle().transition_to(
        ControlLoopState.ANALYZING
    )

    with pytest.raises(
        ValueError,
        match="PREDICTING",
    ):
        service.decide(
            cycle,
            make_analysis(),
            make_prediction(),
        )


def test_decision_requires_matching_event() -> None:
    service = ControlLoopDecisionService()

    prediction = make_prediction().model_copy(
        update={"source_event_id": "different-event"}
    )

    with pytest.raises(
        ValueError,
        match="event IDs",
    ):
        service.decide(
            make_cycle(),
            make_analysis(),
            prediction,
        )