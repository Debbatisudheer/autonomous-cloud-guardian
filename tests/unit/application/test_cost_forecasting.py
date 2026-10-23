from datetime import UTC, datetime, timedelta

import pytest

from guardian.application.cost_forecasting import CostForecastingService
from guardian.domain.cost import CostCategory, CostObservation, CostSource
from guardian.domain.cost_forecast import (
    CostForecastConfidence,
    CostForecastDirection,
)


def make_observations(
    amounts: list[float],
    *,
    evidence_available: bool = True,
    resource_id: str = "resource-1",
    category: CostCategory = CostCategory.COMPUTE,
    currency: str = "USD",
) -> list[CostObservation]:
    base = datetime(2026, 10, 23, 10, 0, tzinfo=UTC)

    return [
        CostObservation(
            resource_id=resource_id,
            amount=amount,
            currency=currency,
            category=category,
            source=CostSource.AWS,
            observed_at=base + timedelta(hours=index),
            evidence_available=evidence_available,
        )
        for index, amount in enumerate(amounts)
    ]


def test_forecast_increasing_cost() -> None:
    service = CostForecastingService()

    observations = make_observations([10.0, 20.0])

    result = service.forecast(observations)

    assert result.current_amount == 20.0
    assert result.forecast_amount == 30.0
    assert result.direction == CostForecastDirection.INCREASING
    assert result.confidence == CostForecastConfidence.LOW
    assert result.sample_count == 2
    assert result.evidence_available is True


def test_forecast_decreasing_cost() -> None:
    service = CostForecastingService()

    observations = make_observations([30.0, 20.0])

    result = service.forecast(observations)

    assert result.current_amount == 20.0
    assert result.forecast_amount == 10.0
    assert result.direction == CostForecastDirection.DECREASING


def test_forecast_never_becomes_negative() -> None:
    service = CostForecastingService()

    observations = make_observations([10.0, 2.0])

    result = service.forecast(observations)

    assert result.forecast_amount == 0.0
    assert result.forecast_amount >= 0.0


def test_forecast_stable_cost() -> None:
    service = CostForecastingService()

    observations = make_observations([20.0, 20.0])

    result = service.forecast(observations)

    assert result.forecast_amount == 20.0
    assert result.direction == CostForecastDirection.STABLE


def test_forecast_requires_two_observations() -> None:
    service = CostForecastingService()

    observations = make_observations([20.0])

    with pytest.raises(ValueError, match="At least two"):
        service.forecast(observations)


def test_forecast_rejects_mixed_resources() -> None:
    service = CostForecastingService()

    observations = make_observations([10.0, 20.0])
    observations[1] = observations[1].model_copy(
        update={"resource_id": "resource-2"}
    )

    with pytest.raises(ValueError, match="same resource"):
        service.forecast(observations)


def test_forecast_rejects_mixed_categories() -> None:
    service = CostForecastingService()

    observations = make_observations([10.0, 20.0])
    observations[1] = observations[1].model_copy(
        update={"category": CostCategory.STORAGE}
    )

    with pytest.raises(ValueError, match="same category"):
        service.forecast(observations)


def test_forecast_rejects_mixed_currencies() -> None:
    service = CostForecastingService()

    observations = make_observations([10.0, 20.0])
    observations[1] = observations[1].model_copy(
        update={"currency": "INR"}
    )

    with pytest.raises(ValueError, match="same currency"):
        service.forecast(observations)


def test_forecast_handles_missing_evidence() -> None:
    service = CostForecastingService()

    observations = make_observations(
        [10.0, 20.0],
        evidence_available=False,
    )

    result = service.forecast(observations)

    assert result.evidence_available is False
    assert result.direction == CostForecastDirection.UNKNOWN
    assert result.confidence == CostForecastConfidence.LOW
    assert result.forecast_amount == 20.0


def test_forecast_confidence_two_samples() -> None:
    service = CostForecastingService()

    result = service.forecast(
        make_observations([10.0, 20.0])
    )

    assert result.confidence == CostForecastConfidence.LOW


def test_forecast_confidence_three_samples() -> None:
    service = CostForecastingService()

    result = service.forecast(
        make_observations([10.0, 20.0, 30.0])
    )

    assert result.confidence == CostForecastConfidence.MEDIUM


def test_forecast_confidence_five_samples() -> None:
    service = CostForecastingService()

    result = service.forecast(
        make_observations([10.0, 20.0, 30.0, 40.0, 50.0])
    )

    assert result.confidence == CostForecastConfidence.HIGH


def test_forecast_uses_latest_observation() -> None:
    service = CostForecastingService()

    observations = make_observations(
        [5.0, 10.0, 15.0, 40.0]
    )

    result = service.forecast(observations)

    assert result.current_amount == 40.0
    assert result.forecast_amount == 65.0
    assert result.sample_count == 4


def test_forecast_for_is_next_interval() -> None:
    service = CostForecastingService()

    observations = make_observations([10.0, 20.0])

    result = service.forecast(observations)

    expected = observations[-1].observed_at + timedelta(hours=1)

    assert result.forecast_for == expected


def test_forecast_many() -> None:
    service = CostForecastingService()

    series = [
        make_observations([10.0, 20.0]),
        make_observations([30.0, 20.0]),
    ]

    results = service.forecast_many(series)

    assert len(results) == 2
    assert (
        results[0].direction
        == CostForecastDirection.INCREASING
    )
    assert (
        results[1].direction
        == CostForecastDirection.DECREASING
    )


def test_forecast_requires_increasing_timestamps() -> None:
    service = CostForecastingService()

    observations = make_observations([10.0, 20.0])

    observations[1] = observations[1].model_copy(
        update={
            "observed_at": observations[0].observed_at,
        }
    )

    with pytest.raises(ValueError, match="increasing timestamps"):
        service.forecast(observations)


def test_forecast_basis_does_not_claim_real_billing() -> None:
    service = CostForecastingService()

    result = service.forecast(
        make_observations([10.0, 20.0])
    )

    assert "billing" not in result.basis.lower()


def test_forecast_does_not_recommend_action() -> None:
    service = CostForecastingService()

    result = service.forecast(
        make_observations([10.0, 20.0])
    )

    action_terms = (
        "restart",
        "resize",
        "delete",
        "terminate",
        "scale",
        "modify",
        "execute",
    )

    assert not any(
        term in result.basis.lower()
        for term in action_terms
    )