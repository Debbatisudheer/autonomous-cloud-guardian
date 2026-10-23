from __future__ import annotations

from guardian.application.control_plane_events import (
    ControlPlaneEventRecorder,
)
from guardian.application.reconciliation import (
    ResourceReconciliationEngine,
)
from guardian.application.resource_health import (
    ResourceHealthAssessor,
)
from guardian.application.resource_lifecycle import (
    ResourceLifecycleManager,
)
from guardian.domain.control_plane_event import (
    ControlPlaneEvent,
)
from guardian.domain.reconciliation import (
    ReconciliationStatus,
    ResourceReconciliation,
)
from guardian.domain.resource import (
    Resource,
    ResourceStatus,
)
from guardian.domain.resource_health import (
    ResourceHealthObservation,
)
from guardian.infrastructure.adapters.base import (
    InfrastructureAdapter,
)


class ControlPlaneOperations:
    """
    Coordinates existing control-plane operations with event recording.

    This component does not invent infrastructure state and does not
    automatically remediate resources.

    Events are generated only from operations actually performed
    through this control-plane interface.
    """

    def __init__(
        self,
        adapter: InfrastructureAdapter,
        event_recorder: ControlPlaneEventRecorder,
        reconciliation_engine: ResourceReconciliationEngine | None = None,
        lifecycle_manager: ResourceLifecycleManager | None = None,
        health_assessor: ResourceHealthAssessor | None = None,
    ) -> None:
        self._adapter = adapter
        self._event_recorder = event_recorder

        self._reconciliation_engine = (
            reconciliation_engine
            or ResourceReconciliationEngine()
        )

        self._lifecycle_manager = (
            lifecycle_manager
            or ResourceLifecycleManager()
        )

        self._health_assessor = (
            health_assessor
            or ResourceHealthAssessor()
        )

    def discover_resources(self) -> list[Resource]:
        """
        Discover resources from the infrastructure adapter.

        A RESOURCE_DISCOVERED event is recorded for every resource
        returned by the adapter.
        """
        resources = self._adapter.discover_resources()

        for resource in resources:
            self._event_recorder.record_resource_discovered(
                resource
            )

        return resources

    def reconcile_resource(
        self,
        resource: Resource,
        desired_status: ResourceStatus,
    ) -> ResourceReconciliation:
        """
        Reconcile one resource against its desired state.

        A RESOURCE_DRIFT_DETECTED event is recorded only when
        actual drift is detected.
        """
        result = self._reconciliation_engine.reconcile(
            resource=resource,
            desired_status=desired_status,
        )

        if result.status == ReconciliationStatus.DRIFTED:
            self._event_recorder.record_resource_drift_detected(
                resource=resource,
                desired_status=desired_status,
            )

        return result

    def reconcile_resources(
        self,
        resources: list[Resource],
        desired_statuses: dict[str, ResourceStatus],
    ) -> list[ResourceReconciliation]:
        """
        Reconcile multiple resources against their desired states.

        A drift event is recorded only for resources that are actually
        detected as drifted.
        """
        results = self._reconciliation_engine.reconcile_all(
            resources=resources,
            desired_statuses=desired_statuses,
        )

        for resource, result in zip(
            resources,
            results,
            strict=True,
        ):
            if result.status == ReconciliationStatus.DRIFTED:
                self._event_recorder.record_resource_drift_detected(
                    resource=resource,
                    desired_status=desired_statuses[
                        resource.id
                    ],
                )

        return results

    def change_lifecycle(
        self,
        resource: Resource,
        target_status: ResourceStatus,
    ) -> object:
        """
        Execute a validated control-plane lifecycle transition.

        A RESOURCE_LIFECYCLE_CHANGED event is recorded when the
        lifecycle transition succeeds.

        Important:
        The existing lifecycle manager only changes the in-memory
        Resource model. It does not call Docker or another provider.
        """
        previous_status = resource.status

        operation = self._lifecycle_manager.execute(
            resource=resource,
            target=target_status,
        )

        if operation.changed:
            self._event_recorder.record_resource_lifecycle_changed(
                resource=resource,
                previous_status=previous_status,
            )

        return operation

    def assess_health(
        self,
        resource: Resource,
    ) -> ResourceHealthObservation:
        """
        Assess resource health.

        A RESOURCE_HEALTH_CHANGED event is recorded only if the
        observed health differs from the resource's previous health.
        """
        previous_health = resource.health

        observation = self._health_assessor.assess(
            resource
        )

        if observation.health != previous_health:
            self._event_recorder.record_resource_health_changed(
                resource=resource,
                previous_health=previous_health.value,
            )

        return observation

    def event_recorder(
        self,
    ) -> ControlPlaneEventRecorder:
        """
        Return the event recorder used by this control plane.
        """
        return self._event_recorder

    def events(self) -> list[ControlPlaneEvent]:
        """
        Return all events recorded by this control plane.
        """
        return self._event_recorder.list_events()