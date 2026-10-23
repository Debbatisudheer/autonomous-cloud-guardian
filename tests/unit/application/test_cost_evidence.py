from guardian.application.cost_evidence import (
    CostEvidenceProvider,
    CostEvidenceResult,
)
from guardian.infrastructure.docker.cost import (
    DockerCostEvidenceProvider,
)


def test_cost_evidence_result_without_evidence():
    result = CostEvidenceResult(
        observation=None,
        evidence_available=False,
        reason="Cost evidence unavailable.",
    )

    assert result.observation is None
    assert result.evidence_available is False
    assert result.reason == "Cost evidence unavailable."


def test_docker_cost_provider_does_not_fabricate_cost():
    provider = DockerCostEvidenceProvider()

    result = provider.get_cost("docker-resource-1")

    assert result.observation is None
    assert result.evidence_available is False
    assert "No real Docker billing" in result.reason


def test_docker_provider_implements_cost_evidence_provider():
    provider = DockerCostEvidenceProvider()

    assert isinstance(provider, CostEvidenceProvider)