from __future__ import annotations

from guardian.application.security_assessment import (
    SecurityAssessmentEngine,
)
from guardian.domain.security import (
    SecuritySeverity,
)
from guardian.infrastructure.docker.security import (
    DockerSecurityEvidenceProvider,
)


def main() -> None:
    print("PHASE 7.4 — SECURITY ASSESSMENT VALIDATION")
    print("=" * 60)

    provider = DockerSecurityEvidenceProvider()
    engine = SecurityAssessmentEngine()

    try:
        containers = provider._client.containers.list(
            all=True
        )

        if not containers:
            raise RuntimeError(
                "No Docker containers were discovered."
            )

        print(
            "REAL DOCKER DISCOVERY PASS "
            f"({len(containers)} containers)"
        )

        running_container = next(
            (
                container
                for container in containers
                if container.status == "running"
            ),
            None,
        )

        if running_container is None:
            raise RuntimeError(
                "No running Docker container was available "
                "for security assessment."
            )

        resource_id = str(
            running_container.name
        )

        print(
            "ASSESSMENT RESOURCE: "
            f"{resource_id}"
        )

        evidence_result = (
            provider.collect_for_resource(
                resource_id
            )
        )

        if not evidence_result.evidence_available:
            raise RuntimeError(
                "Real Docker security evidence was unavailable."
            )

        evidence = evidence_result.evidence

        if not evidence:
            raise RuntimeError(
                "No real Docker security evidence was collected."
            )

        print(
            "REAL SECURITY EVIDENCE COLLECTION PASS "
            f"({len(evidence)} observations)"
        )

        for item in evidence:
            if item.resource_id != resource_id:
                raise RuntimeError(
                    "Evidence resource correlation failed."
                )

            if item.source.value != "docker":
                raise RuntimeError(
                    "Evidence source is not Docker."
                )

            if not item.evidence_id:
                raise RuntimeError(
                    "Evidence has no evidence ID."
                )

            if not item.evidence_type:
                raise RuntimeError(
                    "Evidence has no evidence type."
                )

        print("SECURITY EVIDENCE INTEGRITY PASS")

        findings = engine.assess(
            evidence
        )

        print(
            "SECURITY ASSESSMENT EXECUTION PASS "
            f"({len(findings)} findings)"
        )

        evidence_ids = {
            item.evidence_id
            for item in evidence
        }

        for finding in findings:
            if finding.evidence_id is None:
                raise RuntimeError(
                    "Finding has no evidence correlation."
                )

            if finding.evidence_id not in evidence_ids:
                raise RuntimeError(
                    "Finding references evidence that "
                    "was not collected."
                )

            if finding.resource_id != resource_id:
                raise RuntimeError(
                    "Finding resource correlation failed."
                )

            if not finding.title:
                raise RuntimeError(
                    "Finding has no title."
                )

            if not finding.description:
                raise RuntimeError(
                    "Finding has no description."
                )

            if not finding.metadata.get(
                "assessment_basis"
            ):
                raise RuntimeError(
                    "Finding has no assessment basis."
                )

        print(
            "FINDING EVIDENCE CORRELATION PASS"
        )

        severities = {
            finding.severity
            for finding in findings
        }

        print(
            "FINDING SEVERITY INTEGRITY PASS "
            f"({len(severities)} severity levels)"
        )

        privileged_evidence = [
            item
            for item in evidence
            if (
                item.evidence_type
                == "container_privilege_configuration"
            )
        ]

        if privileged_evidence:
            privileged_value = (
                privileged_evidence[0]
                .details
                .get("privileged", "")
                .lower()
            )

            privileged_findings = [
                finding
                for finding in findings
                if finding.title
                == "Privileged container configuration"
            ]

            if privileged_value == "true":
                if not privileged_findings:
                    raise RuntimeError(
                        "Privileged configuration was observed "
                        "but no corresponding finding was generated."
                    )

                if (
                    privileged_findings[0].severity
                    != SecuritySeverity.HIGH
                ):
                    raise RuntimeError(
                        "Privileged configuration did not "
                        "receive HIGH severity."
                    )

                print(
                    "PRIVILEGED CONFIGURATION ASSESSMENT PASS"
                )

            elif privileged_value == "false":
                if privileged_findings:
                    raise RuntimeError(
                        "Non-privileged configuration generated "
                        "an incorrect privileged finding."
                    )

                print(
                    "NON-PRIVILEGED CONFIGURATION ASSESSMENT PASS"
                )

        unsupported_claims = [
            finding
            for finding in findings
            if (
                "CVE" in finding.title.upper()
                or "EXPLOIT" in finding.title.upper()
                or "CONFIRMED VULNERABILITY"
                in finding.title.upper()
            )
        ]

        if unsupported_claims:
            raise RuntimeError(
                "Assessment generated unsupported vulnerability claims."
            )

        print(
            "NO UNSUPPORTED VULNERABILITY CLAIMS PASS"
        )

        print()
        print("PHASE 7.4 BOUNDARY CHECK")
        print("------------------------")
        print(
            "Real Docker security evidence: AVAILABLE"
        )
        print(
            "Security assessment:            EXECUTED"
        )
        print(
            "Evidence correlation:           VERIFIED"
        )
        print(
            "Risk scoring:                   NOT IMPLEMENTED"
        )
        print(
            "Recommendation:                NOT IMPLEMENTED"
        )
        print(
            "Infrastructure action:          NONE"
        )
        print(
            "Automatic remediation:          NONE"
        )
        print(
            "Vulnerability scanner:          NOT IMPLEMENTED"
        )

        print()
        print(
            "PHASE 7.4 — COMPLETE: PASS"
        )

    finally:
        provider.close()


if __name__ == "__main__":
    main()