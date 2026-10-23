from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ActionType(StrEnum):
    RESTART_CONTAINER = "restart_container"


class ActionStatus(StrEnum):
    REQUESTED = "requested"
    VALIDATED = "validated"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"


class ActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(
        default_factory=lambda: str(uuid4())
    )
    source_event_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    action_type: ActionType
    rationale: str = Field(min_length=1)
    requested_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )


class ActionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    action_type: ActionType
    status: ActionStatus

    pre_action_state: str = Field(min_length=1)
    post_action_state: str = Field(min_length=1)

    executed: bool
    success: bool

    message: str = Field(min_length=1)

    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )