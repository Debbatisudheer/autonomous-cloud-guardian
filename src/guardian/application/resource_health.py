from __future__ import annotations

from datetime import UTC, datetime

from guardian.domain.resource import (
    Resource,
    ResourceHealth,
    ResourceStatus,
)
from guardian.domain.resource_health import ResourceHealthObservation


class ResourceHealthAssessor:
    """
    Assesses resource health from already-observed resource evidence.

    This component does not contact infrastructure providers and does
    not invent health information.
    """

    def assess(
        self,
        resource: Resource,
    ) -> ResourceHealthObservation:
        """
        Produce an evidence-backed health observation.

        Existing explicit health information is preserved. For running
        resources without a provider healthcheck, the result remains
        UNKNOWN rather than being interpreted as HEALTHY.
        """

        health = resource.health
        reason = self._reason(resource)

        return ResourceHealthObservation(
            resource_id=resource.id,
            status=resource.status,
            health=health,
            observed_at=datetime.now(UTC),
            reason=reason,
        )

    def assess_all(
        self,
        resources: list[Resource],
    ) -> list[ResourceHealthObservation]:
        """Assess the health of multiple resources."""
        return [self.assess(resource) for resource in resources]

    @staticmethod
    def _reason(resource: Resource) -> str:
        """Explain the evidence behind the health result."""

        if resource.health == ResourceHealth.HEALTHY:
            return "Provider healthcheck reports the resource as healthy."

        if resource.health == ResourceHealth.UNHEALTHY:
            return "Provider healthcheck reports the resource as unhealthy."

        if resource.health == ResourceHealth.DEGRADED:
            return "Provider health evidence indicates degraded health."

        if resource.status == ResourceStatus.RUNNING:
            return (
                "Resource is running, but no provider healthcheck evidence "
                "is available."
            )

        if resource.status == ResourceStatus.STOPPED:
            return "Resource is stopped; no active health evidence is available."

        if resource.status == ResourceStatus.FAILED:
            return "Resource is in a failed lifecycle state."

        return "No sufficient provider health evidence is available."