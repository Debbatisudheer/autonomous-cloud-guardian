from __future__ import annotations

from guardian.domain.cost_forecast import CostForecast
from guardian.domain.cost_recommendation import (
    CostRecommendation,
    CostRecommendationOutcome,
    CostRecommendationPriority,
)
from guardian.domain.cost_signal import CostOptimizationSignal


class CostRecommendationService:
    """Produces explainable recommendations from cost evidence.

    This service does not execute infrastructure actions.
    """

    def recommend(
        self,
        signal: CostOptimizationSignal,
        forecast: CostForecast,
    ) -> CostRecommendation:
        self._validate_correlation(signal, forecast)

        if not signal.evidence_available:
            return self._build(
                signal=signal,
                forecast=forecast,
                outcome=CostRecommendationOutcome.NO_RECOMMENDATION,
                priority=CostRecommendationPriority.LOW,
                rationale=(
                    "Reliable cost evidence is unavailable. "
                    "No optimization recommendation can be made."
                ),
            )

        if (
            signal.signal_type
            == signal.signal_type.INSUFFICIENT_EVIDENCE
        ):
            return self._build(
                signal=signal,
                forecast=forecast,
                outcome=CostRecommendationOutcome.NO_RECOMMENDATION,
                priority=CostRecommendationPriority.LOW,
                rationale=(
                    "Cost evidence is insufficient for a reliable "
                    "optimization recommendation."
                ),
            )

        if (
            signal.signal_type == signal.signal_type.RISING_COST
            and forecast.direction
            == forecast.direction.INCREASING
            and forecast.confidence
            == forecast.confidence.HIGH
        ):
            return self._build(
                signal=signal,
                forecast=forecast,
                outcome=(
                    CostRecommendationOutcome.OPTIMIZATION_RECOMMENDED
                ),
                priority=CostRecommendationPriority.HIGH,
                rationale=(
                    "Historical cost evidence shows the latest "
                    "cost above its available baseline and the "
                    "forecast indicates continued increase with "
                    "high confidence. Review this resource for "
                    "potential cost optimization."
                ),
            )

        if (
            signal.signal_type == signal.signal_type.RISING_COST
            and forecast.direction
            == forecast.direction.INCREASING
        ):
            return self._build(
                signal=signal,
                forecast=forecast,
                outcome=CostRecommendationOutcome.REVIEW,
                priority=CostRecommendationPriority.MEDIUM,
                rationale=(
                    "Historical cost evidence shows an elevated "
                    "latest cost and an increasing forecast. "
                    "Review the resource before taking any "
                    "optimization action."
                ),
            )

        return self._build(
            signal=signal,
            forecast=forecast,
            outcome=CostRecommendationOutcome.NO_RECOMMENDATION,
            priority=CostRecommendationPriority.LOW,
            rationale=(
                "Available cost evidence and forecast do not "
                "currently justify an optimization recommendation."
            ),
        )

    def _build(
        self,
        *,
        signal: CostOptimizationSignal,
        forecast: CostForecast,
        outcome: CostRecommendationOutcome,
        priority: CostRecommendationPriority,
        rationale: str,
    ) -> CostRecommendation:
        return CostRecommendation(
            resource_id=signal.resource_id,
            category=signal.category,
            currency=signal.currency,
            signal_type=signal.signal_type,
            signal_severity=signal.severity,
            forecast_direction=forecast.direction,
            forecast_confidence=forecast.confidence,
            current_amount=forecast.current_amount,
            forecast_amount=forecast.forecast_amount,
            outcome=outcome,
            priority=priority,
            evidence_available=(
                signal.evidence_available
                and forecast.evidence_available
            ),
            observation_count=forecast.sample_count,
            rationale=rationale,
        )

    @staticmethod
    def _validate_correlation(
        signal: CostOptimizationSignal,
        forecast: CostForecast,
    ) -> None:
        if signal.resource_id != forecast.resource_id:
            raise ValueError(
                "Signal and forecast resource identities must match."
            )

        if signal.category != forecast.category:
            raise ValueError(
                "Signal and forecast categories must match."
            )

        if signal.currency != forecast.currency:
            raise ValueError(
                "Signal and forecast currencies must match."
            )

        if signal.current_amount != forecast.current_amount:
            raise ValueError(
                "Signal and forecast current amounts must match."
            )