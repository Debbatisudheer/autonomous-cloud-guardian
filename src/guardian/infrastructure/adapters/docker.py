from __future__ import annotations

import docker
from docker.client import DockerClient
from docker.errors import DockerException

from guardian.domain.resource import Resource
from guardian.infrastructure.adapters.base import InfrastructureAdapter


class InfrastructureAdapterError(Exception):
    """Base error for infrastructure adapter failures."""


class DockerInfrastructureAdapter(InfrastructureAdapter):
    """
    Infrastructure adapter for Docker.

    Provides the control plane with resources discovered from the
    real Docker Engine.
    """

    def __init__(self, client: DockerClient | None = None) -> None:
        try:
            self._client = client or docker.from_env()
        except DockerException as exc:
            raise InfrastructureAdapterError(
                "Unable to connect to the Docker infrastructure provider."
            ) from exc

    def discover_resources(self) -> list[Resource]:
        try:
            from guardian.infrastructure.docker.discovery import DockerDiscovery

            discovery = DockerDiscovery(client=self._client)
            return discovery.discover()
        except DockerException as exc:
            raise InfrastructureAdapterError(
                "Unable to discover resources from the Docker infrastructure provider."
            ) from exc