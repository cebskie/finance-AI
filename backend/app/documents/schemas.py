from datetime import datetime

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: str
    original_filename: str
    mime_type: str
    size_bytes: int
    status: str
    storage_bucket: str
    storage_key: str
    created_at: datetime


class DocumentProcessingReportPage(BaseModel):
    page_number: int
    document_type: str | None
    classification_confidence: int | None
    ocr_text_length: int
    segmentation_object_count: int
    extraction_json: dict | None


class DocumentProcessingReportResponse(BaseModel):
    document_id: str
    original_filename: str
    page_count: int
    pages: list[DocumentProcessingReportPage]
