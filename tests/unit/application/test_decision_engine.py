
import pytest

from guardian.application.decision_engine import DecisionEngine
from guardian.domain.decision import (
    DecisionOutcome,
    DecisionPriority,
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


def make_analysis(
    level: EvidenceAnalysisLevel,
    value: float = 100.0,
) -> EvidenceAnalysis:
    return EvidenceAnalysis(
        source_event_id="event-1",
        resource_id="resource-1",
        metric="network_tx_bytes",
        level=level,
        value=value,
        unit="bytes",
        evidence_available=True,
        finding="Real telemetry evidence.",
    )


def make_prediction(
    direction: PredictionDirection,
    confidence: PredictionConfidence,
    current_value: float = 100.0,
    predicted_value: float = 120.0,
) -> PredictionResult:
    return PredictionResult(
        source_event_id="event-1",
        resource_id="resource-1",
        metric="network_tx_bytes",
        current_value=current_value,
        predicted_value=predicted_value,
        direction=direction,
        confidence=confidence,
        sample_count=7,
        evidence_available=True,
        basis=(
            "Projection derived from 7 ordered "
            "historical telemetry observations."
        ),
    )


def test_healthy_increasing_high_confidence_monitors() -> None:
    engine = DecisionEngine()

    result = engine.decide(
        make_analysis(
            EvidenceAnalysisLevel.NORMAL,
        ),
        make_prediction(
            PredictionDirection.INCREASING,
            PredictionConfidence.HIGH,
        ),
    )

    assert result.outcome == DecisionOutcome.MONITOR
    assert result.priority == DecisionPriority.LOW
    assert result.evidence_available is True


def test_critical_evidence_recommends_action() -> None:
    engine = DecisionEngine()

    result = engine.decide(
        make_analysis(
            EvidenceAnalysisLevel.CRITICAL,
        ),
        make_prediction(
            PredictionDirection.INCREASING,
            PredictionConfidence.HIGH,
        ),
    )

    assert result.outcome == DecisionOutcome.ACTION_RECOMMENDED
    assert result.priority == DecisionPriority.HIGH


def test_warning_increasing_recommends_action() -> None:
    engine = DecisionEngine()

    result = engine.decide(
        make_analysis(
            EvidenceAnalysisLevel.WARNING,
        ),
        make_prediction(
            PredictionDirection.INCREASING,
            PredictionConfidence.MEDIUM,
        ),
    )

    assert result.outcome == DecisionOutcome.ACTION_RECOMMENDED
    assert result.priority == DecisionPriority.MEDIUM


def test_warning_stable_monitors() -> None:
    engine = DecisionEngine()

    result = engine.decide(
        make_analysis(
            EvidenceAnalysisLevel.WARNING,
        ),
        make_prediction(
            PredictionDirection.STABLE,
            PredictionConfidence.MEDIUM,
        ),
    )

    assert result.outcome == DecisionOutcome.MONITOR


def test_normal_non_increasing_no_action() -> None:
    engine = DecisionEngine()

    result = engine.decide(
        make_analysis(
            EvidenceAnalysisLevel.NORMAL,
        ),
        make_prediction(
            PredictionDirection.STABLE,
            PredictionConfidence.MEDIUM,
        ),
    )

    assert result.outcome == DecisionOutcome.NO_ACTION


def test_correlation_mismatch_is_rejected() -> None:
    engine = DecisionEngine()

    prediction = make_prediction(
        PredictionDirection.INCREASING,
        PredictionConfidence.HIGH,
    ).model_copy(
        update={"resource_id": "different-resource"}
    )

    with pytest.raises(ValueError, match="resource IDs"):
        engine.decide(
            make_analysis(
                EvidenceAnalysisLevel.NORMAL,
            ),
            prediction,
        )