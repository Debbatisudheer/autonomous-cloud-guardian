from datetime import UTC, datetime

from guardian.application.security_risk import (
    SecurityRiskSignalEngine,
)
from guardian.domain.security import (
    SecurityCategory,
    SecurityFinding,
    SecuritySeverity,
    SecuritySource,
)
from guardian.domain.security_risk import (
    SecurityRiskSignalType,
)


def make_finding(
    *,
    severity: SecuritySeverity,
    evidence_available: bool = True,
) -> SecurityFinding:
    return SecurityFinding(
        finding_id="finding-001",
        resource_id="resource-001",
        category=SecurityCategory.CONTAINER,
        severity=severity,
        source=SecuritySource.DOCKER,
        title="Security configuration finding",
        description="Evidence-backed security finding.",
        evidence_id="evidence-001",
        evidence_available=evidence_available,
        detected_at=datetime(
            2026,
            10,
            23,
            12,
            0,
            tzinfo=UTC,
        ),
    )


def test_high_finding_generates_high_risk_signal() -> None:
    engine = SecurityRiskSignalEngine()

    signals = engine.generate(
        [
            make_finding(
                severity=SecuritySeverity.HIGH
            )
        ]
    )

    assert len(signals) == 1

    signal = signals[0]

    assert (
        signal.signal_type
        == SecurityRiskSignalType.HIGH_SECURITY_RISK
    )

    assert signal.severity == SecuritySeverity.HIGH
    assert signal.finding_id == "finding-001"
    assert signal.evidence_id == "evidence-001"


def test_critical_finding_generates_critical_signal() -> None:
    engine = SecurityRiskSignalEngine()

    signals = engine.generate(
        [
            make_finding(
                severity=SecuritySeverity.CRITICAL
            )
        ]
    )

    assert (
        signals[0].signal_type
        == SecurityRiskSignalType.CRITICAL_SECURITY_RISK
    )


def test_medium_finding_generates_elevated_signal() -> None:
    engine = SecurityRiskSignalEngine()

    signals = engine.generate(
        [
            make_finding(
                severity=SecuritySeverity.MEDIUM
            )
        ]
    )

    assert (
        signals[0].signal_type
        == SecurityRiskSignalType.ELEVATED_SECURITY_RISK
    )


def test_low_finding_generates_elevated_signal() -> None:
    engine = SecurityRiskSignalEngine()

    signals = engine.generate(
        [
            make_finding(
                severity=SecuritySeverity.LOW
            )
        ]
    )

    assert (
        signals[0].signal_type
        == SecurityRiskSignalType.ELEVATED_SECURITY_RISK
    )


def test_info_finding_generates_informational_signal() -> None:
    engine = SecurityRiskSignalEngine()

    signals = engine.generate(
        [
            make_finding(
                severity=SecuritySeverity.INFO
            )
        ]
    )

    assert (
        signals[0].signal_type
        == SecurityRiskSignalType
        .INFORMATIONAL_SECURITY_SIGNAL
    )


def test_unknown_finding_generates_unknown_signal() -> None:
    engine = SecurityRiskSignalEngine()

    signals = engine.generate(
        [
            make_finding(
                severity=SecuritySeverity.UNKNOWN
            )
        ]
    )

    assert (
        signals[0].signal_type
        == SecurityRiskSignalType.UNKNOWN_SECURITY_RISK
    )


def test_unavailable_evidence_remains_unavailable() -> None:
    engine = SecurityRiskSignalEngine()

    signals = engine.generate(
        [
            make_finding(
                severity=SecuritySeverity.UNKNOWN,
                evidence_available=False,
            )
        ]
    )

    assert len(signals) == 1

    signal = signals[0]

    assert signal.evidence_available is False
    assert signal.evidence_id == "evidence-001"


def test_signal_preserves_finding_correlation() -> None:
    engine = SecurityRiskSignalEngine()

    finding = make_finding(
        severity=SecuritySeverity.HIGH
    )

    signals = engine.generate(
        [finding]
    )

    signal = signals[0]

    assert signal.finding_id == finding.finding_id
    assert signal.evidence_id == finding.evidence_id
    assert signal.resource_id == finding.resource_id


def test_empty_findings_produce_no_signals() -> None:
    engine = SecurityRiskSignalEngine()

    signals = engine.generate([])

    assert signals == []


def test_multiple_findings_generate_multiple_signals() -> None:
    engine = SecurityRiskSignalEngine()

    findings = [
        make_finding(
            severity=SecuritySeverity.HIGH
        ),
        SecurityFinding(
            finding_id="finding-002",
            resource_id="resource-002",
            category=SecurityCategory.NETWORK,
            severity=SecuritySeverity.INFO,
            source=SecuritySource.DOCKER,
            title="Network observation",
            description="Network evidence.",
            evidence_id="evidence-002",
            evidence_available=True,
        ),
    ]

    signals = engine.generate(
        findings
    )

    assert len(signals) == 2

    assert {
        signal.finding_id
        for signal in signals
    } == {
        "finding-001",
        "finding-002",
    }


def test_signal_contains_source_metadata() -> None:
    engine = SecurityRiskSignalEngine()

    signals = engine.generate(
        [
            make_finding(
                severity=SecuritySeverity.HIGH
            )
        ]
    )

    signal = signals[0]

    assert (
        signal.metadata["source_finding"]
        == "finding-001"
    )

    assert (
        signal.metadata["source_evidence"]
        == "evidence-001"
    )