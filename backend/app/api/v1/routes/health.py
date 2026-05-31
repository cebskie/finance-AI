from fastapi import APIRouter, Depends, HTTPException, status
from minio import Minio
from pydantic import BaseModel
from redis import Redis
from redis.exceptions import RedisError

from app.api.dependencies import get_app_settings, get_minio_client, get_redis_client
from app.core.config import Settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str


class DependencyHealthResponse(BaseModel):
    status: str
    service: str


@router.get("", response_model=HealthResponse)
def health_check(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/redis", response_model=DependencyHealthResponse)
def redis_health_check(
    redis_client: Redis = Depends(get_redis_client),
) -> DependencyHealthResponse:
    try:
        is_available = redis_client.ping()
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unavailable", "service": "redis"},
        ) from exc

    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unavailable", "service": "redis"},
        )

    return DependencyHealthResponse(status="ok", service="redis")


@router.get("/minio", response_model=DependencyHealthResponse)
def minio_health_check(
    minio_client: Minio = Depends(get_minio_client),
) -> DependencyHealthResponse:
    try:
        minio_client.list_buckets()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unavailable", "service": "minio"},
        ) from exc

    return DependencyHealthResponse(status="ok", service="minio")
