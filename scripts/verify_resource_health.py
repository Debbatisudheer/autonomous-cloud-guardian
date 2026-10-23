from __future__ import annotations

import docker

from guardian.application.resource_health import ResourceHealthAssessor
from guardian.infrastructure.docker.discovery import DockerDiscovery


def main() -> None:
    client = docker.from_env()

    discovery = DockerDiscovery(client)
    assessor = ResourceHealthAssessor()

    resources = discovery.discover()
    observations = assessor.assess_all(resources)

    print(f"Resources discovered: {len(resources)}")
    print(f"Health observations: {len(observations)}")
    print()

    for observation in observations:
        resource = next(
            resource
            for resource in resources
            if resource.id == observation.resource_id
        )

        print(
            f"{resource.name} | "
            f"provider={resource.provider.value} | "
            f"type={resource.resource_type} | "
            f"status={observation.status.value} | "
            f"health={observation.health.value}"
        )
        print(f"  reason={observation.reason}")


if __name__ == "__main__":
    main()