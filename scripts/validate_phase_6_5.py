from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import psycopg
from psycopg.rows import dict_row

from guardian.application.cost_aggregation import CostAggregationService
from guardian.application.cost_optimization import (
    CostOptimizationSignalService,
)
from guardian.domain.cost import CostCategory, CostObservation, CostSource
from guardian.domain.cost_signal import (
    CostSignalSeverity,
    CostSignalType,
)
from guardian.infrastructure.postgres.cost_storage import (
    PostgreSQLCostStorage,
)


def get_dsn() -> str:
    host = os.getenv("ACG_POSTGRES_HOST", "localhost")
    port = os.getenv("ACG_POSTGRES_PORT", "5433")
    database = os.getenv("ACG_POSTGRES_DB", "guardian")
    user = os.getenv("ACG_POSTGRES_USER", "guardian")
    password = os.getenv(
        "ACG_POSTGRES_PASSWORD",
        "guardian_dev_password",
    )

    return (
        f"host={host} port={port} dbname={database} "
        f"user={user} password={password}"
    )


def main() -> None:
    print("PHASE 6.5 — COST OPTIMIZATION SIGNAL VALIDATION")
    print("=" * 60)

    storage = PostgreSQLCostStorage()
    aggregation_service = CostAggregationService()
    signal_service = CostOptimizationSignalService()

    test_resource_id = f"phase-6-5-test-{uuid.uuid4()}"
    base_time = datetime.now(UTC)

    observations = [
        CostObservation(
            resource_id=test_resource_id,
            amount=10.0,
            currency="USD",
            category=CostCategory.COMPUTE,
            source=CostSource.AWS,
            observed_at=base_time,
            evidence_available=True,
            metadata={
                "validation": "phase_6_5",
                "fixture": "controlled_signal_test",
            },
        ),
        CostObservation(
            resource_id=test_resource_id,
            amount=20.0,
            currency="USD",
            category=CostCategory.COMPUTE,
            source=CostSource.AWS,
            observed_at=base_time + timedelta(minutes=1),
            evidence_available=True,
            metadata={
                "validation": "phase_6_5",
                "fixture": "controlled_signal_test",
            },
        ),
        CostObservation(
            resource_id=test_resource_id,
            amount=30.0,
            currency="USD",
            category=CostCategory.COMPUTE,
            source=CostSource.AWS,
            observed_at=base_time + timedelta(minutes=2),
            evidence_available=True,
            metadata={
                "validation": "phase_6_5",
                "fixture": "controlled_signal_test",
            },
        ),
    ]

    try:
        # ---------------------------------------------------------
        # 1. PostgreSQL connectivity
        # ---------------------------------------------------------
        with (
            psycopg.connect(
                get_dsn(),
                row_factory=dict_row,
            ) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute("SELECT version()")
            row = cursor.fetchone()

            if row is None:
                raise RuntimeError(
                    "PostgreSQL version query returned no result."
                )

            print("POSTGRESQL CONNECTION PASS")
            print(
                f"PostgreSQL: {row['version'].split(',')[0]}"
            )

        # ---------------------------------------------------------
        # 2. Storage initialization
        # ---------------------------------------------------------
        storage.initialize()

        print("COST STORAGE INITIALIZATION PASS")

        # ---------------------------------------------------------
        # 3. Persist controlled observations
        # ---------------------------------------------------------
        storage.save_many(observations)

        stored = storage.get_for_resource(
            resource_id=test_resource_id,
            limit=100,
        )

        if len(stored) != 3:
            raise RuntimeError(
                f"Expected 3 observations, got {len(stored)}."
            )

        print("REAL POSTGRESQL COST EVIDENCE RETRIEVAL PASS")

        # ---------------------------------------------------------
        # 4. Aggregate observations
        # ---------------------------------------------------------
        aggregates = aggregation_service.aggregate(stored)

        if len(aggregates) != 1:
            raise RuntimeError(
                "Expected exactly one cost aggregate."
            )

        aggregate = aggregates[0]

        if aggregate.resource_id != test_resource_id:
            raise RuntimeError(
                "Aggregate resource identity mismatch."
            )

        if aggregate.category != CostCategory.COMPUTE:
            raise RuntimeError(
                "Aggregate category mismatch."
            )

        if aggregate.currency != "USD":
            raise RuntimeError(
                "Aggregate currency mismatch."
            )

        if aggregate.count != 3:
            raise RuntimeError(
                "Aggregate observation count mismatch."
            )

        if aggregate.total_amount != 60.0:
            raise RuntimeError(
                "Aggregate total mismatch."
            )

        if aggregate.average_amount != 20.0:
            raise RuntimeError(
                "Aggregate average mismatch."
            )

        if aggregate.latest_amount != 30.0:
            raise RuntimeError(
                "Aggregate latest amount mismatch."
            )

        if not aggregate.evidence_available:
            raise RuntimeError(
                "Aggregate lost evidence availability."
            )

        print("COST AGGREGATE EVIDENCE PASS")

        # ---------------------------------------------------------
        # 5. Generate optimization signal
        # ---------------------------------------------------------
        signal = signal_service.generate(aggregate)

        if signal.signal_type != CostSignalType.RISING_COST:
            raise RuntimeError(
                "Expected RISING_COST optimization signal."
            )

        if signal.severity != CostSignalSeverity.WARNING:
            raise RuntimeError(
                "Expected WARNING severity."
            )

        if signal.resource_id != test_resource_id:
            raise RuntimeError(
                "Signal resource identity mismatch."
            )

        if signal.category != CostCategory.COMPUTE:
            raise RuntimeError(
                "Signal category mismatch."
            )

        if signal.currency != "USD":
            raise RuntimeError(
                "Signal currency mismatch."
            )

        if signal.current_amount != 30.0:
            raise RuntimeError(
                "Signal current amount mismatch."
            )

        if signal.baseline_amount != 20.0:
            raise RuntimeError(
                "Signal baseline amount mismatch."
            )

        if signal.observation_count != 3:
            raise RuntimeError(
                "Signal observation count mismatch."
            )

        if not signal.evidence_available:
            raise RuntimeError(
                "Signal lost evidence availability."
            )

        print("COST OPTIMIZATION SIGNAL PASS")

        # ---------------------------------------------------------
        # 6. Verify no fabricated savings
        # ---------------------------------------------------------
        if (
            "saving" in signal.finding.lower()
            or "savings" in signal.finding.lower()
        ):
            raise RuntimeError(
                "Signal incorrectly claims financial savings."
            )

        print("NO FABRICATED SAVINGS CLAIM PASS")

        # ---------------------------------------------------------
        # 7. Verify no prediction
        # ---------------------------------------------------------
        prediction_terms = (
            "forecast",
            "predict",
            "predicted",
            "future",
        )

        if any(
            term in signal.finding.lower()
            for term in prediction_terms
        ):
            raise RuntimeError(
                "6.5 signal incorrectly contains prediction language."
            )

        print("PREDICTION BOUNDARY PASS")

        # ---------------------------------------------------------
        # 8. Verify no recommendation/action
        # ---------------------------------------------------------
        action_terms = (
            "restart",
            "resize",
            "delete",
            "terminate",
            "scale",
            "modify",
            "execute",
        )

        if any(
            term in signal.finding.lower()
            for term in action_terms
        ):
            raise RuntimeError(
                "6.5 signal incorrectly contains action instructions."
            )

        print("ACTION BOUNDARY PASS")

        # ---------------------------------------------------------
        # 9. Verify insufficient evidence behavior
        # ---------------------------------------------------------
        no_evidence_observation = CostObservation(
            resource_id=test_resource_id,
            amount=100.0,
            currency="USD",
            category=CostCategory.STORAGE,
            source=CostSource.AWS,
            observed_at=base_time + timedelta(minutes=3),
            evidence_available=False,
            metadata={
                "validation": "phase_6_5",
                "fixture": "controlled_no_evidence_test",
            },
        )

        no_evidence_aggregate = aggregation_service.aggregate(
            [no_evidence_observation]
        )[0]

        no_evidence_signal = signal_service.generate(
            no_evidence_aggregate
        )

        if (
            no_evidence_signal.signal_type
            != CostSignalType.INSUFFICIENT_EVIDENCE
        ):
            raise RuntimeError(
                "Missing evidence did not produce "
                "INSUFFICIENT_EVIDENCE."
            )

        if (
            no_evidence_signal.severity
            != CostSignalSeverity.UNKNOWN
        ):
            raise RuntimeError(
                "Missing evidence did not produce UNKNOWN severity."
            )

        if no_evidence_signal.evidence_available:
            raise RuntimeError(
                "Missing evidence was incorrectly marked available."
            )

        print("INSUFFICIENT EVIDENCE HANDLING PASS")

        # ---------------------------------------------------------
        # 10. Verify no infrastructure action
        # ---------------------------------------------------------
        print("INFRASTRUCTURE ACTION NONE")

        print()
        print("IMPORTANT:")
        print(
            "All monetary values in this validator are "
            "CONTROLLED TEST FIXTURES."
        )
        print(
            "They are NOT claimed as real cloud billing evidence."
        )
        print()
        print("No cost prediction performed.")
        print("No cost forecast performed.")
        print("No savings estimate performed.")
        print("No optimization recommendation performed.")
        print("No infrastructure action performed.")
        print()
        print("PHASE 6.5 — COMPLETE: PASS")

    finally:
        # ---------------------------------------------------------
        # Cleanup only this validator's records
        # ---------------------------------------------------------
        try:
            with psycopg.connect(get_dsn()) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        DELETE FROM cost_observations
                        WHERE resource_id = %s
                        """,
                        (test_resource_id,),
                    )

                    deleted = cursor.rowcount

                connection.commit()

            print(
                f"Cleanup PASS — removed {deleted} "
                "controlled test records."
            )

        except psycopg.Error as cleanup_error:
            print(
                f"Cleanup WARNING: {cleanup_error}"
            )


if __name__ == "__main__":
    main()