from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg

from guardian.domain.security import (
    SecurityCategory,
    SecurityEvidence,
    SecuritySource,
)
from guardian.infrastructure.postgres.security_storage import (
    PostgreSQLSecurityStorage,
)


def main() -> None:
    print("PHASE 7.3 — SECURITY STORAGE REAL POSTGRESQL VALIDATION")
    print("=" * 64)

    storage = PostgreSQLSecurityStorage()

    connection = None

    try:
        connection = psycopg.connect(
            host="localhost",
            port=5433,
            dbname="guardian",
            user="guardian",
            password="guardian_dev_password",
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version_row = cursor.fetchone()

        if version_row is None:
            raise RuntimeError(
                "PostgreSQL version could not be retrieved."
            )

        print("POSTGRESQL CONNECTION PASS")
        print(f"PostgreSQL: {version_row[0]}")

    finally:
        if connection is not None:
            connection.close()

    storage.initialize()

    print("SECURITY STORAGE INITIALIZATION PASS")

    test_resource_id = (
        f"phase-7-3-test-{uuid4()}"
    )

    now = datetime.now(UTC)

    evidence_records = [
        SecurityEvidence(
            evidence_id=str(uuid4()),
            resource_id=test_resource_id,
            category=SecurityCategory.CONTAINER,
            source=SecuritySource.DOCKER,
            evidence_type="container_runtime_configuration",
            observed_at=now - timedelta(minutes=4),
            evidence_available=True,
            details={
                "container_name": "phase-7-3-test",
                "status": "running",
                "privileged": "false",
            },
        ),
        SecurityEvidence(
            evidence_id=str(uuid4()),
            resource_id=test_resource_id,
            category=SecurityCategory.NETWORK,
            source=SecuritySource.DOCKER,
            evidence_type="container_network_configuration",
            observed_at=now - timedelta(minutes=3),
            evidence_available=True,
            details={
                "network_mode": "bridge",
                "published_ports": "",
            },
        ),
        SecurityEvidence(
            evidence_id=str(uuid4()),
            resource_id=test_resource_id,
            category=SecurityCategory.ACCESS_CONTROL,
            source=SecuritySource.DOCKER,
            evidence_type="container_privilege_configuration",
            observed_at=now - timedelta(minutes=2),
            evidence_available=True,
            details={
                "privileged": "false",
                "cap_add": "",
                "cap_drop": "NET_RAW",
            },
        ),
        SecurityEvidence(
            evidence_id=str(uuid4()),
            resource_id=test_resource_id,
            category=SecurityCategory.CONTAINER,
            source=SecuritySource.DOCKER,
            evidence_type="container_mount_configuration",
            observed_at=now - timedelta(minutes=1),
            evidence_available=True,
            details={
                "mount_count": "0",
                "mounts": "",
            },
        ),
        SecurityEvidence(
            evidence_id=str(uuid4()),
            resource_id=test_resource_id,
            category=SecurityCategory.VULNERABILITY,
            source=SecuritySource.DOCKER,
            evidence_type="vulnerability_scan",
            observed_at=now,
            evidence_available=False,
            details={
                "reason": "No vulnerability scanner evidence available.",
            },
        ),
    ]

    try:
        inserted_count = storage.save_many(
            evidence_records
        )

        if inserted_count != len(evidence_records):
            raise RuntimeError(
                "Not all controlled security evidence records "
                "were persisted."
            )

        print(
            "CONTROLLED SECURITY EVIDENCE WRITE PASS "
            f"({inserted_count} records)"
        )

        stored = storage.get_for_resource(
            resource_id=test_resource_id,
            limit=100,
        )

        if len(stored) != len(evidence_records):
            raise RuntimeError(
                "Not all security evidence records were "
                "retrieved."
            )

        print(
            "SECURITY EVIDENCE RETRIEVAL PASS "
            f"({len(stored)} records)"
        )

        stored_ids = {
            item.evidence_id
            for item in stored
        }

        expected_ids = {
            item.evidence_id
            for item in evidence_records
        }

        if stored_ids != expected_ids:
            raise RuntimeError(
                "Security evidence IDs do not match "
                "the persisted records."
            )

        print("EVIDENCE ID INTEGRITY PASS")

        for item in stored:
            if item.resource_id != test_resource_id:
                raise RuntimeError(
                    "Resource correlation failed."
                )

            if not item.evidence_id:
                raise RuntimeError(
                    "Persisted evidence has no evidence ID."
                )

            if not item.evidence_type:
                raise RuntimeError(
                    "Persisted evidence has no evidence type."
                )

            if not item.source:
                raise RuntimeError(
                    "Persisted evidence has no source."
                )

        print("SECURITY EVIDENCE INTEGRITY PASS")

        recent = storage.get_recent(
            limit=100,
        )

        recent_ids = {
            item.evidence_id
            for item in recent
        }

        if not expected_ids.issubset(recent_ids):
            raise RuntimeError(
                "Recent security evidence retrieval "
                "did not return the controlled records."
            )

        print("RECENT SECURITY EVIDENCE QUERY PASS")

        resource_records = storage.get_for_resource(
            resource_id=test_resource_id,
            limit=100,
        )

        if len(resource_records) != 5:
            raise RuntimeError(
                "Resource-specific security evidence retrieval failed."
            )

        print("RESOURCE SECURITY EVIDENCE QUERY PASS")

        window_start = now - timedelta(minutes=10)
        window_end = now + timedelta(minutes=1)

        window_records = storage.get_between(
            start=window_start,
            end=window_end,
            limit=100,
        )

        window_ids = {
            item.evidence_id
            for item in window_records
        }

        if not expected_ids.issubset(window_ids):
            raise RuntimeError(
                "Time-range security evidence retrieval failed."
            )

        print("TIME-RANGE SECURITY EVIDENCE QUERY PASS")

        unavailable_records = [
            item
            for item in stored
            if not item.evidence_available
        ]

        if len(unavailable_records) != 1:
            raise RuntimeError(
                "Unavailable evidence state was not preserved."
            )

        print("EVIDENCE AVAILABILITY INTEGRITY PASS")

        vulnerability_record = unavailable_records[0]

        if (
            vulnerability_record.evidence_type
            != "vulnerability_scan"
        ):
            raise RuntimeError(
                "Unavailable vulnerability evidence type was not preserved."
            )

        if vulnerability_record.details.get("reason") is None:
            raise RuntimeError(
                "Unavailable evidence reason was not preserved."
            )

        print("UNAVAILABLE EVIDENCE PRESERVATION PASS")

        print()
        print("PHASE 7.3 BOUNDARY CHECK")
        print("------------------------")
        print("Security evidence storage:    COMPLETE")
        print("PostgreSQL persistence:        VERIFIED")
        print("Evidence retrieval:            VERIFIED")
        print("Security assessment:           NOT IMPLEMENTED")
        print("Risk scoring:                  NOT IMPLEMENTED")
        print("Recommendation:                NOT IMPLEMENTED")
        print("Infrastructure action:         NONE")
        print("Automatic remediation:         NONE")
        print()
        print("IMPORTANT:")
        print(
            "All inserted records are CONTROLLED SECURITY "
            "STORAGE TEST FIXTURES."
        )
        print(
            "They are not claimed as real security findings."
        )
        print()
        print("PHASE 7.3 — COMPLETE: PASS")

    finally:
        cleanup_connection = None

        try:
            cleanup_connection = psycopg.connect(
                host="localhost",
                port=5433,
                dbname="guardian",
                user="guardian",
                password="guardian_dev_password",
            )

            with cleanup_connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM security_evidence
                    WHERE resource_id = %s
                    """,
                    (test_resource_id,),
                )

                deleted_count = cursor.rowcount

            cleanup_connection.commit()

            print(
                "Cleanup PASS — removed "
                f"{deleted_count} controlled security evidence records."
            )

        finally:
            if cleanup_connection is not None:
                cleanup_connection.close()


if __name__ == "__main__":
    main()