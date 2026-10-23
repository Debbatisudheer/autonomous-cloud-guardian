from __future__ import annotations

from dataclasses import dataclass

from guardian.application.decision_engine import DecisionEngine
from guardian.domain.control_loop import (
    ControlLoopCycle,
    ControlLoopState,
)
from guardian.domain.decision import DecisionResult
from guardian.domain.evidence_analysis import EvidenceAnalysis
from guardian.domain.prediction import PredictionResult


@dataclass(frozen=True)
class ControlLoopDecisionResult:
    cycle: ControlLoopCycle
    decision: DecisionResult


class ControlLoopDecisionService:
    """
    Integrates decision generation into the autonomous
    control-loop lifecycle.

    This service does NOT execute infrastructure actions.
    """

    def __init__(
        self,
        decision_engine: DecisionEngine | None = None,
    ) -> None:
        self._engine = (
            decision_engine
            if decision_engine is not None
            else DecisionEngine()
        )

    def decide(
        self,
        cycle: ControlLoopCycle,
        analysis: EvidenceAnalysis,
        prediction: PredictionResult,
    ) -> ControlLoopDecisionResult:
        if cycle.state != ControlLoopState.PREDICTING:
            raise ValueError(
                "Control loop must be in PREDICTING state "
                "before decision generation."
            )

        if not prediction.evidence_available:
            raise ValueError(
                "Prediction evidence must be available "
                "before decision generation."
            )

        if (
            cycle.source_event_id
            != prediction.source_event_id
        ):
            raise ValueError(
                "Cycle and prediction event IDs do not match."
            )

        if cycle.resource_id != prediction.resource_id:
            raise ValueError(
                "Cycle and prediction resource IDs do not match."
            )

        if cycle.metric != prediction.metric:
            raise ValueError(
                "Cycle and prediction metrics do not match."
            )

        decision = self._engine.decide(
            analysis,
            prediction,
        )

        updated_cycle = cycle.transition_to(
            ControlLoopState.DECIDING
        )

        return ControlLoopDecisionResult(
            cycle=updated_cycle,
            decision=decision,
        )