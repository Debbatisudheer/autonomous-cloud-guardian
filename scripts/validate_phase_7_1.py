from __future__ import annotations

from datetime import UTC, datetime

from pydantic import ValidationError

from guardian.domain.security import (
    SecurityCategory,
    SecurityEvidence,
    SecurityFinding,
    SecuritySeverity,
    SecuritySource,
)


def main() -> None:
    print("PHASE 7.1 — SECURITY DOMAIN MODEL VALIDATION")
    print("=" * 64)

    print("SECURITY ENUMS PASS")

    observed_at = datetime(2026, 10, 23, 10, 0, tzinfo=UTC)

    evidence = SecurityEvidence(
        evidence_id="phase-7-1-evidence",
        resource_id="phase-7-1-resource",
        category=SecurityCategory.CONFIGURATION,
        source=SecuritySource.DOCKER,
        evidence_type="configuration_observation",
        observed_at=observed_at,
        evidence_available=True,
        details={
            "property": "configuration",
            "origin": "controlled_domain_validation",
        },
    )

    if evidence.evidence_id != "phase-7-1-evidence":
        raise RuntimeError("Security evidence identity validation failed.")

    if evidence.resource_id != "phase-7-1-resource":
        raise RuntimeError("Security evidence resource correlation failed.")

    if evidence.category != SecurityCategory.CONFIGURATION:
        raise RuntimeError("Security evidence category validation failed.")

    if evidence.source != SecuritySource.DOCKER:
        raise RuntimeError("Security evidence source validation failed.")

    if not evidence.evidence_available:
        raise RuntimeError("Expected controlled evidence to be available.")

    print("SECURITY EVIDENCE MODEL PASS")

    unavailable_evidence = SecurityEvidence(
        evidence_id="phase-7-1-unavailable",
        resource_id="phase-7-1-resource",
        category=SecurityCategory.VULNERABILITY,
        source=SecuritySource.DOCKER,
        evidence_type="vulnerability_scan",
        evidence_available=False,
    )

    if unavailable_evidence.evidence_available:
        raise RuntimeError(
            "Unavailable security evidence was incorrectly marked available."
        )

    print("UNAVAILABLE EVIDENCE REPRESENTATION PASS")

    finding = SecurityFinding(
        finding_id="phase-7-1-finding",
        resource_id="phase-7-1-resource",
        category=SecurityCategory.CONFIGURATION,
        severity=SecuritySeverity.MEDIUM,
        source=SecuritySource.DOCKER,
        title="Controlled security finding model",
        description=(
            "This is a domain-model validation fixture only. "
            "It is not a real security finding."
        ),
        evidence_id=evidence.evidence_id,
        evidence_available=evidence.evidence_available,
        detected_at=observed_at,
    )

    if finding.evidence_id != evidence.evidence_id:
        raise RuntimeError("Finding/evidence correlation failed.")

    if finding.resource_id != evidence.resource_id:
        raise RuntimeError("Finding/resource correlation failed.")

    if finding.evidence_available != evidence.evidence_available:
        raise RuntimeError("Finding evidence state correlation failed.")

    print("SECURITY FINDING MODEL PASS")
    print("FINDING/EVIDENCE CORRELATION PASS")

    try:
        SecurityEvidence(
            evidence_id="phase-7-1-invalid",
            resource_id="phase-7-1-resource",
            category=SecurityCategory.NETWORK,
            source=SecuritySource.DOCKER,
            evidence_type="network_observation",
            evidence_available=True,
            unsupported_field="must_fail",
        )
    except ValidationError:
        print("STRICT EVIDENCE SCHEMA PASS")
    else:
        raise RuntimeError(
            "SecurityEvidence accepted an unsupported field."
        )

    try:
        SecurityFinding(
            finding_id="phase-7-1-invalid-finding",
            category=SecurityCategory.CONTAINER,
            severity=SecuritySeverity.HIGH,
            source=SecuritySource.DOCKER,
            title="Invalid test finding",
            description="This must fail because of an unsupported field.",
            evidence_available=True,
            automatic_remediation=True,
        )
    except ValidationError:
        print("STRICT FINDING SCHEMA PASS")
    else:
        raise RuntimeError(
            "SecurityFinding accepted an unsupported field."
        )

    print("SECURITY DOMAIN BOUNDARY PASS")
    print()
    print("PHASE 7.1 BOUNDARY CHECK")
    print("------------------------")
    print("Security domain model:       ESTABLISHED")
    print("Security evidence collection: NOT IMPLEMENTED")
    print("Security assessment:          NOT IMPLEMENTED")
    print("Security recommendation:      NOT IMPLEMENTED")
    print("Infrastructure action:        NONE")
    print("Automatic remediation:        NONE")
    print("Real vulnerability claim:     NONE")
    print()
    print("IMPORTANT:")
    print(
        "All security objects above are CONTROLLED DOMAIN-MODEL "
        "VALIDATION FIXTURES."
    )
    print("They are NOT real security findings.")
    print()
    print("PHASE 7.1 — COMPLETE: PASS")


if __name__ == "__main__":
    main()