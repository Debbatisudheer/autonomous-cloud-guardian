from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RelationshipType(StrEnum):
    """Relationship between two infrastructure resources."""

    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"


class ResourceRelationship(BaseModel):
    """
    Describes a relationship between two infrastructure resources.

    The relationship is directional: source_resource_id is related
    to target_resource_id according to relationship_type.
    """

    model_config = ConfigDict(extra="forbid")

    source_resource_id: str = Field(min_length=1)
    target_resource_id: str = Field(min_length=1)
    relationship_type: RelationshipType
