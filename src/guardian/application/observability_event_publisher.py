from __future__ import annotations

from abc import ABC, abstractmethod

from guardian.domain.observability_event import (
    ObservabilityEvent,
)


class ObservabilityEventPublisher(ABC):
    """
    Application abstraction for publishing observability events.
    """

    @abstractmethod
    def publish(
        self,
        event: ObservabilityEvent,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def publish_many(
        self,
        events: list[ObservabilityEvent],
    ) -> None:
        raise NotImplementedError