from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SecurityRecommendationOutcome(StrEnum):
    NO_RECOMMENDATION = "no_recommendation"
    REVIEW = "review"
    REMEDIATION_RECOMMENDED = (
        "remediation_recommended"
    )


class SecurityRecommendationPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SecurityRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(min_length=1)

    finding_id: str = Field(min_length=1)
    signal_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)

    resource_id: str | None = None

    outcome: SecurityRecommendationOutcome
    priority: SecurityRecommendationPriority

    title: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    rationale: str = Field(min_length=1)

    evidence_available: bool

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    metadata: dict[str, str] = Field(
        default_factory=dict
    )