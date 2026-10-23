from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from guardian.domain.cost import CostCategory
from guardian.domain.cost_forecast import (
    CostForecast,
    CostForecastConfidence,
    CostForecastDirection,
)


def test_cost_forecast_model() -> None:
    timestamp = datetime.now(UTC)

    forecast = CostForecast(
        resource_id="resource-1",
        category=CostCategory.COMPUTE,
        currency="USD",
        current_amount=20.0,
        forecast_amount=30.0,
        direction=CostForecastDirection.INCREASING,
        confidence=CostForecastConfidence.LOW,
        sample_count=2,
        evidence_available=True,
        latest_observed_at=timestamp,
        forecast_for=timestamp,
        basis="Historical trend.",
    )

    assert forecast.resource_id == "resource-1"
    assert forecast.category == CostCategory.COMPUTE
    assert forecast.currency == "USD"
    assert forecast.current_amount == 20.0
    assert forecast.forecast_amount == 30.0
    assert forecast.direction == CostForecastDirection.INCREASING
    assert forecast.confidence == CostForecastConfidence.LOW
    assert forecast.sample_count == 2
    assert forecast.evidence_available is True


def test_cost_forecast_rejects_negative_current_amount() -> None:
    timestamp = datetime.now(UTC)

    with pytest.raises(ValidationError):
        CostForecast(
            resource_id="resource-1",
            category=CostCategory.COMPUTE,
            currency="USD",
            current_amount=-1.0,
            forecast_amount=10.0,
            direction=CostForecastDirection.INCREASING,
            confidence=CostForecastConfidence.LOW,
            sample_count=2,
            evidence_available=True,
            latest_observed_at=timestamp,
            forecast_for=timestamp,
            basis="Historical trend.",
        )


def test_cost_forecast_rejects_negative_forecast_amount() -> None:
    timestamp = datetime.now(UTC)

    with pytest.raises(ValidationError):
        CostForecast(
            resource_id="resource-1",
            category=CostCategory.COMPUTE,
            currency="USD",
            current_amount=10.0,
            forecast_amount=-1.0,
            direction=CostForecastDirection.INCREASING,
            confidence=CostForecastConfidence.LOW,
            sample_count=2,
            evidence_available=True,
            latest_observed_at=timestamp,
            forecast_for=timestamp,
            basis="Historical trend.",
        )


def test_cost_forecast_requires_two_samples() -> None:
    timestamp = datetime.now(UTC)

    with pytest.raises(ValidationError):
        CostForecast(
            resource_id="resource-1",
            category=CostCategory.COMPUTE,
            currency="USD",
            current_amount=10.0,
            forecast_amount=10.0,
            direction=CostForecastDirection.UNKNOWN,
            confidence=CostForecastConfidence.LOW,
            sample_count=1,
            evidence_available=False,
            latest_observed_at=timestamp,
            forecast_for=timestamp,
            basis="Insufficient evidence.",
        )


def test_cost_forecast_rejects_extra_fields() -> None:
    timestamp = datetime.now(UTC)

    with pytest.raises(ValidationError):
        CostForecast(
            resource_id="resource-1",
            category=CostCategory.COMPUTE,
            currency="USD",
            current_amount=10.0,
            forecast_amount=10.0,
            direction=CostForecastDirection.STABLE,
            confidence=CostForecastConfidence.LOW,
            sample_count=2,
            evidence_available=True,
            latest_observed_at=timestamp,
            forecast_for=timestamp,
            basis="Historical trend.",
            unexpected="value",
        )