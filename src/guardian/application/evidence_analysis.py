from __future__ import annotations

from guardian.domain.evidence_analysis import (
    EvidenceAnalysis,
    EvidenceAnalysisLevel,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
)


class EvidenceAnalysisService:
    """
    Performs deterministic analysis of observability evidence.

    The service only interprets the evidence already present in an
    observability event.

    It does not generate predictions, decisions, recommendations,
    remediation commands, or infrastructure actions.
    """

    def analyze(
        self,
        event: ObservabilityEvent,
    ) -> EvidenceAnalysis:
        level = self._determine_level(event)

        return EvidenceAnalysis(
            source_event_id=event.event_id,
            resource_id=event.resource_id,
            metric=event.metric,
            level=level,
            value=event.value,
            unit=event.unit,
            evidence_available=True,
            finding=self._build_finding(
                event,
                level,
            ),
        )

    @staticmethod
    def _determine_level(
        event: ObservabilityEvent,
    ) -> EvidenceAnalysisLevel:
        health_level = event.health_level.value

        if health_level == "critical":
            return EvidenceAnalysisLevel.CRITICAL

        if health_level == "warning":
            return EvidenceAnalysisLevel.WARNING

        if health_level == "healthy":
            return EvidenceAnalysisLevel.NORMAL

        return EvidenceAnalysisLevel.UNKNOWN

    @staticmethod
    def _build_finding(
        event: ObservabilityEvent,
        level: EvidenceAnalysisLevel,
    ) -> str:
        if level == EvidenceAnalysisLevel.CRITICAL:
            return (
                f"Observed {event.metric} value "
                f"{event.value} {event.unit} is currently "
                "classified as critical."
            )

        if level == EvidenceAnalysisLevel.WARNING:
            return (
                f"Observed {event.metric} value "
                f"{event.value} {event.unit} is currently "
                "classified as warning."
            )

        if level == EvidenceAnalysisLevel.NORMAL:
            return (
                f"Observed {event.metric} value "
                f"{event.value} {event.unit} is currently "
                "within the healthy operational classification."
            )

        return (
            f"Observed {event.metric} value "
            f"{event.value} {event.unit} has insufficient "
            "health classification evidence."
        )