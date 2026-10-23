from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import psycopg
from psycopg.rows import dict_row

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
    print("PHASE 6.3 — COST STORAGE REAL POSTGRESQL VALIDATION")
    print("=" * 60)

    storage = PostgreSQLCostStorage()

    test_resource_id = f"phase-6-3-test-{uuid.uuid4()}"
    observed_at = datetime.now(UTC)

    observation = CostObservation(
        resource_id=test_resource_id,
        amount=12.50,
        currency="USD",
        category=CostCategory.COMPUTE,
        source=CostSource.AWS,
        observed_at=observed_at,
        billing_period_start=observed_at - timedelta(hours=1),
        billing_period_end=observed_at,
        evidence_available=True,
        metadata={
            "validation": "phase_6_3",
            "fixture": "controlled_storage_test",
        },
    )

    try:
        # ---------------------------------------------------------
        # 1. Real PostgreSQL connection
        # ---------------------------------------------------------
        with (
            psycopg.connect(get_dsn(), row_factory=dict_row) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute("SELECT version()")
            row = cursor.fetchone()

            if row is None:
                raise RuntimeError("PostgreSQL version query returned no result.")

            print("POSTGRESQL CONNECTION PASS")
            print(f"PostgreSQL: {row['version'].split(',')[0]}")

            # -----------------------------------------------------
            # 2. Initialize storage schema
            # -----------------------------------------------------
            storage.initialize()

            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'cost_observations'
                ) AS exists
                """
            )

            table_row = cursor.fetchone()

            if not table_row or not table_row["exists"]:
                raise RuntimeError(
                    "cost_observations table was not found."
                )

            print("COST STORAGE TABLE PASS")

            # -----------------------------------------------------
            # 3. Verify expected columns
            # -----------------------------------------------------
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'cost_observations'
                ORDER BY ordinal_position
                """
            )

            columns = {
                item["column_name"]
                for item in cursor.fetchall()
            }

            expected_columns = {
                "id",
                "resource_id",
                "amount",
                "currency",
                "category",
                "source",
                "observed_at",
                "billing_period_start",
                "billing_period_end",
                "evidence_available",
                "metadata",
                "created_at",
            }

            missing = expected_columns - columns

            if missing:
                raise RuntimeError(
                    f"Missing cost storage columns: {sorted(missing)}"
                )

            print("COST STORAGE SCHEMA PASS")

        # ---------------------------------------------------------
        # 4. Persist controlled storage fixture
        # ---------------------------------------------------------
        storage.save(observation)

        print("COST OBSERVATION PERSISTENCE PASS")
        print(
            "Controlled storage fixture inserted "
            f"for resource {test_resource_id}"
        )

        # ---------------------------------------------------------
        # 5. Recent retrieval
        # ---------------------------------------------------------
        recent = storage.get_recent(limit=100)

        recent_match = next(
            (
                item
                for item in recent
                if item.resource_id == test_resource_id
            ),
            None,
        )

        if recent_match is None:
            raise RuntimeError(
                "Inserted cost observation was not found by get_recent()."
            )

        print("RECENT RETRIEVAL PASS")

        # ---------------------------------------------------------
        # 6. Resource retrieval
        # ---------------------------------------------------------
        resource_results = storage.get_for_resource(
            resource_id=test_resource_id,
            limit=100,
        )

        if len(resource_results) != 1:
            raise RuntimeError(
                "Expected exactly one resource-specific cost observation."
            )

        resource_match = resource_results[0]

        if resource_match.resource_id != test_resource_id:
            raise RuntimeError("Resource ID mismatch.")

        print("RESOURCE RETRIEVAL PASS")

        # ---------------------------------------------------------
        # 7. Time-range retrieval
        # ---------------------------------------------------------
        start = observed_at - timedelta(minutes=1)
        end = observed_at + timedelta(minutes=1)

        time_results = storage.get_between(
            start=start,
            end=end,
        )

        time_match = next(
            (
                item
                for item in time_results
                if item.resource_id == test_resource_id
            ),
            None,
        )

        if time_match is None:
            raise RuntimeError(
                "Inserted cost observation was not found by "
                "get_between()."
            )

        print("TIME-RANGE RETRIEVAL PASS")

        # ---------------------------------------------------------
        # 8. Data integrity
        # ---------------------------------------------------------
        checks = {
            "resource_id": (
                resource_match.resource_id
                == observation.resource_id
            ),
            "amount": (
                resource_match.amount
                == observation.amount
            ),
            "currency": (
                resource_match.currency
                == observation.currency
            ),
            "category": (
                resource_match.category
                == observation.category
            ),
            "source": (
                resource_match.source
                == observation.source
            ),
            "evidence_available": (
                resource_match.evidence_available
                == observation.evidence_available
            ),
            "metadata": (
                resource_match.metadata
                == observation.metadata
            ),
        }

        failed_checks = [
            name
            for name, passed in checks.items()
            if not passed
        ]

        if failed_checks:
            raise RuntimeError(
                "Cost observation integrity failure: "
                f"{failed_checks}"
            )

        print("COST DATA INTEGRITY PASS")

        # ---------------------------------------------------------
        # 9. Evidence semantics
        # ---------------------------------------------------------
        if not resource_match.evidence_available:
            raise RuntimeError(
                "Controlled validation observation unexpectedly "
                "lost its evidence_available=true flag."
            )

        if (
            resource_match.metadata.get("fixture")
            != "controlled_storage_test"
        ):
            raise RuntimeError(
                "Controlled fixture metadata was not preserved."
            )

        print("EVIDENCE METADATA PASS")

        print()
        print("IMPORTANT:")
        print(
            "The $12.50 value above is a CONTROLLED "
            "STORAGE TEST FIXTURE."
        )
        print(
            "It is NOT claimed as real AWS billing evidence."
        )

        print()
        print("PHASE 6.3 — COMPLETE: PASS")

    finally:
        # ---------------------------------------------------------
        # 10. Remove ONLY this validator's record
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

            if deleted:
                print(
                    f"Cleanup PASS — removed {deleted} "
                    "controlled test record."
                )
            else:
                print(
                    "Cleanup PASS — no test record remained."
                )

        except psycopg.Error as cleanup_error:
            print(
                f"Cleanup WARNING: {cleanup_error}"
            )


if __name__ == "__main__":
    main()