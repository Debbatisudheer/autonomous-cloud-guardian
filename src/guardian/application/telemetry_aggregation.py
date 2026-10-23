from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from guardian.domain.telemetry import TelemetryMetric, TelemetryObservation


@dataclass(frozen=True)
class TelemetryAggregate:
    """
    Statistical aggregate calculated from real telemetry observations.

    The aggregate contains descriptive statistics only. It does not
    represent a prediction, recommendation, or health assessment.
    """

    resource_id: str
    metric: TelemetryMetric

    count: int
    minimum: float
    maximum: float
    average: float

    latest: float
    latest_observed_at: datetime


class TelemetryAggregator:
    """
    Aggregates evidence-backed telemetry observations.

    This class does not collect telemetry and does not persist telemetry.
    It operates only on observations supplied by the caller.
    """

    def aggregate(
        self,
        observations: list[TelemetryObservation],
    ) -> list[TelemetryAggregate]:
        """
        Aggregate observations by resource and metric.
        """

        if not observations:
            return []

        grouped: dict[
            tuple[str, TelemetryMetric],
            list[TelemetryObservation],
        ] = defaultdict(list)

        for observation in observations:
            grouped[
                (
                    observation.resource_id,
                    observation.metric,
                )
            ].append(observation)

        aggregates: list[TelemetryAggregate] = []

        for (
            resource_id,
            metric,
        ), grouped_observations in grouped.items():

            ordered = sorted(
                grouped_observations,
                key=lambda observation: observation.observed_at,
            )

            values = [
                observation.value
                for observation in ordered
            ]

            latest_observation = ordered[-1]

            aggregates.append(
                TelemetryAggregate(
                    resource_id=resource_id,
                    metric=metric,
                    count=len(values),
                    minimum=min(values),
                    maximum=max(values),
                    average=sum(values) / len(values),
                    latest=latest_observation.value,
                    latest_observed_at=(
                        latest_observation.observed_at
                    ),
                )
            )

        return sorted(
            aggregates,
            key=lambda aggregate: (
                aggregate.resource_id,
                aggregate.metric.value,
            ),
        )

    def aggregate_for_resource(
        self,
        observations: list[TelemetryObservation],
        resource_id: str,
    ) -> list[TelemetryAggregate]:
        """
        Aggregate telemetry for one resource.
        """

        resource_observations = [
            observation
            for observation in observations
            if observation.resource_id == resource_id
        ]

        return self.aggregate(resource_observations)

    def aggregate_for_metric(
        self,
        observations: list[TelemetryObservation],
        metric: TelemetryMetric,
    ) -> list[TelemetryAggregate]:
        """
        Aggregate telemetry for one metric across resources.
        """

        metric_observations = [
            observation
            for observation in observations
            if observation.metric == metric
        ]

        return self.aggregate(metric_observations)

    def aggregate_between(
        self,
        observations: list[TelemetryObservation],
        start: datetime,
        end: datetime,
    ) -> list[TelemetryAggregate]:
        """
        Aggregate telemetry within an inclusive time window.
        """

        if end < start:
            raise ValueError(
                "Aggregation end time must not be before start time."
            )

        window_observations = [
            observation
            for observation in observations
            if start
            <= observation.observed_at
            <= end
        ]

        return self.aggregate(window_observations)