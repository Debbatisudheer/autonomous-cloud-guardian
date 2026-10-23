from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import docker
from docker.client import DockerClient
from docker.errors import DockerException, NotFound

from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetryObservation,
    TelemetrySource,
)


class DockerTelemetryError(Exception):
    """Base error for Docker telemetry collection."""


class DockerTelemetryCollector:
    """
    Collects real telemetry from the Docker Engine.

    This collector does not generate, estimate, or fabricate telemetry.
    Every returned observation comes from Docker container statistics.
    """

    def __init__(self, client: DockerClient | None = None) -> None:
        try:
            self._client = client or docker.from_env()
        except DockerException as exc:
            raise DockerTelemetryError(
                "Unable to connect to the Docker Engine."
            ) from exc

    def collect_container(
        self,
        container_id: str,
    ) -> list[TelemetryObservation]:
        """
        Collect one real Docker stats snapshot.

        If Docker cannot provide statistics, an error is raised.
        No zero values are fabricated for unavailable telemetry.
        """
        try:
            container = self._client.containers.get(container_id)

            if not container.id:
                raise DockerTelemetryError(
                    "Docker returned a container without an ID."
                )

            if not container.name:
                raise DockerTelemetryError(
                    "Docker returned a container without a name."
                )

            # Docker SDK:
            # decode=True is only supported with stream=True.
            # For a single snapshot, stream=False is sufficient.
            stats = container.stats(
                stream=False,
            )

        except NotFound as exc:
            raise DockerTelemetryError(
                f"Docker container '{container_id}' was not found."
            ) from exc

        except DockerException as exc:
            raise DockerTelemetryError(
                "Unable to collect Docker telemetry for "
                f"container '{container_id}'."
            ) from exc

        if not isinstance(stats, dict):
            raise DockerTelemetryError(
                f"Docker returned invalid stats for "
                f"container '{container_id}'."
            )

        return self._build_observations(
            container_id=container.id,
            container_name=container.name,
            stats=stats,
        )

    def collect_all(self) -> list[TelemetryObservation]:
        """
        Collect telemetry from all Docker containers for which
        Docker provides a valid stats snapshot.

        Containers without available runtime statistics are skipped.
        They are not represented with fabricated values.
        """
        try:
            containers = self._client.containers.list(all=True)
        except DockerException as exc:
            raise DockerTelemetryError(
                "Unable to list Docker containers."
            ) from exc

        observations: list[TelemetryObservation] = []

        for container in containers:
            if not container.id:
                continue

            try:
                observations.extend(
                    self.collect_container(container.id)
                )
            except DockerTelemetryError:
                # A stopped container or a container without
                # available runtime statistics must not produce
                # fabricated telemetry.
                continue

        return observations

    @staticmethod
    def _build_observations(
        container_id: str,
        container_name: str,
        stats: dict[str, Any],
    ) -> list[TelemetryObservation]:
        observations: list[TelemetryObservation] = []

        observed_at = DockerTelemetryCollector._extract_timestamp(
            stats
        )

        # ---------------------------------------------------------
        # CPU
        # ---------------------------------------------------------

        cpu_percent = DockerTelemetryCollector._calculate_cpu_percent(
            stats
        )

        if cpu_percent is not None:
            observations.append(
                TelemetryObservation(
                    resource_id=container_id,
                    metric=TelemetryMetric.CPU_USAGE_PERCENT,
                    value=cpu_percent,
                    unit="percent",
                    observed_at=observed_at,
                    source=TelemetrySource.DOCKER,
                    metadata={
                        "container_name": container_name,
                        "measurement": "docker_stats",
                    },
                )
            )

        # ---------------------------------------------------------
        # Memory usage bytes
        # ---------------------------------------------------------

        memory_usage = DockerTelemetryCollector._memory_usage_bytes(
            stats
        )

        if memory_usage is not None:
            observations.append(
                TelemetryObservation(
                    resource_id=container_id,
                    metric=TelemetryMetric.MEMORY_USAGE_BYTES,
                    value=float(memory_usage),
                    unit="bytes",
                    observed_at=observed_at,
                    source=TelemetrySource.DOCKER,
                    metadata={
                        "container_name": container_name,
                        "measurement": "docker_stats",
                    },
                )
            )

        # ---------------------------------------------------------
        # Memory usage percentage
        # ---------------------------------------------------------

        memory_percent = DockerTelemetryCollector._memory_usage_percent(
            stats
        )

        if memory_percent is not None:
            observations.append(
                TelemetryObservation(
                    resource_id=container_id,
                    metric=TelemetryMetric.MEMORY_USAGE_PERCENT,
                    value=memory_percent,
                    unit="percent",
                    observed_at=observed_at,
                    source=TelemetrySource.DOCKER,
                    metadata={
                        "container_name": container_name,
                        "measurement": "docker_stats",
                    },
                )
            )

        # ---------------------------------------------------------
        # Network
        # ---------------------------------------------------------

        network_rx, network_tx = (
            DockerTelemetryCollector._network_usage(stats)
        )

        if network_rx is not None:
            observations.append(
                TelemetryObservation(
                    resource_id=container_id,
                    metric=TelemetryMetric.NETWORK_RX_BYTES,
                    value=float(network_rx),
                    unit="bytes",
                    observed_at=observed_at,
                    source=TelemetrySource.DOCKER,
                    metadata={
                        "container_name": container_name,
                        "measurement": "docker_stats",
                    },
                )
            )

        if network_tx is not None:
            observations.append(
                TelemetryObservation(
                    resource_id=container_id,
                    metric=TelemetryMetric.NETWORK_TX_BYTES,
                    value=float(network_tx),
                    unit="bytes",
                    observed_at=observed_at,
                    source=TelemetrySource.DOCKER,
                    metadata={
                        "container_name": container_name,
                        "measurement": "docker_stats",
                    },
                )
            )

        return observations

    @staticmethod
    def _calculate_cpu_percent(
        stats: dict[str, Any],
    ) -> float | None:
        """
        Calculate CPU usage percentage using Docker's CPU counters.

        Formula:

            cpu_delta / system_delta
            × online_cpus
            × 100
        """
        cpu_stats = stats.get("cpu_stats") or {}
        precpu_stats = stats.get("precpu_stats") or {}

        if not isinstance(cpu_stats, dict):
            return None

        if not isinstance(precpu_stats, dict):
            return None

        cpu_usage = cpu_stats.get("cpu_usage") or {}
        previous_cpu_usage = precpu_stats.get("cpu_usage") or {}

        if not isinstance(cpu_usage, dict):
            return None

        if not isinstance(previous_cpu_usage, dict):
            return None

        total_usage = cpu_usage.get("total_usage")
        previous_total_usage = previous_cpu_usage.get(
            "total_usage"
        )

        system_usage = cpu_stats.get("system_cpu_usage")
        previous_system_usage = precpu_stats.get(
            "system_cpu_usage"
        )

        if not isinstance(total_usage, int | float):
            return None

        if not isinstance(previous_total_usage, int | float):
            return None

        if not isinstance(system_usage, int | float):
            return None

        if not isinstance(previous_system_usage, int | float):
            return None

        cpu_delta = total_usage - previous_total_usage
        system_delta = system_usage - previous_system_usage

        if cpu_delta < 0:
            return None

        if system_delta <= 0:
            return None

        online_cpus = cpu_stats.get("online_cpus")

        if not isinstance(online_cpus, int | float):
            percpu_usage = cpu_usage.get("percpu_usage")

            if (
                isinstance(percpu_usage, list)
                and len(percpu_usage) > 0
            ):
                online_cpus = len(percpu_usage)

        if not isinstance(online_cpus, int | float):
            return None

        if online_cpus <= 0:
            return None

        return (
            (cpu_delta / system_delta)
            * float(online_cpus)
            * 100.0
        )

    @staticmethod
    def _memory_usage_bytes(
        stats: dict[str, Any],
    ) -> int | None:
        memory_stats = stats.get("memory_stats") or {}

        if not isinstance(memory_stats, dict):
            return None

        usage = memory_stats.get("usage")

        if not isinstance(usage, int | float):
            return None

        if usage < 0:
            return None

        return int(usage)

    @staticmethod
    def _memory_usage_percent(
        stats: dict[str, Any],
    ) -> float | None:
        memory_stats = stats.get("memory_stats") or {}

        if not isinstance(memory_stats, dict):
            return None

        usage = memory_stats.get("usage")
        limit = memory_stats.get("limit")

        if not isinstance(usage, int | float):
            return None

        if not isinstance(limit, int | float):
            return None

        if usage < 0:
            return None

        if limit <= 0:
            return None

        return (float(usage) / float(limit)) * 100.0

    @staticmethod
    def _network_usage(
        stats: dict[str, Any],
    ) -> tuple[int | None, int | None]:
        networks = stats.get("networks") or {}

        if not isinstance(networks, dict):
            return None, None

        if not networks:
            return None, None

        total_rx = 0
        total_tx = 0

        rx_found = False
        tx_found = False

        for interface_stats in networks.values():
            if not isinstance(interface_stats, dict):
                continue

            rx_bytes = interface_stats.get("rx_bytes")
            tx_bytes = interface_stats.get("tx_bytes")

            if (
                isinstance(rx_bytes, int | float)
                and rx_bytes >= 0
            ):
                total_rx += int(rx_bytes)
                rx_found = True

            if (
                isinstance(tx_bytes, int | float)
                and tx_bytes >= 0
            ):
                total_tx += int(tx_bytes)
                tx_found = True

        return (
            total_rx if rx_found else None,
            total_tx if tx_found else None,
        )

    @staticmethod
    def _extract_timestamp(
        stats: dict[str, Any],
    ) -> datetime:
        value = stats.get("read")

        if isinstance(value, str):
            normalized = value.replace(
                "Z",
                "+00:00",
            )

            try:
                parsed = datetime.fromisoformat(
                    normalized
                )

                if parsed.tzinfo is None:
                    return parsed.replace(
                        tzinfo=UTC
                    )

                return parsed.astimezone(UTC)

            except ValueError:
                pass

        return datetime.now(UTC)