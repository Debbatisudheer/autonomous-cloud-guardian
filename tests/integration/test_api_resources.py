from fastapi.testclient import TestClient

from guardian.api.app import app

client = TestClient(app)


def test_list_resources_endpoint() -> None:
    response = client.get("/resources")

    assert response.status_code == 200

    resources = response.json()

    assert isinstance(resources, list)

    for resource in resources:
        assert "id" in resource
        assert "name" in resource
        assert "resource_type" in resource
        assert "provider" in resource
        assert "status" in resource
        assert "health" in resource


def test_get_resource_endpoint() -> None:
    list_response = client.get("/resources")

    assert list_response.status_code == 200

    resources = list_response.json()

    assert resources

    resource_id = resources[0]["id"]

    response = client.get(f"/resources/{resource_id}")

    assert response.status_code == 200

    resource = response.json()

    assert resource["id"] == resource_id


def test_get_resource_returns_404_for_unknown_resource() -> None:
    response = client.get("/resources/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource 'does-not-exist' was not found.",
    }


def test_get_resource_state_endpoint() -> None:
    list_response = client.get("/resources")

    assert list_response.status_code == 200

    resources = list_response.json()

    assert resources

    resource_id = resources[0]["id"]

    response = client.get(f"/resources/{resource_id}/state")

    assert response.status_code == 200

    state = response.json()

    assert state["resource_id"] == resource_id
    assert "status" in state
    assert "health" in state
    assert "observed_at" in state
    assert "attributes" in state


def test_get_resource_state_returns_404_for_unknown_resource() -> None:
    response = client.get("/resources/does-not-exist/state")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource 'does-not-exist' was not found.",
    }


def test_get_resource_health_endpoint() -> None:
    list_response = client.get("/resources")

    assert list_response.status_code == 200

    resources = list_response.json()

    assert resources

    resource_id = resources[0]["id"]

    response = client.get(f"/resources/{resource_id}/health")

    assert response.status_code == 200

    health = response.json()

    assert health["resource_id"] == resource_id
    assert "status" in health
    assert "health" in health
    assert "observed_at" in health
    assert "reason" in health


def test_get_resource_health_returns_404_for_unknown_resource() -> None:
    response = client.get("/resources/does-not-exist/health")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource 'does-not-exist' was not found.",
    }


def test_get_resource_relationships_endpoint() -> None:
    list_response = client.get("/resources")

    assert list_response.status_code == 200

    resources = list_response.json()

    assert resources

    resource_id = resources[0]["id"]

    response = client.get(
        f"/resources/{resource_id}/relationships"
    )

    assert response.status_code == 200

    relationships = response.json()

    assert isinstance(relationships, list)


def test_get_resource_relationships_returns_404_for_unknown_resource() -> None:
    response = client.get(
        "/resources/does-not-exist/relationships"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Resource 'does-not-exist' was not found.",
    }