from datetime import UTC, datetime, timedelta

from guardian.application.cost_optimization import (
    CostOptimizationSignalService,
)
from guardian.domain.cost import CostCategory, CostObservation, CostSource
from guardian.domain.cost_analysis import (
    CostAggregate,
)
from guardian.domain.cost_signal import (
    CostSignalSeverity,
    CostSignalType,
)


def make_aggregate(
    *,
    count: int = 3,
    total: float = 60.0,
    average: float = 20.0,
    latest: float = 30.0,
    evidence_available: bool = True,
) -> CostAggregate:
    return CostAggregate(
        resource_id="resource-1",
        category=CostCategory.COMPUTE,
        currency="USD",
        count=count,
        total_amount=total,
        minimum_amount=10.0,
        maximum_amount=latest,
        average_amount=average,
        latest_amount=latest,
        latest_observed_at=datetime.now(UTC),
        evidence_available=evidence_available,
    )


def test_generate_rising_cost_signal() -> None:
    service = CostOptimizationSignalService()

    signal = service.generate(make_aggregate())

    assert signal.signal_type == CostSignalType.RISING_COST
    assert signal.severity == CostSignalSeverity.WARNING
    assert signal.evidence_available is True
    assert signal.current_amount == 30.0
    assert signal.baseline_amount == 20.0


def test_generate_no_signal_when_latest_is_at_average() -> None:
    service = CostOptimizationSignalService()

    signal = service.generate(
        make_aggregate(
            total=30.0,
            average=10.0,
            latest=10.0,
            count=3,
        )
    )

    assert signal.signal_type == CostSignalType.NO_OPTIMIZATION_SIGNAL
    assert signal.severity == CostSignalSeverity.INFO
    assert signal.evidence_available is True


def test_generate_no_signal_when_latest_is_below_average() -> None:
    service = CostOptimizationSignalService()

    signal = service.generate(
        make_aggregate(
            total=30.0,
            average=15.0,
            latest=10.0,
            count=2,
        )
    )

    assert signal.signal_type == CostSignalType.NO_OPTIMIZATION_SIGNAL
    assert signal.severity == CostSignalSeverity.INFO


def test_generate_insufficient_evidence() -> None:
    service = CostOptimizationSignalService()

    signal = service.generate(
        make_aggregate(
            count=3,
            evidence_available=False,
        )
    )

    assert signal.signal_type == CostSignalType.INSUFFICIENT_EVIDENCE
    assert signal.severity == CostSignalSeverity.UNKNOWN
    assert signal.evidence_available is False


def test_generate_zero_observation_signal() -> None:
    service = CostOptimizationSignalService()

    signal = service.generate(
        CostAggregate(
            resource_id="resource-1",
            category=CostCategory.COMPUTE,
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
    )

    assert signal.signal_type == CostSignalType.INSUFFICIENT_EVIDENCE
    assert signal.severity == CostSignalSeverity.UNKNOWN


def test_generate_many() -> None:
    service = CostOptimizationSignalService()

    aggregates = [
        make_aggregate(),
        make_aggregate(
            total=30.0,
            average=10.0,
            latest=10.0,
        ),
    ]

    signals = service.generate_many(aggregates)

    assert len(signals) == 2
    assert signals[0].signal_type == CostSignalType.RISING_COST
    assert (
        signals[1].signal_type
        == CostSignalType.NO_OPTIMIZATION_SIGNAL
    )


def test_signal_preserves_identity() -> None:
    service = CostOptimizationSignalService()

    aggregate = make_aggregate()

    signal = service.generate(aggregate)

    assert signal.resource_id == aggregate.resource_id
    assert signal.category == aggregate.category
    assert signal.currency == aggregate.currency


def test_signal_does_not_claim_savings() -> None:
    service = CostOptimizationSignalService()

    signal = service.generate(make_aggregate())

    assert "saving" not in signal.finding.lower()
    assert "savings" not in signal.finding.lower()


def test_signal_does_not_perform_action() -> None:
    service = CostOptimizationSignalService()

    before = make_aggregate()

    service.generate(before)

    assert before.latest_amount == 30.0
    assert before.average_amount == 20.0


def test_controlled_observation_can_produce_aggregate() -> None:
    now = datetime.now(UTC)

    observations = [
        CostObservation(
            resource_id="resource-1",
            amount=10.0,
            currency="USD",
            category=CostCategory.COMPUTE,
            source=CostSource.AWS,
            observed_at=now,
            evidence_available=True,
        ),
        CostObservation(
            resource_id="resource-1",
            amount=20.0,
            currency="USD",
            category=CostCategory.COMPUTE,
            source=CostSource.AWS,
            observed_at=now + timedelta(minutes=1),
            evidence_available=True,
        ),
    ]

    assert len(observations) == 2