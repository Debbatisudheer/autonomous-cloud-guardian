from __future__ import annotations

from guardian.domain.reconciliation import (
    ReconciliationStatus,
    ResourceReconciliation,
)
from guardian.domain.resource import Resource, ResourceStatus


class ResourceReconciliationEngine:
    """
    Compares desired resource state with observed resource state.

    This component detects drift only. It does not perform
    infrastructure operations or automatically remediate resources.
    """

    def reconcile(
        self,
        resource: Resource,
        desired_status: ResourceStatus,
    ) -> ResourceReconciliation:
        observed_status = resource.status

        if observed_status == desired_status:
            return ResourceReconciliation(
                resource_id=resource.id,
                desired_status=desired_status,
                observed_status=observed_status,
                status=ReconciliationStatus.IN_SYNC,
                reason="Observed state matches desired state.",
            )

        return ResourceReconciliation(
            resource_id=resource.id,
            desired_status=desired_status,
            observed_status=observed_status,
            status=ReconciliationStatus.DRIFTED,
            reason=(
                "Observed state does not match desired state: "
                f"expected {desired_status.value}, "
                f"observed {observed_status.value}."
            ),
        )

    def reconcile_all(
        self,
        resources: list[Resource],
        desired_statuses: dict[str, ResourceStatus],
    ) -> list[ResourceReconciliation]:
        """
        Reconcile multiple resources against their desired states.

        Every resource must have a corresponding desired status.
        No infrastructure operation is performed.
        """
        results: list[ResourceReconciliation] = []

        for resource in resources:
            if resource.id not in desired_statuses:
                raise ValueError(
                    f"No desired status was provided for resource '{resource.id}'."
                )

            result = self.reconcile(
                resource=resource,
                desired_status=desired_statuses[resource.id],
            )

            results.append(result)

        return results