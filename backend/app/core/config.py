from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "Finance AI System"
    app_version: str = "0.1.0"
    debug: bool = True
    environment: str = "development"

    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str

    supabase_url: str
    supabase_service_role_key: str
    document_bucket: str = "documents"

    # Logging
    log_level: str = "INFO"

    # OCR
    ocr_language: str = "eng"
    ocr_min_confidence: float = 0.5
    tesseract_path: str = ""
    poppler_path: str = ""

    # Classification
    classification_min_confidence: float = 0.5
    classification_rules_path: str = ""

    # Upload
    max_upload_bytes: int = 10485760

    # PDF
    pdf_split_dpi: int = 200

    # Segmentation
    segmentation_threshold: int = 245
    segmentation_min_area: int = 5000
    segmentation_merge_padding: int = 24
    segmentation_fallback_min_regions: int = 2

    # Preprocessing
    preprocessed_image_suffix: str = "_preprocessed.png"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # Redis
    redis_url: str = "redis://localhost:6379"

@lru_cache
def get_settings():
    return Settings()