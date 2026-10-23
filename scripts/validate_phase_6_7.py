from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import psycopg
from psycopg.rows import dict_row

from guardian.application.cost_aggregation import (
    CostAggregationService,
)
from guardian.application.cost_forecasting import (
    CostForecastingService,
)
from guardian.application.cost_recommendation import (
    CostRecommendationService,
)
from guardian.domain.cost import (
    CostCategory,
    CostObservation,
    CostSource,
)
from guardian.domain.cost_recommendation import (
    CostRecommendationOutcome,
    CostRecommendationPriority,
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
    print("PHASE 6.7 — COST RECOMMENDATION VALIDATION")
    print("=" * 60)

    storage = PostgreSQLCostStorage()
    aggregation_service = CostAggregationService()
    forecasting_service = CostForecastingService()
    recommendation_service = CostRecommendationService()

    test_resource_id = f"phase-6-7-test-{uuid.uuid4()}"
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
                "validation": "phase_6_7",
                "fixture": "controlled_recommendation_test",
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
                "validation": "phase_6_7",
                "fixture": "controlled_recommendation_test",
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
                "validation": "phase_6_7",
                "fixture": "controlled_recommendation_test",
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
                "validation": "phase_6_7",
                "fixture": "controlled_recommendation_test",
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
                "validation": "phase_6_7",
                "fixture": "controlled_recommendation_test",
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
        # 2. Storage
        # ---------------------------------------------------------
        storage.initialize()
        storage.save_many(observations)

        stored = storage.get_for_resource(
            resource_id=test_resource_id,
            limit=100,
        )

        if len(stored) != 5:
            raise RuntimeError(
                f"Expected 5 observations, got {len(stored)}."
            )

        print("REAL POSTGRESQL COST EVIDENCE PASS")

        # ---------------------------------------------------------
        # 3. Aggregate
        # ---------------------------------------------------------
        aggregates = aggregation_service.aggregate(stored)

        if len(aggregates) != 1:
            raise RuntimeError(
                "Expected exactly one cost aggregate."
            )

        aggregate = aggregates[0]

        if aggregate.latest_amount != 50.0:
            raise RuntimeError(
                "Unexpected latest cost amount."
            )

        if aggregate.average_amount != 30.0:
            raise RuntimeError(
                "Unexpected average cost amount."
            )

        print("COST AGGREGATION PASS")

        # ---------------------------------------------------------
        # 4. Optimization signal
        # ---------------------------------------------------------
        from guardian.application.cost_optimization import (
            CostOptimizationSignalService,
        )

        signal_service = CostOptimizationSignalService()
        signal = signal_service.generate(aggregate)

        if signal.evidence_available is not True:
            raise RuntimeError(
                "Optimization signal lost evidence."
            )

        print("COST OPTIMIZATION SIGNAL PASS")

        # ---------------------------------------------------------
        # 5. Forecast
        # ---------------------------------------------------------
        forecast = forecasting_service.forecast(stored)

        if forecast.current_amount != 50.0:
            raise RuntimeError(
                "Forecast current amount mismatch."
            )

        if forecast.forecast_amount != 60.0:
            raise RuntimeError(
                "Forecast amount mismatch."
            )

        if not forecast.evidence_available:
            raise RuntimeError(
                "Forecast lost evidence."
            )

        print("COST FORECAST PASS")

        # ---------------------------------------------------------
        # 6. Recommendation
        # ---------------------------------------------------------
        recommendation = recommendation_service.recommend(
            signal,
            forecast,
        )

        if (
            recommendation.outcome
            != CostRecommendationOutcome.OPTIMIZATION_RECOMMENDED
        ):
            raise RuntimeError(
                "Expected optimization recommendation."
            )

        if (
            recommendation.priority
            != CostRecommendationPriority.HIGH
        ):
            raise RuntimeError(
                "Expected HIGH recommendation priority."
            )

        if recommendation.resource_id != test_resource_id:
            raise RuntimeError(
                "Recommendation resource identity mismatch."
            )

        if recommendation.current_amount != 50.0:
            raise RuntimeError(
                "Recommendation current amount mismatch."
            )

        if recommendation.forecast_amount != 60.0:
            raise RuntimeError(
                "Recommendation forecast amount mismatch."
            )

        if not recommendation.evidence_available:
            raise RuntimeError(
                "Recommendation lost evidence."
            )

        print("COST RECOMMENDATION PASS")

        # ---------------------------------------------------------
        # 7. Explainability
        # ---------------------------------------------------------
        if not recommendation.rationale.strip():
            raise RuntimeError(
                "Recommendation rationale is empty."
            )

        print("RECOMMENDATION RATIONALE PASS")

        # ---------------------------------------------------------
        # 8. No fabricated savings
        # ---------------------------------------------------------
        savings_terms = (
            "saving",
            "savings",
            "$",
            "₹",
            "inr",
            "usd saved",
        )

        if any(
            term in recommendation.rationale.lower()
            for term in savings_terms
        ):
            raise RuntimeError(
                "Recommendation incorrectly claims "
                "financial savings."
            )

        print("NO FABRICATED SAVINGS CLAIM PASS")

        # ---------------------------------------------------------
        # 9. No infrastructure action
        # ---------------------------------------------------------
        action_terms = (
            "restart",
            "resize",
            "delete",
            "terminate",
            "execute",
            "modify",
            "scale",
        )

        if any(
            term in recommendation.rationale.lower()
            for term in action_terms
        ):
            raise RuntimeError(
                "Recommendation incorrectly contains "
                "an infrastructure action."
            )

        print("NO INFRASTRUCTURE ACTION PASS")

        # ---------------------------------------------------------
        # 10. Evidence boundary
        # ---------------------------------------------------------
        if recommendation.observation_count != 5:
            raise RuntimeError(
                "Recommendation evidence count mismatch."
            )

        print("EVIDENCE CORRELATION PASS")

        # ---------------------------------------------------------
        # 11. Final boundary
        # ---------------------------------------------------------
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
        print("No infrastructure action performed.")
        print("No savings estimate performed.")
        print("No automatic remediation performed.")
        print()
        print("PHASE 6.7 — COMPLETE: PASS")

    finally:
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