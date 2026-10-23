from datetime import UTC, datetime

import pytest

from guardian.domain.cost import (
    CostCategory,
    CostObservation,
    CostSource,
)
from guardian.infrastructure.postgres.cost_storage import (
    PostgreSQLCostStorage,
)


def make_observation(
    resource_id: str = "resource-1",
    amount: float = 12.50,
    observed_at: datetime | None = None,
) -> CostObservation:
    return CostObservation(
        resource_id=resource_id,
        amount=amount,
        currency="USD",
        category=CostCategory.COMPUTE,
        source=CostSource.AWS,
        observed_at=observed_at or datetime.now(UTC),
        evidence_available=True,
        metadata={"billing_source": "provider"},
    )


def test_storage_builds_default_dsn() -> None:
    storage = PostgreSQLCostStorage()

    assert "host=localhost" in storage._dsn
    assert "port=5433" in storage._dsn
    assert "dbname=guardian" in storage._dsn
    assert "user=guardian" in storage._dsn


def test_save_many_empty_list_does_not_fail() -> None:
    storage = PostgreSQLCostStorage()

    storage.save_many([])


def test_invalid_recent_limit_is_rejected() -> None:
    storage = PostgreSQLCostStorage()

    with pytest.raises(ValueError):
        storage.get_recent(0)


def test_invalid_resource_id_is_rejected() -> None:
    storage = PostgreSQLCostStorage()

    with pytest.raises(ValueError):
        storage.get_for_resource("")


def test_invalid_resource_limit_is_rejected() -> None:
    storage = PostgreSQLCostStorage()

    with pytest.raises(ValueError):
        storage.get_for_resource("resource-1", 0)


def test_invalid_time_range_is_rejected() -> None:
    storage = PostgreSQLCostStorage()

    start = datetime(2026, 10, 2, tzinfo=UTC)
    end = datetime(2026, 10, 1, tzinfo=UTC)

    with pytest.raises(ValueError):
        storage.get_between(start, end)


def test_observation_factory_contains_real_cost_evidence() -> None:
    observation = make_observation()

    assert observation.evidence_available is True
    assert observation.amount == 12.50
    assert observation.currency == "USD"
    assert observation.source == CostSource.AWS