import logging
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings
from app.documents.models import Document
from app.documents.repository import DocumentRepository
from app.pdf.page_splitter import PdfPageSplittingService
from app.segmentation.service import PageSegmentationService
from app.storage.service import ObjectStorageService

logger = logging.getLogger(__name__)


class UploadValidationError(ValueError):
    pass


class DocumentUploadService:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: DocumentRepository,
        storage: ObjectStorageService,
        page_splitter: PdfPageSplittingService,
        page_segmenter: PageSegmentationService,
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.storage = storage
        self.page_splitter = page_splitter
        self.page_segmenter = page_segmenter

    async def upload_pdf(self, file: UploadFile) -> Document:
        content = await file.read()
        self._validate_pdf(file, content)

        document_id = str(uuid4())
        object_key = f"documents/{document_id}/{Path(file.filename or 'document.pdf').name}"

        logger.info(
            "Uploading PDF to object storage",
            extra={
                "document_id": document_id,
                "original_filename": file.filename,
                "size_bytes": len(content),
                "storage_bucket": self.settings.document_bucket,
                "storage_key": object_key,
            },
        )
        self.storage.upload_pdf(
            bucket_name=self.settings.document_bucket,
            object_key=object_key,
            content=content,
        )

        document = self.repository.create(
            document_id=document_id,
            original_filename=file.filename or "document.pdf",
            mime_type="application/pdf",
            size_bytes=len(content),
            storage_bucket=self.settings.document_bucket,
            storage_key=object_key,
        )

        logger.info(
            "PDF upload metadata persisted",
            extra={
                "document_id": document.id,
                "original_filename": document.original_filename,
                "size_bytes": document.size_bytes,
                "storage_bucket": document.storage_bucket,
                "storage_key": document.storage_key,
            },
        )
        document = self._split_uploaded_pdf(document)
        return document

    def _split_uploaded_pdf(self, document: Document) -> Document:
        document = self.repository.update_status(
            document=document,
            status="processing_pages",
        )
        logger.info(
            "Retrieving original PDF from object storage for page splitting",
            extra={
                "document_id": document.id,
                "storage_bucket": document.storage_bucket,
                "storage_key": document.storage_key,
            },
        )

        try:
            pdf_content = self.storage.get_object_bytes(
                bucket_name=document.storage_bucket,
                object_key=document.storage_key,
            )
            pages = self.page_splitter.split_pdf(
                document=document,
                pdf_content=pdf_content,
            )
            document = self.repository.update_status(
                document=document,
                status="segmenting_pages",
            )
            segmented_object_count = 0
            for page in pages:
                segmented_object_count += len(self.page_segmenter.segment_page(page=page))
        except Exception:
            logger.exception(
                "PDF page processing failed after upload",
                extra={"document_id": document.id},
            )
            return self.repository.update_status(
                document=document,
                status="page_processing_failed",
            )

        logger.info(
            "PDF page images and segmented objects persisted",
            extra={
                "document_id": document.id,
                "page_count": len(pages),
                "segmented_object_count": segmented_object_count,
            },
        )
        return self.repository.update_status(
            document=document,
            status="segmentation_ready",
        )

    def _validate_pdf(self, file: UploadFile, content: bytes) -> None:
        filename = file.filename or ""
        if not filename.lower().endswith(".pdf"):
            raise UploadValidationError("Only .pdf files are supported.")

        if file.content_type != "application/pdf":
            raise UploadValidationError("File content type must be application/pdf.")

        if not content:
            raise UploadValidationError("Uploaded PDF cannot be empty.")

        if len(content) > self.settings.max_upload_bytes:
            raise UploadValidationError("Uploaded PDF exceeds the configured size limit.")

        if not content.startswith(b"%PDF-"):
            raise UploadValidationError("Uploaded file is not a valid PDF.")
