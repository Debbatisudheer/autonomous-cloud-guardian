from __future__ import annotations

from dataclasses import dataclass

from guardian.application.prediction_engine import (
    PredictionEngine,
)
from guardian.domain.control_loop import (
    ControlLoopCycle,
    ControlLoopState,
)
from guardian.domain.prediction import (
    PredictionResult,
)
from guardian.domain.telemetry import (
    TelemetryObservation,
)


@dataclass(frozen=True)
class ControlLoopPredictionResult:
    """
    Prediction result attached to one control-loop cycle.
    """

    cycle: ControlLoopCycle

    prediction: PredictionResult


class ControlLoopPredictionService:
    """
    Runs prediction for a control cycle using historical telemetry.

    Prediction is informational only. No decision or action is made.
    """

    def __init__(
        self,
        prediction_engine: PredictionEngine | None = None,
    ) -> None:
        self._prediction_engine = (
            prediction_engine
            or PredictionEngine()
        )

    def predict(
        self,
        cycle: ControlLoopCycle,
        observations: list[TelemetryObservation],
    ) -> ControlLoopPredictionResult:
        if cycle.state != ControlLoopState.ANALYZING:
            raise ValueError(
                "Control cycle must be in ANALYZING state "
                "before prediction."
            )

        if not observations:
            raise ValueError(
                "Prediction requires telemetry evidence."
            )

        for observation in observations:
            if observation.resource_id != cycle.resource_id:
                raise ValueError(
                    "Prediction evidence resource does not "
                    "match the control cycle."
                )

            if observation.metric.value != cycle.metric:
                raise ValueError(
                    "Prediction evidence metric does not "
                    "match the control cycle."
                )

        prediction = self._prediction_engine.predict(
            observations=observations,
            source_event_id=cycle.source_event_id,
        )

        predicting_cycle = cycle.transition_to(
            ControlLoopState.PREDICTING
        )

        return ControlLoopPredictionResult(
            cycle=predicting_cycle,
            prediction=prediction,
        )