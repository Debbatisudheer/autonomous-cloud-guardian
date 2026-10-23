from datetime import UTC, datetime

import pytest

from guardian.domain.security import (
    SecurityCategory,
    SecurityEvidence,
    SecuritySource,
)
from guardian.infrastructure.postgres.security_storage import (
    PostgreSQLSecurityStorage,
)


def make_storage() -> PostgreSQLSecurityStorage:
    return PostgreSQLSecurityStorage()


def make_evidence() -> SecurityEvidence:
    return SecurityEvidence(
        evidence_id="test-evidence-001",
        resource_id="test-resource-001",
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
            "privileged": "false",
        },
    )


def test_storage_defaults() -> None:
    storage = make_storage()

    assert storage._host == "localhost"
    assert storage._port == 5433
    assert storage._database == "guardian"
    assert storage._user == "guardian"
    assert storage._password == "guardian_dev_password"


def test_storage_rejects_invalid_recent_limit() -> None:
    storage = make_storage()

    with pytest.raises(ValueError):
        storage.get_recent(limit=0)


def test_storage_rejects_invalid_resource_limit() -> None:
    storage = make_storage()

    with pytest.raises(ValueError):
        storage.get_for_resource(
            resource_id="resource-001",
            limit=0,
        )


def test_storage_rejects_empty_resource() -> None:
    storage = make_storage()

    with pytest.raises(ValueError):
        storage.get_for_resource(
            resource_id="",
            limit=100,
        )


def test_storage_rejects_invalid_time_window() -> None:
    storage = make_storage()

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

    with pytest.raises(ValueError):
        storage.get_between(
            start=start,
            end=end,
        )


def test_storage_rejects_invalid_time_window_limit() -> None:
    storage = make_storage()

    timestamp = datetime(
        2026,
        10,
        23,
        12,
        0,
        tzinfo=UTC,
    )

    with pytest.raises(ValueError):
        storage.get_between(
            start=timestamp,
            end=timestamp,
            limit=0,
        )


def test_evidence_fixture_is_valid() -> None:
    evidence = make_evidence()

    assert evidence.details["status"] == "running"
    assert evidence.details["privileged"] == "false"