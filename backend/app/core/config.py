from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Finance AI Document Processing"
    app_version: str = "0.1.0"
    environment: str = Field(default="local", validation_alias="ENVIRONMENT")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    api_v1_prefix: str = "/api/v1"
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, validation_alias="MAX_UPLOAD_BYTES")
    pdf_split_dpi: int = Field(default=200, validation_alias="PDF_SPLIT_DPI")
    preprocessed_image_suffix: str = Field(
        default="-preprocessed.png",
        validation_alias="PREPROCESSED_IMAGE_SUFFIX",
    )
    ocr_language: str = Field(default="eng", validation_alias="OCR_LANGUAGE")
    ocr_min_confidence: float = Field(default=55.0, validation_alias="OCR_MIN_CONFIDENCE")
    classification_rules_path: str = Field(
        default="",
        validation_alias="CLASSIFICATION_RULES_PATH",
    )
    classification_min_confidence: float = Field(
        default=0.45,
        validation_alias="CLASSIFICATION_MIN_CONFIDENCE",
    )
    segmentation_fallback_min_regions: int = Field(
        default=2,
        validation_alias="SEGMENTATION_FALLBACK_MIN_REGIONS",
    )
    segmentation_threshold: int = Field(default=245, validation_alias="SEGMENTATION_THRESHOLD")
    segmentation_min_area: int = Field(default=5000, validation_alias="SEGMENTATION_MIN_AREA")
    segmentation_merge_padding: int = Field(
        default=24,
        validation_alias="SEGMENTATION_MERGE_PADDING",
    )

    postgres_user: str = Field(default="postgres", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", validation_alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="finance_ai", validation_alias="POSTGRES_DB")
    postgres_host: str = Field(default="postgres", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")

    redis_host: str = Field(default="redis", validation_alias="REDIS_HOST")
    redis_port: int = Field(default=6379, validation_alias="REDIS_PORT")

    minio_endpoint: str = Field(default="minio:9000", validation_alias="MINIO_ENDPOINT")
    minio_root_user: str = Field(default="minio", validation_alias="MINIO_ROOT_USER")
    minio_root_password: str = Field(default="minio123", validation_alias="MINIO_ROOT_PASSWORD")
    minio_secure: bool = Field(default=False, validation_alias="MINIO_SECURE")
    document_bucket: str = Field(default="documents", validation_alias="DOCUMENT_BUCKET")

    openrouter_api_key: str = Field(default="", validation_alias="OPENROUTER_API_KEY")
    tesseract_path: str = Field(default="/usr/bin/tesseract", validation_alias="TESSERACT_PATH")
    poppler_path: str = Field(default="", validation_alias="POPPLER_PATH")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()
