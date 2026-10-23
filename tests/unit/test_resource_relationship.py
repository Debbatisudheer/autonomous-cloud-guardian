import pytest
from pydantic import ValidationError

from guardian.domain.resource_relationship import (
    RelationshipType,
    ResourceRelationship,
)


def test_dependency_relationship() -> None:
    relationship = ResourceRelationship(
        source_resource_id="resource-a",
        target_resource_id="resource-b",
        relationship_type=RelationshipType.DEPENDS_ON,
    )

    assert relationship.source_resource_id == "resource-a"
    assert relationship.target_resource_id == "resource-b"
    assert relationship.relationship_type == RelationshipType.DEPENDS_ON


def test_related_relationship() -> None:
    relationship = ResourceRelationship(
        source_resource_id="resource-a",
        target_resource_id="resource-b",
        relationship_type=RelationshipType.RELATED_TO,
    )

    assert relationship.relationship_type == RelationshipType.RELATED_TO


def test_empty_source_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ResourceRelationship(
            source_resource_id="",
            target_resource_id="resource-b",
            relationship_type=RelationshipType.DEPENDS_ON,
        )


def test_empty_target_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ResourceRelationship(
            source_resource_id="resource-a",
            target_resource_id="",
            relationship_type=RelationshipType.DEPENDS_ON,
        )


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        ResourceRelationship(
            source_resource_id="resource-a",
            target_resource_id="resource-b",
            relationship_type=RelationshipType.DEPENDS_ON,
            unexpected="value",
        )
