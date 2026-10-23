from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from guardian.domain.security import SecurityEvidence


@dataclass(frozen=True)
class SecurityEvidenceResult:
    evidence: list[SecurityEvidence]
    evidence_available: bool
    reason: str


class SecurityEvidenceProvider(ABC):
    @abstractmethod
    def collect_for_resource(
        self,
        resource_id: str,
    ) -> SecurityEvidenceResult:
        """Collect security evidence for a resource."""
        raise NotImplementedError