from __future__ import annotations

from guardian.application.cost_evidence import (
    CostEvidenceProvider,
    CostEvidenceResult,
)


class DockerCostEvidenceProvider(CostEvidenceProvider):
    def get_cost(self, resource_id: str) -> CostEvidenceResult:
        return CostEvidenceResult(
            observation=None,
            evidence_available=False,
            reason=(
                "No real Docker billing or provider pricing evidence "
                "is available from the local Docker runtime."
            ),
        )