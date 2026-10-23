from guardian.application.security_recommendation import (
    SecurityRecommendationEngine,
)
from guardian.domain.security import (
    SecurityCategory,
    SecurityFinding,
    SecuritySeverity,
    SecuritySource,
)
from guardian.domain.security_recommendation import (
    SecurityRecommendationOutcome,
    SecurityRecommendationPriority,
)
from guardian.domain.security_risk import (
    SecurityRiskSignal,
    SecurityRiskSignalType,
)


def make_finding(
    severity: SecuritySeverity,
    evidence_available: bool = True,
) -> SecurityFinding:
    return SecurityFinding(
        finding_id="finding-001",
        resource_id="resource-001",
        category=SecurityCategory.CONTAINER,
        severity=severity,
        source=SecuritySource.DOCKER,
        title="Container security configuration",
        description="Observed Docker security configuration.",
        evidence_id="evidence-001",
        evidence_available=evidence_available,
    )


def make_signal(
    severity: SecuritySeverity,
) -> SecurityRiskSignal:
    signal_type = {
        SecuritySeverity.UNKNOWN: (
            SecurityRiskSignalType.UNKNOWN_SECURITY_RISK
        ),
        SecuritySeverity.INFO: (
            SecurityRiskSignalType
            .INFORMATIONAL_SECURITY_SIGNAL
        ),
        SecuritySeverity.LOW: (
            SecurityRiskSignalType.ELEVATED_SECURITY_RISK
        ),
        SecuritySeverity.MEDIUM: (
            SecurityRiskSignalType.ELEVATED_SECURITY_RISK
        ),
        SecuritySeverity.HIGH: (
            SecurityRiskSignalType.HIGH_SECURITY_RISK
        ),
        SecuritySeverity.CRITICAL: (
            SecurityRiskSignalType
            .CRITICAL_SECURITY_RISK
        ),
    }[severity]

    return SecurityRiskSignal(
        signal_id="signal-001",
        finding_id="finding-001",
        evidence_id="evidence-001",
        resource_id="resource-001",
        signal_type=signal_type,
        severity=severity,
        title="Security risk signal",
        description="Evidence-backed security signal.",
        evidence_available=True,
    )


def test_critical_finding_recommends_high_priority_remediation_review() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.CRITICAL
    )

    signal = make_signal(
        SecuritySeverity.CRITICAL
    )

    recommendation = engine.generate(
        finding,
        signal,
    )

    assert (
        recommendation.outcome
        == SecurityRecommendationOutcome
        .REMEDIATION_RECOMMENDED
    )

    assert (
        recommendation.priority
        == SecurityRecommendationPriority.HIGH
    )


def test_high_finding_recommends_high_priority_remediation_review() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.HIGH
    )

    signal = make_signal(
        SecuritySeverity.HIGH
    )

    recommendation = engine.generate(
        finding,
        signal,
    )

    assert (
        recommendation.outcome
        == SecurityRecommendationOutcome
        .REMEDIATION_RECOMMENDED
    )

    assert (
        recommendation.priority
        == SecurityRecommendationPriority.HIGH
    )


def test_medium_finding_generates_medium_review() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.MEDIUM
    )

    signal = make_signal(
        SecuritySeverity.MEDIUM
    )

    recommendation = engine.generate(
        finding,
        signal,
    )

    assert (
        recommendation.outcome
        == SecurityRecommendationOutcome.REVIEW
    )

    assert (
        recommendation.priority
        == SecurityRecommendationPriority.MEDIUM
    )


def test_low_finding_generates_low_review() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.LOW
    )

    signal = make_signal(
        SecuritySeverity.LOW
    )

    recommendation = engine.generate(
        finding,
        signal,
    )

    assert (
        recommendation.outcome
        == SecurityRecommendationOutcome.REVIEW
    )

    assert (
        recommendation.priority
        == SecurityRecommendationPriority.LOW
    )


def test_info_finding_generates_low_review() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.INFO
    )

    signal = make_signal(
        SecuritySeverity.INFO
    )

    recommendation = engine.generate(
        finding,
        signal,
    )

    assert (
        recommendation.outcome
        == SecurityRecommendationOutcome.REVIEW
    )

    assert (
        recommendation.priority
        == SecurityRecommendationPriority.LOW
    )


def test_unknown_finding_generates_no_recommendation() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.UNKNOWN
    )

    signal = make_signal(
        SecuritySeverity.UNKNOWN
    )

    recommendation = engine.generate(
        finding,
        signal,
    )

    assert (
        recommendation.outcome
        == SecurityRecommendationOutcome
        .NO_RECOMMENDATION
    )

    assert (
        recommendation.priority
        == SecurityRecommendationPriority.LOW
    )


def test_unavailable_evidence_generates_no_recommendation() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.HIGH,
        evidence_available=False,
    )

    signal = make_signal(
        SecuritySeverity.HIGH
    )

    recommendation = engine.generate(
        finding,
        signal,
    )

    assert (
        recommendation.outcome
        == SecurityRecommendationOutcome
        .NO_RECOMMENDATION
    )

    assert (
        recommendation.evidence_available
        is False
    )


def test_finding_and_signal_correlation_is_preserved() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.HIGH
    )

    signal = make_signal(
        SecuritySeverity.HIGH
    )

    recommendation = engine.generate(
        finding,
        signal,
    )

    assert (
        recommendation.finding_id
        == finding.finding_id
    )

    assert (
        recommendation.signal_id
        == signal.signal_id
    )

    assert (
        recommendation.evidence_id
        == finding.evidence_id
    )

    assert (
        recommendation.resource_id
        == finding.resource_id
    )


def test_mismatched_finding_id_is_rejected() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.HIGH
    )

    signal = make_signal(
        SecuritySeverity.HIGH
    )

    signal = signal.model_copy(
        update={
            "finding_id": "different-finding"
        }
    )

    try:
        engine.generate(
            finding,
            signal,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected finding correlation failure."
    )


def test_mismatched_evidence_id_is_rejected() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.HIGH
    )

    signal = make_signal(
        SecuritySeverity.HIGH
    )

    signal = signal.model_copy(
        update={
            "evidence_id": "different-evidence"
        }
    )

    try:
        engine.generate(
            finding,
            signal,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected evidence correlation failure."
    )


def test_mismatched_resource_is_rejected() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.HIGH
    )

    signal = make_signal(
        SecuritySeverity.HIGH
    )

    signal = signal.model_copy(
        update={
            "resource_id": "different-resource"
        }
    )

    try:
        engine.generate(
            finding,
            signal,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected resource correlation failure."
    )


def test_mismatched_severity_is_rejected() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.HIGH
    )

    signal = make_signal(
        SecuritySeverity.MEDIUM
    )

    try:
        engine.generate(
            finding,
            signal,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected severity correlation failure."
    )


def test_recommendation_contains_source_metadata() -> None:
    engine = SecurityRecommendationEngine()

    finding = make_finding(
        SecuritySeverity.HIGH
    )

    signal = make_signal(
        SecuritySeverity.HIGH
    )

    recommendation = engine.generate(
        finding,
        signal,
    )

    assert (
        recommendation.metadata["source_finding"]
        == finding.finding_id
    )

    assert (
        recommendation.metadata["source_signal"]
        == signal.signal_id
    )