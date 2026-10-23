from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EvidenceAnalysisLevel(StrEnum):
    UNKNOWN = "unknown"
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


class EvidenceAnalysis(BaseModel):
    """
    Deterministic analysis of already observed infrastructure evidence.

    This model describes what the evidence currently indicates.
    It does not predict future behavior, make decisions, or execute
    infrastructure actions.
    """

    model_config = ConfigDict(extra="forbid")

    source_event_id: str = Field(min_length=1)

    resource_id: str = Field(min_length=1)

    metric: str = Field(min_length=1)

    level: EvidenceAnalysisLevel

    value: float = Field(ge=0)

    unit: str = Field(min_length=1)

    evidence_available: bool = True

    finding: str = Field(min_length=1)