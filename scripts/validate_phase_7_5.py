from __future__ import annotations

from guardian.application.security_assessment import (
    SecurityAssessmentEngine,
)
from guardian.application.security_risk import (
    SecurityRiskSignalEngine,
)
from guardian.domain.security_risk import (
    SecurityRiskSignalType,
)
from guardian.infrastructure.docker.security import (
    DockerSecurityEvidenceProvider,
)


def main() -> None:
    print(
        "PHASE 7.5 — SECURITY RISK SIGNAL VALIDATION"
    )
    print("=" * 60)

    provider = DockerSecurityEvidenceProvider()
    assessment_engine = SecurityAssessmentEngine()
    risk_engine = SecurityRiskSignalEngine()

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
                "No running Docker container available."
            )

        resource_id = str(
            running_container.name
        )

        print(
            "RISK SIGNAL RESOURCE: "
            f"{resource_id}"
        )

        evidence_result = (
            provider.collect_for_resource(
                resource_id
            )
        )

        if not evidence_result.evidence_available:
            raise RuntimeError(
                "Security evidence was unavailable."
            )

        evidence = evidence_result.evidence

        if not evidence:
            raise RuntimeError(
                "No security evidence was collected."
            )

        print(
            "REAL SECURITY EVIDENCE PASS "
            f"({len(evidence)} observations)"
        )

        findings = assessment_engine.assess(
            evidence
        )

        print(
            "SECURITY ASSESSMENT PASS "
            f"({len(findings)} findings)"
        )

        signals = risk_engine.generate(
            findings
        )

        print(
            "SECURITY RISK SIGNAL GENERATION PASS "
            f"({len(signals)} signals)"
        )

        if len(signals) != len(findings):
            raise RuntimeError(
                "Every security finding should produce "
                "exactly one risk signal."
            )

        print(
            "FINDING-TO-SIGNAL CARDINALITY PASS"
        )

        finding_ids = {
            finding.finding_id
            for finding in findings
        }

        evidence_ids = {
            item.evidence_id
            for item in evidence
        }

        for signal in signals:
            if signal.finding_id not in finding_ids:
                raise RuntimeError(
                    "Risk signal references a finding "
                    "that does not exist."
                )

            if signal.evidence_id not in evidence_ids:
                raise RuntimeError(
                    "Risk signal references evidence "
                    "that was not collected."
                )

            if signal.resource_id != resource_id:
                raise RuntimeError(
                    "Risk signal resource correlation failed."
                )

            if not signal.signal_id:
                raise RuntimeError(
                    "Risk signal has no signal ID."
                )

            if not signal.title:
                raise RuntimeError(
                    "Risk signal has no title."
                )

            if not signal.description:
                raise RuntimeError(
                    "Risk signal has no description."
                )

        print(
            "RISK SIGNAL EVIDENCE CORRELATION PASS"
        )

        for finding, signal in zip(
            findings,
            signals,
        ):
            if (
                signal.severity
                != finding.severity
            ):
                raise RuntimeError(
                    "Risk signal severity does not "
                    "match its source finding."
                )

            expected_source = (
                finding.finding_id
            )

            if (
                signal.metadata.get(
                    "source_finding"
                )
                != expected_source
            ):
                raise RuntimeError(
                    "Risk signal source finding metadata "
                    "does not match."
                )

        print(
            "RISK SIGNAL SEVERITY CORRELATION PASS"
        )

        valid_signal_types = {
            SecurityRiskSignalType.UNKNOWN_SECURITY_RISK,
            SecurityRiskSignalType.INFORMATIONAL_SECURITY_SIGNAL,
            SecurityRiskSignalType.ELEVATED_SECURITY_RISK,
            SecurityRiskSignalType.HIGH_SECURITY_RISK,
            SecurityRiskSignalType.CRITICAL_SECURITY_RISK,
        }

        for signal in signals:
            if signal.signal_type not in valid_signal_types:
                raise RuntimeError(
                    "Invalid security risk signal type."
                )

        print(
            "RISK SIGNAL TYPE INTEGRITY PASS"
        )

        unsupported_actions = [
            signal
            for signal in signals
            if any(
                keyword in signal.description.lower()
                for keyword in (
                    "restart",
                    "delete",
                    "terminate",
                    "remediate",
                    "execute",
                )
            )
        ]

        if unsupported_actions:
            raise RuntimeError(
                "Risk signals contain remediation "
                "or execution instructions."
            )

        print(
            "NO REMEDIATION IN RISK SIGNALS PASS"
        )

        unsupported_recommendations = [
            signal
            for signal in signals
            if "recommend" in signal.description.lower()
        ]

        if unsupported_recommendations:
            raise RuntimeError(
                "Recommendation logic leaked into "
                "the risk signal layer."
            )

        print(
            "NO RECOMMENDATION LOGIC PASS"
        )

        print()
        print(
            "PHASE 7.5 BOUNDARY CHECK"
        )
        print(
            "------------------------"
        )
        print(
            "Real security evidence:       AVAILABLE"
        )
        print(
            "Security assessment:          EXECUTED"
        )
        print(
            "Security risk signals:        EXECUTED"
        )
        print(
            "Recommendations:              NOT IMPLEMENTED"
        )
        print(
            "Infrastructure action:        NONE"
        )
        print(
            "Automatic remediation:        NONE"
        )

        print()
        print(
            "PHASE 7.5 — COMPLETE: PASS"
        )

    finally:
        provider.close()


if __name__ == "__main__":
    main()