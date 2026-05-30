from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_app_settings
from app.core.config import Settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str


@router.get("", response_model=HealthResponse)
def health_check(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
