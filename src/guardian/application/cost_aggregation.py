from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from guardian.domain.cost import CostCategory, CostObservation
from guardian.domain.cost_analysis import (
    CostAggregate,
    CostAnalysis,
    CostAnalysisLevel,
)


class CostAggregationService:
    """Aggregates and analyzes evidence-backed cost observations."""

    def aggregate(
        self,
        observations: list[CostObservation],
    ) -> list[CostAggregate]:
        if not observations:
            return []

        groups: dict[
            tuple[str, CostCategory, str],
            list[CostObservation],
        ] = defaultdict(list)

        for observation in observations:
            groups[
                (
                    observation.resource_id,
                    observation.category,
                    observation.currency,
                )
            ].append(observation)

        return [
            self._build_aggregate(
                group_observations,
                resource_id=key[0],
                category=key[1],
                currency=key[2],
            )
            for key, group_observations in groups.items()
        ]

    def aggregate_for_resource(
        self,
        observations: list[CostObservation],
        resource_id: str,
    ) -> list[CostAggregate]:
        if not resource_id:
            raise ValueError("resource_id must not be empty.")

        filtered = [
            observation
            for observation in observations
            if observation.resource_id == resource_id
        ]

        return self.aggregate(filtered)

    def aggregate_for_category(
        self,
        observations: list[CostObservation],
        category: CostCategory,
    ) -> list[CostAggregate]:
        filtered = [
            observation
            for observation in observations
            if observation.category == category
        ]

        return self.aggregate(filtered)

    def aggregate_between(
        self,
        observations: list[CostObservation],
        start: datetime,
        end: datetime,
    ) -> list[CostAggregate]:
        if end < start:
            raise ValueError("end must be greater than or equal to start.")

        filtered = [
            observation
            for observation in observations
            if start <= observation.observed_at <= end
        ]

        return self.aggregate(filtered)

    def analyze(
        self,
        aggregate: CostAggregate,
    ) -> CostAnalysis:
        if aggregate.count == 0:
            return CostAnalysis(
                resource_id=aggregate.resource_id,
                category=aggregate.category,
                currency=aggregate.currency,
                level=CostAnalysisLevel.UNKNOWN,
                total_amount=aggregate.total_amount,
                average_amount=aggregate.average_amount,
                latest_amount=aggregate.latest_amount,
                observation_count=aggregate.count,
                evidence_available=False,
                finding="No cost observations are available.",
            )

        if not aggregate.evidence_available:
            return CostAnalysis(
                resource_id=aggregate.resource_id,
                category=aggregate.category,
                currency=aggregate.currency,
                level=CostAnalysisLevel.UNKNOWN,
                total_amount=aggregate.total_amount,
                average_amount=aggregate.average_amount,
                latest_amount=aggregate.latest_amount,
                observation_count=aggregate.count,
                evidence_available=False,
                finding=(
                    "Cost observations exist, but billing evidence "
                    "is unavailable."
                ),
            )

        if aggregate.latest_amount > aggregate.average_amount:
            level = CostAnalysisLevel.ELEVATED
            finding = (
                "Latest observed cost is above the available "
                "average cost."
            )
        else:
            level = CostAnalysisLevel.NORMAL
            finding = (
                "Available cost evidence does not indicate "
                "an elevated latest cost."
            )

        return CostAnalysis(
            resource_id=aggregate.resource_id,
            category=aggregate.category,
            currency=aggregate.currency,
            level=level,
            total_amount=aggregate.total_amount,
            average_amount=aggregate.average_amount,
            latest_amount=aggregate.latest_amount,
            observation_count=aggregate.count,
            evidence_available=True,
            finding=finding,
        )

    def analyze_many(
        self,
        aggregates: list[CostAggregate],
    ) -> list[CostAnalysis]:
        return [self.analyze(aggregate) for aggregate in aggregates]

    @staticmethod
    def _build_aggregate(
        observations: list[CostObservation],
        resource_id: str,
        category: CostCategory,
        currency: str,
    ) -> CostAggregate:
        if not observations:
            raise ValueError(
                "Cannot build an aggregate from empty observations."
            )

        amounts = [observation.amount for observation in observations]

        latest = max(
            observations,
            key=lambda observation: observation.observed_at,
        )

        return CostAggregate(
            resource_id=resource_id,
            category=category,
            currency=currency,
            count=len(observations),
            total_amount=sum(amounts),
            minimum_amount=min(amounts),
            maximum_amount=max(amounts),
            average_amount=sum(amounts) / len(amounts),
            latest_amount=latest.amount,
            latest_observed_at=latest.observed_at,
            evidence_available=all(
                observation.evidence_available
                for observation in observations
            ),
        )