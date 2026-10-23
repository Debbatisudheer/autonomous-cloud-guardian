from __future__ import annotations

import docker

from guardian.infrastructure.docker.security import (
    DockerSecurityEvidenceProvider,
)


def main() -> None:
    print("PHASE 7.2 — SECURITY EVIDENCE COLLECTION VALIDATION")
    print("=" * 64)

    client = docker.from_env()
    client.ping()

    print("DOCKER CONNECTIVITY PASS")

    containers = client.containers.list(all=True)

    if not containers:
        raise RuntimeError(
            "No Docker containers were discovered."
        )

    print(
        f"REAL DOCKER DISCOVERY PASS "
        f"({len(containers)} containers discovered)"
    )

    target = next(
        (
            container
            for container in containers
            if container.status == "running"
        ),
        None,
    )

    if target is None:
        raise RuntimeError(
            "No running Docker container is available for validation."
        )

    print(
        "CONTROLLED VALIDATION RESOURCE: "
        f"{target.name} ({target.id[:12]})"
    )

    provider = DockerSecurityEvidenceProvider(client)

    try:
        result = provider.collect_for_resource(target.id)

        if not result.evidence_available:
            raise RuntimeError(
                "Docker security evidence was unexpectedly unavailable: "
                f"{result.reason}"
            )

        if not result.evidence:
            raise RuntimeError(
                "Docker security provider returned no evidence."
            )

        print("REAL SECURITY EVIDENCE COLLECTION PASS")

        resource_ids = {
            evidence.resource_id
            for evidence in result.evidence
        }

        if resource_ids != {target.id}:
            raise RuntimeError(
                "Security evidence resource correlation failed."
            )

        print("EVIDENCE RESOURCE CORRELATION PASS")

        for evidence in result.evidence:
            if not evidence.evidence_available:
                raise RuntimeError(
                    "Collected evidence was marked unavailable."
                )

            if not evidence.evidence_id:
                raise RuntimeError(
                    "Collected evidence has no evidence ID."
                )

            if evidence.source.value != "docker":
                raise RuntimeError(
                    "Collected evidence has an unexpected source."
                )

            if not evidence.details:
                raise RuntimeError(
                    "Collected evidence contains no observed details."
                )

        print("SECURITY EVIDENCE INTEGRITY PASS")

        evidence_types = {
            evidence.evidence_type
            for evidence in result.evidence
        }

        required_types = {
            "container_runtime_configuration",
            "container_network_configuration",
            "container_privilege_configuration",
            "container_mount_configuration",
        }

        if not required_types.issubset(evidence_types):
            missing = required_types - evidence_types
            raise RuntimeError(
                f"Required Docker evidence types are missing: {missing}"
            )

        print("DOCKER SECURITY EVIDENCE COVERAGE PASS")

        unavailable_result = provider.collect_for_resource(
            "phase-7-2-resource-that-does-not-exist"
        )

        if unavailable_result.evidence_available:
            raise RuntimeError(
                "Missing Docker resource was incorrectly marked "
                "as evidence available."
            )

        if unavailable_result.evidence:
            raise RuntimeError(
                "Missing Docker resource unexpectedly produced evidence."
            )

        print("UNAVAILABLE RESOURCE HANDLING PASS")

        print()
        print("PHASE 7.2 BOUNDARY CHECK")
        print("------------------------")
        print("Real Docker security evidence: AVAILABLE")
        print("Security assessment:            NOT IMPLEMENTED")
        print("Risk scoring:                   NOT IMPLEMENTED")
        print("Recommendation:                 NOT IMPLEMENTED")
        print("Infrastructure action:          NONE")
        print("Automatic remediation:          NONE")
        print("Vulnerability claim:            NONE")
        print()
        print(
            "IMPORTANT: Evidence collected here represents "
            "directly observed Docker configuration."
        )
        print(
            "It does NOT by itself establish that a vulnerability exists."
        )
        print()
        print("PHASE 7.2 — COMPLETE: PASS")

    finally:
        client.close()


if __name__ == "__main__":
    main()