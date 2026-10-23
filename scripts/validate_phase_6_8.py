from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import psycopg
from psycopg.rows import dict_row

from guardian.application.cost_aggregation import CostAggregationService
from guardian.application.cost_forecasting import CostForecastingService
from guardian.application.cost_optimization import (
    CostOptimizationSignalService,
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


def build_controlled_observations(
    resource_id: str,
    base_time: datetime,
) -> list[CostObservation]:
    amounts = [10.0, 20.0, 30.0, 40.0, 50.0]

    return [
        CostObservation(
            resource_id=resource_id,
            amount=amount,
            currency="USD",
            category=CostCategory.COMPUTE,
            source=CostSource.AWS,
            observed_at=base_time + timedelta(hours=index),
            evidence_available=True,
            metadata={
                "validation": "phase_6_8",
                "fixture": "controlled_integration_test",
            },
        )
        for index, amount in enumerate(amounts)
    ]


def main() -> None:
    print("PHASE 6.8 — COST INTELLIGENCE INTEGRATION VALIDATION")
    print("=" * 64)

    storage = PostgreSQLCostStorage()
    aggregation_service = CostAggregationService()
    optimization_service = CostOptimizationSignalService()
    forecasting_service = CostForecastingService()
    recommendation_service = CostRecommendationService()

    test_resource_id = f"phase-6-8-test-{uuid.uuid4()}"
    base_time = datetime.now(UTC)

    observations = build_controlled_observations(
        resource_id=test_resource_id,
        base_time=base_time,
    )

    try:
        # =========================================================
        # 1. PostgreSQL connectivity
        # =========================================================
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

        # =========================================================
        # 2. Cost storage initialization
        # =========================================================
        storage.initialize()

        print("COST STORAGE INITIALIZATION PASS")

        # =========================================================
        # 3. Persist controlled historical evidence
        # =========================================================
        storage.save_many(observations)

        print(
            "CONTROLLED COST EVIDENCE WRITE COMPLETED "
            f"({len(observations)} observations submitted)"
        )

        # =========================================================
        # 4. Retrieve evidence from PostgreSQL
        # =========================================================
        stored_observations = storage.get_for_resource(
            resource_id=test_resource_id,
            limit=100,
        )

        if len(stored_observations) != len(observations):
            raise RuntimeError(
                "Not all controlled cost observations were "
                "persisted and retrievable."
            )

        if not all(
            observation.evidence_available
            for observation in stored_observations
        ):
            raise RuntimeError(
                "One or more observations lost evidence metadata."
            )

        if any(
            observation.resource_id != test_resource_id
            for observation in stored_observations
        ):
            raise RuntimeError(
                "Resource identity correlation failed."
            )

        print("REAL POSTGRESQL COST EVIDENCE RETRIEVAL PASS")
        print("COST EVIDENCE INTEGRITY PASS")
        print(
            f"COST EVIDENCE PERSISTENCE PASS "
            f"({len(stored_observations)} observations)"
        )

        # =========================================================
        # 5. Aggregate cost evidence
        # =========================================================
        aggregates = aggregation_service.aggregate(
            stored_observations
        )

        if len(aggregates) != 1:
            raise RuntimeError(
                "Expected exactly one aggregate."
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

        if aggregate.count != 5:
            raise RuntimeError(
                "Aggregate observation count mismatch."
            )

        if aggregate.total_amount != 150.0:
            raise RuntimeError(
                "Aggregate total amount mismatch."
            )

        if aggregate.average_amount != 30.0:
            raise RuntimeError(
                "Aggregate average amount mismatch."
            )

        if aggregate.latest_amount != 50.0:
            raise RuntimeError(
                "Aggregate latest amount mismatch."
            )

        if not aggregate.evidence_available:
            raise RuntimeError(
                "Aggregate lost evidence availability."
            )

        print("COST AGGREGATION PASS")
        print("COST AGGREGATE INTEGRITY PASS")

        # =========================================================
        # 6. Generate optimization signal
        # =========================================================
        signal = optimization_service.generate(aggregate)

        if signal.resource_id != test_resource_id:
            raise RuntimeError(
                "Optimization signal resource mismatch."
            )

        if signal.category != CostCategory.COMPUTE:
            raise RuntimeError(
                "Optimization signal category mismatch."
            )

        if signal.currency != "USD":
            raise RuntimeError(
                "Optimization signal currency mismatch."
            )

        if signal.current_amount != 50.0:
            raise RuntimeError(
                "Optimization signal current amount mismatch."
            )

        if signal.baseline_amount != 30.0:
            raise RuntimeError(
                "Optimization signal baseline mismatch."
            )

        if signal.observation_count != 5:
            raise RuntimeError(
                "Optimization signal observation count mismatch."
            )

        if not signal.evidence_available:
            raise RuntimeError(
                "Optimization signal lost evidence."
            )

        print("COST OPTIMIZATION SIGNAL PASS")
        print("SIGNAL EVIDENCE CORRELATION PASS")

        # =========================================================
        # 7. Generate forecast from historical evidence
        # =========================================================
        forecast = forecasting_service.forecast(
            stored_observations
        )

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

        if forecast.sample_count != 5:
            raise RuntimeError(
                "Forecast sample count mismatch."
            )

        if not forecast.evidence_available:
            raise RuntimeError(
                "Forecast lost evidence."
            )

        if forecast.forecast_for <= forecast.latest_observed_at:
            raise RuntimeError(
                "Forecast time must be after latest observation."
            )

        print("COST FORECAST PASS")
        print("FORECAST EVIDENCE CORRELATION PASS")
        print("FORECAST TIME WINDOW PASS")

        # =========================================================
        # 8. Generate final recommendation
        # =========================================================
        recommendation = recommendation_service.recommend(
            signal,
            forecast,
        )

        if recommendation.resource_id != test_resource_id:
            raise RuntimeError(
                "Recommendation resource identity mismatch."
            )

        if recommendation.category != CostCategory.COMPUTE:
            raise RuntimeError(
                "Recommendation category mismatch."
            )

        if recommendation.currency != "USD":
            raise RuntimeError(
                "Recommendation currency mismatch."
            )

        if recommendation.current_amount != 50.0:
            raise RuntimeError(
                "Recommendation current amount mismatch."
            )

        if recommendation.forecast_amount != 60.0:
            raise RuntimeError(
                "Recommendation forecast amount mismatch."
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

        if not recommendation.evidence_available:
            raise RuntimeError(
                "Recommendation lost evidence."
            )

        if recommendation.observation_count != 5:
            raise RuntimeError(
                "Recommendation observation count mismatch."
            )

        if not recommendation.rationale.strip():
            raise RuntimeError(
                "Recommendation rationale is empty."
            )

        print("COST RECOMMENDATION PASS")
        print("RECOMMENDATION EVIDENCE CORRELATION PASS")
        print("RECOMMENDATION RATIONALE PASS")

        # =========================================================
        # 9. Verify no fabricated savings claim
        # =========================================================
        rationale = recommendation.rationale.lower()

        forbidden_savings_terms = (
            "savings",
            "saved",
            "save $",
            "save ₹",
            "usd saved",
            "inr saved",
        )

        if any(
            term in rationale
            for term in forbidden_savings_terms
        ):
            raise RuntimeError(
                "Recommendation contains an unsupported "
                "savings claim."
            )

        print("NO FABRICATED SAVINGS CLAIM PASS")

        # =========================================================
        # 10. Verify no infrastructure action
        # =========================================================
        infrastructure_action_terms = (
            "restart",
            "resize",
            "delete",
            "terminate",
            "execute",
            "modify",
            "scale",
            "provision",
            "destroy",
        )

        if any(
            term in rationale
            for term in infrastructure_action_terms
        ):
            raise RuntimeError(
                "Recommendation rationale contains an "
                "infrastructure execution instruction."
            )

        print("AUTONOMOUS ACTION BOUNDARY PASS")

        # =========================================================
        # 11. Verify evidence is preserved end-to-end
        # =========================================================
        if not (
            signal.evidence_available
            and forecast.evidence_available
            and recommendation.evidence_available
        ):
            raise RuntimeError(
                "Evidence availability was not preserved "
                "through the complete pipeline."
            )

        print("END-TO-END EVIDENCE CHAIN PASS")

        # =========================================================
        # 12. Final Phase 6 boundary
        # =========================================================
        print()
        print("PHASE 6 BOUNDARY CHECK")
        print("----------------------")
        print("Cost evidence:          AVAILABLE")
        print("Cost aggregation:       EXECUTED")
        print("Optimization signal:    GENERATED")
        print("Cost forecast:          GENERATED")
        print("Recommendation:         GENERATED")
        print("Infrastructure action:  NONE")
        print("Savings estimate:       NONE")
        print("Automatic remediation:  NONE")

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
        print("PHASE 6.8 — COMPLETE: PASS")
        print("PHASE 6 — COST INTELLIGENCE: COMPLETE")

    finally:
        # =========================================================
        # Cleanup only Phase 6.8 controlled records
        # =========================================================
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