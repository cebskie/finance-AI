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
