from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from guardian.domain.cost import (
    CostCategory,
    CostObservation,
    CostSource,
)


def test_cost_observation_defaults():
    observation = CostObservation(
        resource_id="resource-1",
        amount=12.50,
        currency="USD",
    )

    assert observation.resource_id == "resource-1"
    assert observation.amount == 12.50
    assert observation.currency == "USD"
    assert observation.category == CostCategory.UNKNOWN
    assert observation.source == CostSource.UNKNOWN
    assert observation.evidence_available is False
    assert observation.metadata == {}
    assert observation.observed_at.tzinfo == UTC


def test_cost_observation_with_full_evidence():
    start = datetime(2026, 10, 1, tzinfo=UTC)
    end = datetime(2026, 10, 31, tzinfo=UTC)

    observation = CostObservation(
        resource_id="docker-container-1",
        amount=25.75,
        currency="USD",
        category=CostCategory.COMPUTE,
        source=CostSource.AWS,
        observed_at=end,
        billing_period_start=start,
        billing_period_end=end,
        evidence_available=True,
        metadata={"billing_source": "provider"},
    )

    assert observation.amount == 25.75
    assert observation.category == CostCategory.COMPUTE
    assert observation.source == CostSource.AWS
    assert observation.billing_period_start == start
    assert observation.billing_period_end == end
    assert observation.evidence_available is True
    assert observation.metadata["billing_source"] == "provider"


def test_cost_amount_cannot_be_negative():
    with pytest.raises(ValidationError):
        CostObservation(
            resource_id="resource-1",
            amount=-1.0,
            currency="USD",
        )


def test_resource_id_cannot_be_empty():
    with pytest.raises(ValidationError):
        CostObservation(
            resource_id="",
            amount=1.0,
            currency="USD",
        )


def test_currency_cannot_be_empty():
    with pytest.raises(ValidationError):
        CostObservation(
            resource_id="resource-1",
            amount=1.0,
            currency="",
        )


def test_extra_fields_are_rejected():
    with pytest.raises(ValidationError):
        CostObservation(
            resource_id="resource-1",
            amount=1.0,
            currency="USD",
            unexpected_field="value",
        )


def test_cost_categories():
    assert CostCategory.COMPUTE.value == "compute"
    assert CostCategory.STORAGE.value == "storage"
    assert CostCategory.NETWORK.value == "network"
    assert CostCategory.DATABASE.value == "database"
    assert CostCategory.UNKNOWN.value == "unknown"


def test_cost_sources():
    assert CostSource.DOCKER.value == "docker"
    assert CostSource.KUBERNETES.value == "kubernetes"
    assert CostSource.AWS.value == "aws"
    assert CostSource.UNKNOWN.value == "unknown"