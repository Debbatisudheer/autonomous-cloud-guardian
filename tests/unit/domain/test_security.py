from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from guardian.domain.security import (
    SecurityCategory,
    SecurityEvidence,
    SecurityFinding,
    SecuritySeverity,
    SecuritySource,
)


def test_security_severity_values() -> None:
    assert SecuritySeverity.UNKNOWN.value == "unknown"
    assert SecuritySeverity.INFO.value == "info"
    assert SecuritySeverity.LOW.value == "low"
    assert SecuritySeverity.MEDIUM.value == "medium"
    assert SecuritySeverity.HIGH.value == "high"
    assert SecuritySeverity.CRITICAL.value == "critical"


def test_security_category_values() -> None:
    assert SecurityCategory.CONFIGURATION.value == "configuration"
    assert SecurityCategory.ACCESS_CONTROL.value == "access_control"
    assert SecurityCategory.NETWORK.value == "network"
    assert SecurityCategory.CONTAINER.value == "container"
    assert SecurityCategory.IMAGE.value == "image"
    assert SecurityCategory.SECRETS.value == "secrets"
    assert SecurityCategory.VULNERABILITY.value == "vulnerability"
    assert SecurityCategory.COMPLIANCE.value == "compliance"
    assert SecurityCategory.UNKNOWN.value == "unknown"


def test_security_source_values() -> None:
    assert SecuritySource.DOCKER.value == "docker"
    assert SecuritySource.KUBERNETES.value == "kubernetes"
    assert SecuritySource.TERRAFORM.value == "terraform"
    assert SecuritySource.AWS.value == "aws"
    assert SecuritySource.UNKNOWN.value == "unknown"


def test_security_evidence_creation() -> None:
    observed_at = datetime(2026, 10, 23, 10, 0, tzinfo=UTC)

    evidence = SecurityEvidence(
        evidence_id="evidence-001",
        resource_id="resource-001",
        category=SecurityCategory.CONFIGURATION,
        source=SecuritySource.DOCKER,
        evidence_type="container_configuration",
        observed_at=observed_at,
        evidence_available=True,
        details={
            "runtime": "docker",
            "property": "healthcheck",
        },
    )

    assert evidence.evidence_id == "evidence-001"
    assert evidence.resource_id == "resource-001"
    assert evidence.category == SecurityCategory.CONFIGURATION
    assert evidence.source == SecuritySource.DOCKER
    assert evidence.evidence_type == "container_configuration"
    assert evidence.observed_at == observed_at
    assert evidence.evidence_available is True
    assert evidence.details["runtime"] == "docker"


def test_security_evidence_default_timestamp() -> None:
    evidence = SecurityEvidence(
        evidence_id="evidence-002",
        resource_id="resource-002",
        category=SecurityCategory.CONTAINER,
        source=SecuritySource.DOCKER,
        evidence_type="container_state",
        evidence_available=False,
    )

    assert evidence.observed_at.tzinfo is not None


def test_security_evidence_allows_unavailable_evidence() -> None:
    evidence = SecurityEvidence(
        evidence_id="evidence-003",
        resource_id="resource-003",
        category=SecurityCategory.VULNERABILITY,
        source=SecuritySource.DOCKER,
        evidence_type="vulnerability_scan",
        evidence_available=False,
    )

    assert evidence.evidence_available is False
    assert evidence.details == {}


def test_security_evidence_requires_resource_id() -> None:
    with pytest.raises(ValidationError):
        SecurityEvidence(
            evidence_id="evidence-004",
            resource_id="",
            category=SecurityCategory.NETWORK,
            source=SecuritySource.DOCKER,
            evidence_type="network_configuration",
            evidence_available=True,
        )


def test_security_evidence_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SecurityEvidence(
            evidence_id="evidence-005",
            resource_id="resource-005",
            category=SecurityCategory.NETWORK,
            source=SecuritySource.DOCKER,
            evidence_type="network_configuration",
            evidence_available=True,
            fabricated_finding="critical",
        )


def test_security_finding_creation() -> None:
    finding = SecurityFinding(
        finding_id="finding-001",
        resource_id="resource-001",
        category=SecurityCategory.CONFIGURATION,
        severity=SecuritySeverity.MEDIUM,
        source=SecuritySource.DOCKER,
        title="Configuration requires review",
        description="Observed configuration evidence requires security review.",
        evidence_id="evidence-001",
        evidence_available=True,
        metadata={
            "assessment": "configuration_review",
        },
    )

    assert finding.finding_id == "finding-001"
    assert finding.resource_id == "resource-001"
    assert finding.category == SecurityCategory.CONFIGURATION
    assert finding.severity == SecuritySeverity.MEDIUM
    assert finding.source == SecuritySource.DOCKER
    assert finding.evidence_id == "evidence-001"
    assert finding.evidence_available is True
    assert finding.metadata["assessment"] == "configuration_review"


def test_security_finding_can_have_no_resource() -> None:
    finding = SecurityFinding(
        finding_id="finding-002",
        resource_id=None,
        category=SecurityCategory.UNKNOWN,
        severity=SecuritySeverity.UNKNOWN,
        source=SecuritySource.UNKNOWN,
        title="Security evidence unavailable",
        description="No security evidence is currently available.",
        evidence_id=None,
        evidence_available=False,
    )

    assert finding.resource_id is None
    assert finding.evidence_id is None
    assert finding.evidence_available is False


def test_security_finding_default_timestamp() -> None:
    finding = SecurityFinding(
        finding_id="finding-003",
        category=SecurityCategory.COMPLIANCE,
        severity=SecuritySeverity.INFO,
        source=SecuritySource.TERRAFORM,
        title="Compliance evidence recorded",
        description="Configuration evidence was recorded for assessment.",
        evidence_available=True,
    )

    assert finding.detected_at.tzinfo is not None


def test_security_finding_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SecurityFinding(
            finding_id="finding-004",
            category=SecurityCategory.SECRETS,
            severity=SecuritySeverity.HIGH,
            source=SecuritySource.DOCKER,
            title="Potential issue",
            description="Requires investigation.",
            evidence_available=True,
            remediation_executed=True,
        )