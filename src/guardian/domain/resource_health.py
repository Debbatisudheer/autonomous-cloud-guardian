from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.resource import ResourceHealth, ResourceStatus


class ResourceHealthObservation(BaseModel):
    """
    Evidence-backed health observation for an infrastructure resource.

    UNKNOWN means that sufficient health evidence was not available.
    It does not mean that the resource is unhealthy.
    """

    model_config = ConfigDict(extra="forbid")

    resource_id: str = Field(min_length=1)

    status: ResourceStatus
    health: ResourceHealth

    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    reason: str = Field(min_length=1)