from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from guardian.domain.resource import ResourceHealth, ResourceStatus
from guardian.domain.resource_state import ResourceState


def test_resource_state_defaults() -> None:
    state = ResourceState(resource_id="container-123")

    assert state.resource_id == "container-123"
    assert state.status == ResourceStatus.UNKNOWN
    assert state.health == ResourceHealth.UNKNOWN
    assert state.attributes == {}
    assert state.observed_at.tzinfo == UTC


def test_resource_state_accepts_current_state() -> None:
    observed_at = datetime.now(UTC)

    state = ResourceState(
        resource_id="container-123",
        status=ResourceStatus.RUNNING,
        health=ResourceHealth.HEALTHY,
        observed_at=observed_at,
        attributes={
            "docker_status": "running",
            "restart_count": 0,
        },
    )

    assert state.resource_id == "container-123"
    assert state.status == ResourceStatus.RUNNING
    assert state.health == ResourceHealth.HEALTHY
    assert state.observed_at == observed_at
    assert state.attributes["docker_status"] == "running"


def test_resource_state_rejects_empty_resource_id() -> None:
    with pytest.raises(ValidationError):
        ResourceState(resource_id="")


def test_resource_state_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ResourceState(
            resource_id="container-123",
            unexpected="value",
        )


def test_resource_state_timestamp_is_timezone_aware() -> None:
    state = ResourceState(resource_id="container-123")

    assert state.observed_at.tzinfo is not None
    assert state.observed_at.utcoffset() is not None


def test_resource_state_serializes() -> None:
    state = ResourceState(
        resource_id="container-123",
        status=ResourceStatus.RUNNING,
        health=ResourceHealth.HEALTHY,
    )

    data = state.model_dump()

    assert data["resource_id"] == "container-123"
    assert data["status"] == ResourceStatus.RUNNING
    assert data["health"] == ResourceHealth.HEALTHY
