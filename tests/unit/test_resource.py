from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from guardian.domain.resource import (
    Resource,
    ResourceHealth,
    ResourceProvider,
    ResourceStatus,
)


def test_resource_defaults_are_applied() -> None:
    resource = Resource(
        id="resource-1",
        name="acg-test",
        resource_type="container",
    )

    assert resource.provider == ResourceProvider.UNKNOWN
    assert resource.status == ResourceStatus.UNKNOWN
    assert resource.health == ResourceHealth.UNKNOWN
    assert resource.region is None
    assert resource.metadata == {}
    assert resource.dependencies == []
    assert resource.created_at.tzinfo == UTC
    assert resource.updated_at.tzinfo == UTC


def test_resource_accepts_valid_infrastructure_resource() -> None:
    resource = Resource(
        id="container-1",
        name="acg-terraform-test",
        resource_type="container",
        provider=ResourceProvider.DOCKER,
        status=ResourceStatus.RUNNING,
        health=ResourceHealth.HEALTHY,
        region="local",
        metadata={"image": "alpine:3.22"},
        dependencies=["docker-engine"],
    )

    assert resource.id == "container-1"
    assert resource.name == "acg-terraform-test"
    assert resource.resource_type == "container"
    assert resource.provider == ResourceProvider.DOCKER
    assert resource.status == ResourceStatus.RUNNING
    assert resource.health == ResourceHealth.HEALTHY
    assert resource.region == "local"
    assert resource.metadata["image"] == "alpine:3.22"
    assert resource.dependencies == ["docker-engine"]


def test_resource_rejects_empty_identity_fields() -> None:
    with pytest.raises(ValidationError):
        Resource(
            id="",
            name="acg-test",
            resource_type="container",
        )

    with pytest.raises(ValidationError):
        Resource(
            id="resource-1",
            name="",
            resource_type="container",
        )

    with pytest.raises(ValidationError):
        Resource(
            id="resource-1",
            name="acg-test",
            resource_type="",
        )


def test_resource_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Resource(
            id="resource-1",
            name="acg-test",
            resource_type="container",
            unsupported_field="value",
        )


def test_resource_timestamps_are_utc() -> None:
    resource = Resource(
        id="resource-1",
        name="acg-test",
        resource_type="container",
    )

    assert isinstance(resource.created_at, datetime)
    assert isinstance(resource.updated_at, datetime)
    assert resource.created_at.tzinfo == UTC
    assert resource.updated_at.tzinfo == UTC


def test_resource_serializes_to_json_compatible_data() -> None:
    resource = Resource(
        id="resource-1",
        name="acg-test",
        resource_type="container",
        provider=ResourceProvider.DOCKER,
        status=ResourceStatus.RUNNING,
        health=ResourceHealth.HEALTHY,
    )

    data = resource.model_dump(mode="json")

    assert data["id"] == "resource-1"
    assert data["provider"] == "docker"
    assert data["status"] == "running"
    assert data["health"] == "healthy"
    assert isinstance(data["created_at"], str)
    assert isinstance(data["updated_at"], str)