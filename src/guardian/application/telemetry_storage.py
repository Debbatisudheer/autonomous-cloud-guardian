from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from guardian.domain.telemetry import TelemetryObservation


class TelemetryStorage(ABC):
    """
    Application-level interface for persistent telemetry storage.
    """

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the storage schema if it does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        observation: TelemetryObservation,
    ) -> None:
        """
        Persist one telemetry observation.
        """
        raise NotImplementedError

    @abstractmethod
    def save_many(
        self,
        observations: list[TelemetryObservation],
    ) -> None:
        """
        Persist multiple telemetry observations atomically.
        """
        raise NotImplementedError

    @abstractmethod
    def get_recent(
        self,
        limit: int = 100,
    ) -> list[TelemetryObservation]:
        """
        Retrieve the most recent observations.
        """
        raise NotImplementedError

    @abstractmethod
    def get_for_resource(
        self,
        resource_id: str,
        limit: int = 100,
    ) -> list[TelemetryObservation]:
        """
        Retrieve recent observations for one resource.
        """
        raise NotImplementedError

    @abstractmethod
    def get_for_resource_and_metric(
        self,
        resource_id: str,
        metric: str,
        limit: int = 100,
    ) -> list[TelemetryObservation]:
        """
        Retrieve recent observations for one resource and metric.
        """
        raise NotImplementedError

    @abstractmethod
    def get_between(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[TelemetryObservation]:
        """
        Retrieve observations inside a time range.
        """
        raise NotImplementedError