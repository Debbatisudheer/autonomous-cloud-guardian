from __future__ import annotations

from guardian.domain.cost_analysis import CostAggregate
from guardian.domain.cost_signal import (
    CostOptimizationSignal,
    CostSignalSeverity,
    CostSignalType,
)


class CostOptimizationSignalService:
    """Generates evidence-backed cost optimization signals.

    This service does not predict costs, recommend actions,
    or modify infrastructure.
    """

    def generate(
        self,
        aggregate: CostAggregate,
    ) -> CostOptimizationSignal:
        if aggregate.count == 0:
            return CostOptimizationSignal(
                signal_type=CostSignalType.INSUFFICIENT_EVIDENCE,
                severity=CostSignalSeverity.UNKNOWN,
                resource_id=aggregate.resource_id,
                category=aggregate.category,
                currency=aggregate.currency,
                current_amount=aggregate.latest_amount,
                baseline_amount=aggregate.average_amount,
                evidence_available=False,
                observation_count=aggregate.count,
                finding="No cost observations are available.",
            )

        if not aggregate.evidence_available:
            return CostOptimizationSignal(
                signal_type=CostSignalType.INSUFFICIENT_EVIDENCE,
                severity=CostSignalSeverity.UNKNOWN,
                resource_id=aggregate.resource_id,
                category=aggregate.category,
                currency=aggregate.currency,
                current_amount=aggregate.latest_amount,
                baseline_amount=aggregate.average_amount,
                evidence_available=False,
                observation_count=aggregate.count,
                finding=(
                    "Cost observations exist, but reliable billing "
                    "evidence is unavailable."
                ),
            )

        if (
            aggregate.latest_amount > aggregate.average_amount
            and aggregate.count >= 2
        ):
            return CostOptimizationSignal(
                signal_type=CostSignalType.RISING_COST,
                severity=CostSignalSeverity.WARNING,
                resource_id=aggregate.resource_id,
                category=aggregate.category,
                currency=aggregate.currency,
                current_amount=aggregate.latest_amount,
                baseline_amount=aggregate.average_amount,
                evidence_available=True,
                observation_count=aggregate.count,
                finding=(
                    "The latest observed cost is above the "
                    "available historical average."
                ),
            )

        return CostOptimizationSignal(
            signal_type=CostSignalType.NO_OPTIMIZATION_SIGNAL,
            severity=CostSignalSeverity.INFO,
            resource_id=aggregate.resource_id,
            category=aggregate.category,
            currency=aggregate.currency,
            current_amount=aggregate.latest_amount,
            baseline_amount=aggregate.average_amount,
            evidence_available=True,
            observation_count=aggregate.count,
            finding=(
                "Available cost evidence does not currently "
                "produce an optimization signal."
            ),
        )

    def generate_many(
        self,
        aggregates: list[CostAggregate],
    ) -> list[CostOptimizationSignal]:
        return [self.generate(aggregate) for aggregate in aggregates]