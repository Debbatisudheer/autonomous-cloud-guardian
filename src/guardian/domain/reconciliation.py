from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from guardian.domain.resource import ResourceStatus


class ReconciliationStatus(StrEnum):
    IN_SYNC = "in_sync"
    DRIFTED = "drifted"


class ResourceReconciliation(BaseModel):
    """
    Result of comparing desired and observed resource state.

    This model describes detected drift only. It does not perform
    infrastructure changes.
    """

    model_config = ConfigDict(extra="forbid")

    resource_id: str = Field(min_length=1)
    desired_status: ResourceStatus
    observed_status: ResourceStatus
    status: ReconciliationStatus
    reason: str = Field(min_length=1)