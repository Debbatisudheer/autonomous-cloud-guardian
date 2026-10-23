from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from guardian.application.security_storage import SecurityStorage
from guardian.domain.security import (
    SecurityCategory,
    SecurityEvidence,
    SecuritySource,
)


class PostgreSQLSecurityStorage(SecurityStorage):
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        self._host = host or os.getenv(
            "ACG_POSTGRES_HOST",
            "localhost",
        )

        self._port = port or int(
            os.getenv(
                "ACG_POSTGRES_PORT",
                "5433",
            )
        )

        self._database = database or os.getenv(
            "ACG_POSTGRES_DB",
            "guardian",
        )

        self._user = user or os.getenv(
            "ACG_POSTGRES_USER",
            "guardian",
        )

        self._password = password or os.getenv(
            "ACG_POSTGRES_PASSWORD",
            "guardian_dev_password",
        )

    def _connect(self) -> psycopg.Connection[Any]:
        return psycopg.connect(
            host=self._host,
            port=self._port,
            dbname=self._database,
            user=self._user,
            password=self._password,
            row_factory=dict_row,
        )

    def initialize(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS security_evidence (
                        id BIGSERIAL PRIMARY KEY,
                        evidence_id TEXT NOT NULL UNIQUE,
                        resource_id TEXT NOT NULL,
                        category TEXT NOT NULL,
                        source TEXT NOT NULL,
                        evidence_type TEXT NOT NULL,
                        observed_at TIMESTAMPTZ NOT NULL,
                        evidence_available BOOLEAN NOT NULL,
                        details JSONB NOT NULL DEFAULT '{}'::jsonb,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_security_evidence_resource_observed
                    ON security_evidence (
                        resource_id,
                        observed_at DESC
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_security_evidence_category_observed
                    ON security_evidence (
                        category,
                        observed_at DESC
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_security_evidence_source_observed
                    ON security_evidence (
                        source,
                        observed_at DESC
                    )
                    """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_security_evidence_observed
                    ON security_evidence (
                        observed_at DESC
                    )
                    """
                )

            connection.commit()

    def save(
        self,
        evidence: SecurityEvidence,
    ) -> int:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO security_evidence (
                        evidence_id,
                        resource_id,
                        category,
                        source,
                        evidence_type,
                        observed_at,
                        evidence_available,
                        details
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                    """,
                (
                    evidence.evidence_id,
                    evidence.resource_id,
                    evidence.category.value,
                    evidence.source.value,
                    evidence.evidence_type,
                    evidence.observed_at,
                    evidence.evidence_available,
                    json.dumps(evidence.details),
                ),
            )

            row = cursor.fetchone()

            if row is None:
                raise RuntimeError(
                    "PostgreSQL did not return the inserted "
                    "security evidence ID."
                )

            connection.commit()

            return int(row["id"])

    def save_many(
        self,
        evidence: list[SecurityEvidence],
    ) -> int:
        if not evidence:
            return 0

        with self._connect() as connection:
            with connection.cursor() as cursor:
                for item in evidence:
                    cursor.execute(
                        """
                        INSERT INTO security_evidence (
                            evidence_id,
                            resource_id,
                            category,
                            source,
                            evidence_type,
                            observed_at,
                            evidence_available,
                            details
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            item.evidence_id,
                            item.resource_id,
                            item.category.value,
                            item.source.value,
                            item.evidence_type,
                            item.observed_at,
                            item.evidence_available,
                            json.dumps(item.details),
                        ),
                    )

            connection.commit()

            return len(evidence)

    def get_recent(
        self,
        limit: int = 100,
    ) -> list[SecurityEvidence]:
        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                    SELECT
                        evidence_id,
                        resource_id,
                        category,
                        source,
                        evidence_type,
                        observed_at,
                        evidence_available,
                        details
                    FROM security_evidence
                    ORDER BY observed_at DESC
                    LIMIT %s
                    """,
                (limit,),
            )

            rows = cursor.fetchall()

        return [
            self._row_to_evidence(row)
            for row in rows
        ]

    def get_for_resource(
        self,
        resource_id: str,
        limit: int = 100,
    ) -> list[SecurityEvidence]:
        if not resource_id:
            raise ValueError(
                "resource_id must not be empty."
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                    SELECT
                        evidence_id,
                        resource_id,
                        category,
                        source,
                        evidence_type,
                        observed_at,
                        evidence_available,
                        details
                    FROM security_evidence
                    WHERE resource_id = %s
                    ORDER BY observed_at DESC
                    LIMIT %s
                    """,
                (
                    resource_id,
                    limit,
                ),
            )

            rows = cursor.fetchall()

        return [
            self._row_to_evidence(row)
            for row in rows
        ]

    def get_between(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[SecurityEvidence]:
        if end < start:
            raise ValueError(
                "end must be greater than or equal to start."
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                    SELECT
                        evidence_id,
                        resource_id,
                        category,
                        source,
                        evidence_type,
                        observed_at,
                        evidence_available,
                        details
                    FROM security_evidence
                    WHERE observed_at >= %s
                      AND observed_at <= %s
                    ORDER BY observed_at ASC
                    LIMIT %s
                    """,
                (
                    start,
                    end,
                    limit,
                ),
            )

            rows = cursor.fetchall()

        return [
            self._row_to_evidence(row)
            for row in rows
        ]

    @staticmethod
    def _row_to_evidence(
        row: dict[str, Any],
    ) -> SecurityEvidence:
        details_value = row["details"]

        if isinstance(details_value, str):
            details = json.loads(details_value)
        else:
            details = details_value

        return SecurityEvidence(
            evidence_id=str(
                row["evidence_id"]
            ),
            resource_id=str(
                row["resource_id"]
            ),
            category=SecurityCategory(
                row["category"]
            ),
            source=SecuritySource(
                row["source"]
            ),
            evidence_type=str(
                row["evidence_type"]
            ),
            observed_at=row["observed_at"],
            evidence_available=bool(
                row["evidence_available"]
            ),
            details={
                str(key): str(value)
                for key, value in details.items()
            },
        )