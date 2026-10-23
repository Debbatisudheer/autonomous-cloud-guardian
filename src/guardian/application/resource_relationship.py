from __future__ import annotations

from guardian.domain.resource_relationship import (
    RelationshipType,
    ResourceRelationship,
)


class ResourceRelationshipError(Exception):
    """Base exception for resource relationship errors."""


class ResourceRelationshipAlreadyExistsError(ResourceRelationshipError):
    """Raised when a relationship already exists."""


class ResourceRelationshipNotFoundError(ResourceRelationshipError):
    """Raised when a relationship does not exist."""


class ResourceRelationshipManager:
    """
    Manages relationships between resources known to the control plane.

    This component does not infer or invent infrastructure relationships.
    Relationships must be explicitly supplied by a discovery or
    infrastructure-specific adapter.
    """

    def __init__(self) -> None:
        self._relationships: dict[
            tuple[str, str, RelationshipType],
            ResourceRelationship,
        ] = {}

    def add(self, relationship: ResourceRelationship) -> None:
        """Add an explicitly discovered relationship."""
        key = self._key(relationship)

        if key in self._relationships:
            raise ResourceRelationshipAlreadyExistsError(
                "The resource relationship already exists."
            )

        self._relationships[key] = relationship

    def get_all(self) -> list[ResourceRelationship]:
        """Return all known relationships."""
        return list(self._relationships.values())

    def for_resource(
        self,
        resource_id: str,
    ) -> list[ResourceRelationship]:
        """Return relationships where the resource is source or target."""
        return [
            relationship
            for relationship in self._relationships.values()
            if (
                relationship.source_resource_id == resource_id
                or relationship.target_resource_id == resource_id
            )
        ]

    def remove(self, relationship: ResourceRelationship) -> None:
        """Remove an existing relationship."""
        key = self._key(relationship)

        if key not in self._relationships:
            raise ResourceRelationshipNotFoundError(
                "The resource relationship was not found."
            )

        del self._relationships[key]

    def clear(self) -> None:
        """Remove all known relationships."""
        self._relationships.clear()

    @staticmethod
    def _key(
        relationship: ResourceRelationship,
    ) -> tuple[str, str, RelationshipType]:
        """Build the unique identity key for a relationship."""
        return (
            relationship.source_resource_id,
            relationship.target_resource_id,
            relationship.relationship_type,
        )