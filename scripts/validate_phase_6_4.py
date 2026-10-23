from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import psycopg
from psycopg.rows import dict_row

from guardian.application.cost_aggregation import CostAggregationService
from guardian.domain.cost import CostCategory, CostObservation, CostSource
from guardian.infrastructure.postgres.cost_storage import PostgreSQLCostStorage


def get_dsn() -> str:
    host = os.getenv("ACG_POSTGRES_HOST", "localhost")
    port = os.getenv("ACG_POSTGRES_PORT", "5433")
    database = os.getenv("ACG_POSTGRES_DB", "guardian")
    user = os.getenv("ACG_POSTGRES_USER", "guardian")
    password = os.getenv("ACG_POSTGRES_PASSWORD", "guardian_dev_password")

    return (
        f"host={host} port={port} dbname={database} "
        f"user={user} password={password}"
    )


def main() -> None:
    print("PHASE 6.4 — COST AGGREGATION & ANALYSIS VALIDATION")
    print("=" * 60)

    storage = PostgreSQLCostStorage()
    aggregation = CostAggregationService()

    test_resource_id = f"phase-6-4-test-{uuid.uuid4()}"
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
                "validation": "phase_6_4",
                "fixture": "controlled_aggregation_test",
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
                "validation": "phase_6_4",
                "fixture": "controlled_aggregation_test",
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
                "validation": "phase_6_4",
                "fixture": "controlled_aggregation_test",
            },
        ),
        CostObservation(
            resource_id=test_resource_id,
            amount=5.0,
            currency="USD",
            category=CostCategory.STORAGE,
            source=CostSource.AWS,
            observed_at=base_time + timedelta(minutes=1),
            evidence_available=True,
            metadata={
                "validation": "phase_6_4",
                "fixture": "controlled_aggregation_test",
            },
        ),
    ]

    try:
        # ---------------------------------------------------------
        # 1. PostgreSQL connectivity
        # ---------------------------------------------------------
        with (
            psycopg.connect(get_dsn(), row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute("SELECT version()")
            row = cursor.fetchone()

            if row is None:
                raise RuntimeError(
                    "PostgreSQL version query returned no result."
                )

            print("POSTGRESQL CONNECTION PASS")
            print(f"PostgreSQL: {row['version'].split(',')[0]}")

        # ---------------------------------------------------------
        # 2. Ensure storage exists
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

        if len(stored) != len(observations):
            raise RuntimeError(
                "Stored observation count does not match "
                "the controlled fixture count."
            )

        print(
            f"REAL POSTGRESQL RETRIEVAL PASS "
            f"({len(stored)} observations)"
        )

        # ---------------------------------------------------------
        # 4. Aggregation
        # ---------------------------------------------------------
        aggregates = aggregation.aggregate(stored)

        if len(aggregates) != 2:
            raise RuntimeError(
                "Expected two aggregates: COMPUTE and STORAGE."
            )

        print("COST AGGREGATION PASS")

        # ---------------------------------------------------------
        # 5. Compute aggregate validation
        # ---------------------------------------------------------
        compute = next(
            item
            for item in aggregates
            if item.category == CostCategory.COMPUTE
        )

        if compute.count != 3:
            raise RuntimeError(
                f"Expected 3 compute observations, got {compute.count}."
            )

        if compute.total_amount != 60.0:
            raise RuntimeError(
                f"Expected compute total 60.0, "
                f"got {compute.total_amount}."
            )

        if compute.minimum_amount != 10.0:
            raise RuntimeError(
                "Compute minimum aggregation failed."
            )

        if compute.maximum_amount != 30.0:
            raise RuntimeError(
                "Compute maximum aggregation failed."
            )

        if compute.average_amount != 20.0:
            raise RuntimeError(
                "Compute average aggregation failed."
            )

        if compute.latest_amount != 30.0:
            raise RuntimeError(
                "Compute latest amount selection failed."
            )

        if not compute.evidence_available:
            raise RuntimeError(
                "Compute evidence flag was lost."
            )

        print("COMPUTE AGGREGATE INTEGRITY PASS")

        # ---------------------------------------------------------
        # 6. Storage aggregate validation
        # ---------------------------------------------------------
        storage_aggregate = next(
            item
            for item in aggregates
            if item.category == CostCategory.STORAGE
        )

        if storage_aggregate.count != 1:
            raise RuntimeError(
                "Storage observation count is incorrect."
            )

        if storage_aggregate.total_amount != 5.0:
            raise RuntimeError(
                "Storage total aggregation failed."
            )

        print("STORAGE AGGREGATE INTEGRITY PASS")

        # ---------------------------------------------------------
        # 7. Resource aggregation
        # ---------------------------------------------------------
        resource_aggregates = aggregation.aggregate_for_resource(
            stored,
            test_resource_id,
        )

        if len(resource_aggregates) != 2:
            raise RuntimeError(
                "Resource aggregation did not preserve categories."
            )

        print("RESOURCE AGGREGATION PASS")

        # ---------------------------------------------------------
        # 8. Category aggregation
        # ---------------------------------------------------------
        category_aggregates = aggregation.aggregate_for_category(
            stored,
            CostCategory.COMPUTE,
        )

        if len(category_aggregates) != 1:
            raise RuntimeError(
                "Category aggregation returned unexpected groups."
            )

        if category_aggregates[0].total_amount != 60.0:
            raise RuntimeError(
                "Category aggregation total is incorrect."
            )

        print("CATEGORY AGGREGATION PASS")

        # ---------------------------------------------------------
        # 9. Time-window aggregation
        # ---------------------------------------------------------
        window_aggregates = aggregation.aggregate_between(
            stored,
            start=base_time,
            end=base_time + timedelta(minutes=1),
        )

        compute_window = next(
            (
                item
                for item in window_aggregates
                if item.category == CostCategory.COMPUTE
            ),
            None,
        )

        if compute_window is None:
            raise RuntimeError(
                "Expected compute aggregate in time window."
            )

        if compute_window.count != 2:
            raise RuntimeError(
                "Inclusive time-window aggregation failed."
            )

        if compute_window.total_amount != 30.0:
            raise RuntimeError(
                "Time-window total is incorrect."
            )

        print("TIME-WINDOW AGGREGATION PASS")

        # ---------------------------------------------------------
        # 10. Cost analysis
        # ---------------------------------------------------------
        analyses = aggregation.analyze_many(aggregates)

        if len(analyses) != 2:
            raise RuntimeError(
                "Expected one analysis result per aggregate."
            )

        compute_analysis = next(
            item
            for item in analyses
            if item.category == CostCategory.COMPUTE
        )

        if not compute_analysis.evidence_available:
            raise RuntimeError(
                "Cost analysis lost evidence availability."
            )

        if compute_analysis.total_amount != 60.0:
            raise RuntimeError(
                "Cost analysis total is incorrect."
            )

        if compute_analysis.average_amount != 20.0:
            raise RuntimeError(
                "Cost analysis average is incorrect."
            )

        if compute_analysis.latest_amount != 30.0:
            raise RuntimeError(
                "Cost analysis latest amount is incorrect."
            )

        if compute_analysis.observation_count != 3:
            raise RuntimeError(
                "Cost analysis observation count is incorrect."
            )

        print("COST ANALYSIS PASS")

        # ---------------------------------------------------------
        # 11. Currency separation
        # ---------------------------------------------------------
        inr_observation = CostObservation(
            resource_id=test_resource_id,
            amount=1000.0,
            currency="INR",
            category=CostCategory.COMPUTE,
            source=CostSource.AWS,
            observed_at=base_time + timedelta(minutes=3),
            evidence_available=True,
            metadata={
                "validation": "phase_6_4",
                "fixture": "controlled_currency_test",
            },
        )

        storage.save(inr_observation)

        currency_stored = storage.get_for_resource(
            resource_id=test_resource_id,
            limit=100,
        )

        currency_aggregates = aggregation.aggregate(currency_stored)

        currencies = {
            item.currency
            for item in currency_aggregates
        }

        if currencies != {"USD", "INR"}:
            raise RuntimeError(
                f"Currency mixing detected: {currencies}"
            )

        print("CURRENCY SEPARATION PASS")

        # ---------------------------------------------------------
        # 12. Boundary validation
        # ---------------------------------------------------------
        if any(
            analysis.observation_count <= 0
            and analysis.evidence_available
            for analysis in analyses
        ):
            raise RuntimeError(
                "Invalid evidence-backed analysis with zero observations."
            )

        print("ANALYSIS BOUNDARY PASS")

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
        print("No optimization recommendation performed.")
        print("No infrastructure action performed.")
        print()
        print("PHASE 6.4 — COMPLETE: PASS")

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