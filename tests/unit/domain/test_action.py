from guardian.domain.action import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    ActionType,
)


def test_action_request_defaults() -> None:
    request = ActionRequest(
        source_event_id="event-1",
        resource_id="container-1",
        action_type=ActionType.RESTART_CONTAINER,
        rationale="Controlled recovery action.",
    )

    assert request.action_type == ActionType.RESTART_CONTAINER
    assert request.source_event_id == "event-1"
    assert request.resource_id == "container-1"


def test_action_result_success() -> None:
    result = ActionResult(
        action_id="action-1",
        resource_id="container-1",
        action_type=ActionType.RESTART_CONTAINER,
        status=ActionStatus.SUCCEEDED,
        pre_action_state="running",
        post_action_state="running",
        executed=True,
        success=True,
        message="Container restarted.",
    )

    assert result.executed is True
    assert result.success is True
    assert result.status == ActionStatus.SUCCEEDED


def test_action_result_rejected() -> None:
    result = ActionResult(
        action_id="action-2",
        resource_id="container-2",
        action_type=ActionType.RESTART_CONTAINER,
        status=ActionStatus.REJECTED,
        pre_action_state="unknown",
        post_action_state="unknown",
        executed=False,
        success=False,
        message="Resource not authorized.",
    )

    assert result.executed is False
    assert result.success is False
    assert result.status == ActionStatus.REJECTED