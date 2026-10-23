from guardian.domain.action import (
    ActionRequest,
    ActionStatus,
    ActionType,
)


class FakeActionExecutor:
    def execute(self, request: ActionRequest):
        return {
            "action_id": request.action_id,
            "resource_id": request.resource_id,
            "action_type": request.action_type,
            "status": ActionStatus.SUCCEEDED,
        }


def test_action_request_can_be_passed_to_executor() -> None:
    executor = FakeActionExecutor()

    request = ActionRequest(
        source_event_id="event-1",
        resource_id="container-1",
        action_type=ActionType.RESTART_CONTAINER,
        rationale="Controlled recovery.",
    )

    result = executor.execute(request)

    assert result["resource_id"] == "container-1"
    assert result["action_type"] == ActionType.RESTART_CONTAINER
    assert result["status"] == ActionStatus.SUCCEEDED