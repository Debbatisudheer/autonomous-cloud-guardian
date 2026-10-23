from datetime import UTC, datetime

from guardian.domain.security import (
    SecuritySeverity,
)
from guardian.domain.security_risk import (
    SecurityRiskSignal,
    SecurityRiskSignalType,
)


def test_security_risk_signal_accepts_valid_data() -> None:
    signal = SecurityRiskSignal(
        signal_id="signal-001",
        finding_id="finding-001",
        evidence_id="evidence-001",
        resource_id="resource-001",
        signal_type=(
            SecurityRiskSignalType.HIGH_SECURITY_RISK
        ),
        severity=SecuritySeverity.HIGH,
        title="High security risk",
        description="Evidence-backed security risk.",
        evidence_available=True,
        generated_at=datetime(
            2026,
            10,
            23,
            12,
            0,
            tzinfo=UTC,
        ),
        metadata={
            "source_finding": "finding-001",
        },
    )

    assert signal.signal_id == "signal-001"
    assert signal.finding_id == "finding-001"
    assert signal.evidence_id == "evidence-001"
    assert signal.severity == SecuritySeverity.HIGH


def test_security_risk_signal_rejects_empty_signal_id() -> None:
    try:
        SecurityRiskSignal(
            signal_id="",
            finding_id="finding-001",
            evidence_id="evidence-001",
            signal_type=(
                SecurityRiskSignalType.UNKNOWN_SECURITY_RISK
            ),
            severity=SecuritySeverity.UNKNOWN,
            title="Unknown",
            description="Unknown security risk.",
            evidence_available=False,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected validation failure for empty signal ID."
    )


def test_security_risk_signal_rejects_extra_fields() -> None:
    try:
        SecurityRiskSignal(
            signal_id="signal-001",
            finding_id="finding-001",
            evidence_id="evidence-001",
            signal_type=(
                SecurityRiskSignalType.HIGH_SECURITY_RISK
            ),
            severity=SecuritySeverity.HIGH,
            title="High risk",
            description="Risk",
            evidence_available=True,
            unexpected_field="not_allowed",
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected extra-field validation failure."
    )


def test_unknown_signal_type_exists() -> None:
    assert (
        SecurityRiskSignalType.UNKNOWN_SECURITY_RISK
        == "unknown_security_risk"
    )


def test_critical_signal_type_exists() -> None:
    assert (
        SecurityRiskSignalType.CRITICAL_SECURITY_RISK
        == "critical_security_risk"
    )