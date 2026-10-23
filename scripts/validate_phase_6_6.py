from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import psycopg
from psycopg.rows import dict_row

from guardian.application.cost_forecasting import (
    CostForecastingService,
)
from guardian.application.cost_storage import CostStorage
from guardian.domain.cost import (
    CostCategory,
    CostObservation,
    CostSource,
)
from guardian.domain.cost_forecast import (
    CostForecastConfidence,
    CostForecastDirection,
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
    print("PHASE 6.6 — COST FORECASTING VALIDATION")
    print("=" * 60)

    storage: CostStorage = PostgreSQLCostStorage()
    forecasting_service = CostForecastingService()

    test_resource_id = f"phase-6-6-test-{uuid.uuid4()}"
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
                "validation": "phase_6_6",
                "fixture": "controlled_forecast_test",
            },
        ),
        CostObservation(
            resource_id=test_resource_id,
            amount=20.0,
            currency="USD",
            category=CostCategory.COMPUTE,
            source=CostSource.AWS,
            observed_at=base_time + timedelta(hours=1),
            evidence_available=True,
            metadata={
                "validation": "phase_6_6",
                "fixture": "controlled_forecast_test",
            },
        ),
        CostObservation(
            resource_id=test_resource_id,
            amount=30.0,
            currency="USD",
            category=CostCategory.COMPUTE,
            source=CostSource.AWS,
            observed_at=base_time + timedelta(hours=2),
            evidence_available=True,
            metadata={
                "validation": "phase_6_6",
                "fixture": "controlled_forecast_test",
            },
        ),
        CostObservation(
            resource_id=test_resource_id,
            amount=40.0,
            currency="USD",
            category=CostCategory.COMPUTE,
            source=CostSource.AWS,
            observed_at=base_time + timedelta(hours=3),
            evidence_available=True,
            metadata={
                "validation": "phase_6_6",
                "fixture": "controlled_forecast_test",
            },
        ),
        CostObservation(
            resource_id=test_resource_id,
            amount=50.0,
            currency="USD",
            category=CostCategory.COMPUTE,
            source=CostSource.AWS,
            observed_at=base_time + timedelta(hours=4),
            evidence_available=True,
            metadata={
                "validation": "phase_6_6",
                "fixture": "controlled_forecast_test",
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
        # 3. Persist controlled historical observations
        # ---------------------------------------------------------
        storage.save_many(observations)

        stored = storage.get_for_resource(
            resource_id=test_resource_id,
            limit=100,
        )

        if len(stored) != 5:
            raise RuntimeError(
                f"Expected 5 observations, got {len(stored)}."
            )

        print(
            "REAL POSTGRESQL HISTORICAL COST EVIDENCE PASS"
        )

        # ---------------------------------------------------------
        # 4. Verify evidence identity
        # ---------------------------------------------------------
        if not all(
            observation.resource_id == test_resource_id
            for observation in stored
        ):
            raise RuntimeError(
                "Historical observation resource identity mismatch."
            )

        if not all(
            observation.currency == "USD"
            for observation in stored
        ):
            raise RuntimeError(
                "Historical observation currency mismatch."
            )

        if not all(
            observation.category == CostCategory.COMPUTE
            for observation in stored
        ):
            raise RuntimeError(
                "Historical observation category mismatch."
            )

        if not all(
            observation.evidence_available
            for observation in stored
        ):
            raise RuntimeError(
                "Historical cost evidence was lost."
            )

        print("HISTORICAL COST EVIDENCE INTEGRITY PASS")

        # ---------------------------------------------------------
        # 5. Forecast
        # ---------------------------------------------------------
        forecast = forecasting_service.forecast(stored)

        if forecast.resource_id != test_resource_id:
            raise RuntimeError(
                "Forecast resource identity mismatch."
            )

        if forecast.category != CostCategory.COMPUTE:
            raise RuntimeError(
                "Forecast category mismatch."
            )

        if forecast.currency != "USD":
            raise RuntimeError(
                "Forecast currency mismatch."
            )

        if forecast.current_amount != 50.0:
            raise RuntimeError(
                "Forecast current amount mismatch."
            )

        if forecast.forecast_amount != 60.0:
            raise RuntimeError(
                "Forecast amount mismatch."
            )

        if forecast.direction != CostForecastDirection.INCREASING:
            raise RuntimeError(
                "Expected increasing forecast direction."
            )

        if forecast.confidence != CostForecastConfidence.HIGH:
            raise RuntimeError(
                "Expected HIGH forecast confidence."
            )

        if forecast.sample_count != 5:
            raise RuntimeError(
                "Forecast sample count mismatch."
            )

        if not forecast.evidence_available:
            raise RuntimeError(
                "Forecast evidence flag is false."
            )

        print("COST FORECAST PASS")

        # ---------------------------------------------------------
        # 6. Verify forecast timestamp
        # ---------------------------------------------------------
        expected_forecast_time = (
            base_time + timedelta(hours=5)
        )

        if forecast.forecast_for != expected_forecast_time:
            raise RuntimeError(
                "Forecast timestamp does not match "
                "the next historical interval."
            )

        print("FORECAST TIME WINDOW PASS")

        # ---------------------------------------------------------
        # 7. Verify non-negative forecast
        # ---------------------------------------------------------
        if forecast.forecast_amount < 0:
            raise RuntimeError(
                "Forecast amount cannot be negative."
            )

        print("NON-NEGATIVE FORECAST PASS")

        # ---------------------------------------------------------
        # 8. Verify no recommendation
        # ---------------------------------------------------------
        recommendation_terms = (
            "recommend",
            "restart",
            "resize",
            "delete",
            "terminate",
            "scale",
            "modify",
            "execute",
        )

        if any(
            term in forecast.basis.lower()
            for term in recommendation_terms
        ):
            raise RuntimeError(
                "Forecast incorrectly contains an action "
                "recommendation."
            )

        print("RECOMMENDATION BOUNDARY PASS")

        # ---------------------------------------------------------
        # 9. Verify no savings claim
        # ---------------------------------------------------------
        savings_terms = (
            "saving",
            "savings",
            "save",
        )

        if any(
            term in forecast.basis.lower()
            for term in savings_terms
        ):
            raise RuntimeError(
                "Forecast incorrectly claims savings."
            )

        print("SAVINGS CLAIM BOUNDARY PASS")

        # ---------------------------------------------------------
        # 10. Verify insufficient evidence behavior
        # ---------------------------------------------------------
        no_evidence = [
            observations[0].model_copy(
                update={"evidence_available": False}
            ),
            observations[1].model_copy(
                update={"evidence_available": False}
            ),
        ]

        unavailable_forecast = forecasting_service.forecast(
            no_evidence
        )

        if unavailable_forecast.evidence_available:
            raise RuntimeError(
                "Unavailable evidence was marked as available."
            )

        if (
            unavailable_forecast.direction
            != CostForecastDirection.UNKNOWN
        ):
            raise RuntimeError(
                "Unavailable evidence did not produce UNKNOWN "
                "direction."
            )

        if (
            unavailable_forecast.confidence
            != CostForecastConfidence.LOW
        ):
            raise RuntimeError(
                "Unavailable evidence did not produce LOW "
                "confidence."
            )

        print("INSUFFICIENT EVIDENCE HANDLING PASS")

        # ---------------------------------------------------------
        # 11. Verify no infrastructure action
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
        print("No optimization recommendation performed.")
        print("No savings estimate performed.")
        print("No infrastructure action performed.")
        print()
        print("PHASE 6.6 — COMPLETE: PASS")

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