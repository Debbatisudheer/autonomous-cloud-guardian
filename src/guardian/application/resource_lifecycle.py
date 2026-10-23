from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.resource import Resource, ResourceStatus


class InvalidResourceTransitionError(Exception):
    """Raised when a resource lifecycle transition is not allowed."""


class ResourceLifecycleOperation(BaseModel):
    """
    Result of a validated resource lifecycle operation.

    This model records the lifecycle transition in the control plane.
    It does not represent proof that an infrastructure provider
    performed the operation.
    """

    model_config = ConfigDict(extra="forbid")

    resource_id: str = Field(min_length=1)
    previous_status: ResourceStatus
    target_status: ResourceStatus
    observed_status: ResourceStatus
    changed: bool
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )


class ResourceLifecycleManager:
    """
    Validates and applies resource lifecycle transitions.

    This component only updates the in-memory Resource model.
    It does not perform infrastructure operations.
    """

    _ALLOWED_TRANSITIONS: ClassVar[
        dict[ResourceStatus, set[ResourceStatus]]
    ] = {
        ResourceStatus.UNKNOWN: {
            ResourceStatus.CREATING,
            ResourceStatus.RUNNING,
            ResourceStatus.STOPPED,
            ResourceStatus.FAILED,
        },
        ResourceStatus.CREATING: {
            ResourceStatus.RUNNING,
            ResourceStatus.FAILED,
            ResourceStatus.DELETING,
        },
        ResourceStatus.RUNNING: {
            ResourceStatus.STOPPED,
            ResourceStatus.FAILED,
            ResourceStatus.DELETING,
        },
        ResourceStatus.STOPPED: {
            ResourceStatus.CREATING,
            ResourceStatus.RUNNING,
            ResourceStatus.DELETING,
        },
        ResourceStatus.FAILED: {
            ResourceStatus.CREATING,
            ResourceStatus.DELETING,
        },
        ResourceStatus.DELETING: {
            ResourceStatus.DELETED,
            ResourceStatus.FAILED,
        },
        ResourceStatus.DELETED: set(),
    }

    def can_transition(
        self,
        current: ResourceStatus,
        target: ResourceStatus,
    ) -> bool:
        """Return whether the requested lifecycle transition is valid."""
        return target in self._ALLOWED_TRANSITIONS.get(current, set())

    def transition(
        self,
        current: ResourceStatus,
        target: ResourceStatus,
    ) -> ResourceStatus:
        """
        Validate and return the requested target state.

        No infrastructure action is performed here.
        """
        if not self.can_transition(current, target):
            raise InvalidResourceTransitionError(
                f"Invalid resource lifecycle transition: "
                f"{current.value} -> {target.value}."
            )

        return target

    def transition_resource(
        self,
        resource: Resource,
        target: ResourceStatus,
    ) -> Resource:
        """
        Apply a validated lifecycle transition to a Resource.

        The existing Resource object is updated only after the
        transition has been validated.
        """
        new_status = self.transition(
            current=resource.status,
            target=target,
        )

        resource.status = new_status

        return resource

    def execute(
        self,
        resource: Resource,
        target: ResourceStatus,
    ) -> ResourceLifecycleOperation:
        """
        Validate and apply a lifecycle operation to the in-memory resource.

        This is a control-plane state operation only. It does not call
        Docker or any other infrastructure provider.
        """
        previous_status = resource.status

        self.transition_resource(
            resource=resource,
            target=target,
        )

        return ResourceLifecycleOperation(
            resource_id=resource.id,
            previous_status=previous_status,
            target_status=target,
            observed_status=resource.status,
            changed=previous_status != resource.status,
        )