from guardian.application.health import HealthService


def test_health_service_returns_healthy_status() -> None:
    service = HealthService()

    result = service.get_status()

    assert result.status == "healthy"
    assert result.service == "autonomous-cloud-guardian"