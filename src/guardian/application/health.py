from dataclasses import dataclass


@dataclass(frozen=True)
class HealthStatus:
    status: str
    service: str


class HealthService:
    """Application-level health information."""

    def get_status(self) -> HealthStatus:
        return HealthStatus(
            status="healthy",
            service="autonomous-cloud-guardian",
        )