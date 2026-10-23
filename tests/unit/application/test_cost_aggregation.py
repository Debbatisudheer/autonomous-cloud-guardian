from datetime import UTC, datetime, timedelta

import pytest

from guardian.application.cost_aggregation import CostAggregationService
from guardian.domain.cost import CostCategory, CostObservation, CostSource
from guardian.domain.cost_analysis import CostAnalysisLevel


def make_observation(
    resource_id: str,
    amount: float,
    observed_at: datetime,
    *,
    category: CostCategory = CostCategory.COMPUTE,
    currency: str = "USD",
    evidence_available: bool = True,
) -> CostObservation:
    return CostObservation(
        resource_id=resource_id,
        amount=amount,
        currency=currency,
        category=category,
        source=CostSource.AWS,
        observed_at=observed_at,
        evidence_available=evidence_available,
    )


def test_aggregate_groups_by_resource_category_and_currency() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    observations = [
        make_observation("resource-1", 10.0, now),
        make_observation("resource-1", 20.0, now + timedelta(minutes=1)),
        make_observation("resource-2", 50.0, now),
    ]

    aggregates = service.aggregate(observations)

    assert len(aggregates) == 2

    resource_one = next(
        item
        for item in aggregates
        if item.resource_id == "resource-1"
    )

    assert resource_one.count == 2
    assert resource_one.total_amount == 30.0
    assert resource_one.minimum_amount == 10.0
    assert resource_one.maximum_amount == 20.0
    assert resource_one.average_amount == 15.0
    assert resource_one.latest_amount == 20.0
    assert resource_one.evidence_available is True


def test_aggregate_separates_categories() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    observations = [
        make_observation(
            "resource-1",
            10.0,
            now,
            category=CostCategory.COMPUTE,
        ),
        make_observation(
            "resource-1",
            25.0,
            now + timedelta(minutes=1),
            category=CostCategory.STORAGE,
        ),
    ]

    aggregates = service.aggregate(observations)

    assert len(aggregates) == 2


def test_aggregate_separates_currencies() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    observations = [
        make_observation(
            "resource-1",
            10.0,
            now,
            currency="USD",
        ),
        make_observation(
            "resource-1",
            1000.0,
            now + timedelta(minutes=1),
            currency="INR",
        ),
    ]

    aggregates = service.aggregate(observations)

    assert len(aggregates) == 2

    currencies = {item.currency for item in aggregates}

    assert currencies == {"USD", "INR"}


def test_aggregate_empty_returns_empty_list() -> None:
    service = CostAggregationService()

    assert service.aggregate([]) == []


def test_aggregate_for_resource() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    observations = [
        make_observation("resource-1", 10.0, now),
        make_observation(
            "resource-2",
            20.0,
            now + timedelta(minutes=1),
        ),
    ]

    aggregates = service.aggregate_for_resource(
        observations,
        "resource-1",
    )

    assert len(aggregates) == 1
    assert aggregates[0].resource_id == "resource-1"
    assert aggregates[0].total_amount == 10.0


def test_aggregate_for_resource_rejects_empty_resource_id() -> None:
    service = CostAggregationService()

    with pytest.raises(ValueError, match="resource_id"):
        service.aggregate_for_resource([], "")


def test_aggregate_for_category() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    observations = [
        make_observation(
            "resource-1",
            10.0,
            now,
            category=CostCategory.COMPUTE,
        ),
        make_observation(
            "resource-2",
            20.0,
            now + timedelta(minutes=1),
            category=CostCategory.STORAGE,
        ),
    ]

    aggregates = service.aggregate_for_category(
        observations,
        CostCategory.COMPUTE,
    )

    assert len(aggregates) == 1
    assert aggregates[0].category == CostCategory.COMPUTE
    assert aggregates[0].total_amount == 10.0


def test_aggregate_between_uses_inclusive_window() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    observations = [
        make_observation("resource-1", 10.0, now),
        make_observation(
            "resource-1",
            20.0,
            now + timedelta(minutes=5),
        ),
        make_observation(
            "resource-1",
            30.0,
            now + timedelta(minutes=10),
        ),
    ]

    aggregates = service.aggregate_between(
        observations,
        start=now,
        end=now + timedelta(minutes=5),
    )

    assert len(aggregates) == 1
    assert aggregates[0].count == 2
    assert aggregates[0].total_amount == 30.0


def test_aggregate_between_rejects_invalid_window() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    with pytest.raises(
        ValueError,
        match="greater than or equal",
    ):
        service.aggregate_between(
            [],
            start=now + timedelta(minutes=1),
            end=now,
        )


def test_analysis_normal_when_latest_is_not_above_average() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    observations = [
        make_observation("resource-1", 20.0, now),
        make_observation(
            "resource-1",
            10.0,
            now + timedelta(minutes=1),
        ),
    ]

    aggregate = service.aggregate(observations)[0]

    analysis = service.analyze(aggregate)

    assert analysis.level == CostAnalysisLevel.NORMAL
    assert analysis.evidence_available is True
    assert analysis.latest_amount == 10.0


def test_analysis_elevated_when_latest_is_above_average() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    observations = [
        make_observation("resource-1", 10.0, now),
        make_observation(
            "resource-1",
            30.0,
            now + timedelta(minutes=1),
        ),
    ]

    aggregate = service.aggregate(observations)[0]

    analysis = service.analyze(aggregate)

    assert analysis.level == CostAnalysisLevel.ELEVATED
    assert analysis.evidence_available is True
    assert analysis.latest_amount == 30.0


def test_analysis_marks_missing_evidence_unknown() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    observations = [
        make_observation(
            "resource-1",
            10.0,
            now,
            evidence_available=False,
        ),
        make_observation(
            "resource-1",
            20.0,
            now + timedelta(minutes=1),
            evidence_available=False,
        ),
    ]

    aggregate = service.aggregate(observations)[0]

    analysis = service.analyze(aggregate)

    assert analysis.level == CostAnalysisLevel.UNKNOWN
    assert analysis.evidence_available is False
    assert "billing evidence" in analysis.finding


def test_analyze_many() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    observations = [
        make_observation("resource-1", 10.0, now),
        make_observation(
            "resource-2",
            20.0,
            now + timedelta(minutes=1),
        ),
    ]

    aggregates = service.aggregate(observations)
    analyses = service.analyze_many(aggregates)

    assert len(analyses) == 2
    assert all(
        analysis.observation_count == 1
        for analysis in analyses
    )


def test_aggregate_latest_observation_is_selected_by_timestamp() -> None:
    service = CostAggregationService()

    now = datetime.now(UTC)

    observations = [
        make_observation(
            "resource-1",
            100.0,
            now + timedelta(minutes=10),
        ),
        make_observation(
            "resource-1",
            50.0,
            now,
        ),
    ]

    aggregate = service.aggregate(observations)[0]

    assert aggregate.latest_amount == 100.0
    assert aggregate.latest_observed_at == now + timedelta(minutes=10)


def test_aggregate_requires_observations_for_internal_builder() -> None:
    with pytest.raises(
        ValueError,
        match="empty observations",
    ):
        CostAggregationService._build_aggregate(
            [],
            resource_id="resource-1",
            category=CostCategory.COMPUTE,
            currency="USD",
        )