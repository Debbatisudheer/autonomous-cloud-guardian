from __future__ import annotations

import pytest

from guardian.application.reconciliation import (
    ResourceReconciliationEngine,
)
from guardian.domain.reconciliation import ReconciliationStatus
from guardian.domain.resource import Resource, ResourceStatus


def test_reconcile_running_resource_as_in_sync() -> None:
    engine = ResourceReconciliationEngine()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
        status=ResourceStatus.RUNNING,
    )

    result = engine.reconcile(
        resource=resource,
        desired_status=ResourceStatus.RUNNING,
    )

    assert result.resource_id == "resource-1"
    assert result.desired_status == ResourceStatus.RUNNING
    assert result.observed_status == ResourceStatus.RUNNING
    assert result.status == ReconciliationStatus.IN_SYNC
    assert result.reason == "Observed state matches desired state."


def test_reconcile_stopped_resource_as_drifted() -> None:
    engine = ResourceReconciliationEngine()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
        status=ResourceStatus.STOPPED,
    )

    result = engine.reconcile(
        resource=resource,
        desired_status=ResourceStatus.RUNNING,
    )

    assert result.resource_id == "resource-1"
    assert result.desired_status == ResourceStatus.RUNNING
    assert result.observed_status == ResourceStatus.STOPPED
    assert result.status == ReconciliationStatus.DRIFTED
    assert (
        result.reason
        == "Observed state does not match desired state: "
        "expected running, observed stopped."
    )


def test_reconcile_failed_resource_as_drifted() -> None:
    engine = ResourceReconciliationEngine()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
        status=ResourceStatus.FAILED,
    )

    result = engine.reconcile(
        resource=resource,
        desired_status=ResourceStatus.RUNNING,
    )

    assert result.status == ReconciliationStatus.DRIFTED
    assert result.observed_status == ResourceStatus.FAILED


def test_reconciliation_does_not_modify_resource() -> None:
    engine = ResourceReconciliationEngine()

    resource = Resource(
        id="resource-1",
        name="test-resource",
        resource_type="container",
        status=ResourceStatus.STOPPED,
    )

    engine.reconcile(
        resource=resource,
        desired_status=ResourceStatus.RUNNING,
    )

    assert resource.status == ResourceStatus.STOPPED


def test_reconcile_all_returns_result_for_each_resource() -> None:
    engine = ResourceReconciliationEngine()

    resources = [
        Resource(
            id="resource-1",
            name="running-resource",
            resource_type="container",
            status=ResourceStatus.RUNNING,
        ),
        Resource(
            id="resource-2",
            name="stopped-resource",
            resource_type="container",
            status=ResourceStatus.STOPPED,
        ),
    ]

    desired_statuses = {
        "resource-1": ResourceStatus.RUNNING,
        "resource-2": ResourceStatus.RUNNING,
    }

    results = engine.reconcile_all(
        resources=resources,
        desired_statuses=desired_statuses,
    )

    assert len(results) == 2
    assert results[0].status == ReconciliationStatus.IN_SYNC
    assert results[1].status == ReconciliationStatus.DRIFTED


def test_reconcile_all_preserves_resource_order() -> None:
    engine = ResourceReconciliationEngine()

    resources = [
        Resource(
            id="resource-a",
            name="resource-a",
            resource_type="container",
            status=ResourceStatus.RUNNING,
        ),
        Resource(
            id="resource-b",
            name="resource-b",
            resource_type="container",
            status=ResourceStatus.STOPPED,
        ),
    ]

    desired_statuses = {
        "resource-a": ResourceStatus.RUNNING,
        "resource-b": ResourceStatus.STOPPED,
    }

    results = engine.reconcile_all(
        resources=resources,
        desired_statuses=desired_statuses,
    )

    assert [result.resource_id for result in results] == [
        "resource-a",
        "resource-b",
    ]


def test_reconcile_all_requires_desired_status_for_every_resource() -> None:
    engine = ResourceReconciliationEngine()

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

    desired_statuses = {
        "resource-1": ResourceStatus.RUNNING,
    }

    with pytest.raises(ValueError, match="resource-2"):
        engine.reconcile_all(
            resources=resources,
            desired_statuses=desired_statuses,
        )


def test_reconcile_all_does_not_modify_resources() -> None:
    engine = ResourceReconciliationEngine()

    resources = [
        Resource(
            id="resource-1",
            name="resource-1",
            resource_type="container",
            status=ResourceStatus.STOPPED,
        ),
        Resource(
            id="resource-2",
            name="resource-2",
            resource_type="container",
            status=ResourceStatus.FAILED,
        ),
    ]

    desired_statuses = {
        "resource-1": ResourceStatus.RUNNING,
        "resource-2": ResourceStatus.RUNNING,
    }

    engine.reconcile_all(
        resources=resources,
        desired_statuses=desired_statuses,
    )

    assert resources[0].status == ResourceStatus.STOPPED
    assert resources[1].status == ResourceStatus.FAILED