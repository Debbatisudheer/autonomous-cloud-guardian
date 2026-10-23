from __future__ import annotations

from guardian.domain.cost import CostObservation
from guardian.domain.cost_forecast import (
    CostForecast,
    CostForecastConfidence,
    CostForecastDirection,
)


class CostForecastingService:
    """Produces deterministic forecasts from historical cost evidence."""

    def forecast(
        self,
        observations: list[CostObservation],
    ) -> CostForecast:
        if len(observations) < 2:
            raise ValueError(
                "At least two cost observations are required "
                "for forecasting."
            )

        ordered = sorted(
            observations,
            key=lambda observation: observation.observed_at,
        )

        first = ordered[0]
        latest = ordered[-1]

        for observation in ordered:
            if observation.resource_id != first.resource_id:
                raise ValueError(
                    "All observations must belong to the same resource."
                )

            if observation.category != first.category:
                raise ValueError(
                    "All observations must use the same category."
                )

            if observation.currency != first.currency:
                raise ValueError(
                    "All observations must use the same currency."
                )

        if not all(
            observation.evidence_available
            for observation in ordered
        ):
            return CostForecast(
                resource_id=latest.resource_id,
                category=latest.category,
                currency=latest.currency,
                current_amount=latest.amount,
                forecast_amount=latest.amount,
                direction=CostForecastDirection.UNKNOWN,
                confidence=CostForecastConfidence.LOW,
                sample_count=len(ordered),
                evidence_available=False,
                latest_observed_at=latest.observed_at,
                forecast_for=latest.observed_at,
                basis=(
                    "Reliable billing evidence is unavailable; "
                    "no forecast was produced."
                ),
            )

        previous = ordered[-2]

        interval_seconds = (
            latest.observed_at - previous.observed_at
        ).total_seconds()

        if interval_seconds <= 0:
            raise ValueError(
                "Forecast observations must have increasing "
                "timestamps."
            )

        delta = latest.amount - previous.amount

        forecast_amount = max(
            0.0,
            latest.amount + delta,
        )

        forecast_for = (
            latest.observed_at
            + (latest.observed_at - previous.observed_at)
        )

        if abs(delta) <= max(abs(latest.amount) * 0.01, 0.01):
            direction = CostForecastDirection.STABLE
        elif delta > 0:
            direction = CostForecastDirection.INCREASING
        else:
            direction = CostForecastDirection.DECREASING

        confidence = self._confidence(len(ordered))

        return CostForecast(
            resource_id=latest.resource_id,
            category=latest.category,
            currency=latest.currency,
            current_amount=latest.amount,
            forecast_amount=forecast_amount,
            direction=direction,
            confidence=confidence,
            sample_count=len(ordered),
            evidence_available=True,
            latest_observed_at=latest.observed_at,
            forecast_for=forecast_for,
            basis=(
                "Forecast is based on the latest observed cost "
                "change over the latest historical interval."
            ),
        )

    def forecast_many(
        self,
        observation_series: list[list[CostObservation]],
    ) -> list[CostForecast]:
        return [
            self.forecast(observations)
            for observations in observation_series
        ]

    @staticmethod
    def _confidence(
        sample_count: int,
    ) -> CostForecastConfidence:
        if sample_count >= 5:
            return CostForecastConfidence.HIGH

        if sample_count >= 3:
            return CostForecastConfidence.MEDIUM

        return CostForecastConfidence.LOW