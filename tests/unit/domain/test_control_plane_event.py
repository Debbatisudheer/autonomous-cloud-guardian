from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from guardian.domain.control_plane_event import (
    ControlPlaneEvent,
    ControlPlaneEventType,
)


def test_control_plane_event_can_be_created() -> None:
    event = ControlPlaneEvent(
        event_id="event-1",
        event_type=ControlPlaneEventType.RESOURCE_DISCOVERED,
        resource_id="resource-1",
        reason="Resource was discovered by the Docker adapter.",
    )

    assert event.event_id == "event-1"
    assert event.event_type == ControlPlaneEventType.RESOURCE_DISCOVERED
    assert event.resource_id == "resource-1"
    assert event.reason == (
        "Resource was discovered by the Docker adapter."
    )
    assert event.occurred_at.tzinfo == UTC


def test_control_plane_event_supports_details() -> None:
    event = ControlPlaneEvent(
        event_id="event-2",
        event_type=ControlPlaneEventType.RESOURCE_STATE_CHANGED,
        resource_id="resource-1",
        reason="Observed resource state changed.",
        details={
            "previous_status": "stopped",
            "observed_status": "running",
        },
    )

    assert event.details == {
        "previous_status": "stopped",
        "observed_status": "running",
    }


def test_control_plane_event_accepts_explicit_timestamp() -> None:
    occurred_at = datetime(
        2026,
        10,
        23,
        7,
        30,
        tzinfo=UTC,
    )

    event = ControlPlaneEvent(
        event_id="event-3",
        event_type=ControlPlaneEventType.RESOURCE_DRIFT_DETECTED,
        resource_id="resource-1",
        occurred_at=occurred_at,
        reason="Observed state differs from desired state.",
    )

    assert event.occurred_at == occurred_at


def test_control_plane_event_rejects_empty_event_id() -> None:
    with pytest.raises(ValidationError):
        ControlPlaneEvent(
            event_id="",
            event_type=ControlPlaneEventType.RESOURCE_DISCOVERED,
            resource_id="resource-1",
            reason="Resource discovered.",
        )


def test_control_plane_event_rejects_empty_resource_id() -> None:
    with pytest.raises(ValidationError):
        ControlPlaneEvent(
            event_id="event-1",
            event_type=ControlPlaneEventType.RESOURCE_DISCOVERED,
            resource_id="",
            reason="Resource discovered.",
        )


def test_control_plane_event_rejects_empty_reason() -> None:
    with pytest.raises(ValidationError):
        ControlPlaneEvent(
            event_id="event-1",
            event_type=ControlPlaneEventType.RESOURCE_DISCOVERED,
            resource_id="resource-1",
            reason="",
        )


def test_control_plane_event_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ControlPlaneEvent(
            event_id="event-1",
            event_type=ControlPlaneEventType.RESOURCE_DISCOVERED,
            resource_id="resource-1",
            reason="Resource discovered.",
            unexpected_field="not-allowed",
        )