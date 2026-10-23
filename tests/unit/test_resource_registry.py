import pytest

from guardian.application.resource_registry import (
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ResourceRegistry,
)
from guardian.domain.resource import (
    Resource,
    ResourceHealth,
    ResourceProvider,
    ResourceStatus,
)


def make_resource(
    resource_id: str,
    name: str,
    status: ResourceStatus = ResourceStatus.RUNNING,
) -> Resource:
    return Resource(
        id=resource_id,
        name=name,
        resource_type="container",
        provider=ResourceProvider.DOCKER,
        status=status,
        health=ResourceHealth.HEALTHY,
        region="local",
    )


def test_registry_starts_empty() -> None:
    registry = ResourceRegistry()

    assert registry.list() == []


def test_registry_adds_and_gets_resource() -> None:
    registry = ResourceRegistry()
    resource = make_resource("resource-1", "acg-test")

    registry.add(resource)

    assert registry.get("resource-1") == resource


def test_registry_lists_all_resources() -> None:
    registry = ResourceRegistry()
    resource_one = make_resource("resource-1", "acg-one")
    resource_two = make_resource("resource-2", "acg-two")

    registry.add(resource_one)
    registry.add(resource_two)

    resources = registry.list()

    assert resources == [resource_one, resource_two]


def test_registry_rejects_duplicate_resource_id() -> None:
    registry = ResourceRegistry()
    resource = make_resource("resource-1", "acg-test")

    registry.add(resource)

    with pytest.raises(ResourceAlreadyExistsError):
        registry.add(resource)


def test_registry_updates_existing_resource() -> None:
    registry = ResourceRegistry()
    original = make_resource(
        "resource-1",
        "acg-test",
        ResourceStatus.RUNNING,
    )
    updated = make_resource(
        "resource-1",
        "acg-test",
        ResourceStatus.STOPPED,
    )

    registry.add(original)
    registry.update(updated)

    assert registry.get("resource-1") == updated
    assert registry.get("resource-1").status == ResourceStatus.STOPPED


def test_registry_rejects_update_for_unknown_resource() -> None:
    registry = ResourceRegistry()
    resource = make_resource("resource-1", "acg-test")

    with pytest.raises(ResourceNotFoundError):
        registry.update(resource)


def test_registry_removes_resource() -> None:
    registry = ResourceRegistry()
    resource = make_resource("resource-1", "acg-test")

    registry.add(resource)

    removed = registry.remove("resource-1")

    assert removed == resource
    assert registry.list() == []


def test_registry_rejects_get_for_unknown_resource() -> None:
    registry = ResourceRegistry()

    with pytest.raises(ResourceNotFoundError):
        registry.get("missing-resource")


def test_registry_rejects_remove_for_unknown_resource() -> None:
    registry = ResourceRegistry()

    with pytest.raises(ResourceNotFoundError):
        registry.remove("missing-resource")


def test_registry_clear_removes_all_resources() -> None:
    registry = ResourceRegistry()
    registry.add(make_resource("resource-1", "acg-one"))
    registry.add(make_resource("resource-2", "acg-two"))

    registry.clear()

    assert registry.list() == []


def test_registries_are_isolated() -> None:
    first_registry = ResourceRegistry()
    second_registry = ResourceRegistry()

    resource = make_resource("resource-1", "acg-test")

    first_registry.add(resource)

    assert first_registry.list() == [resource]
    assert second_registry.list() == []