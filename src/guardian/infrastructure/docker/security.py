from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import docker
from docker.errors import DockerException, NotFound
from docker.models.containers import Container

from guardian.application.security_evidence import (
    SecurityEvidenceProvider,
    SecurityEvidenceResult,
)
from guardian.domain.security import (
    SecurityCategory,
    SecurityEvidence,
    SecuritySource,
)


class DockerSecurityEvidenceProvider(SecurityEvidenceProvider):
    def __init__(
        self,
        client: docker.DockerClient | None = None,
    ) -> None:
        self._client = client or docker.from_env()

    def collect_for_resource(
        self,
        resource_id: str,
    ) -> SecurityEvidenceResult:
        try:
            container = self._find_container(resource_id)

            observed_at = datetime.now(UTC)

            evidence: list[SecurityEvidence] = []

            evidence.append(
                self._build_container_state_evidence(
                    resource_id,
                    container,
                    observed_at,
                )
            )

            evidence.append(
                self._build_network_evidence(
                    resource_id,
                    container,
                    observed_at,
                )
            )

            evidence.append(
                self._build_privilege_evidence(
                    resource_id,
                    container,
                    observed_at,
                )
            )

            evidence.append(
                self._build_mount_evidence(
                    resource_id,
                    container,
                    observed_at,
                )
            )

            return SecurityEvidenceResult(
                evidence=evidence,
                evidence_available=True,
                reason=(
                    "Security-related Docker runtime configuration "
                    "was observed directly from the Docker API."
                ),
            )

        except NotFound:
            return SecurityEvidenceResult(
                evidence=[],
                evidence_available=False,
                reason=(
                    f"Docker resource '{resource_id}' was not found."
                ),
            )

        except DockerException as exc:
            return SecurityEvidenceResult(
                evidence=[],
                evidence_available=False,
                reason=(
                    "Docker security evidence could not be collected: "
                    f"{exc}"
                ),
            )

    def _find_container(
        self,
        resource_id: str,
    ) -> Container:
        containers = self._client.containers.list(all=True)

        for container in containers:
            if container.id == resource_id:
                return container

            if container.name == resource_id:
                return container

        raise NotFound(
            f"Container '{resource_id}' was not found."
        )

    def _build_container_state_evidence(
        self,
        resource_id: str,
        container: Container,
        observed_at: datetime,
    ) -> SecurityEvidence:
        image = container.image

        image_id = ""
        image_tags: list[str] = []

        if image is not None:
            image_id = str(image.id)
            image_tags = [
                str(tag)
                for tag in image.tags
            ]

        return SecurityEvidence(
            evidence_id=str(uuid4()),
            resource_id=resource_id,
            category=SecurityCategory.CONTAINER,
            source=SecuritySource.DOCKER,
            evidence_type="container_runtime_configuration",
            observed_at=observed_at,
            evidence_available=True,
            details={
                "container_name": str(container.name),
                "status": str(container.status),
                "image_id": image_id,
                "image_tags": ",".join(image_tags),
            },
        )

    def _build_network_evidence(
        self,
        resource_id: str,
        container: Container,
        observed_at: datetime,
    ) -> SecurityEvidence:
        attrs: dict[str, Any] = container.attrs

        host_config: dict[str, Any] = attrs.get(
            "HostConfig",
            {},
        )

        network_settings: dict[str, Any] = attrs.get(
            "NetworkSettings",
            {},
        )

        ports: dict[str, Any] = network_settings.get(
            "Ports"
        ) or {}

        network_mode = str(
            host_config.get(
                "NetworkMode",
                "",
            )
        )

        published_ports: list[str] = []

        for container_port, bindings in ports.items():
            container_port_value = str(
                container_port
            )

            if not bindings:
                published_ports.append(
                    container_port_value
                )
                continue

            for binding in bindings:
                host_ip = str(
                    binding.get(
                        "HostIp",
                        "",
                    )
                )

                host_port = str(
                    binding.get(
                        "HostPort",
                        "",
                    )
                )

                published_ports.append(
                    f"{host_ip}:{host_port}"
                    f"->{container_port_value}"
                )

        published_ports_value = ",".join(
            published_ports
        )

        return SecurityEvidence(
            evidence_id=str(uuid4()),
            resource_id=resource_id,
            category=SecurityCategory.NETWORK,
            source=SecuritySource.DOCKER,
            evidence_type="container_network_configuration",
            observed_at=observed_at,
            evidence_available=True,
            details={
                "network_mode": network_mode,
                "published_ports": published_ports_value,
            },
        )

    def _build_privilege_evidence(
        self,
        resource_id: str,
        container: Container,
        observed_at: datetime,
    ) -> SecurityEvidence:
        attrs: dict[str, Any] = container.attrs

        host_config: dict[str, Any] = attrs.get(
            "HostConfig",
            {},
        )

        privileged = bool(
            host_config.get(
                "Privileged",
                False,
            )
        )

        cap_add: list[Any] = (
            host_config.get("CapAdd")
            or []
        )

        cap_drop: list[Any] = (
            host_config.get("CapDrop")
            or []
        )

        cap_add_value = ",".join(
            str(value)
            for value in cap_add
        )

        cap_drop_value = ",".join(
            str(value)
            for value in cap_drop
        )

        return SecurityEvidence(
            evidence_id=str(uuid4()),
            resource_id=resource_id,
            category=SecurityCategory.ACCESS_CONTROL,
            source=SecuritySource.DOCKER,
            evidence_type="container_privilege_configuration",
            observed_at=observed_at,
            evidence_available=True,
            details={
                "privileged": str(
                    privileged
                ).lower(),
                "cap_add": cap_add_value,
                "cap_drop": cap_drop_value,
            },
        )

    def _build_mount_evidence(
        self,
        resource_id: str,
        container: Container,
        observed_at: datetime,
    ) -> SecurityEvidence:
        attrs: dict[str, Any] = container.attrs

        mounts: list[dict[str, Any]] = (
            attrs.get("Mounts")
            or []
        )

        mount_descriptions: list[str] = []

        for mount in mounts:
            source = str(
                mount.get(
                    "Source",
                    "",
                )
            )

            destination = str(
                mount.get(
                    "Destination",
                    "",
                )
            )

            mode = str(
                mount.get(
                    "Mode",
                    "",
                )
            )

            mount_descriptions.append(
                f"{source}->{destination}:{mode}"
            )

        mount_value = ",".join(
            mount_descriptions
        )

        return SecurityEvidence(
            evidence_id=str(uuid4()),
            resource_id=resource_id,
            category=SecurityCategory.CONTAINER,
            source=SecuritySource.DOCKER,
            evidence_type="container_mount_configuration",
            observed_at=observed_at,
            evidence_available=True,
            details={
                "mount_count": str(
                    len(mounts)
                ),
                "mounts": mount_value,
            },
        )

    def close(self) -> None:
        self._client.close()