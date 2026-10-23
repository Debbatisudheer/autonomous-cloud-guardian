from fastapi import FastAPI

from guardian.api.routes.resources import router as resources_router
from guardian.application.health import HealthService
from guardian.config.settings import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description=(
            "Evidence-driven autonomous cloud optimization, "
            "security and reliability control plane."
        ),
    )

    health_service = HealthService()

    @app.get("/health")
    def health() -> dict[str, str]:
        result = health_service.get_status()

        return {
            "status": result.status,
            "service": result.service,
            "environment": settings.environment,
        }

    app.include_router(resources_router)

    return app


app = create_app()