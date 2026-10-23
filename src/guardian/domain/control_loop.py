from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.observability_event import (
    ObservabilityEvent,
)


class ControlLoopState(StrEnum):
    """
    Lifecycle state of an autonomous control cycle.

    These states define the control-loop boundary. They do not
    imply that prediction, decision, action, verification, or
    learning capabilities have already been implemented.
    """

    RECEIVED = "received"
    ANALYZING = "analyzing"
    PREDICTING = "predicting"
    DECIDING = "deciding"
    ACTING = "acting"
    VERIFYING = "verifying"
    LEARNING = "learning"
    COMPLETED = "completed"
    FAILED = "failed"


class ControlLoopCycle(BaseModel):
    """
    Evidence-linked context for one autonomous control cycle.

    A cycle begins from an existing observability event and carries
    its identity through the future control-loop stages.

    This model does not generate predictions, decisions, actions,
    or remediation results.
    """

    model_config = ConfigDict(extra="forbid")

    cycle_id: str = Field(
        default_factory=lambda: str(uuid4()),
        min_length=1,
    )

    source_event_id: str = Field(min_length=1)

    resource_id: str = Field(min_length=1)

    metric: str = Field(min_length=1)

    state: ControlLoopState = ControlLoopState.RECEIVED

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    failure_reason: str | None = None

    @classmethod
    def from_observability_event(
        cls,
        event: ObservabilityEvent,
    ) -> ControlLoopCycle:
        """
        Create a control cycle from an existing observability event.

        The event itself remains the source of evidence. No new
        telemetry, prediction, decision, or action is generated.
        """

        now = datetime.now(UTC)

        return cls(
            source_event_id=event.event_id,
            resource_id=event.resource_id,
            metric=event.metric,
            state=ControlLoopState.RECEIVED,
            created_at=now,
            updated_at=now,
        )

    def transition_to(
        self,
        state: ControlLoopState,
    ) -> ControlLoopCycle:
        """
        Create a new cycle representation with an updated lifecycle state.

        This method only changes lifecycle metadata. It does not
        execute the capability represented by the state.
        """

        return self.model_copy(
            update={
                "state": state,
                "updated_at": datetime.now(UTC),
            }
        )

    def fail(
        self,
        reason: str,
    ) -> ControlLoopCycle:
        """
        Mark the cycle as failed with an explicit reason.

        Failure recording is bookkeeping only. No remediation is
        automatically performed.
        """

        if not reason.strip():
            raise ValueError(
                "Failure reason must not be empty."
            )

        return self.model_copy(
            update={
                "state": ControlLoopState.FAILED,
                "failure_reason": reason,
                "updated_at": datetime.now(UTC),
            }
        )