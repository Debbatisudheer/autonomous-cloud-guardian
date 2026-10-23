from __future__ import annotations

from guardian.domain.security import (
    SecurityEvidence,
    SecurityFinding,
    SecuritySeverity,
)


class SecurityAssessmentEngine:
    """
    Deterministic, evidence-backed security assessment engine.

    This engine interprets directly observed security configuration.
    It does not perform vulnerability scanning, exploit testing,
    risk scoring, remediation, or infrastructure actions.
    """

    def assess(
        self,
        evidence: list[SecurityEvidence],
    ) -> list[SecurityFinding]:
        findings: list[SecurityFinding] = []

        for item in evidence:
            findings.extend(
                self._assess_evidence(item)
            )

        return findings

    def _assess_evidence(
        self,
        evidence: SecurityEvidence,
    ) -> list[SecurityFinding]:
        if not evidence.evidence_available:
            return [
                self._build_unavailable_evidence_finding(
                    evidence
                )
            ]

        if (
            evidence.evidence_type
            == "container_privilege_configuration"
        ):
            return self._assess_privilege_configuration(
                evidence
            )

        if (
            evidence.evidence_type
            == "container_network_configuration"
        ):
            return self._assess_network_configuration(
                evidence
            )

        if (
            evidence.evidence_type
            == "container_mount_configuration"
        ):
            return self._assess_mount_configuration(
                evidence
            )

        if (
            evidence.evidence_type
            == "container_runtime_configuration"
        ):
            return self._assess_runtime_configuration(
                evidence
            )

        return []

    def _assess_privilege_configuration(
        self,
        evidence: SecurityEvidence,
    ) -> list[SecurityFinding]:
        privileged = (
            evidence.details.get("privileged", "")
            .strip()
            .lower()
        )

        if privileged == "true":
            return [
                self._build_finding(
                    evidence=evidence,
                    severity=SecuritySeverity.HIGH,
                    title="Privileged container configuration",
                    description=(
                        "The Docker container is configured "
                        "with privileged mode enabled. This "
                        "configuration grants the container "
                        "elevated access to the host and "
                        "requires explicit security review."
                    ),
                )
            ]

        return []

    def _assess_network_configuration(
        self,
        evidence: SecurityEvidence,
    ) -> list[SecurityFinding]:
        published_ports = (
            evidence.details.get(
                "published_ports",
                "",
            ).strip()
        )

        if not published_ports:
            return []

        return [
            self._build_finding(
                evidence=evidence,
                severity=SecuritySeverity.INFO,
                title="Published container network ports",
                description=(
                    "The Docker container exposes one or more "
                    "published network ports. This is an "
                    "observable network exposure configuration "
                    "and should be reviewed against the intended "
                    "service boundary."
                ),
            )
        ]

    def _assess_mount_configuration(
        self,
        evidence: SecurityEvidence,
    ) -> list[SecurityFinding]:
        mount_count_value = evidence.details.get(
            "mount_count",
            "0",
        ).strip()

        try:
            mount_count = int(
                mount_count_value
            )
        except ValueError:
            return [
                self._build_finding(
                    evidence=evidence,
                    severity=SecuritySeverity.UNKNOWN,
                    title="Uninterpretable mount configuration",
                    description=(
                        "The observed Docker mount count could "
                        "not be interpreted from the collected "
                        "security evidence."
                    ),
                )
            ]

        if mount_count == 0:
            return []

        return [
            self._build_finding(
                evidence=evidence,
                severity=SecuritySeverity.INFO,
                title="Container filesystem mounts detected",
                description=(
                    "The Docker container has one or more "
                    "filesystem mounts. Mount configuration is "
                    "observable security evidence and should be "
                    "reviewed against the intended access boundary."
                ),
            )
        ]

    def _assess_runtime_configuration(
        self,
        evidence: SecurityEvidence,
    ) -> list[SecurityFinding]:
        status = (
            evidence.details.get(
                "status",
                "",
            ).strip().lower()
        )

        if status == "running":
            return []

        if status:
            return [
                self._build_finding(
                    evidence=evidence,
                    severity=SecuritySeverity.INFO,
                    title="Container runtime state",
                    description=(
                        "The observed Docker container runtime "
                        f"state is '{status}'. The state is "
                        "recorded as security evidence but is not "
                        "itself treated as a confirmed vulnerability."
                    ),
                )
            ]

        return []

    def _build_unavailable_evidence_finding(
        self,
        evidence: SecurityEvidence,
    ) -> SecurityFinding:
        return self._build_finding(
            evidence=evidence,
            severity=SecuritySeverity.UNKNOWN,
            title="Security evidence unavailable",
            description=(
                "Security evidence for this observation was "
                "unavailable. No security conclusion is made "
                "without supporting evidence."
            ),
        )

    @staticmethod
    def _build_finding(
        evidence: SecurityEvidence,
        severity: SecuritySeverity,
        title: str,
        description: str,
    ) -> SecurityFinding:
        return SecurityFinding(
            finding_id=SecurityAssessmentEngine._finding_id(
                evidence,
                title,
            ),
            resource_id=evidence.resource_id,
            category=evidence.category,
            severity=severity,
            source=evidence.source,
            title=title,
            description=description,
            evidence_id=evidence.evidence_id,
            evidence_available=evidence.evidence_available,
            detected_at=evidence.observed_at,
            metadata={
                "assessment_basis": evidence.evidence_type,
            },
        )

    @staticmethod
    def _finding_id(
        evidence: SecurityEvidence,
        title: str,
    ) -> str:
        normalized_title = (
            title.lower()
            .replace(" ", "_")
            .replace("/", "_")
        )

        return (
            f"{evidence.evidence_id}:"
            f"{normalized_title}"
        )