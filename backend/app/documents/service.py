import logging
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import Settings
from app.documents.models import Document
from app.documents.repository import DocumentRepository
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
    ) -> None:
        self.settings = settings
        self.repository = repository
        self.storage = storage

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
        return document

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
