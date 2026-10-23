from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from guardian.domain.cost import CostCategory
from guardian.domain.cost_analysis import (
    CostAggregate,
    CostAnalysis,
    CostAnalysisLevel,
)


def test_cost_aggregate_defaults_and_fields() -> None:
    observed_at = datetime.now(UTC)

    aggregate = CostAggregate(
        resource_id="resource-1",
        category=CostCategory.COMPUTE,
        currency="USD",
        count=3,
        total_amount=30.0,
        minimum_amount=5.0,
        maximum_amount=15.0,
        average_amount=10.0,
        latest_amount=15.0,
        latest_observed_at=observed_at,
        evidence_available=True,
    )

    assert aggregate.resource_id == "resource-1"
    assert aggregate.category == CostCategory.COMPUTE
    assert aggregate.currency == "USD"
    assert aggregate.count == 3
    assert aggregate.total_amount == 30.0
    assert aggregate.minimum_amount == 5.0
    assert aggregate.maximum_amount == 15.0
    assert aggregate.average_amount == 10.0
    assert aggregate.latest_amount == 15.0
    assert aggregate.evidence_available is True


def test_cost_aggregate_allows_resource_and_category_to_be_none() -> None:
    aggregate = CostAggregate(
        currency="USD",
        count=0,
        total_amount=0.0,
        minimum_amount=0.0,
        maximum_amount=0.0,
        average_amount=0.0,
        latest_amount=0.0,
        latest_observed_at=datetime.now(UTC),
        evidence_available=False,
    )

    assert aggregate.resource_id is None
    assert aggregate.category is None


def test_cost_aggregate_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        CostAggregate(
            currency="USD",
            count=1,
            total_amount=-1.0,
            minimum_amount=0.0,
            maximum_amount=0.0,
            average_amount=0.0,
            latest_amount=0.0,
            latest_observed_at=datetime.now(UTC),
        )


def test_cost_analysis_model() -> None:
    analysis = CostAnalysis(
        resource_id="resource-1",
        category=CostCategory.COMPUTE,
        currency="USD",
        level=CostAnalysisLevel.NORMAL,
        total_amount=100.0,
        average_amount=20.0,
        latest_amount=20.0,
        observation_count=5,
        evidence_available=True,
        finding="Cost is within the available evidence.",
    )

    assert analysis.resource_id == "resource-1"
    assert analysis.category == CostCategory.COMPUTE
    assert analysis.currency == "USD"
    assert analysis.level == CostAnalysisLevel.NORMAL
    assert analysis.total_amount == 100.0
    assert analysis.average_amount == 20.0
    assert analysis.latest_amount == 20.0
    assert analysis.observation_count == 5
    assert analysis.evidence_available is True


def test_cost_analysis_rejects_negative_observation_count() -> None:
    with pytest.raises(ValidationError):
        CostAnalysis(
            currency="USD",
            level=CostAnalysisLevel.UNKNOWN,
            total_amount=0.0,
            average_amount=0.0,
            latest_amount=0.0,
            observation_count=-1,
            evidence_available=False,
            finding="No evidence.",
        )


def test_cost_analysis_requires_finding() -> None:
    with pytest.raises(ValidationError):
        CostAnalysis(
            currency="USD",
            level=CostAnalysisLevel.UNKNOWN,
            total_amount=0.0,
            average_amount=0.0,
            latest_amount=0.0,
            observation_count=0,
            evidence_available=False,
        )


def test_cost_aggregate_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        CostAggregate(
            currency="USD",
            count=1,
            total_amount=10.0,
            minimum_amount=10.0,
            maximum_amount=10.0,
            average_amount=10.0,
            latest_amount=10.0,
            latest_observed_at=datetime.now(UTC),
            unexpected="value",
        )