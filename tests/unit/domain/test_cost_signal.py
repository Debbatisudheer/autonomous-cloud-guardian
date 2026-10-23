from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from guardian.domain.cost import CostCategory
from guardian.domain.cost_signal import (
    CostOptimizationSignal,
    CostSignalSeverity,
    CostSignalType,
)


def test_cost_signal_model() -> None:
    signal = CostOptimizationSignal(
        signal_type=CostSignalType.RISING_COST,
        severity=CostSignalSeverity.WARNING,
        resource_id="resource-1",
        category=CostCategory.COMPUTE,
        currency="USD",
        current_amount=30.0,
        baseline_amount=20.0,
        evidence_available=True,
        observation_count=3,
        finding="Latest cost is above average.",
    )

    assert signal.signal_type == CostSignalType.RISING_COST
    assert signal.severity == CostSignalSeverity.WARNING
    assert signal.resource_id == "resource-1"
    assert signal.category == CostCategory.COMPUTE
    assert signal.currency == "USD"
    assert signal.current_amount == 30.0
    assert signal.baseline_amount == 20.0
    assert signal.evidence_available is True
    assert signal.observation_count == 3


def test_cost_signal_allows_optional_resource_and_category() -> None:
    signal = CostOptimizationSignal(
        signal_type=CostSignalType.INSUFFICIENT_EVIDENCE,
        severity=CostSignalSeverity.UNKNOWN,
        currency="USD",
        current_amount=0.0,
        baseline_amount=0.0,
        evidence_available=False,
        observation_count=0,
        finding="No evidence.",
    )

    assert signal.resource_id is None
    assert signal.category is None


def test_cost_signal_rejects_negative_current_amount() -> None:
    with pytest.raises(ValidationError):
        CostOptimizationSignal(
            signal_type=CostSignalType.RISING_COST,
            severity=CostSignalSeverity.WARNING,
            currency="USD",
            current_amount=-1.0,
            baseline_amount=0.0,
            evidence_available=True,
            observation_count=1,
            finding="Invalid.",
        )


def test_cost_signal_rejects_negative_baseline_amount() -> None:
    with pytest.raises(ValidationError):
        CostOptimizationSignal(
            signal_type=CostSignalType.RISING_COST,
            severity=CostSignalSeverity.WARNING,
            currency="USD",
            current_amount=10.0,
            baseline_amount=-1.0,
            evidence_available=True,
            observation_count=1,
            finding="Invalid.",
        )


def test_cost_signal_rejects_negative_observation_count() -> None:
    with pytest.raises(ValidationError):
        CostOptimizationSignal(
            signal_type=CostSignalType.RISING_COST,
            severity=CostSignalSeverity.WARNING,
            currency="USD",
            current_amount=10.0,
            baseline_amount=5.0,
            evidence_available=True,
            observation_count=-1,
            finding="Invalid.",
        )


def test_cost_signal_generated_at_is_datetime() -> None:
    signal = CostOptimizationSignal(
        signal_type=CostSignalType.NO_OPTIMIZATION_SIGNAL,
        severity=CostSignalSeverity.INFO,
        currency="USD",
        current_amount=10.0,
        baseline_amount=10.0,
        evidence_available=True,
        observation_count=1,
        finding="No signal.",
    )

    assert isinstance(signal.generated_at, datetime)
    assert signal.generated_at.tzinfo == UTC


def test_cost_signal_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        CostOptimizationSignal(
            signal_type=CostSignalType.NO_OPTIMIZATION_SIGNAL,
            severity=CostSignalSeverity.INFO,
            currency="USD",
            current_amount=10.0,
            baseline_amount=10.0,
            evidence_available=True,
            observation_count=1,
            finding="No signal.",
            unexpected="value",
        )