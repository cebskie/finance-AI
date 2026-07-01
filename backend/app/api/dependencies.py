from collections.abc import Generator

from fastapi import Depends
from supabase import Client
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.supabase import create_supabase_client
from app.core.redis import create_redis_client
from app.classification.service import PageClassificationService
from app.documents.repository import (
    DocumentObjectRepository,
    DocumentPageRepository,
    DocumentRepository,
)
from app.documents.service import DocumentUploadService
from app.extraction.service import StructuredExtractionService
from app.ocr.service import FullPageOcrService
from app.pdf.page_splitter import PdfPageSplittingService
from app.pipeline.page_processing import PageProcessingPipeline
from app.preprocessing.service import PagePreprocessingService
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


def get_supabase_client(
    settings: Settings = Depends(get_app_settings),
) -> Client:
    return create_supabase_client(settings)


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
    supabase_client: Client = Depends(get_supabase_client),
) -> ObjectStorageService:
    return ObjectStorageService(supabase_client)


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


def get_page_preprocessing_service(
    settings: Settings = Depends(get_app_settings),
    page_repository: DocumentPageRepository = Depends(get_document_page_repository),
    storage: ObjectStorageService = Depends(get_object_storage_service),
) -> PagePreprocessingService:
    return PagePreprocessingService(
        settings=settings,
        page_repository=page_repository,
        storage=storage,
    )


def get_full_page_ocr_service(
    settings: Settings = Depends(get_app_settings),
    page_repository: DocumentPageRepository = Depends(get_document_page_repository),
) -> FullPageOcrService:
    return FullPageOcrService(
        settings=settings,
        page_repository=page_repository,
    )


def get_page_classification_service(
    settings: Settings = Depends(get_app_settings),
) -> PageClassificationService:
    return PageClassificationService(settings=settings)


def get_structured_extraction_service() -> StructuredExtractionService:
    return StructuredExtractionService()


def get_page_processing_pipeline(
    settings: Settings = Depends(get_app_settings),
    page_repository: DocumentPageRepository = Depends(get_document_page_repository),
    preprocessor: PagePreprocessingService = Depends(get_page_preprocessing_service),
    ocr: FullPageOcrService = Depends(get_full_page_ocr_service),
    classifier: PageClassificationService = Depends(get_page_classification_service),
    extractor: StructuredExtractionService = Depends(get_structured_extraction_service),
    segmenter: PageSegmentationService = Depends(get_page_segmentation_service),
) -> PageProcessingPipeline:
    return PageProcessingPipeline(
        settings=settings,
        page_repository=page_repository,
        preprocessor=preprocessor,
        ocr=ocr,
        classifier=classifier,
        extractor=extractor,
        segmenter=segmenter,
    )


def get_document_upload_service(
    settings: Settings = Depends(get_app_settings),
    repository: DocumentRepository = Depends(get_document_repository),
    storage: ObjectStorageService = Depends(get_object_storage_service),
    page_splitter: PdfPageSplittingService = Depends(get_pdf_page_splitting_service),
    page_pipeline: PageProcessingPipeline = Depends(get_page_processing_pipeline),
) -> DocumentUploadService:
    return DocumentUploadService(
        settings=settings,
        repository=repository,
        storage=storage,
        page_splitter=page_splitter,
        page_pipeline=page_pipeline,
    )
