from __future__ import annotations

from guardian.application.control_plane_events import (
    ControlPlaneEventRecorder,
)
from guardian.application.control_plane_operations import (
    ControlPlaneOperations,
)
from guardian.domain.control_plane_event import (
    ControlPlaneEventType,
)
from guardian.domain.reconciliation import (
    ReconciliationStatus,
)
from guardian.domain.resource import (
    Resource,
    ResourceHealth,
    ResourceStatus,
)
from guardian.infrastructure.adapters.base import (
    InfrastructureAdapter,
)


class FakeInfrastructureAdapter(InfrastructureAdapter):
    """
    Test-only infrastructure adapter.

    It provides deterministic resources without connecting to Docker.
    """

    def __init__(
        self,
        resources: list[Resource],
    ) -> None:
        self._resources = resources

    def discover_resources(self) -> list[Resource]:
        return list(self._resources)


def test_discovery_records_resource_discovered_events() -> None:
    resources = [
        Resource(
            id="resource-1",
            name="resource-1",
            resource_type="container",
            status=ResourceStatus.RUNNING,
        ),
        Resource(
            id="resource-2",
            name="resource-2",
            resource_type="container",
            status=ResourceStatus.STOPPED,
        ),
    ]

    recorder = ControlPlaneEventRecorder()

    operations = ControlPlaneOperations(
        adapter=FakeInfrastructureAdapter(resources),
        event_recorder=recorder,
    )

    discovered = operations.discover_resources()

    assert discovered == resources

    events = operations.events()

    assert len(events) == 2

    assert all(
        event.event_type
        == ControlPlaneEventType.RESOURCE_DISCOVERED
        for event in events
    )

    assert [event.resource_id for event in events] == [
        "resource-1",
        "resource-2",
    ]


def test_reconciliation_records_event_only_for_drift() -> None:
    resource = Resource(
        id="resource-1",
        name="resource-1",
        resource_type="container",
        status=ResourceStatus.STOPPED,
    )

    recorder = ControlPlaneEventRecorder()

    operations = ControlPlaneOperations(
        adapter=FakeInfrastructureAdapter([]),
        event_recorder=recorder,
    )

    result = operations.reconcile_resource(
        resource=resource,
        desired_status=ResourceStatus.RUNNING,
    )

    assert result.status == ReconciliationStatus.DRIFTED

    events = operations.events()

    assert len(events) == 1

    assert (
        events[0].event_type
        == ControlPlaneEventType.RESOURCE_DRIFT_DETECTED
    )

    assert events[0].resource_id == "resource-1"

    assert events[0].details == {
        "desired_status": "running",
        "observed_status": "stopped",
    }


def test_reconciliation_does_not_record_event_when_in_sync() -> None:
    resource = Resource(
        id="resource-1",
        name="resource-1",
        resource_type="container",
        status=ResourceStatus.RUNNING,
    )

    recorder = ControlPlaneEventRecorder()

    operations = ControlPlaneOperations(
        adapter=FakeInfrastructureAdapter([]),
        event_recorder=recorder,
    )

    result = operations.reconcile_resource(
        resource=resource,
        desired_status=ResourceStatus.RUNNING,
    )

    assert result.status == ReconciliationStatus.IN_SYNC

    assert operations.events() == []


def test_multi_resource_reconciliation_records_only_drift_events() -> None:
    resources = [
        Resource(
            id="resource-1",
            name="resource-1",
            resource_type="container",
            status=ResourceStatus.RUNNING,
        ),
        Resource(
            id="resource-2",
            name="resource-2",
            resource_type="container",
            status=ResourceStatus.STOPPED,
        ),
    ]

    recorder = ControlPlaneEventRecorder()

    operations = ControlPlaneOperations(
        adapter=FakeInfrastructureAdapter([]),
        event_recorder=recorder,
    )

    results = operations.reconcile_resources(
        resources=resources,
        desired_statuses={
            "resource-1": ResourceStatus.RUNNING,
            "resource-2": ResourceStatus.RUNNING,
        },
    )

    assert [result.status for result in results] == [
        ReconciliationStatus.IN_SYNC,
        ReconciliationStatus.DRIFTED,
    ]

    events = operations.events()

    assert len(events) == 1

    assert events[0].resource_id == "resource-2"

    assert (
        events[0].event_type
        == ControlPlaneEventType.RESOURCE_DRIFT_DETECTED
    )


def test_lifecycle_change_records_event() -> None:
    resource = Resource(
        id="resource-1",
        name="resource-1",
        resource_type="container",
        status=ResourceStatus.STOPPED,
    )

    recorder = ControlPlaneEventRecorder()

    operations = ControlPlaneOperations(
        adapter=FakeInfrastructureAdapter([]),
        event_recorder=recorder,
    )

    operation = operations.change_lifecycle(
        resource=resource,
        target_status=ResourceStatus.RUNNING,
    )

    assert operation.changed is True

    assert resource.status == ResourceStatus.RUNNING

    events = operations.events()

    assert len(events) == 1

    assert (
        events[0].event_type
        == ControlPlaneEventType.RESOURCE_LIFECYCLE_CHANGED
    )

    assert events[0].details == {
        "previous_status": "stopped",
        "target_status": "running",
    }


def test_health_assessment_does_not_invent_health_change() -> None:
    resource = Resource(
        id="resource-1",
        name="resource-1",
        resource_type="container",
        status=ResourceStatus.RUNNING,
        health=ResourceHealth.UNKNOWN,
    )

    recorder = ControlPlaneEventRecorder()

    operations = ControlPlaneOperations(
        adapter=FakeInfrastructureAdapter([]),
        event_recorder=recorder,
    )

    observation = operations.assess_health(resource)

    assert observation.health == ResourceHealth.UNKNOWN

    assert operations.events() == []


def test_control_plane_operations_exposes_recorder() -> None:
    recorder = ControlPlaneEventRecorder()

    operations = ControlPlaneOperations(
        adapter=FakeInfrastructureAdapter([]),
        event_recorder=recorder,
    )

    assert operations.event_recorder() is recorder