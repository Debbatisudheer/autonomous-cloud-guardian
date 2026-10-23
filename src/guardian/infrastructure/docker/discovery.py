from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import docker
from docker.client import DockerClient

from guardian.domain.resource import (
    Resource,
    ResourceHealth,
    ResourceProvider,
    ResourceStatus,
)


class DockerDiscovery:
    """
    Discovers real Docker containers and converts them into
    provider-agnostic Resource domain objects.

    This component is read-only. It does not create, update,
    restart, stop, or delete Docker resources.
    """

    def __init__(self, client: DockerClient | None = None) -> None:
        self._client = client or docker.from_env()

    def discover(self) -> list[Resource]:
        """Discover all Docker containers, including stopped containers."""
        containers = self._client.containers.list(all=True)

        return [self._to_resource(container) for container in containers]

    def _to_resource(self, container: Any) -> Resource:
        """Convert a Docker container object into a Resource."""
        attrs = container.attrs
        state = attrs.get("State", {})
        config = attrs.get("Config", {})

        status = self._map_status(state.get("Status"))
        health = self._map_health(state)

        created_at = self._parse_docker_timestamp(attrs.get("Created"))
        observed_at = datetime.now(UTC)

        metadata: dict[str, Any] = {
            "container_id": container.id,
            "image": config.get("Image"),
            "command": config.get("Cmd"),
            "docker_status": state.get("Status"),
            "exit_code": state.get("ExitCode"),
            "restart_count": attrs.get("RestartCount", 0),
            "labels": config.get("Labels") or {},
        }

        return Resource(
            id=container.id,
            name=container.name,
            resource_type="container",
            provider=ResourceProvider.DOCKER,
            status=status,
            health=health,
            metadata=metadata,
            created_at=created_at,
            updated_at=observed_at,
        )

    @staticmethod
    def _parse_docker_timestamp(value: str | None) -> datetime:
        """
        Convert Docker's RFC3339 timestamp into a timezone-aware datetime.

        Docker commonly returns timestamps such as:
        2026-10-22T12:34:56.123456789Z
        """
        if not value:
            return datetime.now(UTC)

        normalized = value.replace("Z", "+00:00")

        # Python datetime supports microseconds, while Docker can provide
        # nanosecond precision. Trim fractional seconds to six digits.
        if "." in normalized:
            prefix, suffix = normalized.split(".", 1)
            timezone_start = suffix.find("+")
            if timezone_start == -1:
                timezone_start = suffix.find("-")

            if timezone_start == -1:
                fractional = suffix
                timezone = ""
            else:
                fractional = suffix[:timezone_start]
                timezone = suffix[timezone_start:]

            fractional = fractional[:6].ljust(6, "0")
            normalized = f"{prefix}.{fractional}{timezone}"

        parsed = datetime.fromisoformat(normalized)

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)

        return parsed.astimezone(UTC)

    @staticmethod
    def _map_status(status: str | None) -> ResourceStatus:
        """Map Docker lifecycle status to the ACG resource status."""
        mapping = {
            "created": ResourceStatus.CREATING,
            "running": ResourceStatus.RUNNING,
            "paused": ResourceStatus.STOPPED,
            "restarting": ResourceStatus.CREATING,
            "removing": ResourceStatus.DELETING,
            "exited": ResourceStatus.STOPPED,
            "dead": ResourceStatus.FAILED,
        }

        return mapping.get(status or "", ResourceStatus.UNKNOWN)

    @staticmethod
    def _map_health(state: dict[str, Any]) -> ResourceHealth:
        """Map Docker health information into the ACG health model."""
        health = state.get("Health")

        if not health:
            status = state.get("Status")

            if status == "running":
                return ResourceHealth.UNKNOWN

            if status in {"exited", "dead"}:
                return ResourceHealth.UNHEALTHY

            return ResourceHealth.UNKNOWN

        health_status = health.get("Status")

        mapping = {
            "healthy": ResourceHealth.HEALTHY,
            "unhealthy": ResourceHealth.UNHEALTHY,
            "starting": ResourceHealth.UNKNOWN,
        }

        return mapping.get(health_status, ResourceHealth.UNKNOWN)
