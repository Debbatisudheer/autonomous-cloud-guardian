from datetime import UTC, datetime

from guardian.application.resource_health import ResourceHealthAssessor
from guardian.domain.resource import (
    Resource,
    ResourceHealth,
    ResourceProvider,
    ResourceStatus,
)


def make_resource(
    *,
    resource_id: str = "resource-1",
    status: ResourceStatus = ResourceStatus.RUNNING,
    health: ResourceHealth = ResourceHealth.UNKNOWN,
) -> Resource:
    timestamp = datetime.now(UTC)

    return Resource(
        id=resource_id,
        name="test-resource",
        resource_type="container",
        provider=ResourceProvider.DOCKER,
        status=status,
        health=health,
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_healthy_resource_is_reported_as_healthy() -> None:
    assessor = ResourceHealthAssessor()

    observation = assessor.assess(
        make_resource(
            health=ResourceHealth.HEALTHY,
        )
    )

    assert observation.health == ResourceHealth.HEALTHY
    assert "healthy" in observation.reason.lower()


def test_unhealthy_resource_is_reported_as_unhealthy() -> None:
    assessor = ResourceHealthAssessor()

    observation = assessor.assess(
        make_resource(
            health=ResourceHealth.UNHEALTHY,
        )
    )

    assert observation.health == ResourceHealth.UNHEALTHY
    assert "unhealthy" in observation.reason.lower()


def test_degraded_resource_is_reported_as_degraded() -> None:
    assessor = ResourceHealthAssessor()

    observation = assessor.assess(
        make_resource(
            health=ResourceHealth.DEGRADED,
        )
    )

    assert observation.health == ResourceHealth.DEGRADED
    assert "degraded" in observation.reason.lower()


def test_running_resource_without_healthcheck_remains_unknown() -> None:
    assessor = ResourceHealthAssessor()

    observation = assessor.assess(
        make_resource(
            status=ResourceStatus.RUNNING,
            health=ResourceHealth.UNKNOWN,
        )
    )

    assert observation.health == ResourceHealth.UNKNOWN
    assert "no provider healthcheck evidence" in observation.reason


def test_stopped_resource_without_health_evidence_remains_unknown() -> None:
    assessor = ResourceHealthAssessor()

    observation = assessor.assess(
        make_resource(
            status=ResourceStatus.STOPPED,
            health=ResourceHealth.UNKNOWN,
        )
    )

    assert observation.health == ResourceHealth.UNKNOWN
    assert "stopped" in observation.reason.lower()


def test_failed_resource_is_explained() -> None:
    assessor = ResourceHealthAssessor()

    observation = assessor.assess(
        make_resource(
            status=ResourceStatus.FAILED,
            health=ResourceHealth.UNKNOWN,
        )
    )

    assert observation.health == ResourceHealth.UNKNOWN
    assert "failed lifecycle state" in observation.reason


def test_assess_all_resources() -> None:
    assessor = ResourceHealthAssessor()

    resources = [
        make_resource(
            resource_id="healthy",
            health=ResourceHealth.HEALTHY,
        ),
        make_resource(
            resource_id="unknown",
            health=ResourceHealth.UNKNOWN,
        ),
    ]

    observations = assessor.assess_all(resources)

    assert len(observations) == 2
    assert observations[0].resource_id == "healthy"
    assert observations[0].health == ResourceHealth.HEALTHY
    assert observations[1].resource_id == "unknown"
    assert observations[1].health == ResourceHealth.UNKNOWN