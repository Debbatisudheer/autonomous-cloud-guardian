from __future__ import annotations

from guardian.domain.prediction import (
    PredictionConfidence,
    PredictionDirection,
    PredictionResult,
)
from guardian.domain.telemetry import (
    TelemetryObservation,
)


class PredictionEngine:
    """
    Produces deterministic short-horizon projections from historical
    telemetry observations.

    The engine does not make decisions and does not execute actions.
    """

    def predict(
        self,
        observations: list[TelemetryObservation],
        source_event_id: str,
    ) -> PredictionResult:
        if len(observations) < 2:
            raise ValueError(
                "At least two telemetry observations are required "
                "for prediction."
            )

        ordered = sorted(
            observations,
            key=lambda observation: observation.observed_at,
        )

        latest = ordered[-1]

        self._validate_series(
            ordered,
            latest,
        )

        first_value = ordered[0].value
        latest_value = latest.value

        delta = latest_value - first_value
        direction = self._determine_direction(
            delta,
            first_value,
        )

        predicted_value = max(
            0.0,
            latest_value + (delta / (len(ordered) - 1)),
        )

        confidence = self._determine_confidence(
            len(ordered),
            direction,
        )

        return PredictionResult(
            source_event_id=source_event_id,
            resource_id=latest.resource_id,
            metric=latest.metric.value,
            current_value=latest_value,
            predicted_value=predicted_value,
            direction=direction,
            confidence=confidence,
            sample_count=len(ordered),
            evidence_available=True,
            basis=(
                f"Projection derived from {len(ordered)} "
                "ordered historical telemetry observations."
            ),
        )

    @staticmethod
    def _validate_series(
        observations: list[TelemetryObservation],
        latest: TelemetryObservation,
    ) -> None:
        for observation in observations:
            if observation.resource_id != latest.resource_id:
                raise ValueError(
                    "Prediction observations must belong to "
                    "the same resource."
                )

            if observation.metric != latest.metric:
                raise ValueError(
                    "Prediction observations must use "
                    "the same metric."
                )

            if observation.unit != latest.unit:
                raise ValueError(
                    "Prediction observations must use "
                    "the same unit."
                )

    @staticmethod
    def _determine_direction(
        delta: float,
        first_value: float,
    ) -> PredictionDirection:
        tolerance = max(abs(first_value) * 0.01, 0.000001)

        if delta > tolerance:
            return PredictionDirection.INCREASING

        if delta < -tolerance:
            return PredictionDirection.DECREASING

        return PredictionDirection.STABLE

    @staticmethod
    def _determine_confidence(
        sample_count: int,
        direction: PredictionDirection,
    ) -> PredictionConfidence:
        if direction == PredictionDirection.UNKNOWN:
            return PredictionConfidence.LOW

        if sample_count >= 5:
            return PredictionConfidence.HIGH

        if sample_count >= 3:
            return PredictionConfidence.MEDIUM

        return PredictionConfidence.LOW