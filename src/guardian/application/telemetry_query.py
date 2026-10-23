from __future__ import annotations

from datetime import datetime

from guardian.application.telemetry_storage import TelemetryStorage
from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
)


class TelemetryQueryService:
    """
    Application-level query service for telemetry.

    This service coordinates telemetry retrieval through the
    TelemetryStorage abstraction. It does not access PostgreSQL
    directly and does not generate or modify telemetry.
    """

    def __init__(
        self,
        storage: TelemetryStorage,
    ) -> None:
        self._storage = storage

    def get_recent(
        self,
        limit: int = 100,
    ) -> list[TelemetryObservation]:
        """
        Retrieve the most recent telemetry observations.
        """

        self._validate_limit(limit)

        return self._storage.get_recent(
            limit=limit,
        )

    def get_for_resource(
        self,
        resource_id: str,
        limit: int = 100,
    ) -> list[TelemetryObservation]:
        """
        Retrieve telemetry for one resource.
        """

        self._validate_resource_id(resource_id)
        self._validate_limit(limit)

        return self._storage.get_for_resource(
            resource_id=resource_id,
            limit=limit,
        )

    def get_for_resource_and_metric(
        self,
        resource_id: str,
        metric: TelemetryMetric | str,
        limit: int = 100,
    ) -> list[TelemetryObservation]:
        """
        Retrieve telemetry for one resource and one metric.
        """

        self._validate_resource_id(resource_id)
        self._validate_limit(limit)

        metric_value = self._normalize_metric(metric)

        return self._storage.get_for_resource_and_metric(
            resource_id=resource_id,
            metric=metric_value,
            limit=limit,
        )

    def get_between(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[TelemetryObservation]:
        """
        Retrieve telemetry inside an inclusive time range.
        """

        self._validate_limit(limit)

        if end < start:
            raise ValueError(
                "Query end time must not be before start time."
            )

        return self._storage.get_between(
            start=start,
            end=end,
            limit=limit,
        )

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if limit <= 0:
            raise ValueError(
                "Query limit must be greater than zero."
            )

    @staticmethod
    def _validate_resource_id(
        resource_id: str,
    ) -> None:
        if not resource_id.strip():
            raise ValueError(
                "Resource ID must not be empty."
            )

    @staticmethod
    def _normalize_metric(
        metric: TelemetryMetric | str,
    ) -> str:
        if isinstance(metric, TelemetryMetric):
            return metric.value

        if not metric.strip():
            raise ValueError(
                "Metric must not be empty."
            )

        valid_metrics = {
            telemetry_metric.value
            for telemetry_metric in TelemetryMetric
        }

        if metric not in valid_metrics:
            raise ValueError(
                f"Unsupported telemetry metric: {metric}"
            )

        return metric