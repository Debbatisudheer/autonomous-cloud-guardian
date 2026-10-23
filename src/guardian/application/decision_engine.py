from __future__ import annotations

from guardian.domain.decision import (
    DecisionOutcome,
    DecisionPriority,
    DecisionResult,
)
from guardian.domain.evidence_analysis import (
    EvidenceAnalysis,
    EvidenceAnalysisLevel,
)
from guardian.domain.prediction import PredictionResult


class DecisionEngine:
    """
    Deterministic decision policy.

    This engine produces a decision only.
    It does not execute infrastructure actions.
    """

    def decide(
        self,
        analysis: EvidenceAnalysis,
        prediction: PredictionResult,
    ) -> DecisionResult:
        self._validate_correlation(
            analysis,
            prediction,
        )

        if not analysis.evidence_available:
            return DecisionResult(
                source_event_id=prediction.source_event_id,
                resource_id=prediction.resource_id,
                metric=prediction.metric,
                current_value=prediction.current_value,
                predicted_value=prediction.predicted_value,
                prediction_direction=prediction.direction,
                prediction_confidence=prediction.confidence,
                outcome=DecisionOutcome.NO_ACTION,
                priority=DecisionPriority.LOW,
                evidence_available=False,
                rationale=(
                    "Decision suppressed because "
                    "supporting evidence is unavailable."
                ),
            )

        if (
            analysis.level
            == EvidenceAnalysisLevel.CRITICAL
        ):
            return DecisionResult(
                source_event_id=prediction.source_event_id,
                resource_id=prediction.resource_id,
                metric=prediction.metric,
                current_value=prediction.current_value,
                predicted_value=prediction.predicted_value,
                prediction_direction=prediction.direction,
                prediction_confidence=prediction.confidence,
                outcome=DecisionOutcome.ACTION_RECOMMENDED,
                priority=DecisionPriority.HIGH,
                evidence_available=True,
                rationale=(
                    "Critical evidence is present. "
                    "A controlled action may be considered "
                    "after explicit policy and action validation."
                ),
            )

        if (
            analysis.level
            == EvidenceAnalysisLevel.WARNING
        ):
            if prediction.direction.value == "increasing":
                return DecisionResult(
                    source_event_id=prediction.source_event_id,
                    resource_id=prediction.resource_id,
                    metric=prediction.metric,
                    current_value=prediction.current_value,
                    predicted_value=prediction.predicted_value,
                    prediction_direction=prediction.direction,
                    prediction_confidence=prediction.confidence,
                    outcome=DecisionOutcome.ACTION_RECOMMENDED,
                    priority=DecisionPriority.MEDIUM,
                    evidence_available=True,
                    rationale=(
                        "Warning evidence and an increasing "
                        "prediction indicate that controlled "
                        "action should be considered."
                    ),
                )

            return DecisionResult(
                source_event_id=prediction.source_event_id,
                resource_id=prediction.resource_id,
                metric=prediction.metric,
                current_value=prediction.current_value,
                predicted_value=prediction.predicted_value,
                prediction_direction=prediction.direction,
                prediction_confidence=prediction.confidence,
                outcome=DecisionOutcome.MONITOR,
                priority=DecisionPriority.MEDIUM,
                evidence_available=True,
                rationale=(
                    "Warning evidence exists, but the prediction "
                    "does not justify immediate action."
                ),
            )

        if (
            prediction.direction.value == "increasing"
            and prediction.confidence.value == "high"
        ):
            return DecisionResult(
                source_event_id=prediction.source_event_id,
                resource_id=prediction.resource_id,
                metric=prediction.metric,
                current_value=prediction.current_value,
                predicted_value=prediction.predicted_value,
                prediction_direction=prediction.direction,
                prediction_confidence=prediction.confidence,
                outcome=DecisionOutcome.MONITOR,
                priority=DecisionPriority.LOW,
                evidence_available=True,
                rationale=(
                    "Healthy evidence with a high-confidence "
                    "increasing prediction does not independently "
                    "justify remediation; continue monitoring."
                ),
            )

        return DecisionResult(
            source_event_id=prediction.source_event_id,
            resource_id=prediction.resource_id,
            metric=prediction.metric,
            current_value=prediction.current_value,
            predicted_value=prediction.predicted_value,
            prediction_direction=prediction.direction,
            prediction_confidence=prediction.confidence,
            outcome=DecisionOutcome.NO_ACTION,
            priority=DecisionPriority.LOW,
            evidence_available=True,
            rationale=(
                "Available evidence and prediction do not "
                "justify an action."
            ),
        )

    @staticmethod
    def _validate_correlation(
        analysis: EvidenceAnalysis,
        prediction: PredictionResult,
    ) -> None:
        if (
            analysis.source_event_id
            != prediction.source_event_id
        ):
            raise ValueError(
                "Evidence and prediction event IDs do not match."
            )

        if (
            analysis.resource_id
            != prediction.resource_id
        ):
            raise ValueError(
                "Evidence and prediction resource IDs do not match."
            )

        if analysis.metric != prediction.metric:
            raise ValueError(
                "Evidence and prediction metrics do not match."
            )

        if analysis.value != prediction.current_value:
            raise ValueError(
                "Evidence value and prediction current value do not match."
            )