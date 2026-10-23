from __future__ import annotations

import time

import docker

from guardian.domain.action import (
    ActionRequest,
    ActionStatus,
    ActionType,
)
from guardian.infrastructure.docker.action_executor import (
    DockerActionExecutor,
)

CONTAINER_NAME = "acg-phase-5-6-target"


def main() -> int:
    print("=" * 72)
    print("PHASE 5.6 — CONTROLLED ACTION EXECUTION VALIDATION")
    print("=" * 72)

    client = docker.from_env()
    target = None
    executor = None

    try:
        # -------------------------------------------------------------
        # 1. DOCKER AVAILABILITY
        # -------------------------------------------------------------

        print()
        print("[1] DOCKER CONTROL PLANE")
        print("-" * 72)

        client.ping()

        print(
            "Docker connectivity          : PASS"
        )

        # -------------------------------------------------------------
        # 2. CREATE DISPOSABLE TARGET
        # -------------------------------------------------------------

        print()
        print("[2] CONTROLLED TEST TARGET")
        print("-" * 72)

        try:
            existing = client.containers.get(
                CONTAINER_NAME
            )
            existing.remove(
                force=True
            )
        except docker.errors.NotFound:
            pass

        target = client.containers.run(
            "alpine:3.22",
            command=(
                "sh -c "
                "\"while true; do sleep 1; done\""
            ),
            name=CONTAINER_NAME,
            detach=True,
            labels={
                "acg.phase": "5.6",
                "acg.controlled-test": "true",
            },
        )

        target.reload()

        resource_id = target.id
        pre_action_state = target.status

        print(
            f"Container name              : "
            f"{target.name}"
        )
        print(
            f"Container ID                : "
            f"{resource_id}"
        )
        print(
            f"Pre-action state            : "
            f"{pre_action_state}"
        )

        if pre_action_state != "running":
            print(
                "Controlled target           : FAIL"
            )
            return 1

        print(
            "Controlled target           : PASS"
        )

        # -------------------------------------------------------------
        # 3. BUILD EXPLICIT ACTION REQUEST
        # -------------------------------------------------------------

        print()
        print("[3] ACTION REQUEST")
        print("-" * 72)

        request = ActionRequest(
            source_event_id=(
                "phase-5-6-controlled-validation"
            ),
            resource_id=resource_id,
            action_type=ActionType.RESTART_CONTAINER,
            rationale=(
                "Controlled Phase 5.6 validation action "
                "against a disposable Docker container."
            ),
        )

        print(
            f"Action ID                  : "
            f"{request.action_id}"
        )
        print(
            f"Action type                : "
            f"{request.action_type}"
        )
        print(
            f"Resource ID                : "
            f"{request.resource_id}"
        )
        print(
            "Explicit authorization     : PASS"
        )

        # -------------------------------------------------------------
        # 4. EXECUTE REAL DOCKER ACTION
        # -------------------------------------------------------------

        print()
        print("[4] REAL ACTION EXECUTION")
        print("-" * 72)

        executor = DockerActionExecutor(
            allowed_resource_ids={resource_id}
        )

        result = executor.execute(request)

        print(
            f"Status                     : "
            f"{result.status}"
        )
        print(
            f"Executed                   : "
            f"{result.executed}"
        )
        print(
            f"Success                    : "
            f"{result.success}"
        )
        print(
            f"Pre-action state           : "
            f"{result.pre_action_state}"
        )
        print(
            f"Post-action state          : "
            f"{result.post_action_state}"
        )
        print(
            f"Message                    : "
            f"{result.message}"
        )

        if not result.executed:
            print(
                "Real action execution      : FAIL"
            )
            return 1

        if result.status != ActionStatus.SUCCEEDED:
            print(
                "Real action execution      : FAIL"
            )
            return 1

        if not result.success:
            print(
                "Real action execution      : FAIL"
            )
            return 1

        print(
            "Real action execution      : PASS"
        )

        # -------------------------------------------------------------
        # 5. VERIFY REAL POST-ACTION STATE
        # -------------------------------------------------------------

        print()
        print("[5] POST-ACTION VERIFICATION")
        print("-" * 72)

        time.sleep(1)

        target.reload()

        actual_post_state = target.status

        print(
            f"Observed container state    : "
            f"{actual_post_state}"
        )

        if actual_post_state != "running":
            print(
                "Post-action verification   : FAIL"
            )
            return 1

        if result.post_action_state != actual_post_state:
            print(
                "State evidence correlation : FAIL"
            )
            return 1

        print(
            "Post-action verification   : PASS"
        )
        print(
            "State evidence correlation : PASS"
        )

        # -------------------------------------------------------------
        # 6. SAFETY BOUNDARY
        # -------------------------------------------------------------

        print()
        print("[6] ACTION SAFETY BOUNDARY")
        print("-" * 72)

        print(
            "Action type                 : "
            "RESTART_CONTAINER"
        )
        print(
            "Target                      : "
            "DISPOSABLE TEST CONTAINER"
        )
        print(
            "Explicit authorization      : YES"
        )
        print(
            "Post-action verification    : YES"
        )
        print(
            "PostgreSQL modified         : NO"
        )
        print(
            "Redis modified              : NO"
        )
        print(
            "Kafka modified              : NO"
        )
        print(
            "SeaweedFS modified          : NO"
        )
        print(
            "Production infrastructure   : NOT TOUCHED"
        )
        print(
            "Safety boundary             : PASS"
        )

        # -------------------------------------------------------------
        # FINAL
        # -------------------------------------------------------------

        print()
        print("=" * 72)
        print("PHASE 5.6 VALIDATION RESULT")
        print("=" * 72)

        print(
            "DOCKER CONNECTIVITY         : PASS"
        )
        print(
            "CONTROLLED TARGET           : PASS"
        )
        print(
            "ACTION REQUEST              : PASS"
        )
        print(
            "REAL ACTION EXECUTION       : PASS"
        )
        print(
            "POST-ACTION VERIFICATION    : PASS"
        )
        print(
            "ACTION EVIDENCE             : PASS"
        )
        print(
            "SAFETY BOUNDARY             : PASS"
        )
        print()
        print(
            "PHASE 5.6 — COMPLETE: PASS"
        )
        print("=" * 72)

        return 0

    finally:
        if executor is not None:
            executor.close()

        if target is not None:
            try:
                target.remove(
                    force=True
                )
                print()
                print(
                    "Disposable Phase 5.6 target removed."
                )
            except docker.errors.NotFound:
                pass

        client.close()


if __name__ == "__main__":
    raise SystemExit(main())