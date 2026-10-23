from __future__ import annotations

import time
from datetime import UTC, datetime

import docker

from guardian.application.control_loop_decision import (
    ControlLoopDecisionService,
)
from guardian.application.control_loop_evidence import (
    ControlLoopEvidenceService,
)
from guardian.application.control_loop_orchestrator import (
    ControlLoopOrchestrator,
)
from guardian.application.control_loop_prediction import (
    ControlLoopPredictionService,
)
from guardian.application.decision_engine import (
    DecisionEngine,
)
from guardian.application.evidence_analysis import (
    EvidenceAnalysisService,
)
from guardian.application.prediction_engine import (
    PredictionEngine,
)
from guardian.domain.action import (
    ActionRequest,
    ActionStatus,
    ActionType,
)
from guardian.domain.control_loop import (
    ControlLoopState,
)
from guardian.domain.health_signal import (
    HealthSignalLevel,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
    ObservabilityEventType,
)
from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
    TelemetrySource,
)
from guardian.infrastructure.docker.action_executor import (
    DockerActionExecutor,
)

CONTAINER_NAME = "acg-phase-5-7-target"


def collect_cpu_percent(
    container: docker.models.containers.Container,
) -> float:
    """Collect one real CPU observation from Docker."""

    stats = container.stats(stream=False)

    cpu_stats = stats.get("cpu_stats", {})
    precpu_stats = stats.get("precpu_stats", {})

    cpu_usage = cpu_stats.get("cpu_usage", {})
    precpu_usage = precpu_stats.get("cpu_usage", {})

    total_usage = cpu_usage.get(
        "total_usage",
        0,
    )

    previous_total_usage = precpu_usage.get(
        "total_usage",
        0,
    )

    system_usage = cpu_stats.get(
        "system_cpu_usage",
        0,
    )

    previous_system_usage = precpu_stats.get(
        "system_cpu_usage",
        0,
    )

    cpu_delta = (
        total_usage
        - previous_total_usage
    )

    system_delta = (
        system_usage
        - previous_system_usage
    )

    online_cpus = cpu_stats.get(
        "online_cpus",
        1,
    )

    if system_delta <= 0 or cpu_delta < 0:
        return 0.0

    return (
        cpu_delta
        / system_delta
        * online_cpus
        * 100.0
    )


def cpu_health_level(
    value: float,
) -> HealthSignalLevel:
    """
    CPU health classification matching Phase 4.6.
    """

    if value >= 90.0:
        return HealthSignalLevel.CRITICAL

    if value >= 70.0:
        return HealthSignalLevel.WARNING

    return HealthSignalLevel.HEALTHY


def main() -> int:
    print("=" * 76)
    print(
        "PHASE 5.7 — CONTROL LOOP INTEGRATION VALIDATION"
    )
    print("=" * 76)

    client = docker.from_env()

    target = None
    action_executor = None

    try:
        # =============================================================
        # 1. DOCKER CONTROL PLANE
        # =============================================================

        print()
        print("[1] DOCKER CONTROL PLANE")
        print("-" * 76)

        client.ping()

        print(
            "Docker connectivity          : PASS"
        )

        # =============================================================
        # 2. CONTROLLED INTEGRATION TARGET
        # =============================================================

        print()
        print(
            "[2] CONTROLLED INTEGRATION TARGET"
        )
        print("-" * 76)

        try:
            existing = client.containers.get(
                CONTAINER_NAME
            )
            existing.remove(force=True)
        except docker.errors.NotFound:
            pass

        target = client.containers.run(
            "alpine:3.22",
            command=(
                "sh -c "
                "\"while true; do "
                "echo acg-phase-5-7; "
                "sleep 1; "
                "done\""
            ),
            name=CONTAINER_NAME,
            detach=True,
            labels={
                "acg.phase": "5.7",
                "acg.controlled-test": "true",
            },
        )

        target.reload()

        resource_id = target.id

        print(
            f"Container name              : "
            f"{target.name}"
        )

        print(
            f"Resource ID                 : "
            f"{resource_id}"
        )

        print(
            f"Initial state               : "
            f"{target.status}"
        )

        if target.status != "running":
            print(
                "Integration target          : FAIL"
            )
            return 1

        print(
            "Integration target          : PASS"
        )

        # =============================================================
        # 3. FIRST REAL TELEMETRY SAMPLE
        # =============================================================

        print()
        print(
            "[3] REAL TELEMETRY — FIRST SAMPLE"
        )
        print("-" * 76)

        cpu_percent_1 = collect_cpu_percent(
            target
        )

        observed_at_1 = datetime.now(UTC)

        print(
            f"CPU observation 1          : "
            f"{cpu_percent_1}"
        )

        if cpu_percent_1 < 0:
            print(
                "Real telemetry              : FAIL"
            )
            return 1

        print(
            "Real telemetry              : PASS"
        )

        # =============================================================
        # 4. SECOND / CURRENT REAL TELEMETRY SAMPLE
        # =============================================================

        print()
        print(
            "[4] REAL TELEMETRY — CURRENT SAMPLE"
        )
        print("-" * 76)

        time.sleep(1)

        target.reload()

        cpu_percent_2 = collect_cpu_percent(
            target
        )

        observed_at_2 = datetime.now(UTC)

        print(
            f"CPU observation 1          : "
            f"{cpu_percent_1}"
        )

        print(
            f"CPU observation 2          : "
            f"{cpu_percent_2}"
        )

        if cpu_percent_2 < 0:
            print(
                "Current telemetry           : FAIL"
            )
            return 1

        print(
            "Current telemetry           : PASS"
        )

        # =============================================================
        # 5. TELEMETRY DOMAIN EVIDENCE
        # =============================================================

        print()
        print(
            "[5] TELEMETRY DOMAIN EVIDENCE"
        )
        print("-" * 76)

        observation_1 = TelemetryObservation(
            resource_id=resource_id,
            metric=TelemetryMetric.CPU_USAGE_PERCENT,
            value=cpu_percent_1,
            unit="percent",
            observed_at=observed_at_1,
            source=TelemetrySource.DOCKER,
        )

        observation_2 = TelemetryObservation(
            resource_id=resource_id,
            metric=TelemetryMetric.CPU_USAGE_PERCENT,
            value=cpu_percent_2,
            unit="percent",
            observed_at=observed_at_2,
            source=TelemetrySource.DOCKER,
        )

        observations = [
            observation_1,
            observation_2,
        ]

        resource_correlation = (
            observation_1.resource_id == resource_id
            and observation_2.resource_id == resource_id
        )

        metric_correlation = (
            observation_1.metric
            == observation_2.metric
        )

        chronological_ordering = (
            observation_1.observed_at
            < observation_2.observed_at
        )

        print(
            "Observation count           : "
            f"{len(observations)}"
        )

        print(
            "Resource correlation        : "
            f"{resource_correlation}"
        )

        print(
            "Metric correlation          : "
            f"{metric_correlation}"
        )

        print(
            "Chronological ordering      : "
            f"{chronological_ordering}"
        )

        if not resource_correlation:
            print(
                "Telemetry correlation       : FAIL"
            )
            return 1

        if not metric_correlation:
            print(
                "Telemetry metric            : FAIL"
            )
            return 1

        if not chronological_ordering:
            print(
                "Telemetry ordering          : FAIL"
            )
            return 1

        print(
            "Telemetry domain evidence   : PASS"
        )

        # =============================================================
        # 6. CURRENT HEALTH SIGNAL
        # =============================================================

        print()
        print(
            "[6] CURRENT HEALTH SIGNAL"
        )
        print("-" * 76)

        # The latest observation is the current evidence
        # consumed by the control loop.

        current_health_level = cpu_health_level(
            cpu_percent_2
        )

        print(
            f"Current CPU value           : "
            f"{cpu_percent_2}"
        )

        print(
            f"Current health level        : "
            f"{current_health_level}"
        )

        print(
            "Health signal               : PASS"
        )

        # =============================================================
        # 7. OBSERVABILITY EVENT
        # =============================================================

        print()
        print(
            "[7] OBSERVABILITY EVENT"
        )
        print("-" * 76)

        # IMPORTANT:
        # The event uses the latest/current observation.
        #
        # Therefore:
        #
        # event.value
        #     ==
        # observation_2.value
        #     ==
        # prediction.current_value
        #
        # This is required by DecisionEngine correlation validation.

        event = ObservabilityEvent(
            event_type=(
                ObservabilityEventType.TELEMETRY_OBSERVED
            ),
            resource_id=resource_id,
            metric=TelemetryMetric.CPU_USAGE_PERCENT,
            value=observation_2.value,
            unit=observation_2.unit,
            observed_at=observation_2.observed_at,
            source=TelemetrySource.DOCKER,
            health_level=current_health_level,
            metadata={
                "phase": "5.7",
                "controlled_target": "true",
                "evidence_sample": "latest",
            },
        )

        print(
            f"Event ID                    : "
            f"{event.event_id}"
        )

        print(
            "Resource correlation        : "
            f"{event.resource_id == resource_id}"
        )

        print(
            f"Metric                      : "
            f"{event.metric}"
        )

        print(
            f"Event value                 : "
            f"{event.value}"
        )

        print(
            f"Current telemetry value     : "
            f"{observation_2.value}"
        )

        print(
            f"Health level                : "
            f"{event.health_level}"
        )

        print(
            f"Source                      : "
            f"{event.source}"
        )

        if event.resource_id != resource_id:
            print(
                "Observability event         : FAIL"
            )
            return 1

        if event.value != observation_2.value:
            print(
                "Event value correlation     : FAIL"
            )
            return 1

        if event.health_level != (
            current_health_level
        ):
            print(
                "Health correlation          : FAIL"
            )
            return 1

        print(
            "Observability event         : PASS"
        )

        # =============================================================
        # 8. CONTROL LOOP INITIALIZATION
        # =============================================================

        print()
        print(
            "[8] CONTROL LOOP INITIALIZATION"
        )
        print("-" * 76)

        orchestrator = ControlLoopOrchestrator()

        cycle = orchestrator.start(event)

        print(
            f"Cycle ID                    : "
            f"{cycle.cycle_id}"
        )

        print(
            f"Initial state               : "
            f"{cycle.state}"
        )

        print(
            f"Cycle resource              : "
            f"{cycle.resource_id}"
        )

        print(
            f"Cycle metric                : "
            f"{cycle.metric}"
        )

        if cycle.state != (
            ControlLoopState.RECEIVED
        ):
            print(
                "Cycle initialization       : FAIL"
            )
            return 1

        if cycle.resource_id != resource_id:
            print(
                "Cycle resource correlation : FAIL"
            )
            return 1

        print(
            "Cycle initialization       : PASS"
        )

        # =============================================================
        # 9. EVIDENCE ANALYSIS
        # =============================================================

        print()
        print("[9] EVIDENCE ANALYSIS")
        print("-" * 76)

        evidence_service = (
            ControlLoopEvidenceService(
                EvidenceAnalysisService()
            )
        )

        evidence_result = (
            evidence_service.intake_and_analyze(
                cycle,
                event,
            )
        )

        cycle = evidence_result.cycle
        analysis = evidence_result.analysis

        print(
            f"Analysis level             : "
            f"{analysis.level}"
        )

        print(
            f"Evidence available         : "
            f"{analysis.evidence_available}"
        )

        print(
            f"Analysis value             : "
            f"{analysis.value}"
        )

        print(
            f"Current telemetry value    : "
            f"{observation_2.value}"
        )

        print(
            f"Finding                    : "
            f"{analysis.finding}"
        )

        print(
            f"Cycle state                : "
            f"{cycle.state}"
        )

        if not analysis.evidence_available:
            print(
                "Evidence analysis          : FAIL"
            )
            return 1

        if analysis.value != observation_2.value:
            print(
                "Evidence value correlation : FAIL"
            )
            return 1

        if cycle.state != (
            ControlLoopState.ANALYZING
        ):
            print(
                "Evidence lifecycle         : FAIL"
            )
            return 1

        print(
            "Evidence analysis          : PASS"
        )

        # =============================================================
        # 10. PREDICTION
        # =============================================================

        print()
        print("[10] PREDICTION")
        print("-" * 76)

        prediction_service = (
            ControlLoopPredictionService(
                PredictionEngine()
            )
        )

        # Actual ControlLoopPredictionService API:
        #
        #     predict(cycle, observations)
        #
        # Both real observations are supplied.
        # The prediction engine uses the latest observation
        # as current_value.

        prediction_result = (
            prediction_service.predict(
                cycle,
                observations,
            )
        )

        cycle = prediction_result.cycle
        prediction = prediction_result.prediction

        print(
            f"Current value              : "
            f"{prediction.current_value}"
        )

        print(
            f"Latest telemetry value     : "
            f"{observation_2.value}"
        )

        print(
            f"Predicted value            : "
            f"{prediction.predicted_value}"
        )

        print(
            f"Direction                  : "
            f"{prediction.direction}"
        )

        print(
            f"Confidence                 : "
            f"{prediction.confidence}"
        )

        print(
            f"Sample count               : "
            f"{prediction.sample_count}"
        )

        print(
            f"Evidence available         : "
            f"{prediction.evidence_available}"
        )

        print(
            f"Cycle state                : "
            f"{cycle.state}"
        )

        if not prediction.evidence_available:
            print(
                "Prediction                 : FAIL"
            )
            return 1

        if prediction.current_value != (
            observation_2.value
        ):
            print(
                "Prediction current value   : FAIL"
            )
            return 1

        if prediction.resource_id != resource_id:
            print(
                "Prediction resource        : FAIL"
            )
            return 1

        if prediction.metric != (
            TelemetryMetric.CPU_USAGE_PERCENT.value
        ):
            print(
                "Prediction metric          : FAIL"
            )
            return 1

        if prediction.sample_count != 2:
            print(
                "Prediction sample count    : FAIL"
            )
            return 1

        if cycle.state != (
            ControlLoopState.PREDICTING
        ):
            print(
                "Prediction lifecycle       : FAIL"
            )
            return 1

        print(
            "Prediction                 : PASS"
        )

        # =============================================================
        # 11. EVIDENCE / PREDICTION CORRELATION
        # =============================================================

        print()
        print(
            "[11] EVIDENCE / PREDICTION CORRELATION"
        )
        print("-" * 76)

        print(
            f"Evidence value             : "
            f"{analysis.value}"
        )

        print(
            f"Prediction current value   : "
            f"{prediction.current_value}"
        )

        print(
            f"Evidence resource          : "
            f"{analysis.resource_id}"
        )

        print(
            f"Prediction resource        : "
            f"{prediction.resource_id}"
        )

        print(
            f"Evidence metric            : "
            f"{analysis.metric}"
        )

        print(
            f"Prediction metric          : "
            f"{prediction.metric}"
        )

        value_correlation = (
            analysis.value
            == prediction.current_value
        )

        resource_correlation = (
            analysis.resource_id
            == prediction.resource_id
        )

        metric_correlation = (
            analysis.metric
            == prediction.metric
        )

        print(
            "Value correlation          : "
            f"{value_correlation}"
        )

        print(
            "Resource correlation       : "
            f"{resource_correlation}"
        )

        print(
            "Metric correlation         : "
            f"{metric_correlation}"
        )

        if not value_correlation:
            print(
                "Value correlation          : FAIL"
            )
            return 1

        if not resource_correlation:
            print(
                "Resource correlation       : FAIL"
            )
            return 1

        if not metric_correlation:
            print(
                "Metric correlation         : FAIL"
            )
            return 1

        print(
            "Evidence/prediction        : PASS"
        )

        # =============================================================
        # 12. DECISION
        # =============================================================

        print()
        print("[12] DECISION")
        print("-" * 76)

        decision_service = (
            ControlLoopDecisionService(
                DecisionEngine()
            )
        )

        decision_result = (
            decision_service.decide(
                cycle,
                analysis,
                prediction,
            )
        )

        cycle = decision_result.cycle
        decision = decision_result.decision

        print(
            f"Decision outcome           : "
            f"{decision.outcome}"
        )

        print(
            f"Decision priority          : "
            f"{decision.priority}"
        )

        print(
            f"Evidence available         : "
            f"{decision.evidence_available}"
        )

        print(
            f"Current value              : "
            f"{decision.current_value}"
        )

        print(
            f"Predicted value            : "
            f"{decision.predicted_value}"
        )

        print(
            f"Rationale                  : "
            f"{decision.rationale}"
        )

        print(
            f"Cycle state                : "
            f"{cycle.state}"
        )

        if cycle.state != (
            ControlLoopState.DECIDING
        ):
            print(
                "Decision lifecycle         : FAIL"
            )
            return 1

        if decision.resource_id != resource_id:
            print(
                "Decision resource          : FAIL"
            )
            return 1

        if decision.metric != (
            TelemetryMetric.CPU_USAGE_PERCENT.value
        ):
            print(
                "Decision metric            : FAIL"
            )
            return 1

        if decision.current_value != (
            prediction.current_value
        ):
            print(
                "Decision value correlation : FAIL"
            )
            return 1

        if decision.predicted_value != (
            prediction.predicted_value
        ):
            print(
                "Decision prediction        : FAIL"
            )
            return 1

        print(
            "Decision generation        : PASS"
        )

        # =============================================================
        # 13. ACTION DECISION BOUNDARY
        # =============================================================

        print()
        print(
            "[13] ACTION DECISION BOUNDARY"
        )
        print("-" * 76)

        if decision.outcome.value != (
            "action_recommended"
        ):
            print(
                f"Decision outcome           : "
                f"{decision.outcome}"
            )

            print(
                "Infrastructure action      : NONE"
            )

            print(
                "Reason                     : "
                "Real evidence and prediction "
                "did not justify an infrastructure "
                "action."
            )

            print(
                "No-action boundary         : PASS"
            )

            print()
            print("=" * 76)

            print(
                "REAL DOCKER TELEMETRY      : PASS"
            )

            print(
                "HEALTH SIGNAL              : PASS"
            )

            print(
                "OBSERVABILITY EVENT        : PASS"
            )

            print(
                "CONTROL LOOP               : PASS"
            )

            print(
                "EVIDENCE ANALYSIS          : PASS"
            )

            print(
                "PREDICTION                 : PASS"
            )

            print(
                "EVIDENCE/PREDICTION        : PASS"
            )

            print(
                "DECISION                   : PASS"
            )

            print(
                "ACTION BOUNDARY            : PASS"
            )

            print(
                "INFRASTRUCTURE ACTION      : NONE"
            )

            print()
            print(
                "PHASE 5.7 — COMPLETE: PASS"
            )
            print("=" * 76)

            return 0

        # =============================================================
        # 14. CONTROLLED REAL ACTION
        # =============================================================

        print()
        print(
            "[14] CONTROLLED REAL ACTION"
        )
        print("-" * 76)

        action_executor = DockerActionExecutor(
            allowed_resource_ids={
                resource_id
            }
        )

        action_request = ActionRequest(
            source_event_id=event.event_id,
            resource_id=resource_id,
            action_type=ActionType.RESTART_CONTAINER,
            rationale=decision.rationale,
        )

        print(
            "Explicit authorization       : PASS"
        )

        print(
            f"Action type                  : "
            f"{action_request.action_type}"
        )

        action_result = (
            action_executor.execute(
                action_request
            )
        )

        print(
            f"Action status                : "
            f"{action_result.status}"
        )

        print(
            f"Action executed              : "
            f"{action_result.executed}"
        )

        print(
            f"Action success               : "
            f"{action_result.success}"
        )

        print(
            f"Pre-action state             : "
            f"{action_result.pre_action_state}"
        )

        print(
            f"Post-action state            : "
            f"{action_result.post_action_state}"
        )

        print(
            f"Message                      : "
            f"{action_result.message}"
        )

        if (
            action_result.status
            != ActionStatus.SUCCEEDED
        ):
            print(
                "Controlled action            : FAIL"
            )
            return 1

        if not action_result.executed:
            print(
                "Action execution             : FAIL"
            )
            return 1

        if not action_result.success:
            print(
                "Action success               : FAIL"
            )
            return 1

        print(
            "Controlled action            : PASS"
        )

        # =============================================================
        # 15. POST-ACTION VERIFICATION
        # =============================================================

        print()
        print(
            "[15] POST-ACTION VERIFICATION"
        )
        print("-" * 76)

        time.sleep(1)

        target.reload()

        final_state = target.status

        print(
            f"Final Docker state           : "
            f"{final_state}"
        )

        print(
            f"Recorded post-action state  : "
            f"{action_result.post_action_state}"
        )

        if final_state != "running":
            print(
                "Final verification           : FAIL"
            )
            return 1

        if (
            action_result.post_action_state
            != final_state
        ):
            print(
                "State evidence correlation   : FAIL"
            )
            return 1

        print(
            "Final verification           : PASS"
        )

        print(
            "State evidence correlation   : PASS"
        )

        # =============================================================
        # 16. FINAL INTEGRATION RESULT
        # =============================================================

        print()
        print("=" * 76)
        print(
            "PHASE 5.7 — CONTROL LOOP INTEGRATION RESULT"
        )
        print("=" * 76)

        print(
            "REAL DOCKER TELEMETRY        : PASS"
        )

        print(
            "HEALTH SIGNAL                : PASS"
        )

        print(
            "OBSERVABILITY EVENT          : PASS"
        )

        print(
            "CONTROL LOOP                 : PASS"
        )

        print(
            "EVIDENCE ANALYSIS            : PASS"
        )

        print(
            "PREDICTION                   : PASS"
        )

        print(
            "EVIDENCE/PREDICTION          : PASS"
        )

        print(
            "DECISION                     : PASS"
        )

        print(
            "ACTION AUTHORIZATION         : PASS"
        )

        print(
            "REAL CONTROLLED ACTION       : PASS"
        )

        print(
            "POST-ACTION VERIFICATION     : PASS"
        )

        print()
        print(
            "PHASE 5.7 — COMPLETE: PASS"
        )

        print("=" * 76)

        return 0

    finally:
        if action_executor is not None:
            action_executor.close()

        if target is not None:
            try:
                target.remove(force=True)

                print()
                print(
                    "Disposable Phase 5.7 target removed."
                )

            except docker.errors.NotFound:
                pass

        client.close()


if __name__ == "__main__":
    raise SystemExit(main())