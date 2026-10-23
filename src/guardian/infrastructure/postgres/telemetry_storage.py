from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from guardian.application.telemetry_storage import TelemetryStorage
from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
    TelemetrySource,
)


class PostgreSQLTelemetryStorageError(Exception):
    """Base error for PostgreSQL telemetry storage."""


class PostgreSQLTelemetryStorage(TelemetryStorage):
    """
    PostgreSQL-backed storage for telemetry observations.

    Telemetry values stored by this component must originate from
    real telemetry observations. This component does not generate,
    estimate, or fabricate telemetry.
    """

    TABLE_NAME = "telemetry_observations"

    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn or self._build_dsn()

    @staticmethod
    def _build_dsn() -> str:
        """
        Build the PostgreSQL DSN.

        Defaults match the existing ACG PostgreSQL container:

            Host:     localhost
            Port:     5433
            Database: guardian
            User:     guardian
            Password: guardian_dev_password

        Every value can be overridden through an environment variable.
        """

        host = os.getenv(
            "ACG_POSTGRES_HOST",
            "localhost",
        )

        port = os.getenv(
            "ACG_POSTGRES_PORT",
            "5433",
        )

        database = os.getenv(
            "ACG_POSTGRES_DB",
            "guardian",
        )

        user = os.getenv(
            "ACG_POSTGRES_USER",
            "guardian",
        )

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
        """
        Open a PostgreSQL connection using the configured DSN.
        """

        try:
            return psycopg.connect(
                self._dsn,
                row_factory=dict_row,
            )

        except psycopg.Error as exc:
            raise PostgreSQLTelemetryStorageError(
                "Unable to connect to PostgreSQL telemetry storage."
            ) from exc

    def initialize(self) -> None:
        """
        Create the telemetry storage table and indexes.

        This operation is idempotent and does not delete existing data.
        """

        query = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id BIGSERIAL PRIMARY KEY,

            resource_id TEXT NOT NULL,

            metric TEXT NOT NULL,

            value DOUBLE PRECISION NOT NULL,

            unit TEXT NOT NULL,

            observed_at TIMESTAMPTZ NOT NULL,

            source TEXT NOT NULL,

            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,

            created_at TIMESTAMPTZ NOT NULL
                DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS
            idx_telemetry_resource_observed_at
        ON {self.TABLE_NAME} (
            resource_id,
            observed_at DESC
        );

        CREATE INDEX IF NOT EXISTS
            idx_telemetry_metric_observed_at
        ON {self.TABLE_NAME} (
            metric,
            observed_at DESC
        );

        CREATE INDEX IF NOT EXISTS
            idx_telemetry_observed_at
        ON {self.TABLE_NAME} (
            observed_at DESC
        );
        """

        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query)

                connection.commit()

        except PostgreSQLTelemetryStorageError:
            raise

        except psycopg.Error as exc:
            raise PostgreSQLTelemetryStorageError(
                "Unable to initialize PostgreSQL telemetry storage."
            ) from exc

    def save(
        self,
        observation: TelemetryObservation,
    ) -> None:
        """
        Persist one telemetry observation.
        """

        query = f"""
        INSERT INTO {self.TABLE_NAME} (
            resource_id,
            metric,
            value,
            unit,
            observed_at,
            source,
            metadata
        )
        VALUES (
            %(resource_id)s,
            %(metric)s,
            %(value)s,
            %(unit)s,
            %(observed_at)s,
            %(source)s,
            %(metadata)s
        );
        """

        parameters = self._observation_parameters(
            observation
        )

        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        query,
                        parameters,
                    )

                connection.commit()

        except PostgreSQLTelemetryStorageError:
            raise

        except psycopg.Error as exc:
            raise PostgreSQLTelemetryStorageError(
                "Unable to save telemetry observation."
            ) from exc

    def save_many(
        self,
        observations: list[TelemetryObservation],
    ) -> None:
        """
        Persist multiple telemetry observations in one transaction.

        Empty input is intentionally a no-op.
        """

        if not observations:
            return

        query = f"""
        INSERT INTO {self.TABLE_NAME} (
            resource_id,
            metric,
            value,
            unit,
            observed_at,
            source,
            metadata
        )
        VALUES (
            %(resource_id)s,
            %(metric)s,
            %(value)s,
            %(unit)s,
            %(observed_at)s,
            %(source)s,
            %(metadata)s
        );
        """

        parameters = [
            self._observation_parameters(observation)
            for observation in observations
        ]

        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.executemany(
                        query,
                        parameters,
                    )

                connection.commit()

        except PostgreSQLTelemetryStorageError:
            raise

        except psycopg.Error as exc:
            raise PostgreSQLTelemetryStorageError(
                "Unable to save telemetry observations."
            ) from exc

    def get_recent(
        self,
        limit: int = 100,
    ) -> list[TelemetryObservation]:
        """
        Retrieve the most recent telemetry observations.
        """

        self._validate_limit(limit)

        query = f"""
        SELECT
            resource_id,
            metric,
            value,
            unit,
            observed_at,
            source,
            metadata
        FROM {self.TABLE_NAME}
        ORDER BY observed_at DESC, id DESC
        LIMIT %(limit)s;
        """

        try:
            with self._connect() as connection, connection.cursor() as cursor:
                cursor.execute(
                    query,
                    {"limit": limit},
                )

                rows = cursor.fetchall()

            return [
                self._row_to_observation(row)
                for row in rows
            ]

        except PostgreSQLTelemetryStorageError:
            raise

        except psycopg.Error as exc:
            raise PostgreSQLTelemetryStorageError(
                "Unable to retrieve recent telemetry."
            ) from exc

    def get_for_resource(
        self,
        resource_id: str,
        limit: int = 100,
    ) -> list[TelemetryObservation]:
        """
        Retrieve telemetry for one resource.
        """

        self._validate_resource_id(resource_id)
        self._validate_limit(limit)

        query = f"""
        SELECT
            resource_id,
            metric,
            value,
            unit,
            observed_at,
            source,
            metadata
        FROM {self.TABLE_NAME}
        WHERE resource_id = %(resource_id)s
        ORDER BY observed_at DESC, id DESC
        LIMIT %(limit)s;
        """

        try:
            with self._connect() as connection, connection.cursor() as cursor:
                cursor.execute(
                    query,
                    {
                        "resource_id": resource_id,
                        "limit": limit,
                    },
                )

                rows = cursor.fetchall()

            return [
                self._row_to_observation(row)
                for row in rows
            ]

        except PostgreSQLTelemetryStorageError:
            raise

        except psycopg.Error as exc:
            raise PostgreSQLTelemetryStorageError(
                "Unable to retrieve telemetry for resource "
                f"'{resource_id}'."
            ) from exc

    def get_for_resource_and_metric(
        self,
        resource_id: str,
        metric: str,
        limit: int = 100,
    ) -> list[TelemetryObservation]:
        """
        Retrieve telemetry for one resource and metric.
        """

        self._validate_resource_id(resource_id)
        self._validate_metric(metric)
        self._validate_limit(limit)

        query = f"""
        SELECT
            resource_id,
            metric,
            value,
            unit,
            observed_at,
            source,
            metadata
        FROM {self.TABLE_NAME}
        WHERE resource_id = %(resource_id)s
          AND metric = %(metric)s
        ORDER BY observed_at DESC, id DESC
        LIMIT %(limit)s;
        """

        try:
            with self._connect() as connection, connection.cursor() as cursor:
                cursor.execute(
                    query,
                    {
                        "resource_id": resource_id,
                        "metric": metric,
                        "limit": limit,
                    },
                )

                rows = cursor.fetchall()

            return [
                self._row_to_observation(row)
                for row in rows
            ]

        except PostgreSQLTelemetryStorageError:
            raise

        except psycopg.Error as exc:
            raise PostgreSQLTelemetryStorageError(
                "Unable to retrieve telemetry for resource "
                f"'{resource_id}' and metric '{metric}'."
            ) from exc

    def get_between(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000,
    ) -> list[TelemetryObservation]:
        """
        Retrieve telemetry observations within a time range.
        """

        if start >= end:
            raise ValueError(
                "The start time must be before the end time."
            )

        self._validate_limit(limit)

        query = f"""
        SELECT
            resource_id,
            metric,
            value,
            unit,
            observed_at,
            source,
            metadata
        FROM {self.TABLE_NAME}
        WHERE observed_at >= %(start)s
          AND observed_at <= %(end)s
        ORDER BY observed_at ASC, id ASC
        LIMIT %(limit)s;
        """

        try:
            with self._connect() as connection, connection.cursor() as cursor:
                cursor.execute(
                    query,
                    {
                        "start": start,
                        "end": end,
                        "limit": limit,
                    },
                )

                rows = cursor.fetchall()

            return [
                self._row_to_observation(row)
                for row in rows
            ]

        except PostgreSQLTelemetryStorageError:
            raise

        except psycopg.Error as exc:
            raise PostgreSQLTelemetryStorageError(
                "Unable to retrieve telemetry by time range."
            ) from exc

    @staticmethod
    def _observation_parameters(
        observation: TelemetryObservation,
    ) -> dict[str, Any]:
        """
        Convert a domain observation into PostgreSQL parameters.
        """

        return {
            "resource_id": observation.resource_id,
            "metric": observation.metric.value,
            "value": observation.value,
            "unit": observation.unit,
            "observed_at": observation.observed_at,
            "source": observation.source.value,
            "metadata": json.dumps(
                observation.metadata
            ),
        }

    @staticmethod
    def _row_to_observation(
        row: dict[str, Any] | tuple[Any, ...],
    ) -> TelemetryObservation:
        """
        Convert a PostgreSQL row into a TelemetryObservation.

        Supports:
        - dictionary rows returned by psycopg dict_row
        - tuple rows used by unit tests
        """

        if isinstance(row, dict):
            resource_id = row["resource_id"]
            metric = row["metric"]
            value = row["value"]
            unit = row["unit"]
            observed_at = row["observed_at"]
            source = row["source"]
            metadata = row["metadata"]

        elif isinstance(row, tuple):
            if len(row) != 7:
                raise PostgreSQLTelemetryStorageError(
                    "Telemetry row must contain exactly 7 values."
                )

            (
                resource_id,
                metric,
                value,
                unit,
                observed_at,
                source,
                metadata,
            ) = row

        else:
            raise PostgreSQLTelemetryStorageError(
                "Unsupported telemetry database row type."
            )

        if isinstance(metadata, str):
            parsed_metadata = json.loads(metadata)

        elif isinstance(metadata, dict):
            parsed_metadata = metadata

        else:
            parsed_metadata = {}

        if not isinstance(parsed_metadata, dict):
            raise PostgreSQLTelemetryStorageError(
                "Telemetry metadata must be a JSON object."
            )

        return TelemetryObservation(
            resource_id=str(resource_id),
            metric=TelemetryMetric(str(metric)),
            value=float(value),
            unit=str(unit),
            observed_at=observed_at,
            source=TelemetrySource(str(source)),
            metadata={
                str(key): str(value)
                for key, value in parsed_metadata.items()
            },
        )

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if limit <= 0:
            raise ValueError(
                "The limit must be greater than zero."
            )

    @staticmethod
    def _validate_resource_id(
        resource_id: str,
    ) -> None:
        if not resource_id.strip():
            raise ValueError(
                "The resource ID cannot be empty."
            )

    @staticmethod
    def _validate_metric(
        metric: str,
    ) -> None:
        if not metric.strip():
            raise ValueError(
                "The metric cannot be empty."
            )