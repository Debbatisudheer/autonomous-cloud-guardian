from __future__ import annotations

import pytest

from guardian.application.resource_lifecycle import (
    InvalidResourceTransitionError,
    ResourceLifecycleManager,
)
from guardian.domain.resource import Resource, ResourceStatus


def test_running_to_stopped_is_valid() -> None:
    manager = ResourceLifecycleManager()

    result = manager.transition(
        ResourceStatus.RUNNING,
        ResourceStatus.STOPPED,
    )

    assert result == ResourceStatus.STOPPED


def test_stopped_to_running_is_valid() -> None:
    manager = ResourceLifecycleManager()

    result = manager.transition(
        ResourceStatus.STOPPED,
        ResourceStatus.RUNNING,
    )

    assert result == ResourceStatus.RUNNING


def test_creating_to_running_is_valid() -> None:
    manager = ResourceLifecycleManager()

    assert manager.can_transition(
        ResourceStatus.CREATING,
        ResourceStatus.RUNNING,
    )


def test_deleting_to_deleted_is_valid() -> None:
    manager = ResourceLifecycleManager()

    assert manager.can_transition(
        ResourceStatus.DELETING,
        ResourceStatus.DELETED,
    )


def test_deleted_has_no_valid_transitions() -> None:
    manager = ResourceLifecycleManager()

    assert not manager.can_transition(
        ResourceStatus.DELETED,
        ResourceStatus.RUNNING,
    )


def test_running_to_deleted_is_invalid() -> None:
    manager = ResourceLifecycleManager()

    assert not manager.can_transition(
        ResourceStatus.RUNNING,
        ResourceStatus.DELETED,
    )


def test_invalid_transition_raises_error() -> None:
    manager = ResourceLifecycleManager()

    with pytest.raises(InvalidResourceTransitionError):
        manager.transition(
            ResourceStatus.RUNNING,
            ResourceStatus.DELETED,
        )


def test_transition_resource_updates_resource_status() -> None:
    manager = ResourceLifecycleManager()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
        status=ResourceStatus.RUNNING,
    )

    result = manager.transition_resource(
        resource,
        ResourceStatus.STOPPED,
    )

    assert result is resource
    assert result.status == ResourceStatus.STOPPED


def test_transition_resource_rejects_invalid_transition() -> None:
    manager = ResourceLifecycleManager()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
        status=ResourceStatus.RUNNING,
    )

    with pytest.raises(InvalidResourceTransitionError):
        manager.transition_resource(
            resource,
            ResourceStatus.DELETED,
        )

    assert resource.status == ResourceStatus.RUNNING


def test_execute_returns_lifecycle_operation() -> None:
    manager = ResourceLifecycleManager()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
        status=ResourceStatus.RUNNING,
    )

    operation = manager.execute(
        resource,
        ResourceStatus.STOPPED,
    )

    assert operation.resource_id == "resource-1"
    assert operation.previous_status == ResourceStatus.RUNNING
    assert operation.target_status == ResourceStatus.STOPPED
    assert operation.observed_status == ResourceStatus.STOPPED
    assert operation.changed is True
    assert resource.status == ResourceStatus.STOPPED


def test_execute_rejects_invalid_transition() -> None:
    manager = ResourceLifecycleManager()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
        status=ResourceStatus.RUNNING,
    )

    with pytest.raises(InvalidResourceTransitionError):
        manager.execute(
            resource,
            ResourceStatus.DELETED,
        )

    assert resource.status == ResourceStatus.RUNNING