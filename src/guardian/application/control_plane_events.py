from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from guardian.domain.control_plane_event import (
    ControlPlaneEvent,
    ControlPlaneEventType,
)
from guardian.domain.resource import Resource, ResourceStatus


class ControlPlaneEventRecorder:
    """
    Records control-plane events in memory.

    Events are generated only from explicit control-plane operations.
    This recorder does not publish events externally.
    """

    def __init__(self) -> None:
        self._events: list[ControlPlaneEvent] = []

    def record(self, event: ControlPlaneEvent) -> None:
        """Record an already-created control-plane event."""
        self._events.append(event)

    def record_resource_discovered(
        self,
        resource: Resource,
    ) -> ControlPlaneEvent:
        """Record that a resource was discovered."""
        return self._record_generated_event(
            event_type=ControlPlaneEventType.RESOURCE_DISCOVERED,
            resource=resource,
            reason="Resource was discovered by the control plane.",
        )

    def record_resource_state_changed(
        self,
        resource: Resource,
        previous_status: ResourceStatus,
    ) -> ControlPlaneEvent:
        """Record a resource state change."""
        return self._record_generated_event(
            event_type=ControlPlaneEventType.RESOURCE_STATE_CHANGED,
            resource=resource,
            reason="Observed resource state changed.",
            details={
                "previous_status": previous_status.value,
                "observed_status": resource.status.value,
            },
        )

    def record_resource_drift_detected(
        self,
        resource: Resource,
        desired_status: ResourceStatus,
    ) -> ControlPlaneEvent:
        """Record detected resource drift."""
        return self._record_generated_event(
            event_type=ControlPlaneEventType.RESOURCE_DRIFT_DETECTED,
            resource=resource,
            reason="Observed resource state differs from desired state.",
            details={
                "desired_status": desired_status.value,
                "observed_status": resource.status.value,
            },
        )

    def record_resource_health_changed(
        self,
        resource: Resource,
        previous_health: str,
    ) -> ControlPlaneEvent:
        """Record a resource health change."""
        return self._record_generated_event(
            event_type=ControlPlaneEventType.RESOURCE_HEALTH_CHANGED,
            resource=resource,
            reason="Observed resource health changed.",
            details={
                "previous_health": previous_health,
                "observed_health": resource.health.value,
            },
        )

    def record_resource_lifecycle_changed(
        self,
        resource: Resource,
        previous_status: ResourceStatus,
    ) -> ControlPlaneEvent:
        """Record a resource lifecycle change."""
        return self._record_generated_event(
            event_type=ControlPlaneEventType.RESOURCE_LIFECYCLE_CHANGED,
            resource=resource,
            reason="Resource lifecycle state changed.",
            details={
                "previous_status": previous_status.value,
                "target_status": resource.status.value,
            },
        )

    def list_events(self) -> list[ControlPlaneEvent]:
        """Return all recorded events in insertion order."""
        return list(self._events)

    def get_events_for_resource(
        self,
        resource_id: str,
    ) -> list[ControlPlaneEvent]:
        """Return events associated with a specific resource."""
        return [
            event
            for event in self._events
            if event.resource_id == resource_id
        ]

    def get_events_by_type(
        self,
        event_type: ControlPlaneEventType,
    ) -> list[ControlPlaneEvent]:
        """Return events matching a specific event type."""
        return [
            event
            for event in self._events
            if event.event_type == event_type
        ]

    def clear(self) -> None:
        """Remove all recorded events."""
        self._events.clear()

    def _record_generated_event(
        self,
        event_type: ControlPlaneEventType,
        resource: Resource,
        reason: str,
        details: dict[str, str] | None = None,
    ) -> ControlPlaneEvent:
        event = ControlPlaneEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            resource_id=resource.id,
            occurred_at=datetime.now(UTC),
            reason=reason,
            details=details or {},
        )

        self.record(event)

        return event