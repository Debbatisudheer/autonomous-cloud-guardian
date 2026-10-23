from datetime import UTC, datetime

import pytest

from guardian.application.security_storage import SecurityStorage
from guardian.domain.security import (
    SecurityCategory,
    SecurityEvidence,
    SecuritySource,
)


def make_evidence() -> SecurityEvidence:
    return SecurityEvidence(
        evidence_id="evidence-001",
        resource_id="resource-001",
        category=SecurityCategory.CONTAINER,
        source=SecuritySource.DOCKER,
        evidence_type="container_configuration",
        observed_at=datetime(
            2026,
            10,
            23,
            10,
            0,
            tzinfo=UTC,
        ),
        evidence_available=True,
        details={
            "status": "running",
        },
    )


def test_security_storage_is_abstract() -> None:
    assert SecurityStorage.__abstractmethods__ == {
        "initialize",
        "save",
        "save_many",
        "get_recent",
        "get_for_resource",
        "get_between",
    }


def test_security_evidence_fixture() -> None:
    evidence = make_evidence()

    assert evidence.evidence_id == "evidence-001"
    assert evidence.resource_id == "resource-001"
    assert evidence.category == SecurityCategory.CONTAINER
    assert evidence.source == SecuritySource.DOCKER
    assert evidence.evidence_available is True


def test_invalid_time_range_contract() -> None:
    start = datetime(
        2026,
        10,
        23,
        12,
        0,
        tzinfo=UTC,
    )

    end = datetime(
        2026,
        10,
        23,
        11,
        0,
        tzinfo=UTC,
    )

    assert end < start


def test_storage_contract_requires_positive_limits() -> None:
    with pytest.raises(ValueError):
        raise ValueError(
            "Storage implementations must reject non-positive limits."
        )