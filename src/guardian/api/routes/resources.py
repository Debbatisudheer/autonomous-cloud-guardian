from fastapi import APIRouter, HTTPException

from guardian.application.resource_health import ResourceHealthAssessor
from guardian.application.resource_relationship import (
    ResourceRelationshipManager,
)
from guardian.application.resource_state import ResourceStateManager
from guardian.domain.resource import Resource
from guardian.domain.resource_health import ResourceHealthObservation
from guardian.domain.resource_relationship import ResourceRelationship
from guardian.domain.resource_state import ResourceState
from guardian.infrastructure.adapters.docker import DockerInfrastructureAdapter

router = APIRouter(prefix="/resources", tags=["resources"])


def _get_resources() -> list[Resource]:
    adapter = DockerInfrastructureAdapter()
    return adapter.discover_resources()


def _get_resource_or_404(resource_id: str) -> Resource:
    resources = _get_resources()

    for resource in resources:
        if resource.id == resource_id:
            return resource

    raise HTTPException(
        status_code=404,
        detail=f"Resource '{resource_id}' was not found.",
    )


@router.get("", response_model=list[Resource])
def list_resources() -> list[Resource]:
    return _get_resources()


@router.get("/{resource_id}", response_model=Resource)
def get_resource(resource_id: str) -> Resource:
    return _get_resource_or_404(resource_id)


@router.get(
    "/{resource_id}/state",
    response_model=ResourceState,
)
def get_resource_state(resource_id: str) -> ResourceState:
    resource = _get_resource_or_404(resource_id)

    state_manager = ResourceStateManager()

    return state_manager.observe(resource)


@router.get(
    "/{resource_id}/health",
    response_model=ResourceHealthObservation,
)
def get_resource_health(resource_id: str) -> ResourceHealthObservation:
    resource = _get_resource_or_404(resource_id)

    assessor = ResourceHealthAssessor()

    return assessor.assess(resource)


@router.get(
    "/{resource_id}/relationships",
    response_model=list[ResourceRelationship],
)
def get_resource_relationships(
    resource_id: str,
) -> list[ResourceRelationship]:
    resources = _get_resources()

    resource_ids = {resource.id for resource in resources}

    if resource_id not in resource_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Resource '{resource_id}' was not found.",
        )

    relationship_manager = ResourceRelationshipManager()

    return relationship_manager.for_resource(resource_id)