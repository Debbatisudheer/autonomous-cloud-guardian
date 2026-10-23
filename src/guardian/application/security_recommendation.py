from __future__ import annotations

from guardian.domain.security import (
    SecurityFinding,
    SecuritySeverity,
)
from guardian.domain.security_recommendation import (
    SecurityRecommendation,
    SecurityRecommendationOutcome,
    SecurityRecommendationPriority,
)
from guardian.domain.security_risk import (
    SecurityRiskSignal,
)


class SecurityRecommendationEngine:
    """
    Deterministic, evidence-backed security recommendation engine.

    The engine produces recommendations only.

    It does not:
    - execute infrastructure actions,
    - modify Docker configuration,
    - restart containers,
    - delete resources,
    - perform remediation,
    - claim confirmed vulnerabilities without evidence.
    """

    def generate(
        self,
        finding: SecurityFinding,
        signal: SecurityRiskSignal,
    ) -> SecurityRecommendation:
        self._validate_correlation(
            finding,
            signal,
        )

        if not finding.evidence_available:
            return self._build_no_recommendation(
                finding,
                signal,
            )

        if finding.severity == SecuritySeverity.CRITICAL:
            return self._build_remediation_recommendation(
                finding,
                signal,
                SecurityRecommendationPriority.HIGH,
            )

        if finding.severity == SecuritySeverity.HIGH:
            return self._build_remediation_recommendation(
                finding,
                signal,
                SecurityRecommendationPriority.HIGH,
            )

        if finding.severity == SecuritySeverity.MEDIUM:
            return self._build_review_recommendation(
                finding,
                signal,
                SecurityRecommendationPriority.MEDIUM,
            )

        if finding.severity == SecuritySeverity.LOW:
            return self._build_review_recommendation(
                finding,
                signal,
                SecurityRecommendationPriority.LOW,
            )

        if finding.severity == SecuritySeverity.INFO:
            return self._build_review_recommendation(
                finding,
                signal,
                SecurityRecommendationPriority.LOW,
            )

        return self._build_no_recommendation(
            finding,
            signal,
        )

    @staticmethod
    def _validate_correlation(
        finding: SecurityFinding,
        signal: SecurityRiskSignal,
    ) -> None:
        if signal.finding_id != finding.finding_id:
            raise ValueError(
                "Security risk signal does not "
                "correlate with the supplied finding."
            )

        expected_evidence_id = (
            finding.evidence_id
            or "unavailable"
        )

        if signal.evidence_id != expected_evidence_id:
            raise ValueError(
                "Security risk signal evidence does "
                "not correlate with the supplied finding."
            )

        if signal.resource_id != finding.resource_id:
            raise ValueError(
                "Security risk signal resource does "
                "not correlate with the supplied finding."
            )

        if signal.severity != finding.severity:
            raise ValueError(
                "Security risk signal severity does "
                "not correlate with the supplied finding."
            )

    @staticmethod
    def _build_no_recommendation(
        finding: SecurityFinding,
        signal: SecurityRiskSignal,
    ) -> SecurityRecommendation:
        return SecurityRecommendation(
            recommendation_id=(
                f"{finding.finding_id}:"
                f"{signal.signal_id}:recommendation"
            ),
            finding_id=finding.finding_id,
            signal_id=signal.signal_id,
            evidence_id=(
                finding.evidence_id
                or "unavailable"
            ),
            resource_id=finding.resource_id,
            outcome=(
                SecurityRecommendationOutcome
                .NO_RECOMMENDATION
            ),
            priority=(
                SecurityRecommendationPriority.LOW
            ),
            title="No security recommendation",
            recommendation=(
                "No remediation recommendation is "
                "generated because supporting security "
                "evidence is unavailable or insufficient."
            ),
            rationale=(
                "Security decisions require supporting "
                "evidence. No action is recommended when "
                "evidence is unavailable."
            ),
            evidence_available=(
                finding.evidence_available
            ),
            metadata={
                "source_finding": finding.finding_id,
                "source_signal": signal.signal_id,
            },
        )

    @staticmethod
    def _build_review_recommendation(
        finding: SecurityFinding,
        signal: SecurityRiskSignal,
        priority: SecurityRecommendationPriority,
    ) -> SecurityRecommendation:
        return SecurityRecommendation(
            recommendation_id=(
                f"{finding.finding_id}:"
                f"{signal.signal_id}:recommendation"
            ),
            finding_id=finding.finding_id,
            signal_id=signal.signal_id,
            evidence_id=(
                finding.evidence_id
                or "unavailable"
            ),
            resource_id=finding.resource_id,
            outcome=(
                SecurityRecommendationOutcome.REVIEW
            ),
            priority=priority,
            title=(
                f"Review security finding: "
                f"{finding.title}"
            ),
            recommendation=(
                "Review the observed security "
                "configuration against the intended "
                "security boundary and determine whether "
                "a configuration change is appropriate."
            ),
            rationale=(
                "The recommendation is based on an "
                "evidence-backed security finding and "
                "does not assume that the observed "
                "configuration is inherently a vulnerability."
            ),
            evidence_available=True,
            metadata={
                "source_finding": finding.finding_id,
                "source_signal": signal.signal_id,
            },
        )

    @staticmethod
    def _build_remediation_recommendation(
        finding: SecurityFinding,
        signal: SecurityRiskSignal,
        priority: SecurityRecommendationPriority,
    ) -> SecurityRecommendation:
        return SecurityRecommendation(
            recommendation_id=(
                f"{finding.finding_id}:"
                f"{signal.signal_id}:recommendation"
            ),
            finding_id=finding.finding_id,
            signal_id=signal.signal_id,
            evidence_id=(
                finding.evidence_id
                or "unavailable"
            ),
            resource_id=finding.resource_id,
            outcome=(
                SecurityRecommendationOutcome
                .REMEDIATION_RECOMMENDED
            ),
            priority=priority,
            title=(
                f"Security remediation review: "
                f"{finding.title}"
            ),
            recommendation=(
                "Review the observed configuration and "
                "determine an appropriate remediation "
                "before making any infrastructure change."
            ),
            rationale=(
                "The finding has elevated severity based "
                "on directly observed security evidence. "
                "The recommendation identifies the need "
                "for remediation review but does not "
                "execute remediation automatically."
            ),
            evidence_available=True,
            metadata={
                "source_finding": finding.finding_id,
                "source_signal": signal.signal_id,
            },
        )