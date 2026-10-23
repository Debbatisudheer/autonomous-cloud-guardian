from __future__ import annotations

from typing import Any

from guardian.domain.telemetry import (
    TelemetryMetric,
    TelemetrySource,
)
from guardian.infrastructure.docker.telemetry import (
    DockerTelemetryCollector,
)


class FakeContainer:
    def __init__(
        self,
        container_id: str,
        name: str,
        stats: dict[str, Any],
    ) -> None:
        self.id = container_id
        self.name = name
        self._stats = stats

    def stats(
        self,
        stream: bool = False,
        decode: bool = True,
    ) -> dict[str, Any]:
        assert stream is False
        assert decode is True

        return self._stats


class FakeContainerCollection:
    def __init__(
        self,
        containers: list[FakeContainer],
    ) -> None:
        self._containers = containers

    def list(
        self,
        all: bool = False,
    ) -> list[FakeContainer]:
        assert all is True

        return self._containers

    def get(
        self,
        container_id: str,
    ) -> FakeContainer:
        for container in self._containers:
            if container.id == container_id:
                return container

        raise RuntimeError(
            f"Container '{container_id}' was not found."
        )


class FakeDockerClient:
    def __init__(
        self,
        containers: list[FakeContainer],
    ) -> None:
        self.containers = FakeContainerCollection(
            containers
        )


def make_stats() -> dict[str, Any]:
    return {
        "read": "2026-10-23T07:30:00.000000000Z",
        "cpu_stats": {
            "cpu_usage": {
                "total_usage": 200,
                "percpu_usage": [100, 100],
            },
            "system_cpu_usage": 1000,
            "online_cpus": 2,
        },
        "precpu_stats": {
            "cpu_usage": {
                "total_usage": 100,
                "percpu_usage": [50, 50],
            },
            "system_cpu_usage": 500,
        },
        "memory_stats": {
            "usage": 256,
            "limit": 1024,
        },
        "networks": {
            "eth0": {
                "rx_bytes": 1000,
                "tx_bytes": 2000,
            },
            "eth1": {
                "rx_bytes": 300,
                "tx_bytes": 400,
            },
        },
    }


def make_collector() -> DockerTelemetryCollector:
    container = FakeContainer(
        container_id="container-1",
        name="acg-test",
        stats=make_stats(),
    )

    client = FakeDockerClient([container])

    return DockerTelemetryCollector(
        client=client,  # type: ignore[arg-type]
    )


def test_collect_container_returns_five_metrics() -> None:
    collector = make_collector()

    observations = collector.collect_container(
        "container-1"
    )

    assert len(observations) == 5


def test_collect_container_uses_docker_source() -> None:
    collector = make_collector()

    observations = collector.collect_container(
        "container-1"
    )

    assert all(
        observation.source == TelemetrySource.DOCKER
        for observation in observations
    )


def test_cpu_percentage_is_calculated() -> None:
    collector = make_collector()

    observations = collector.collect_container(
        "container-1"
    )

    cpu = next(
        observation
        for observation in observations
        if observation.metric
        == TelemetryMetric.CPU_USAGE_PERCENT
    )

    assert cpu.value == 40.0
    assert cpu.unit == "percent"


def test_memory_bytes_are_collected() -> None:
    collector = make_collector()

    observations = collector.collect_container(
        "container-1"
    )

    memory = next(
        observation
        for observation in observations
        if observation.metric
        == TelemetryMetric.MEMORY_USAGE_BYTES
    )

    assert memory.value == 256.0
    assert memory.unit == "bytes"


def test_memory_percentage_is_calculated() -> None:
    collector = make_collector()

    observations = collector.collect_container(
        "container-1"
    )

    memory_percent = next(
        observation
        for observation in observations
        if observation.metric
        == TelemetryMetric.MEMORY_USAGE_PERCENT
    )

    assert memory_percent.value == 25.0
    assert memory_percent.unit == "percent"


def test_network_bytes_are_aggregated() -> None:
    collector = make_collector()

    observations = collector.collect_container(
        "container-1"
    )

    network_rx = next(
        observation
        for observation in observations
        if observation.metric
        == TelemetryMetric.NETWORK_RX_BYTES
    )

    network_tx = next(
        observation
        for observation in observations
        if observation.metric
        == TelemetryMetric.NETWORK_TX_BYTES
    )

    assert network_rx.value == 1300.0
    assert network_tx.value == 2400.0


def test_metadata_contains_container_evidence() -> None:
    collector = make_collector()

    observations = collector.collect_container(
        "container-1"
    )

    for observation in observations:
        assert (
            observation.metadata["container_name"]
            == "acg-test"
        )

        assert (
            observation.metadata["measurement"]
            == "docker_stats"
        )


def test_missing_network_data_does_not_create_zero_values() -> None:
    stats = make_stats()
    stats["networks"] = {}

    container = FakeContainer(
        container_id="container-1",
        name="acg-test",
        stats=stats,
    )

    client = FakeDockerClient([container])

    collector = DockerTelemetryCollector(
        client=client,  # type: ignore[arg-type]
    )

    observations = collector.collect_container(
        "container-1"
    )

    metrics = {
        observation.metric
        for observation in observations
    }

    assert (
        TelemetryMetric.NETWORK_RX_BYTES
        not in metrics
    )

    assert (
        TelemetryMetric.NETWORK_TX_BYTES
        not in metrics
    )