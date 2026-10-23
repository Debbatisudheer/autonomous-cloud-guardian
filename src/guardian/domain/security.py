from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SecuritySeverity(StrEnum):
    UNKNOWN = "unknown"
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityCategory(StrEnum):
    CONFIGURATION = "configuration"
    ACCESS_CONTROL = "access_control"
    NETWORK = "network"
    CONTAINER = "container"
    IMAGE = "image"
    SECRETS = "secrets"
    VULNERABILITY = "vulnerability"
    COMPLIANCE = "compliance"
    UNKNOWN = "unknown"


class SecuritySource(StrEnum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    TERRAFORM = "terraform"
    AWS = "aws"
    UNKNOWN = "unknown"


class SecurityEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)

    category: SecurityCategory
    source: SecuritySource

    evidence_type: str = Field(min_length=1)
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    evidence_available: bool
    details: dict[str, str] = Field(default_factory=dict)


class SecurityFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(min_length=1)
    resource_id: str | None = None

    category: SecurityCategory
    severity: SecuritySeverity
    source: SecuritySource

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)

    evidence_id: str | None = None
    evidence_available: bool

    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    metadata: dict[str, str] = Field(default_factory=dict)