from __future__ import annotations

from guardian.domain.security import (
    SecurityFinding,
    SecuritySeverity,
)
from guardian.domain.security_risk import (
    SecurityRiskSignal,
    SecurityRiskSignalType,
)


class SecurityRiskSignalEngine:
    """
    Converts evidence-backed security findings into
    normalized security risk signals.

    This engine does not recommend actions, perform
    remediation, or execute infrastructure changes.
    """

    def generate(
        self,
        findings: list[SecurityFinding],
    ) -> list[SecurityRiskSignal]:
        signals: list[SecurityRiskSignal] = []

        for finding in findings:
            signals.append(
                self._generate_for_finding(
                    finding
                )
            )

        return signals

    def _generate_for_finding(
        self,
        finding: SecurityFinding,
    ) -> SecurityRiskSignal:
        signal_type = (
            self._signal_type_for_severity(
                finding.severity
            )
        )

        return SecurityRiskSignal(
            signal_id=(
                f"{finding.finding_id}:"
                f"risk_signal"
            ),
            finding_id=finding.finding_id,
            evidence_id=(
                finding.evidence_id
                or "unavailable"
            ),
            resource_id=finding.resource_id,
            signal_type=signal_type,
            severity=finding.severity,
            title=(
                f"Security risk signal: "
                f"{finding.title}"
            ),
            description=(
                "Security risk signal derived from "
                "an evidence-backed security finding. "
                "This signal does not itself authorize "
                "or perform remediation."
            ),
            evidence_available=(
                finding.evidence_available
            ),
            metadata={
                "source_finding": finding.finding_id,
                "source_evidence": (
                    finding.evidence_id
                    or "unavailable"
                ),
            },
        )

    @staticmethod
    def _signal_type_for_severity(
        severity: SecuritySeverity,
    ) -> SecurityRiskSignalType:
        if severity == SecuritySeverity.CRITICAL:
            return (
                SecurityRiskSignalType
                .CRITICAL_SECURITY_RISK
            )

        if severity == SecuritySeverity.HIGH:
            return (
                SecurityRiskSignalType
                .HIGH_SECURITY_RISK
            )

        if severity == SecuritySeverity.MEDIUM:
            return (
                SecurityRiskSignalType
                .ELEVATED_SECURITY_RISK
            )

        if severity == SecuritySeverity.INFO:
            return (
                SecurityRiskSignalType
                .INFORMATIONAL_SECURITY_SIGNAL
            )

        if severity == SecuritySeverity.LOW:
            return (
                SecurityRiskSignalType
                .ELEVATED_SECURITY_RISK
            )

        return (
            SecurityRiskSignalType
            .UNKNOWN_SECURITY_RISK
        )