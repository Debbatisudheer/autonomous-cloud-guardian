from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from guardian.domain.security import SecurityEvidence


class SecurityStorage(ABC):
    @abstractmethod
    def initialize(self) -> None:
        """Initialize security evidence storage."""
        raise NotImplementedError

    @abstractmethod
    def save(self, evidence: SecurityEvidence) -> int:
        """Persist one security evidence record."""
        raise NotImplementedError

    @abstractmethod
    def save_many(
        self,
        evidence: list[SecurityEvidence],
    ) -> int:
        """Persist multiple security evidence records."""
        raise NotImplementedError

    @abstractmethod
    def get_recent(
        self,
        limit: int = 100,
    ) -> list[SecurityEvidence]:
        """Retrieve the most recent security evidence."""
        raise NotImplementedError

    @abstractmethod
    def get_for_resource(
        self,
        resource_id: str,
        limit: int = 100,
    ) -> list[SecurityEvidence]:
        """Retrieve security evidence for one resource."""
        raise NotImplementedError

    @abstractmethod
    def get_between(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[SecurityEvidence]:
        """Retrieve security evidence inside a time window."""
        raise NotImplementedError