from __future__ import annotations

from guardian.domain.reconciliation import (
    ReconciliationStatus,
    ResourceReconciliation,
)
from guardian.domain.resource import ResourceStatus


def test_reconciliation_can_represent_in_sync_resource() -> None:
    result = ResourceReconciliation(
        resource_id="resource-1",
        desired_status=ResourceStatus.RUNNING,
        observed_status=ResourceStatus.RUNNING,
        status=ReconciliationStatus.IN_SYNC,
        reason="Observed state matches desired state.",
    )

    assert result.resource_id == "resource-1"
    assert result.desired_status == ResourceStatus.RUNNING
    assert result.observed_status == ResourceStatus.RUNNING
    assert result.status == ReconciliationStatus.IN_SYNC


def test_reconciliation_can_represent_drifted_resource() -> None:
    result = ResourceReconciliation(
        resource_id="resource-1",
        desired_status=ResourceStatus.RUNNING,
        observed_status=ResourceStatus.STOPPED,
        status=ReconciliationStatus.DRIFTED,
        reason="Observed state does not match desired state.",
    )

    assert result.status == ReconciliationStatus.DRIFTED
    assert result.desired_status == ResourceStatus.RUNNING
    assert result.observed_status == ResourceStatus.STOPPED


def test_reconciliation_rejects_empty_resource_id() -> None:
    try:
        ResourceReconciliation(
            resource_id="",
            desired_status=ResourceStatus.RUNNING,
            observed_status=ResourceStatus.RUNNING,
            status=ReconciliationStatus.IN_SYNC,
            reason="Observed state matches desired state.",
        )
    except ValueError:
        return

    raise AssertionError("Expected empty resource ID to be rejected.")


def test_reconciliation_rejects_empty_reason() -> None:
    try:
        ResourceReconciliation(
            resource_id="resource-1",
            desired_status=ResourceStatus.RUNNING,
            observed_status=ResourceStatus.RUNNING,
            status=ReconciliationStatus.IN_SYNC,
            reason="",
        )
    except ValueError:
        return

    raise AssertionError("Expected empty reason to be rejected.")