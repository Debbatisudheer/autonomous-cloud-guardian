from __future__ import annotations

from guardian.application.control_plane_events import (
    ControlPlaneEventRecorder,
)
from guardian.domain.control_plane_event import (
    ControlPlaneEvent,
    ControlPlaneEventType,
)
from guardian.domain.resource import Resource, ResourceStatus


def _event(
    event_id: str,
    resource_id: str,
    event_type: ControlPlaneEventType,
) -> ControlPlaneEvent:
    return ControlPlaneEvent(
        event_id=event_id,
        event_type=event_type,
        resource_id=resource_id,
        reason=f"Test event {event_id}.",
    )


def test_record_stores_event() -> None:
    recorder = ControlPlaneEventRecorder()

    event = _event(
        "event-1",
        "resource-1",
        ControlPlaneEventType.RESOURCE_DISCOVERED,
    )

    recorder.record(event)

    assert recorder.list_events() == [event]


def test_list_events_preserves_insertion_order() -> None:
    recorder = ControlPlaneEventRecorder()

    first = _event(
        "event-1",
        "resource-1",
        ControlPlaneEventType.RESOURCE_DISCOVERED,
    )
    second = _event(
        "event-2",
        "resource-2",
        ControlPlaneEventType.RESOURCE_HEALTH_CHANGED,
    )

    recorder.record(first)
    recorder.record(second)

    assert recorder.list_events() == [first, second]


def test_list_events_returns_copy() -> None:
    recorder = ControlPlaneEventRecorder()

    event = _event(
        "event-1",
        "resource-1",
        ControlPlaneEventType.RESOURCE_DISCOVERED,
    )

    recorder.record(event)

    events = recorder.list_events()
    events.clear()

    assert recorder.list_events() == [event]


def test_get_events_for_resource_filters_correctly() -> None:
    recorder = ControlPlaneEventRecorder()

    resource_one_event = _event(
        "event-1",
        "resource-1",
        ControlPlaneEventType.RESOURCE_DISCOVERED,
    )
    resource_two_event = _event(
        "event-2",
        "resource-2",
        ControlPlaneEventType.RESOURCE_HEALTH_CHANGED,
    )

    recorder.record(resource_one_event)
    recorder.record(resource_two_event)

    assert recorder.get_events_for_resource("resource-1") == [
        resource_one_event
    ]


def test_get_events_by_type_filters_correctly() -> None:
    recorder = ControlPlaneEventRecorder()

    discovered = _event(
        "event-1",
        "resource-1",
        ControlPlaneEventType.RESOURCE_DISCOVERED,
    )
    health_changed = _event(
        "event-2",
        "resource-2",
        ControlPlaneEventType.RESOURCE_HEALTH_CHANGED,
    )
    discovered_again = _event(
        "event-3",
        "resource-3",
        ControlPlaneEventType.RESOURCE_DISCOVERED,
    )

    recorder.record(discovered)
    recorder.record(health_changed)
    recorder.record(discovered_again)

    assert recorder.get_events_by_type(
        ControlPlaneEventType.RESOURCE_DISCOVERED
    ) == [
        discovered,
        discovered_again,
    ]


def test_missing_resource_returns_empty_list() -> None:
    recorder = ControlPlaneEventRecorder()

    recorder.record(
        _event(
            "event-1",
            "resource-1",
            ControlPlaneEventType.RESOURCE_DISCOVERED,
        )
    )

    assert recorder.get_events_for_resource("does-not-exist") == []


def test_missing_event_type_returns_empty_list() -> None:
    recorder = ControlPlaneEventRecorder()

    recorder.record(
        _event(
            "event-1",
            "resource-1",
            ControlPlaneEventType.RESOURCE_DISCOVERED,
        )
    )

    assert recorder.get_events_by_type(
        ControlPlaneEventType.RESOURCE_DRIFT_DETECTED
    ) == []


def test_clear_removes_all_events() -> None:
    recorder = ControlPlaneEventRecorder()

    recorder.record(
        _event(
            "event-1",
            "resource-1",
            ControlPlaneEventType.RESOURCE_DISCOVERED,
        )
    )
    recorder.record(
        _event(
            "event-2",
            "resource-2",
            ControlPlaneEventType.RESOURCE_HEALTH_CHANGED,
        )
    )

    recorder.clear()

    assert recorder.list_events() == []


def test_record_resource_discovered_generates_event() -> None:
    recorder = ControlPlaneEventRecorder()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
    )

    event = recorder.record_resource_discovered(resource)

    assert event.event_type == ControlPlaneEventType.RESOURCE_DISCOVERED
    assert event.resource_id == "resource-1"
    assert event.event_id
    assert event.reason == "Resource was discovered by the control plane."
    assert recorder.list_events() == [event]


def test_record_resource_state_changed_generates_event() -> None:
    recorder = ControlPlaneEventRecorder()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
        status=ResourceStatus.RUNNING,
    )

    event = recorder.record_resource_state_changed(
        resource=resource,
        previous_status=ResourceStatus.STOPPED,
    )

    assert event.event_type == ControlPlaneEventType.RESOURCE_STATE_CHANGED
    assert event.details == {
        "previous_status": "stopped",
        "observed_status": "running",
    }


def test_record_resource_drift_detected_generates_event() -> None:
    recorder = ControlPlaneEventRecorder()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
        status=ResourceStatus.STOPPED,
    )

    event = recorder.record_resource_drift_detected(
        resource=resource,
        desired_status=ResourceStatus.RUNNING,
    )

    assert event.event_type == ControlPlaneEventType.RESOURCE_DRIFT_DETECTED
    assert event.details == {
        "desired_status": "running",
        "observed_status": "stopped",
    }


def test_record_resource_health_changed_generates_event() -> None:
    recorder = ControlPlaneEventRecorder()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
    )

    event = recorder.record_resource_health_changed(
        resource=resource,
        previous_health="unknown",
    )

    assert event.event_type == ControlPlaneEventType.RESOURCE_HEALTH_CHANGED
    assert event.details == {
        "previous_health": "unknown",
        "observed_health": "unknown",
    }


def test_record_resource_lifecycle_changed_generates_event() -> None:
    recorder = ControlPlaneEventRecorder()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
        status=ResourceStatus.RUNNING,
    )

    event = recorder.record_resource_lifecycle_changed(
        resource=resource,
        previous_status=ResourceStatus.STOPPED,
    )

    assert event.event_type == ControlPlaneEventType.RESOURCE_LIFECYCLE_CHANGED
    assert event.details == {
        "previous_status": "stopped",
        "target_status": "running",
    }