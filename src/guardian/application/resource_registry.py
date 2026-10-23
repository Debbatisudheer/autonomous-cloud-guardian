from __future__ import annotations

from guardian.domain.resource import Resource


class ResourceRegistryError(Exception):
    """Base exception for resource registry errors."""


class ResourceAlreadyExistsError(ResourceRegistryError):
    """Raised when a resource ID already exists in the registry."""


class ResourceNotFoundError(ResourceRegistryError):
    """Raised when a requested resource does not exist in the registry."""


class ResourceRegistry:
    """
    In-memory registry of resources known to the control plane.

    The registry is intentionally infrastructure-agnostic. It does not
    discover resources, persist resources, or communicate with providers.
    Those responsibilities belong to later phases.
    """

    def __init__(self) -> None:
        self._resources: dict[str, Resource] = {}

    def add(self, resource: Resource) -> None:
        """
        Add a resource to the registry.

        Raises:
            ResourceAlreadyExistsError: If the resource ID already exists.
        """
        if resource.id in self._resources:
            raise ResourceAlreadyExistsError(
                f"Resource '{resource.id}' already exists."
            )

        self._resources[resource.id] = resource

    def get(self, resource_id: str) -> Resource:
        """
        Retrieve a resource by ID.

        Raises:
            ResourceNotFoundError: If the resource does not exist.
        """
        try:
            return self._resources[resource_id]
        except KeyError as exc:
            raise ResourceNotFoundError(
                f"Resource '{resource_id}' was not found."
            ) from exc

    def list(self) -> list[Resource]:
        """Return all registered resources."""
        return list(self._resources.values())

    def update(self, resource: Resource) -> None:
        """
        Replace an existing resource.

        Raises:
            ResourceNotFoundError: If the resource does not exist.
        """
        if resource.id not in self._resources:
            raise ResourceNotFoundError(
                f"Resource '{resource.id}' was not found."
            )

        self._resources[resource.id] = resource

    def remove(self, resource_id: str) -> Resource:
        """
        Remove and return a resource by ID.

        Raises:
            ResourceNotFoundError: If the resource does not exist.
        """
        try:
            return self._resources.pop(resource_id)
        except KeyError as exc:
            raise ResourceNotFoundError(
                f"Resource '{resource_id}' was not found."
            ) from exc

    def clear(self) -> None:
        """Remove all resources from the registry."""
        self._resources.clear()