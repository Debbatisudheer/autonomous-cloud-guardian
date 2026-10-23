from datetime import UTC, datetime

from guardian.application.security_assessment import (
    SecurityAssessmentEngine,
)
from guardian.domain.security import (
    SecurityCategory,
    SecurityEvidence,
    SecuritySeverity,
    SecuritySource,
)


def make_evidence(
    *,
    evidence_type: str,
    details: dict[str, str],
    evidence_available: bool = True,
) -> SecurityEvidence:
    return SecurityEvidence(
        evidence_id="evidence-test-001",
        resource_id="resource-test-001",
        category=SecurityCategory.CONTAINER,
        source=SecuritySource.DOCKER,
        evidence_type=evidence_type,
        observed_at=datetime(
            2026,
            10,
            23,
            12,
            0,
            tzinfo=UTC,
        ),
        evidence_available=evidence_available,
        details=details,
    )


def test_privileged_container_generates_high_finding() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type=(
            "container_privilege_configuration"
        ),
        details={
            "privileged": "true",
            "cap_add": "",
            "cap_drop": "",
        },
    )

    findings = engine.assess([evidence])

    assert len(findings) == 1

    finding = findings[0]

    assert finding.severity == SecuritySeverity.HIGH
    assert finding.evidence_id == evidence.evidence_id
    assert finding.resource_id == evidence.resource_id
    assert finding.evidence_available is True
    assert (
        finding.title
        == "Privileged container configuration"
    )


def test_non_privileged_container_generates_no_finding() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type=(
            "container_privilege_configuration"
        ),
        details={
            "privileged": "false",
            "cap_add": "",
            "cap_drop": "",
        },
    )

    findings = engine.assess([evidence])

    assert findings == []


def test_published_ports_generate_info_finding() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type=(
            "container_network_configuration"
        ),
        details={
            "network_mode": "bridge",
            "published_ports": (
                "0.0.0.0:8080->8080/tcp"
            ),
        },
    )

    findings = engine.assess([evidence])

    assert len(findings) == 1
    assert (
        findings[0].severity
        == SecuritySeverity.INFO
    )
    assert findings[0].evidence_id == evidence.evidence_id


def test_no_published_ports_generate_no_finding() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type=(
            "container_network_configuration"
        ),
        details={
            "network_mode": "bridge",
            "published_ports": "",
        },
    )

    findings = engine.assess([evidence])

    assert findings == []


def test_mounts_generate_info_finding() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type=(
            "container_mount_configuration"
        ),
        details={
            "mount_count": "2",
            "mounts": (
                "/host/a->/container/a:rw,"
                "/host/b->/container/b:ro"
            ),
        },
    )

    findings = engine.assess([evidence])

    assert len(findings) == 1
    assert (
        findings[0].severity
        == SecuritySeverity.INFO
    )


def test_zero_mounts_generate_no_finding() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type=(
            "container_mount_configuration"
        ),
        details={
            "mount_count": "0",
            "mounts": "",
        },
    )

    findings = engine.assess([evidence])

    assert findings == []


def test_invalid_mount_count_generates_unknown_finding() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type=(
            "container_mount_configuration"
        ),
        details={
            "mount_count": "unknown",
            "mounts": "",
        },
    )

    findings = engine.assess([evidence])

    assert len(findings) == 1
    assert (
        findings[0].severity
        == SecuritySeverity.UNKNOWN
    )


def test_unavailable_evidence_generates_unknown_finding() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type="vulnerability_scan",
        details={
            "reason": (
                "No vulnerability scanner evidence available."
            ),
        },
        evidence_available=False,
    )

    findings = engine.assess([evidence])

    assert len(findings) == 1

    finding = findings[0]

    assert finding.severity == SecuritySeverity.UNKNOWN
    assert finding.evidence_available is False
    assert finding.evidence_id == evidence.evidence_id


def test_running_runtime_generates_no_finding() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type=(
            "container_runtime_configuration"
        ),
        details={
            "container_name": "test",
            "status": "running",
            "image_id": "sha256:test",
            "image_tags": "test:latest",
        },
    )

    findings = engine.assess([evidence])

    assert findings == []


def test_stopped_runtime_generates_info_finding() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type=(
            "container_runtime_configuration"
        ),
        details={
            "container_name": "test",
            "status": "exited",
            "image_id": "sha256:test",
            "image_tags": "test:latest",
        },
    )

    findings = engine.assess([evidence])

    assert len(findings) == 1
    assert (
        findings[0].severity
        == SecuritySeverity.INFO
    )


def test_unknown_evidence_type_does_not_create_claim() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type="unknown_security_observation",
        details={
            "value": "observed",
        },
    )

    findings = engine.assess([evidence])

    assert findings == []


def test_multiple_evidence_records_are_assessed() -> None:
    engine = SecurityAssessmentEngine()

    evidence = [
        make_evidence(
            evidence_type=(
                "container_privilege_configuration"
            ),
            details={
                "privileged": "true",
                "cap_add": "",
                "cap_drop": "",
            },
        ),
        SecurityEvidence(
            evidence_id="evidence-test-002",
            resource_id="resource-test-001",
            category=SecurityCategory.NETWORK,
            source=SecuritySource.DOCKER,
            evidence_type=(
                "container_network_configuration"
            ),
            observed_at=datetime(
                2026,
                10,
                23,
                12,
                1,
                tzinfo=UTC,
            ),
            evidence_available=True,
            details={
                "network_mode": "bridge",
                "published_ports": (
                    "0.0.0.0:8080->8080/tcp"
                ),
            },
        ),
    ]

    findings = engine.assess(evidence)

    assert len(findings) == 2

    evidence_ids = {
        finding.evidence_id
        for finding in findings
    }

    assert evidence_ids == {
        "evidence-test-001",
        "evidence-test-002",
    }


def test_finding_contains_assessment_basis() -> None:
    engine = SecurityAssessmentEngine()

    evidence = make_evidence(
        evidence_type=(
            "container_privilege_configuration"
        ),
        details={
            "privileged": "true",
            "cap_add": "",
            "cap_drop": "",
        },
    )

    findings = engine.assess([evidence])

    assert (
        findings[0].metadata["assessment_basis"]
        == "container_privilege_configuration"
    )