from __future__ import annotations

from guardian.domain.resource import Resource
from guardian.domain.resource_state import ResourceState


class ResourceStateManager:
    """
    Builds current observed state from discovered resources.

    This component does not define desired state and does not
    perform reconciliation or infrastructure mutations.
    """

    def observe(self, resource: Resource) -> ResourceState:
        """Create a current state observation from a resource."""
        return ResourceState(
            resource_id=resource.id,
            status=resource.status,
            health=resource.health,
            observed_at=resource.updated_at,
            attributes={
                "provider": resource.provider.value,
                "resource_type": resource.resource_type,
                **resource.metadata,
            },
        )

    def observe_all(self, resources: list[Resource]) -> list[ResourceState]:
        """Create current state observations for multiple resources."""
        return [self.observe(resource) for resource in resources]
