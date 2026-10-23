from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.resource import ResourceHealth, ResourceStatus


class ResourceState(BaseModel):
    """
    Current observed state of an infrastructure resource.

    ResourceState represents an observation of a resource at a
    particular point in time. It does not define desired state.
    """

    model_config = ConfigDict(extra="forbid")

    resource_id: str = Field(min_length=1)

    status: ResourceStatus = ResourceStatus.UNKNOWN
    health: ResourceHealth = ResourceHealth.UNKNOWN

    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    attributes: dict[str, Any] = Field(default_factory=dict)
