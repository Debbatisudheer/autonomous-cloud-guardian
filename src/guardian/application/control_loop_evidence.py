from __future__ import annotations

from dataclasses import dataclass

from guardian.application.evidence_analysis import (
    EvidenceAnalysisService,
)
from guardian.domain.control_loop import (
    ControlLoopCycle,
    ControlLoopState,
)
from guardian.domain.evidence_analysis import (
    EvidenceAnalysis,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
)


@dataclass(frozen=True)
class ControlLoopEvidenceResult:
    """
    Result of evidence intake and analysis for one control cycle.

    The result contains only evidence and deterministic analysis.
    No prediction, decision, or infrastructure action is produced.
    """

    cycle: ControlLoopCycle

    analysis: EvidenceAnalysis


class ControlLoopEvidenceService:
    """
    Connects observability evidence to the control-loop analysis stage.
    """

    def __init__(
        self,
        analysis_service: EvidenceAnalysisService | None = None,
    ) -> None:
        self._analysis_service = (
            analysis_service
            or EvidenceAnalysisService()
        )

    def intake_and_analyze(
        self,
        cycle: ControlLoopCycle,
        event: ObservabilityEvent,
    ) -> ControlLoopEvidenceResult:
        self._validate_evidence_identity(
            cycle,
            event,
        )

        if cycle.state != ControlLoopState.RECEIVED:
            raise ValueError(
                "Control cycle must be in RECEIVED state "
                "before evidence analysis."
            )

        analyzing_cycle = cycle.transition_to(
            ControlLoopState.ANALYZING
        )

        analysis = self._analysis_service.analyze(event)

        return ControlLoopEvidenceResult(
            cycle=analyzing_cycle,
            analysis=analysis,
        )

    @staticmethod
    def _validate_evidence_identity(
        cycle: ControlLoopCycle,
        event: ObservabilityEvent,
    ) -> None:
        if cycle.source_event_id != event.event_id:
            raise ValueError(
                "Control cycle source event does not match "
                "the supplied observability event."
            )

        if cycle.resource_id != event.resource_id:
            raise ValueError(
                "Control cycle resource does not match "
                "the supplied observability event."
            )

        if cycle.metric != event.metric:
            raise ValueError(
                "Control cycle metric does not match "
                "the supplied observability event."
            )