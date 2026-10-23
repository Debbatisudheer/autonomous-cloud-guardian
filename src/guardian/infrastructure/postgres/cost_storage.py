from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from guardian.application.cost_storage import CostStorage
from guardian.domain.cost import (
    CostCategory,
    CostObservation,
    CostSource,
)


class PostgreSQLCostStorage(CostStorage):
    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or self._build_dsn()

    @staticmethod
    def _build_dsn() -> str:
        host = os.getenv("ACG_POSTGRES_HOST", "localhost")
        port = os.getenv("ACG_POSTGRES_PORT", "5433")
        database = os.getenv("ACG_POSTGRES_DB", "guardian")
        user = os.getenv("ACG_POSTGRES_USER", "guardian")
        password = os.getenv(
            "ACG_POSTGRES_PASSWORD",
            "guardian_dev_password",
        )

        return (
            f"host={host} "
            f"port={port} "
            f"dbname={database} "
            f"user={user} "
            f"password={password}"
        )

    def _connect(self) -> psycopg.Connection[Any]:
        return psycopg.connect(
            self._dsn,
            row_factory=dict_row,
        )

    def initialize(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS cost_observations (
            id BIGSERIAL PRIMARY KEY,
            resource_id TEXT NOT NULL,
            amount DOUBLE PRECISION NOT NULL CHECK (amount >= 0),
            currency TEXT NOT NULL,
            category TEXT NOT NULL,
            source TEXT NOT NULL,
            observed_at TIMESTAMPTZ NOT NULL,
            billing_period_start TIMESTAMPTZ,
            billing_period_end TIMESTAMPTZ,
            evidence_available BOOLEAN NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_cost_resource_observed
            ON cost_observations (resource_id, observed_at DESC);

        CREATE INDEX IF NOT EXISTS idx_cost_source_observed
            ON cost_observations (source, observed_at DESC);

        CREATE INDEX IF NOT EXISTS idx_cost_observed
            ON cost_observations (observed_at DESC);
        """

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(query)

    def save(self, observation: CostObservation) -> None:
        query = """
        INSERT INTO cost_observations (
            resource_id,
            amount,
            currency,
            category,
            source,
            observed_at,
            billing_period_start,
            billing_period_end,
            evidence_available,
            metadata
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    observation.resource_id,
                    observation.amount,
                    observation.currency,
                    observation.category.value,
                    observation.source.value,
                    observation.observed_at,
                    observation.billing_period_start,
                    observation.billing_period_end,
                    observation.evidence_available,
                    json.dumps(observation.metadata),
                ),
            )

    def save_many(
        self,
        observations: list[CostObservation],
    ) -> None:
        if not observations:
            return

        query = """
        INSERT INTO cost_observations (
            resource_id,
            amount,
            currency,
            category,
            source,
            observed_at,
            billing_period_start,
            billing_period_end,
            evidence_available,
            metadata
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        values = [
            (
                observation.resource_id,
                observation.amount,
                observation.currency,
                observation.category.value,
                observation.source.value,
                observation.observed_at,
                observation.billing_period_start,
                observation.billing_period_end,
                observation.evidence_available,
                json.dumps(observation.metadata),
            )
            for observation in observations
        ]

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.executemany(query, values)

    def get_recent(self, limit: int = 100) -> list[CostObservation]:
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        query = """
        SELECT
            resource_id,
            amount,
            currency,
            category,
            source,
            observed_at,
            billing_period_start,
            billing_period_end,
            evidence_available,
            metadata
        FROM cost_observations
        ORDER BY observed_at DESC
        LIMIT %s
        """

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()

        return [self._row_to_observation(row) for row in rows]

    def get_for_resource(
        self,
        resource_id: str,
        limit: int = 100,
    ) -> list[CostObservation]:
        if not resource_id:
            raise ValueError("resource_id must not be empty")

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        query = """
        SELECT
            resource_id,
            amount,
            currency,
            category,
            source,
            observed_at,
            billing_period_start,
            billing_period_end,
            evidence_available,
            metadata
        FROM cost_observations
        WHERE resource_id = %s
        ORDER BY observed_at DESC
        LIMIT %s
        """

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(query, (resource_id, limit))
            rows = cursor.fetchall()

        return [self._row_to_observation(row) for row in rows]

    def get_between(
        self,
        start: datetime,
        end: datetime,
    ) -> list[CostObservation]:
        if end < start:
            raise ValueError("end must not be earlier than start")

        query = """
        SELECT
            resource_id,
            amount,
            currency,
            category,
            source,
            observed_at,
            billing_period_start,
            billing_period_end,
            evidence_available,
            metadata
        FROM cost_observations
        WHERE observed_at >= %s
          AND observed_at <= %s
        ORDER BY observed_at ASC
        """

        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(query, (start, end))
            rows = cursor.fetchall()

        return [self._row_to_observation(row) for row in rows]

    @staticmethod
    def _row_to_observation(
        row: dict[str, Any],
    ) -> CostObservation:
        metadata = row["metadata"]

        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        return CostObservation(
            resource_id=row["resource_id"],
            amount=float(row["amount"]),
            currency=row["currency"],
            category=CostCategory(row["category"]),
            source=CostSource(row["source"]),
            observed_at=row["observed_at"],
            billing_period_start=row["billing_period_start"],
            billing_period_end=row["billing_period_end"],
            evidence_available=row["evidence_available"],
            metadata=metadata,
        )