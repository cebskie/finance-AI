from collections.abc import Generator

from fastapi import Depends
from minio import Minio
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.minio import create_minio_client
from app.core.redis import create_redis_client
from app.documents.repository import (
    DocumentObjectRepository,
    DocumentPageRepository,
    DocumentRepository,
)
from app.documents.service import DocumentUploadService
from app.pdf.page_splitter import PdfPageSplittingService
from app.segmentation.service import PageSegmentationService
from app.storage.service import ObjectStorageService


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


def get_document_repository(
    session: Session = Depends(get_db_session),
) -> DocumentRepository:
    return DocumentRepository(session)


def get_document_page_repository(
    session: Session = Depends(get_db_session),
) -> DocumentPageRepository:
    return DocumentPageRepository(session)


def get_document_object_repository(
    session: Session = Depends(get_db_session),
) -> DocumentObjectRepository:
    return DocumentObjectRepository(session)


def get_object_storage_service(
    minio_client: Minio = Depends(get_minio_client),
) -> ObjectStorageService:
    return ObjectStorageService(minio_client)


def get_pdf_page_splitting_service(
    settings: Settings = Depends(get_app_settings),
    page_repository: DocumentPageRepository = Depends(get_document_page_repository),
    storage: ObjectStorageService = Depends(get_object_storage_service),
) -> PdfPageSplittingService:
    return PdfPageSplittingService(
        settings=settings,
        page_repository=page_repository,
        storage=storage,
    )


def get_page_segmentation_service(
    settings: Settings = Depends(get_app_settings),
    object_repository: DocumentObjectRepository = Depends(get_document_object_repository),
    storage: ObjectStorageService = Depends(get_object_storage_service),
) -> PageSegmentationService:
    return PageSegmentationService(
        settings=settings,
        object_repository=object_repository,
        storage=storage,
    )


def get_document_upload_service(
    settings: Settings = Depends(get_app_settings),
    repository: DocumentRepository = Depends(get_document_repository),
    storage: ObjectStorageService = Depends(get_object_storage_service),
    page_splitter: PdfPageSplittingService = Depends(get_pdf_page_splitting_service),
    page_segmenter: PageSegmentationService = Depends(get_page_segmentation_service),
) -> DocumentUploadService:
    return DocumentUploadService(
        settings=settings,
        repository=repository,
        storage=storage,
        page_splitter=page_splitter,
        page_segmenter=page_segmenter,
    )
