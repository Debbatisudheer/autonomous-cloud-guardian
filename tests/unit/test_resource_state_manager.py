from datetime import UTC, datetime

from guardian.application.resource_state import ResourceStateManager
from guardian.domain.resource import (
    Resource,
    ResourceHealth,
    ResourceProvider,
    ResourceStatus,
)


def make_resource(
    resource_id: str = "container-123",
    name: str = "test-container",
) -> Resource:
    observed_at = datetime.now(UTC)

    return Resource(
        id=resource_id,
        name=name,
        resource_type="container",
        provider=ResourceProvider.DOCKER,
        status=ResourceStatus.RUNNING,
        health=ResourceHealth.HEALTHY,
        metadata={
            "container_id": resource_id,
            "docker_status": "running",
            "restart_count": 0,
        },
        updated_at=observed_at,
    )


def test_observe_creates_current_state() -> None:
    resource = make_resource()

    state = ResourceStateManager().observe(resource)

    assert state.resource_id == resource.id
    assert state.status == ResourceStatus.RUNNING
    assert state.health == ResourceHealth.HEALTHY
    assert state.observed_at == resource.updated_at


def test_observe_preserves_provider_information() -> None:
    resource = make_resource()

    state = ResourceStateManager().observe(resource)

    assert state.attributes["provider"] == "docker"
    assert state.attributes["resource_type"] == "container"


def test_observe_preserves_resource_metadata() -> None:
    resource = make_resource()

    state = ResourceStateManager().observe(resource)

    assert state.attributes["container_id"] == resource.id
    assert state.attributes["docker_status"] == "running"
    assert state.attributes["restart_count"] == 0


def test_observe_all_creates_state_for_every_resource() -> None:
    resources = [
        make_resource("container-1", "postgres"),
        make_resource("container-2", "redis"),
        make_resource("container-3", "kafka"),
    ]

    states = ResourceStateManager().observe_all(resources)

    assert len(states) == 3
    assert [state.resource_id for state in states] == [
        "container-1",
        "container-2",
        "container-3",
    ]
