from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from guardian.domain.cost import CostObservation


@dataclass(frozen=True)
class CostEvidenceResult:
    observation: CostObservation | None
    evidence_available: bool
    reason: str


class CostEvidenceProvider(ABC):
    @abstractmethod
    def get_cost(self, resource_id: str) -> CostEvidenceResult:
        """Return real cost evidence when available."""
        raise NotImplementedError