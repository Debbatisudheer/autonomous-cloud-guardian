from unittest.mock import Mock

from guardian.infrastructure.docker.security import (
    DockerSecurityEvidenceProvider,
)


def test_docker_security_provider_returns_evidence() -> None:
    container = Mock()
    container.id = "container-001"
    container.name = "acg-test"
    container.status = "running"

    container.image.id = "sha256:test"
    container.image.tags = ["test:latest"]

    container.attrs = {
        "HostConfig": {
            "NetworkMode": "bridge",
            "Privileged": False,
            "CapAdd": [],
            "CapDrop": ["NET_RAW"],
        },
        "NetworkSettings": {
            "Ports": {
                "8080/tcp": [
                    {
                        "HostIp": "127.0.0.1",
                        "HostPort": "8080",
                    }
                ]
            }
        },
        "Mounts": [
            {
                "Source": "/tmp/source",
                "Destination": "/tmp/destination",
                "Mode": "rw",
            }
        ],
    }

    client = Mock()
    client.containers.list.return_value = [container]

    provider = DockerSecurityEvidenceProvider(client)

    result = provider.collect_for_resource("container-001")

    assert result.evidence_available is True
    assert len(result.evidence) == 4

    categories = {
        evidence.category
        for evidence in result.evidence
    }

    assert categories


def test_docker_security_provider_handles_missing_resource() -> None:
    client = Mock()
    client.containers.list.return_value = []

    provider = DockerSecurityEvidenceProvider(client)

    result = provider.collect_for_resource("missing-resource")

    assert result.evidence == []
    assert result.evidence_available is False