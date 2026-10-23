from __future__ import annotations

from datetime import UTC, datetime

import docker
from docker.errors import DockerException, NotFound

from guardian.application.action_executor import (
    ActionExecutor,
)
from guardian.domain.action import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    ActionType,
)


class DockerActionExecutor(ActionExecutor):
    """
    Controlled Docker action executor.

    Currently supports only RESTART_CONTAINER.

    The target must be explicitly authorized through
    allowed_resource_ids.
    """

    def __init__(
        self,
        allowed_resource_ids: set[str] | None = None,
    ) -> None:
        self._client = docker.from_env()
        self._allowed_resource_ids = (
            allowed_resource_ids
            if allowed_resource_ids is not None
            else set()
        )

    def execute(
        self,
        request: ActionRequest,
    ) -> ActionResult:
        if request.action_type != ActionType.RESTART_CONTAINER:
            return ActionResult(
                action_id=request.action_id,
                resource_id=request.resource_id,
                action_type=request.action_type,
                status=ActionStatus.REJECTED,
                pre_action_state="unknown",
                post_action_state="unknown",
                executed=False,
                success=False,
                message=(
                    "Action type is not permitted by the "
                    "Docker action executor."
                ),
            )

        if request.resource_id not in self._allowed_resource_ids:
            return ActionResult(
                action_id=request.action_id,
                resource_id=request.resource_id,
                action_type=request.action_type,
                status=ActionStatus.REJECTED,
                pre_action_state="unknown",
                post_action_state="unknown",
                executed=False,
                success=False,
                message=(
                    "Resource is not explicitly authorized "
                    "for controlled action execution."
                ),
            )

        try:
            container = self._client.containers.get(
                request.resource_id
            )
        except NotFound:
            return ActionResult(
                action_id=request.action_id,
                resource_id=request.resource_id,
                action_type=request.action_type,
                status=ActionStatus.FAILED,
                pre_action_state="not_found",
                post_action_state="not_found",
                executed=False,
                success=False,
                message="Docker container was not found.",
            )
        except DockerException as exc:
            return ActionResult(
                action_id=request.action_id,
                resource_id=request.resource_id,
                action_type=request.action_type,
                status=ActionStatus.FAILED,
                pre_action_state="unknown",
                post_action_state="unknown",
                executed=False,
                success=False,
                message=f"Docker lookup failed: {exc}",
            )

        pre_action_state = container.status

        try:
            container.restart(timeout=10)

            container.reload()

            post_action_state = container.status

            success = post_action_state == "running"

            return ActionResult(
                action_id=request.action_id,
                resource_id=request.resource_id,
                action_type=request.action_type,
                status=(
                    ActionStatus.SUCCEEDED
                    if success
                    else ActionStatus.FAILED
                ),
                pre_action_state=pre_action_state,
                post_action_state=post_action_state,
                executed=True,
                success=success,
                message=(
                    "Docker container restarted and is running."
                    if success
                    else (
                        "Docker restart executed, but the "
                        "container did not return to running state."
                    )
                ),
                executed_at=datetime.now(UTC),
            )

        except DockerException as exc:
            try:
                container.reload()
                post_action_state = container.status
            except DockerException:
                post_action_state = "unknown"

            return ActionResult(
                action_id=request.action_id,
                resource_id=request.resource_id,
                action_type=request.action_type,
                status=ActionStatus.FAILED,
                pre_action_state=pre_action_state,
                post_action_state=post_action_state,
                executed=True,
                success=False,
                message=f"Docker restart failed: {exc}",
                executed_at=datetime.now(UTC),
            )

    def close(self) -> None:
        self._client.close()