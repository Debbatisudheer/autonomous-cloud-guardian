from __future__ import annotations

from guardian.application.security_assessment import (
    SecurityAssessmentEngine,
)
from guardian.application.security_recommendation import (
    SecurityRecommendationEngine,
)
from guardian.application.security_risk import (
    SecurityRiskSignalEngine,
)
from guardian.domain.security_recommendation import (
    SecurityRecommendationOutcome,
    SecurityRecommendationPriority,
)
from guardian.infrastructure.docker.security import (
    DockerSecurityEvidenceProvider,
)


def main() -> None:
    print(
        "PHASE 7.6 — SECURITY RECOMMENDATION VALIDATION"
    )
    print("=" * 60)

    provider = DockerSecurityEvidenceProvider()

    assessment_engine = SecurityAssessmentEngine()

    risk_engine = SecurityRiskSignalEngine()

    recommendation_engine = (
        SecurityRecommendationEngine()
    )

    try:
        containers = (
            provider._client.containers.list(
                all=True
            )
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
            "RECOMMENDATION RESOURCE: "
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
            "SECURITY RISK SIGNAL PASS "
            f"({len(signals)} signals)"
        )

        if len(signals) != len(findings):
            raise RuntimeError(
                "Finding and risk signal counts do not match."
            )

        recommendations = []

        for finding, signal in zip(
            findings,
            signals,
        ):
            recommendation = (
                recommendation_engine.generate(
                    finding,
                    signal,
                )
            )

            recommendations.append(
                recommendation
            )

        print(
            "SECURITY RECOMMENDATION GENERATION PASS "
            f"({len(recommendations)} recommendations)"
        )

        if len(recommendations) != len(findings):
            raise RuntimeError(
                "Every assessed finding should produce "
                "one recommendation result."
            )

        print(
            "FINDING-TO-RECOMMENDATION CARDINALITY PASS"
        )

        finding_ids = {
            finding.finding_id
            for finding in findings
        }

        signal_ids = {
            signal.signal_id
            for signal in signals
        }

        evidence_ids = {
            item.evidence_id
            for item in evidence
        }

        for recommendation in recommendations:
            if recommendation.finding_id not in finding_ids:
                raise RuntimeError(
                    "Recommendation references an "
                    "unknown finding."
                )

            if recommendation.signal_id not in signal_ids:
                raise RuntimeError(
                    "Recommendation references an "
                    "unknown risk signal."
                )

            if recommendation.evidence_id not in evidence_ids:
                raise RuntimeError(
                    "Recommendation references evidence "
                    "that was not collected."
                )

            if recommendation.resource_id != resource_id:
                raise RuntimeError(
                    "Recommendation resource correlation failed."
                )

            if not recommendation.recommendation_id:
                raise RuntimeError(
                    "Recommendation ID is missing."
                )

        print(
            "RECOMMENDATION EVIDENCE CORRELATION PASS"
        )

        for finding, signal, recommendation in zip(
            findings,
            signals,
            recommendations,
        ):
            if (
                recommendation.finding_id
                != finding.finding_id
            ):
                raise RuntimeError(
                    "Finding correlation failed."
                )

            if (
                recommendation.signal_id
                != signal.signal_id
            ):
                raise RuntimeError(
                    "Signal correlation failed."
                )

            if (
                recommendation.evidence_id
                != finding.evidence_id
            ):
                raise RuntimeError(
                    "Evidence correlation failed."
                )

            if (
                recommendation.resource_id
                != finding.resource_id
            ):
                raise RuntimeError(
                    "Resource correlation failed."
                )

        print(
            "RECOMMENDATION SOURCE CORRELATION PASS"
        )

        for recommendation in recommendations:
            if (
                recommendation.outcome
                == SecurityRecommendationOutcome
                .REMEDIATION_RECOMMENDED
                and recommendation.priority
                not in {
                    SecurityRecommendationPriority.HIGH,
                }
            ):
                raise RuntimeError(
                    "Remediation recommendations must "
                    "have HIGH priority."
                )

        print(
            "RECOMMENDATION PRIORITY INTEGRITY PASS"
        )

        for recommendation in recommendations:
            text = (
                recommendation.recommendation
                .lower()
            )

            forbidden_execution_terms = (
                "execute docker",
                "restart the container",
                "restart container",
                "delete the container",
                "delete container",
                "terminate the container",
                "terminate container",
                "automatically remediate",
                "automatic remediation",
            )

            if any(
                term in text
                for term in forbidden_execution_terms
            ):
                raise RuntimeError(
                    "Recommendation contains direct "
                    "infrastructure execution instructions."
                )

        print(
            "NO INFRASTRUCTURE EXECUTION IN RECOMMENDATIONS PASS"
        )

        for recommendation in recommendations:
            text = (
                recommendation.recommendation
                .lower()
            )

            if "confirmed vulnerability" in text:
                raise RuntimeError(
                    "Recommendation makes an unsupported "
                    "confirmed-vulnerability claim."
                )

        print(
            "NO UNSUPPORTED VULNERABILITY CLAIMS PASS"
        )

        print()
        print(
            "PHASE 7.6 BOUNDARY CHECK"
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
            "Recommendations:              EXECUTED"
        )
        print(
            "Infrastructure action:        NONE"
        )
        print(
            "Automatic remediation:        NONE"
        )
        print(
            "Security changes applied:     NONE"
        )

        print()
        print(
            "PHASE 7.6 — COMPLETE: PASS"
        )

    finally:
        provider.close()


if __name__ == "__main__":
    main()