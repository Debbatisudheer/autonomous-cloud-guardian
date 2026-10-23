import pytest

from guardian.application.resource_relationship import (
    ResourceRelationshipAlreadyExistsError,
    ResourceRelationshipManager,
    ResourceRelationshipNotFoundError,
)
from guardian.domain.resource_relationship import (
    RelationshipType,
    ResourceRelationship,
)


def make_relationship(
    source: str = "resource-a",
    target: str = "resource-b",
    relationship_type: RelationshipType = RelationshipType.DEPENDS_ON,
) -> ResourceRelationship:
    return ResourceRelationship(
        source_resource_id=source,
        target_resource_id=target,
        relationship_type=relationship_type,
    )


def test_manager_starts_empty() -> None:
    manager = ResourceRelationshipManager()

    assert manager.get_all() == []


def test_add_and_list_relationship() -> None:
    manager = ResourceRelationshipManager()
    relationship = make_relationship()

    manager.add(relationship)

    assert manager.get_all() == [relationship]


def test_duplicate_relationship_is_rejected() -> None:
    manager = ResourceRelationshipManager()
    relationship = make_relationship()

    manager.add(relationship)

    with pytest.raises(ResourceRelationshipAlreadyExistsError):
        manager.add(relationship)


def test_for_resource_returns_matching_relationships() -> None:
    manager = ResourceRelationshipManager()

    dependency = make_relationship(
        source="resource-a",
        target="resource-b",
    )

    related = make_relationship(
        source="resource-c",
        target="resource-a",
        relationship_type=RelationshipType.RELATED_TO,
    )

    unrelated = make_relationship(
        source="resource-x",
        target="resource-y",
    )

    manager.add(dependency)
    manager.add(related)
    manager.add(unrelated)

    relationships = manager.for_resource("resource-a")

    assert len(relationships) == 2
    assert dependency in relationships
    assert related in relationships
    assert unrelated not in relationships


def test_remove_relationship() -> None:
    manager = ResourceRelationshipManager()
    relationship = make_relationship()

    manager.add(relationship)
    manager.remove(relationship)

    assert manager.get_all() == []


def test_remove_missing_relationship_is_rejected() -> None:
    manager = ResourceRelationshipManager()
    relationship = make_relationship()

    with pytest.raises(ResourceRelationshipNotFoundError):
        manager.remove(relationship)


def test_clear_removes_all_relationships() -> None:
    manager = ResourceRelationshipManager()

    manager.add(
        make_relationship(
            "resource-a",
            "resource-b",
        )
    )

    manager.add(
        make_relationship(
            "resource-c",
            "resource-d",
        )
    )

    manager.clear()

    assert manager.get_all() == []