from __future__ import annotations

from guardian.application.control_plane_events import (
    ControlPlaneEventRecorder,
)
from guardian.application.control_plane_operations import (
    ControlPlaneOperations,
)
from guardian.application.resource_health import (
    ResourceHealthAssessor,
)
from guardian.application.resource_state import (
    ResourceStateManager,
)
from guardian.domain.control_plane_event import (
    ControlPlaneEventType,
)
from guardian.domain.reconciliation import (
    ReconciliationStatus,
)
from guardian.infrastructure.adapters.docker import (
    DockerInfrastructureAdapter,
)


def main() -> None:
    print("=" * 72)
    print("PHASE 3 — COMPLETE INTEGRATION VALIDATION")
    print("=" * 72)

    # ------------------------------------------------------------------
    # 1. REAL DOCKER DISCOVERY
    # ------------------------------------------------------------------

    adapter = DockerInfrastructureAdapter()

    recorder = ControlPlaneEventRecorder()

    control_plane = ControlPlaneOperations(
        adapter=adapter,
        event_recorder=recorder,
    )

    resources = control_plane.discover_resources()

    print()
    print("[1] REAL RESOURCE DISCOVERY")
    print("-" * 72)

    if not resources:
        raise RuntimeError(
            "No resources were discovered from the real Docker Engine."
        )

    print(f"Discovered resources: {len(resources)}")

    for resource in resources:
        print(
            f"  {resource.name}: "
            f"status={resource.status.value}, "
            f"health={resource.health.value}"
        )

    # ------------------------------------------------------------------
    # 2. RESOURCE STATE
    # ------------------------------------------------------------------

    state_manager = ResourceStateManager()

    states = state_manager.observe_all(resources)

    print()
    print("[2] RESOURCE STATE")
    print("-" * 72)

    if len(states) != len(resources):
        raise RuntimeError(
            "Resource state count does not match resource count."
        )

    for state in states:
        print(
            f"  {state.resource_id}: "
            f"status={state.status.value}, "
            f"health={state.health.value}"
        )

    # ------------------------------------------------------------------
    # 3. RESOURCE HEALTH
    # ------------------------------------------------------------------

    health_assessor = ResourceHealthAssessor()

    observations = health_assessor.assess_all(resources)

    print()
    print("[3] RESOURCE HEALTH")
    print("-" * 72)

    if len(observations) != len(resources):
        raise RuntimeError(
            "Health observation count does not match resource count."
        )

    for observation in observations:
        print(
            f"  {observation.resource_id}: "
            f"status={observation.status.value}, "
            f"health={observation.health.value}"
        )

    # ------------------------------------------------------------------
    # 4. RECONCILIATION
    # ------------------------------------------------------------------

    desired_statuses = {
        resource.id: resource.status
        for resource in resources
    }

    reconciliation_results = control_plane.reconcile_resources(
        resources=resources,
        desired_statuses=desired_statuses,
    )

    print()
    print("[4] RECONCILIATION")
    print("-" * 72)

    if len(reconciliation_results) != len(resources):
        raise RuntimeError(
            "Reconciliation result count does not match resource count."
        )

    drift_count = sum(
        result.status == ReconciliationStatus.DRIFTED
        for result in reconciliation_results
    )

    in_sync_count = sum(
        result.status == ReconciliationStatus.IN_SYNC
        for result in reconciliation_results
    )

    print(f"  In sync: {in_sync_count}")
    print(f"  Drifted: {drift_count}")

    if drift_count != 0:
        raise RuntimeError(
            "Unexpected drift detected when desired state was built "
            "directly from the observed state."
        )

    # ------------------------------------------------------------------
    # 5. CONTROL-PLANE EVENTS
    # ------------------------------------------------------------------

    events = control_plane.events()

    print()
    print("[5] CONTROL-PLANE EVENTS")
    print("-" * 72)

    discovery_events = [
        event
        for event in events
        if event.event_type
        == ControlPlaneEventType.RESOURCE_DISCOVERED
    ]

    drift_events = [
        event
        for event in events
        if event.event_type
        == ControlPlaneEventType.RESOURCE_DRIFT_DETECTED
    ]

    print(f"  Total events: {len(events)}")
    print(f"  Discovery events: {len(discovery_events)}")
    print(f"  Drift events: {len(drift_events)}")

    if len(discovery_events) != len(resources):
        raise RuntimeError(
            "Discovery event count does not match resource count."
        )

    if drift_events:
        raise RuntimeError(
            "Unexpected drift events were generated."
        )

    # ------------------------------------------------------------------
    # 6. VERIFY EVENT RESOURCE IDs
    # ------------------------------------------------------------------

    discovered_ids = {
        resource.id
        for resource in resources
    }

    event_resource_ids = {
        event.resource_id
        for event in discovery_events
    }

    print()
    print("[6] EVENT RESOURCE ID CORRELATION")
    print("-" * 72)

    if discovered_ids != event_resource_ids:
        raise RuntimeError(
            "Event resource IDs do not match discovered resource IDs."
        )

    print("  All discovered resources have matching event IDs.")

    # ------------------------------------------------------------------
    # 7. FINAL RESULT
    # ------------------------------------------------------------------

    print()
    print("=" * 72)
    print("PHASE 3 INTEGRATION VALIDATION RESULT")
    print("=" * 72)

    print()
    print("REAL DOCKER DISCOVERY       : PASS")
    print("RESOURCE STATE              : PASS")
    print("RESOURCE HEALTH             : PASS")
    print("RECONCILIATION              : PASS")
    print("CONTROL-PLANE EVENTS        : PASS")
    print("EVENT RESOURCE CORRELATION  : PASS")

    print()
    print("PHASE 3 — INTEGRATION VALIDATION: PASS")
    print("PHASE 3 — COMPLETE: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()