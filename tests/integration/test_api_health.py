from fastapi.testclient import TestClient

from guardian.api.app import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "autonomous-cloud-guardian",
        "environment": "development",
    }