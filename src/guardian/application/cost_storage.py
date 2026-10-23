from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from guardian.domain.cost import CostObservation


class CostStorage(ABC):
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the cost storage schema."""
        raise NotImplementedError

    @abstractmethod
    def save(self, observation: CostObservation) -> None:
        """Persist one cost observation."""
        raise NotImplementedError

    @abstractmethod
    def save_many(self, observations: list[CostObservation]) -> None:
        """Persist multiple cost observations."""
        raise NotImplementedError

    @abstractmethod
    def get_recent(self, limit: int = 100) -> list[CostObservation]:
        """Return the most recent cost observations."""
        raise NotImplementedError

    @abstractmethod
    def get_for_resource(
        self,
        resource_id: str,
        limit: int = 100,
    ) -> list[CostObservation]:
        """Return cost observations for one resource."""
        raise NotImplementedError

    @abstractmethod
    def get_between(
        self,
        start: datetime,
        end: datetime,
    ) -> list[CostObservation]:
        """Return cost observations within a time range."""
        raise NotImplementedError