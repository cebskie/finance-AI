import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import (
    get_document_object_repository,
    get_document_page_repository,
    get_document_repository,
    get_document_upload_service,
)
from app.documents.models import DocumentPage
from app.documents.repository import (
    DocumentObjectRepository,
    DocumentPageRepository,
    DocumentRepository,
)
from app.documents.schemas import DocumentProcessingReportResponse, DocumentUploadResponse
from app.documents.service import DocumentUploadService, UploadValidationError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentUploadService = Depends(get_document_upload_service),
) -> DocumentUploadResponse:
    try:
        document = await service.upload_pdf(file)
    except UploadValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        logger.exception("PDF upload failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload failed.",
        )

    return DocumentUploadResponse(
        id=document.id,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        size_bytes=document.size_bytes,
        status=document.status,
        storage_bucket=document.storage_bucket,
        storage_key=document.storage_key,
        created_at=document.created_at,
    )


@router.get(
    "/{document_id}/processing-report",
    response_model=DocumentProcessingReportResponse,
)
def get_processing_report(
    document_id: str,
    document_repository: DocumentRepository = Depends(get_document_repository),
    page_repository: DocumentPageRepository = Depends(get_document_page_repository),
    object_repository: DocumentObjectRepository = Depends(get_document_object_repository),
) -> DocumentProcessingReportResponse:
    document = document_repository.get_by_id(document_id=document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    pages = page_repository.list_by_document_id(document_id=document_id)
    object_counts = object_repository.count_by_page_ids(page_ids=[page.id for page in pages])

    return DocumentProcessingReportResponse(
        document_id=document.id,
        original_filename=document.original_filename,
        page_count=len(pages),
        pages=[
            {
                "page_number": page.page_number,
                "document_type": page.document_type,
                "classification_confidence": page.classification_confidence,
                "ocr_text_length": len(page.ocr_text or ""),
                "segmentation_object_count": object_counts.get(page.id, 0),
                "extraction_json": _get_extraction_json(page),
            }
            for page in pages
        ],
    )


def _get_extraction_json(page: DocumentPage) -> dict | None:
    for metadata in (
        page.classification_metadata,
        page.ocr_metadata,
        page.preprocessing_metadata,
        page.segmentation_metadata,
    ):
        if isinstance(metadata, dict) and isinstance(metadata.get("extraction_json"), dict):
            return metadata["extraction_json"]
    return None
