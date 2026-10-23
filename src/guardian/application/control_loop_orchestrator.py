from __future__ import annotations

from guardian.domain.control_loop import (
    ControlLoopCycle,
    ControlLoopState,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
)


class ControlLoopOrchestrator:
    """
    Coordinates the lifecycle of one autonomous control cycle.

    Phase 5.2 establishes orchestration only. It does not perform
    prediction, decision-making, infrastructure actions,
    remediation, or learning.
    """

    def start(
        self,
        event: ObservabilityEvent,
    ) -> ControlLoopCycle:
        """
        Create a new control cycle from an observability event.
        """

        return ControlLoopCycle.from_observability_event(
            event
        )

    def advance_to_analysis(
        self,
        cycle: ControlLoopCycle,
    ) -> ControlLoopCycle:
        return self._transition(
            cycle,
            ControlLoopState.ANALYZING,
        )

    def advance_to_prediction(
        self,
        cycle: ControlLoopCycle,
    ) -> ControlLoopCycle:
        return self._transition(
            cycle,
            ControlLoopState.PREDICTING,
        )

    def advance_to_decision(
        self,
        cycle: ControlLoopCycle,
    ) -> ControlLoopCycle:
        return self._transition(
            cycle,
            ControlLoopState.DECIDING,
        )

    def advance_to_action(
        self,
        cycle: ControlLoopCycle,
    ) -> ControlLoopCycle:
        return self._transition(
            cycle,
            ControlLoopState.ACTING,
        )

    def advance_to_verification(
        self,
        cycle: ControlLoopCycle,
    ) -> ControlLoopCycle:
        return self._transition(
            cycle,
            ControlLoopState.VERIFYING,
        )

    def advance_to_learning(
        self,
        cycle: ControlLoopCycle,
    ) -> ControlLoopCycle:
        return self._transition(
            cycle,
            ControlLoopState.LEARNING,
        )

    def complete(
        self,
        cycle: ControlLoopCycle,
    ) -> ControlLoopCycle:
        return self._transition(
            cycle,
            ControlLoopState.COMPLETED,
        )

    def fail(
        self,
        cycle: ControlLoopCycle,
        reason: str,
    ) -> ControlLoopCycle:
        return cycle.fail(reason)

    @staticmethod
    def _transition(
        cycle: ControlLoopCycle,
        target_state: ControlLoopState,
    ) -> ControlLoopCycle:
        return cycle.transition_to(target_state)