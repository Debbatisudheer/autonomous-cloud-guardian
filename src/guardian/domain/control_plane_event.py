from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ControlPlaneEventType(StrEnum):
    RESOURCE_DISCOVERED = "resource_discovered"
    RESOURCE_STATE_CHANGED = "resource_state_changed"
    RESOURCE_DRIFT_DETECTED = "resource_drift_detected"
    RESOURCE_HEALTH_CHANGED = "resource_health_changed"
    RESOURCE_LIFECYCLE_CHANGED = "resource_lifecycle_changed"


class ControlPlaneEvent(BaseModel):
    """
    Immutable-style domain representation of a control-plane event.

    An event records something that was observed or changed in the
    control plane. It does not itself perform infrastructure actions.
    """

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    event_type: ControlPlaneEventType
    resource_id: str = Field(min_length=1)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reason: str = Field(min_length=1)
    details: dict[str, str] = Field(default_factory=dict)