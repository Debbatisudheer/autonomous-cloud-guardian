from unittest.mock import Mock

from guardian.application.security_evidence import (
    SecurityEvidenceProvider,
    SecurityEvidenceResult,
)
from guardian.domain.security import (
    SecurityCategory,
    SecurityEvidence,
    SecuritySource,
)


def test_security_evidence_result() -> None:
    evidence = SecurityEvidence(
        evidence_id="evidence-001",
        resource_id="resource-001",
        category=SecurityCategory.CONTAINER,
        source=SecuritySource.DOCKER,
        evidence_type="container_configuration",
        evidence_available=True,
    )

    result = SecurityEvidenceResult(
        evidence=[evidence],
        evidence_available=True,
        reason="Observed directly from Docker.",
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].resource_id == "resource-001"
    assert result.evidence_available is True


def test_security_evidence_provider_is_abstract() -> None:
    assert SecurityEvidenceProvider.__abstractmethods__ == {
        "collect_for_resource"
    }


def test_mock_provider_contract() -> None:
    provider = Mock(spec=SecurityEvidenceProvider)

    result = SecurityEvidenceResult(
        evidence=[],
        evidence_available=False,
        reason="No evidence available.",
    )

    provider.collect_for_resource.return_value = result

    returned = provider.collect_for_resource("resource-001")

    assert returned.evidence == []
    assert returned.evidence_available is False