from collections.abc import Generator

from fastapi import Depends
from minio import Minio
from redis import Redis

from app.core.config import Settings, get_settings
from app.core.minio import create_minio_client
from app.core.redis import create_redis_client


def get_app_settings() -> Generator[Settings, None, None]:
    yield get_settings()


def get_redis_client(
    settings: Settings = Depends(get_app_settings),
) -> Generator[Redis, None, None]:
    client = create_redis_client(settings)
    try:
        yield client
    finally:
        client.close()


def get_minio_client(
    settings: Settings = Depends(get_app_settings),
) -> Minio:
    return create_minio_client(settings)
