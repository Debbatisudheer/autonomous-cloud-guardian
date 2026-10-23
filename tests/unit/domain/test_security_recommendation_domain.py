from datetime import UTC, datetime

from guardian.domain.security_recommendation import (
    SecurityRecommendation,
    SecurityRecommendationOutcome,
    SecurityRecommendationPriority,
)


def test_security_recommendation_accepts_valid_data() -> None:
    recommendation = SecurityRecommendation(
        recommendation_id="recommendation-001",
        finding_id="finding-001",
        signal_id="signal-001",
        evidence_id="evidence-001",
        resource_id="resource-001",
        outcome=(
            SecurityRecommendationOutcome.REVIEW
        ),
        priority=(
            SecurityRecommendationPriority.MEDIUM
        ),
        title="Review security configuration",
        recommendation=(
            "Review the observed configuration."
        ),
        rationale=(
            "The configuration requires review."
        ),
        evidence_available=True,
        generated_at=datetime(
            2026,
            10,
            23,
            12,
            0,
            tzinfo=UTC,
        ),
    )

    assert (
        recommendation.recommendation_id
        == "recommendation-001"
    )

    assert (
        recommendation.finding_id
        == "finding-001"
    )

    assert (
        recommendation.signal_id
        == "signal-001"
    )

    assert (
        recommendation.outcome
        == SecurityRecommendationOutcome.REVIEW
    )


def test_recommendation_rejects_empty_id() -> None:
    try:
        SecurityRecommendation(
            recommendation_id="",
            finding_id="finding-001",
            signal_id="signal-001",
            evidence_id="evidence-001",
            outcome=(
                SecurityRecommendationOutcome.REVIEW
            ),
            priority=(
                SecurityRecommendationPriority.LOW
            ),
            title="Review",
            recommendation="Review it.",
            rationale="Evidence exists.",
            evidence_available=True,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected validation failure."
    )


def test_recommendation_rejects_extra_fields() -> None:
    try:
        SecurityRecommendation(
            recommendation_id="recommendation-001",
            finding_id="finding-001",
            signal_id="signal-001",
            evidence_id="evidence-001",
            outcome=(
                SecurityRecommendationOutcome.REVIEW
            ),
            priority=(
                SecurityRecommendationPriority.LOW
            ),
            title="Review",
            recommendation="Review it.",
            rationale="Evidence exists.",
            evidence_available=True,
            unexpected_field="not_allowed",
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected extra-field validation failure."
    )


def test_recommendation_outcomes_exist() -> None:
    assert (
        SecurityRecommendationOutcome.NO_RECOMMENDATION
        == "no_recommendation"
    )

    assert (
        SecurityRecommendationOutcome.REVIEW
        == "review"
    )

    assert (
        SecurityRecommendationOutcome
        .REMEDIATION_RECOMMENDED
        == "remediation_recommended"
    )


def test_recommendation_priorities_exist() -> None:
    assert (
        SecurityRecommendationPriority.LOW
        == "low"
    )

    assert (
        SecurityRecommendationPriority.MEDIUM
        == "medium"
    )

    assert (
        SecurityRecommendationPriority.HIGH
        == "high"
    )