import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.dependencies import get_document_upload_service
from app.documents.schemas import DocumentUploadResponse
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
