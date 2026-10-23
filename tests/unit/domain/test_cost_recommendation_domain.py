from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from guardian.domain.cost import CostCategory
from guardian.domain.cost_forecast import (
    CostForecastConfidence,
    CostForecastDirection,
)
from guardian.domain.cost_recommendation import (
    CostRecommendation,
    CostRecommendationOutcome,
    CostRecommendationPriority,
)
from guardian.domain.cost_signal import (
    CostSignalSeverity,
    CostSignalType,
)


def make_recommendation() -> CostRecommendation:
    timestamp = datetime.now(UTC)

    return CostRecommendation(
        resource_id="resource-1",
        category=CostCategory.COMPUTE,
        currency="USD",
        signal_type=CostSignalType.RISING_COST,
        signal_severity=CostSignalSeverity.WARNING,
        forecast_direction=CostForecastDirection.INCREASING,
        forecast_confidence=CostForecastConfidence.HIGH,
        current_amount=50.0,
        forecast_amount=60.0,
        outcome=CostRecommendationOutcome.OPTIMIZATION_RECOMMENDED,
        priority=CostRecommendationPriority.HIGH,
        evidence_available=True,
        observation_count=5,
        rationale="Review resource for optimization.",
        generated_at=timestamp,
    )


def test_cost_recommendation_model() -> None:
    recommendation = make_recommendation()

    assert recommendation.resource_id == "resource-1"
    assert recommendation.category == CostCategory.COMPUTE
    assert recommendation.currency == "USD"
    assert recommendation.signal_type == CostSignalType.RISING_COST
    assert (
        recommendation.outcome
        == CostRecommendationOutcome.OPTIMIZATION_RECOMMENDED
    )
    assert recommendation.priority == CostRecommendationPriority.HIGH
    assert recommendation.evidence_available is True


def test_cost_recommendation_rejects_negative_current_amount() -> None:
    values = make_recommendation().model_dump()
    values["current_amount"] = -1.0

    with pytest.raises(ValidationError):
        CostRecommendation(**values)


def test_cost_recommendation_rejects_negative_forecast_amount() -> None:
    values = make_recommendation().model_dump()
    values["forecast_amount"] = -1.0

    with pytest.raises(ValidationError):
        CostRecommendation(**values)


def test_cost_recommendation_rejects_negative_observation_count() -> None:
    values = make_recommendation().model_dump()
    values["observation_count"] = -1

    with pytest.raises(ValidationError):
        CostRecommendation(**values)


def test_cost_recommendation_rejects_extra_fields() -> None:
    values = make_recommendation().model_dump()
    values["unexpected"] = "value"

    with pytest.raises(ValidationError):
        CostRecommendation(**values)


def test_cost_recommendation_requires_rationale() -> None:
    values = make_recommendation().model_dump()
    values.pop("rationale")

    with pytest.raises(ValidationError):
        CostRecommendation(**values)