from datetime import UTC, datetime

import pytest

from guardian.application.cost_recommendation import (
    CostRecommendationService,
)
from guardian.domain.cost import CostCategory
from guardian.domain.cost_forecast import (
    CostForecast,
    CostForecastConfidence,
    CostForecastDirection,
)
from guardian.domain.cost_recommendation import (
    CostRecommendationOutcome,
    CostRecommendationPriority,
)
from guardian.domain.cost_signal import (
    CostOptimizationSignal,
    CostSignalSeverity,
    CostSignalType,
)


def make_signal(
    *,
    signal_type: CostSignalType = CostSignalType.RISING_COST,
    evidence_available: bool = True,
) -> CostOptimizationSignal:
    return CostOptimizationSignal(
        signal_type=signal_type,
        severity=(
            CostSignalSeverity.WARNING
            if signal_type == CostSignalType.RISING_COST
            else CostSignalSeverity.UNKNOWN
        ),
        resource_id="resource-1",
        category=CostCategory.COMPUTE,
        currency="USD",
        current_amount=50.0,
        baseline_amount=30.0,
        evidence_available=evidence_available,
        observation_count=5,
        finding="Controlled cost signal.",
    )


def make_forecast(
    *,
    direction: CostForecastDirection = (
        CostForecastDirection.INCREASING
    ),
    confidence: CostForecastConfidence = (
        CostForecastConfidence.HIGH
    ),
) -> CostForecast:
    timestamp = datetime.now(UTC)

    return CostForecast(
        resource_id="resource-1",
        category=CostCategory.COMPUTE,
        currency="USD",
        current_amount=50.0,
        forecast_amount=60.0,
        direction=direction,
        confidence=confidence,
        sample_count=5,
        evidence_available=True,
        latest_observed_at=timestamp,
        forecast_for=timestamp,
        basis="Controlled historical trend.",
    )


def test_high_confidence_increasing_cost_recommends_optimization() -> None:
    service = CostRecommendationService()

    recommendation = service.recommend(
        make_signal(),
        make_forecast(),
    )

    assert (
        recommendation.outcome
        == CostRecommendationOutcome.OPTIMIZATION_RECOMMENDED
    )
    assert recommendation.priority == CostRecommendationPriority.HIGH
    assert recommendation.evidence_available is True


def test_medium_confidence_increasing_cost_requests_review() -> None:
    service = CostRecommendationService()

    recommendation = service.recommend(
        make_signal(),
        make_forecast(
            confidence=CostForecastConfidence.MEDIUM
        ),
    )

    assert (
        recommendation.outcome
        == CostRecommendationOutcome.REVIEW
    )
    assert recommendation.priority == CostRecommendationPriority.MEDIUM


def test_low_confidence_increasing_cost_requests_review() -> None:
    service = CostRecommendationService()

    recommendation = service.recommend(
        make_signal(),
        make_forecast(
            confidence=CostForecastConfidence.LOW
        ),
    )

    assert (
        recommendation.outcome
        == CostRecommendationOutcome.REVIEW
    )
    assert recommendation.priority == CostRecommendationPriority.MEDIUM


def test_stable_forecast_produces_no_recommendation() -> None:
    service = CostRecommendationService()

    recommendation = service.recommend(
        make_signal(),
        make_forecast(
            direction=CostForecastDirection.STABLE,
        ),
    )

    assert (
        recommendation.outcome
        == CostRecommendationOutcome.NO_RECOMMENDATION
    )
    assert recommendation.priority == CostRecommendationPriority.LOW


def test_decreasing_forecast_produces_no_recommendation() -> None:
    service = CostRecommendationService()

    recommendation = service.recommend(
        make_signal(),
        make_forecast(
            direction=CostForecastDirection.DECREASING,
        ),
    )

    assert (
        recommendation.outcome
        == CostRecommendationOutcome.NO_RECOMMENDATION
    )
    assert recommendation.priority == CostRecommendationPriority.LOW


def test_missing_evidence_produces_no_recommendation() -> None:
    service = CostRecommendationService()

    recommendation = service.recommend(
        make_signal(evidence_available=False),
        make_forecast(),
    )

    assert (
        recommendation.outcome
        == CostRecommendationOutcome.NO_RECOMMENDATION
    )
    assert recommendation.priority == CostRecommendationPriority.LOW
    assert recommendation.evidence_available is False


def test_insufficient_evidence_signal_produces_no_recommendation() -> None:
    service = CostRecommendationService()

    recommendation = service.recommend(
        make_signal(
            signal_type=CostSignalType.INSUFFICIENT_EVIDENCE,
            evidence_available=False,
        ),
        make_forecast(),
    )

    assert (
        recommendation.outcome
        == CostRecommendationOutcome.NO_RECOMMENDATION
    )


def test_resource_identity_must_match() -> None:
    service = CostRecommendationService()

    forecast = make_forecast().model_copy(
        update={"resource_id": "resource-2"}
    )

    with pytest.raises(ValueError, match="resource identities"):
        service.recommend(make_signal(), forecast)


def test_category_must_match() -> None:
    service = CostRecommendationService()

    forecast = make_forecast().model_copy(
        update={"category": CostCategory.STORAGE}
    )

    with pytest.raises(ValueError, match="categories"):
        service.recommend(make_signal(), forecast)


def test_currency_must_match() -> None:
    service = CostRecommendationService()

    forecast = make_forecast().model_copy(
        update={"currency": "INR"}
    )

    with pytest.raises(ValueError, match="currencies"):
        service.recommend(make_signal(), forecast)


def test_current_amount_must_match() -> None:
    service = CostRecommendationService()

    forecast = make_forecast().model_copy(
        update={"current_amount": 75.0}
    )

    with pytest.raises(ValueError, match="current amounts"):
        service.recommend(make_signal(), forecast)


def test_recommendation_does_not_execute_action() -> None:
    service = CostRecommendationService()

    recommendation = service.recommend(
        make_signal(),
        make_forecast(),
    )

    action_terms = (
        "restart",
        "resize",
        "delete",
        "terminate",
        "execute",
    )

    assert not any(
        term in recommendation.rationale.lower()
        for term in action_terms
    )


def test_recommendation_does_not_claim_savings() -> None:
    service = CostRecommendationService()

    recommendation = service.recommend(
        make_signal(),
        make_forecast(),
    )

    assert "saving" not in recommendation.rationale.lower()
    assert "savings" not in recommendation.rationale.lower()