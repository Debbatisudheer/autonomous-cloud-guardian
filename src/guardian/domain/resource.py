from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResourceProvider(StrEnum):
    """Infrastructure provider that owns or manages a resource."""

    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    TERRAFORM = "terraform"
    AWS = "aws"
    UNKNOWN = "unknown"


class ResourceStatus(StrEnum):
    """Current lifecycle status of a resource."""

    UNKNOWN = "unknown"
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    DELETING = "deleting"
    DELETED = "deleted"


class ResourceHealth(StrEnum):
    """Current health assessment of a resource."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class Resource(BaseModel):
    """
    Canonical representation of an infrastructure resource.

    This domain model intentionally contains no Docker, Kubernetes,
    Terraform, or cloud-provider implementation details.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    provider: ResourceProvider = ResourceProvider.UNKNOWN

    status: ResourceStatus = ResourceStatus.UNKNOWN
    health: ResourceHealth = ResourceHealth.UNKNOWN

    region: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )