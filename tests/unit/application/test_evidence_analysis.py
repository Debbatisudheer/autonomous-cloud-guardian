from datetime import UTC, datetime

import pytest

from guardian.application.evidence_analysis import (
    EvidenceAnalysisService,
)
from guardian.domain.evidence_analysis import (
    EvidenceAnalysisLevel,
)
from guardian.domain.health_signal import (
    HealthSignalLevel,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
    ObservabilityEventType,
)


def make_event(
    health_level: HealthSignalLevel,
) -> ObservabilityEvent:
    return ObservabilityEvent(
        event_id="analysis-event-001",
        event_type=(
            ObservabilityEventType.HEALTH_SIGNAL_GENERATED
        ),
        resource_id="resource-001",
        metric="cpu_usage_percent",
        value=82.0,
        unit="percent",
        health_level=health_level,
        observed_at=datetime.now(UTC),
        source="docker",
    )


def test_healthy_evidence_is_classified_as_normal() -> None:
    service = EvidenceAnalysisService()

    result = service.analyze(
        make_event(HealthSignalLevel.HEALTHY)
    )

    assert result.level == EvidenceAnalysisLevel.NORMAL
    assert result.evidence_available is True


def test_warning_evidence_is_classified_as_warning() -> None:
    service = EvidenceAnalysisService()

    result = service.analyze(
        make_event(HealthSignalLevel.WARNING)
    )

    assert result.level == EvidenceAnalysisLevel.WARNING


def test_critical_evidence_is_classified_as_critical() -> None:
    service = EvidenceAnalysisService()

    result = service.analyze(
        make_event(HealthSignalLevel.CRITICAL)
    )

    assert result.level == EvidenceAnalysisLevel.CRITICAL


def test_analysis_preserves_evidence_identity() -> None:
    service = EvidenceAnalysisService()
    event = make_event(HealthSignalLevel.WARNING)

    result = service.analyze(event)

    assert result.source_event_id == event.event_id
    assert result.resource_id == event.resource_id
    assert result.metric == event.metric
    assert result.value == event.value
    assert result.unit == event.unit


def test_analysis_contains_finding() -> None:
    service = EvidenceAnalysisService()

    result = service.analyze(
        make_event(HealthSignalLevel.CRITICAL)
    )

    assert result.finding
    assert "critical" in result.finding


@pytest.mark.parametrize(
    "health_level,expected_level",
    [
        (
            HealthSignalLevel.HEALTHY,
            EvidenceAnalysisLevel.NORMAL,
        ),
        (
            HealthSignalLevel.WARNING,
            EvidenceAnalysisLevel.WARNING,
        ),
        (
            HealthSignalLevel.CRITICAL,
            EvidenceAnalysisLevel.CRITICAL,
        ),
    ],
)
def test_health_classification_mapping(
    health_level: HealthSignalLevel,
    expected_level: EvidenceAnalysisLevel,
) -> None:
    service = EvidenceAnalysisService()

    result = service.analyze(
        make_event(health_level)
    )

    assert result.level == expected_level