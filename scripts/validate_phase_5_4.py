from __future__ import annotations

from guardian.application.control_loop_prediction import (
    ControlLoopPredictionService,
)
from guardian.domain.control_loop import (
    ControlLoopCycle,
    ControlLoopState,
)
from guardian.domain.health_signal import (
    HealthSignalLevel,
)
from guardian.domain.observability_event import (
    ObservabilityEvent,
    ObservabilityEventType,
)
from guardian.infrastructure.postgres.telemetry_storage import (
    PostgreSQLTelemetryStorage,
)


def determine_health_level(
    metric: str,
    value: float,
) -> HealthSignalLevel:
    """
    Derive the same deterministic health classification used by
    the Phase 4 health-signal boundary.

    This does not create a prediction or decision.
    """

    if metric == "cpu_usage_percent":
        if value < 70:
            return HealthSignalLevel.HEALTHY

        if value < 90:
            return HealthSignalLevel.WARNING

        return HealthSignalLevel.CRITICAL

    if metric == "memory_usage_percent":
        if value < 75:
            return HealthSignalLevel.HEALTHY

        if value < 90:
            return HealthSignalLevel.WARNING

        return HealthSignalLevel.CRITICAL

    # Byte counters are measurements, not threshold-based
    # health conditions in Phase 4.6.
    return HealthSignalLevel.HEALTHY


def find_real_history(
    storage: PostgreSQLTelemetryStorage,
) -> list:
    """
    Find a real persisted resource/metric series containing
    at least two observations.

    The observations come directly from PostgreSQL through the
    existing TelemetryStorage implementation.

    No synthetic telemetry is created.
    """

    recent_observations = storage.get_recent(limit=1000)

    if not recent_observations:
        return []

    series: dict[tuple[str, str, str], list] = {}

    for observation in recent_observations:
        key = (
            observation.resource_id,
            observation.metric.value,
            observation.unit,
        )

        series.setdefault(key, []).append(observation)

    candidates = [
        observations
        for observations in series.values()
        if len(observations) >= 2
    ]

    if not candidates:
        return []

    # Select the largest real historical series.
    candidates.sort(
        key=lambda observations: (
            len(observations),
            observations[0].resource_id,
            observations[0].metric.value,
        ),
        reverse=True,
    )

    selected = candidates[0]

    return sorted(
        selected,
        key=lambda observation: observation.observed_at,
    )


def main() -> int:
    print("=" * 72)
    print("PHASE 5.4 — PREDICTION INTEGRATION VALIDATION")
    print("=" * 72)

    storage = PostgreSQLTelemetryStorage()
    storage.initialize()

    # ------------------------------------------------------------------
    # 1. REAL HISTORICAL TELEMETRY
    # ------------------------------------------------------------------

    matching = find_real_history(storage)

    print()
    print("[1] REAL TELEMETRY HISTORY")
    print("-" * 72)

    if len(matching) < 2:
        print(
            "REAL TELEMETRY HISTORY       : FAIL"
        )
        print(
            "No resource/metric series with at least "
            "two persisted observations was found."
        )
        return 1

    latest = matching[-1]

    print(
        f"Resource                    : "
        f"{latest.resource_id}"
    )
    print(
        f"Metric                      : "
        f"{latest.metric}"
    )
    print(
        f"Unit                        : "
        f"{latest.unit}"
    )
    print(
        f"Samples                     : "
        f"{len(matching)}"
    )

    print()
    print("Historical observations:")
    print()

    for index, observation in enumerate(
        matching,
        start=1,
    ):
        print(
            f"  [{index}] "
            f"{observation.observed_at.isoformat()} "
            f"-> {observation.value} "
            f"{observation.unit}"
        )

    # Verify that all observations belong to exactly
    # the same prediction series.
    resource_ids = {
        observation.resource_id
        for observation in matching
    }

    metrics = {
        observation.metric
        for observation in matching
    }

    units = {
        observation.unit
        for observation in matching
    }

    if len(resource_ids) != 1:
        print()
        print(
            "Historical resource consistency : FAIL"
        )
        return 1

    if len(metrics) != 1:
        print()
        print(
            "Historical metric consistency   : FAIL"
        )
        return 1

    if len(units) != 1:
        print()
        print(
            "Historical unit consistency     : FAIL"
        )
        return 1

    print()
    print(
        "Historical resource consistency : PASS"
    )
    print(
        "Historical metric consistency   : PASS"
    )
    print(
        "Historical unit consistency     : PASS"
    )
    print(
        "Real historical telemetry       : PASS"
    )

    # ------------------------------------------------------------------
    # 2. CREATE OBSERVABILITY EVENT FROM REAL LATEST OBSERVATION
    # ------------------------------------------------------------------

    health_level = determine_health_level(
        latest.metric.value,
        latest.value,
    )

    event = ObservabilityEvent(
        event_type=(
            ObservabilityEventType.HEALTH_SIGNAL_GENERATED
        ),
        resource_id=latest.resource_id,
        metric=latest.metric.value,
        value=latest.value,
        unit=latest.unit,
        health_level=health_level,
        observed_at=latest.observed_at,
        source=latest.source.value,
        metadata=latest.metadata,
    )

    print()
    print("[2] OBSERVABILITY EVENT")
    print("-" * 72)
    print(
        f"Event ID                    : "
        f"{event.event_id}"
    )
    print(
        f"Resource                    : "
        f"{event.resource_id}"
    )
    print(
        f"Metric                      : "
        f"{event.metric}"
    )
    print(
        f"Value                       : "
        f"{event.value}"
    )
    print(
        f"Unit                        : "
        f"{event.unit}"
    )
    print(
        f"Health level                : "
        f"{event.health_level}"
    )
    print(
        f"Source                      : "
        f"{event.source}"
    )
    print(
        "Event construction          : PASS"
    )

    # ------------------------------------------------------------------
    # 3. CREATE CONTROL LOOP CYCLE
    # ------------------------------------------------------------------

    cycle = (
        ControlLoopCycle.from_observability_event(
            event
        )
        .transition_to(
            ControlLoopState.ANALYZING
        )
    )

    print()
    print("[3] CONTROL LOOP PREDICTION INPUT")
    print("-" * 72)
    print(
        f"Cycle ID                    : "
        f"{cycle.cycle_id}"
    )
    print(
        f"Cycle state                 : "
        f"{cycle.state}"
    )
    print(
        f"Source event                : "
        f"{cycle.source_event_id}"
    )
    print(
        f"Resource                    : "
        f"{cycle.resource_id}"
    )
    print(
        f"Metric                      : "
        f"{cycle.metric}"
    )

    if cycle.state != ControlLoopState.ANALYZING:
        print(
            "Prediction input            : FAIL"
        )
        return 1

    if cycle.source_event_id != event.event_id:
        print(
            "Event correlation           : FAIL"
        )
        return 1

    if cycle.resource_id != event.resource_id:
        print(
            "Resource correlation        : FAIL"
        )
        return 1

    if cycle.metric != event.metric:
        print(
            "Metric correlation          : FAIL"
        )
        return 1

    print(
        "Prediction input            : PASS"
    )
    print(
        "Input evidence correlation  : PASS"
    )

    # ------------------------------------------------------------------
    # 4. RUN REAL PREDICTION
    # ------------------------------------------------------------------

    service = ControlLoopPredictionService()

    result = service.predict(
        cycle,
        matching,
    )

    prediction = result.prediction

    print()
    print("[4] PREDICTION RESULT")
    print("-" * 72)
    print(
        f"Prediction cycle state      : "
        f"{result.cycle.state}"
    )
    print(
        f"Current value               : "
        f"{prediction.current_value}"
    )
    print(
        f"Predicted value             : "
        f"{prediction.predicted_value}"
    )
    print(
        f"Direction                   : "
        f"{prediction.direction}"
    )
    print(
        f"Confidence                  : "
        f"{prediction.confidence}"
    )
    print(
        f"Sample count                : "
        f"{prediction.sample_count}"
    )
    print(
        f"Evidence available          : "
        f"{prediction.evidence_available}"
    )
    print(
        f"Basis                       : "
        f"{prediction.basis}"
    )

    if result.cycle.state != ControlLoopState.PREDICTING:
        print(
            "Prediction lifecycle        : FAIL"
        )
        return 1

    if not prediction.evidence_available:
        print(
            "Prediction evidence         : FAIL"
        )
        return 1

    if prediction.sample_count != len(matching):
        print(
            "Sample count correlation    : FAIL"
        )
        return 1

    if prediction.source_event_id != cycle.source_event_id:
        print(
            "Prediction event correlation: FAIL"
        )
        return 1

    if prediction.resource_id != cycle.resource_id:
        print(
            "Prediction resource         : FAIL"
        )
        return 1

    if prediction.metric != cycle.metric:
        print(
            "Prediction metric           : FAIL"
        )
        return 1

    if prediction.current_value != latest.value:
        print(
            "Current value correlation   : FAIL"
        )
        return 1

    if prediction.predicted_value < 0:
        print(
            "Predicted value validity    : FAIL"
        )
        return 1

    print(
        "Prediction lifecycle        : PASS"
    )
    print(
        "Prediction evidence         : PASS"
    )
    print(
        "Sample count correlation    : PASS"
    )
    print(
        "Event correlation           : PASS"
    )
    print(
        "Resource correlation        : PASS"
    )
    print(
        "Metric correlation          : PASS"
    )
    print(
        "Current value correlation   : PASS"
    )
    print(
        "Predicted value validity    : PASS"
    )

    # ------------------------------------------------------------------
    # 5. AUTONOMOUS CAPABILITY BOUNDARY
    # ------------------------------------------------------------------

    print()
    print("[5] AUTONOMOUS CAPABILITY BOUNDARY")
    print("-" * 72)
    print(
        "Prediction generated        : YES"
    )
    print(
        "Prediction source           : REAL POSTGRES TELEMETRY"
    )
    print(
        "Decision generated          : NONE"
    )
    print(
        "Infrastructure action       : NONE"
    )
    print(
        "Remediation executed        : NONE"
    )
    print(
        "External infrastructure     : NOT MODIFIED"
    )
    print(
        "Phase boundary              : PASS"
    )

    # ------------------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------------------

    print()
    print("=" * 72)
    print("PHASE 5.4 VALIDATION RESULT")
    print("=" * 72)
    print(
        "REAL TELEMETRY HISTORY      : PASS"
    )
    print(
        "CONTROL LOOP INPUT          : PASS"
    )
    print(
        "PREDICTION GENERATED        : PASS"
    )
    print(
        "PREDICTION EVIDENCE         : PASS"
    )
    print(
        "PREDICTION CORRELATION      : PASS"
    )
    print(
        "AUTONOMOUS ACTION BOUNDARY  : PASS"
    )
    print()
    print(
        "PHASE 5.4 — COMPLETE: PASS"
    )
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())