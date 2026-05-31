import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from app.api.dependencies import get_document_upload_service
from app.core.config import Settings
from app.documents.service import DocumentUploadService, UploadValidationError


class FakeUploadFile:
    def __init__(
        self,
        *,
        filename: str = "statement.pdf",
        content_type: str = "application/pdf",
        content: bytes = b"%PDF-1.7\ncontent",
    ) -> None:
        self.filename = filename
        self.content_type = content_type
        self._content = content

    async def read(self) -> bytes:
        return self._content


class FakeStorage:
    def __init__(self) -> None:
        self.uploads = []

    def upload_pdf(self, *, bucket_name: str, object_key: str, content: bytes) -> None:
        self.uploads.append(
            {
                "bucket_name": bucket_name,
                "object_key": object_key,
                "content": content,
            }
        )


class FakeRepository:
    def __init__(self) -> None:
        self.documents = []

    def create(
        self,
        *,
        document_id: str,
        original_filename: str,
        mime_type: str,
        size_bytes: int,
        storage_bucket: str,
        storage_key: str,
    ):
        document = SimpleNamespace(
            id=document_id,
            original_filename=original_filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            status="uploaded",
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            created_at=datetime.now(UTC),
        )
        self.documents.append(document)
        return document


def build_service(
    *,
    max_upload_bytes: int = 1024,
) -> tuple[DocumentUploadService, FakeRepository, FakeStorage]:
    settings = Settings(
        DOCUMENT_BUCKET="documents",
        MAX_UPLOAD_BYTES=max_upload_bytes,
    )
    repository = FakeRepository()
    storage = FakeStorage()
    service = DocumentUploadService(
        settings=settings,
        repository=repository,
        storage=storage,
    )
    return service, repository, storage


def test_upload_pdf_stores_file_and_persists_metadata():
    service, repository, storage = build_service()

    document = asyncio.run(service.upload_pdf(FakeUploadFile()))

    assert document.status == "uploaded"
    assert document.mime_type == "application/pdf"
    assert document.storage_bucket == "documents"
    assert document.storage_key.startswith(f"documents/{document.id}/")
    assert len(storage.uploads) == 1
    assert len(repository.documents) == 1


def test_upload_pdf_rejects_non_pdf_extension():
    service, _, _ = build_service()

    with pytest.raises(UploadValidationError, match="Only .pdf files"):
        asyncio.run(service.upload_pdf(FakeUploadFile(filename="statement.txt")))


def test_upload_pdf_rejects_invalid_magic_bytes():
    service, _, _ = build_service()

    with pytest.raises(UploadValidationError, match="not a valid PDF"):
        asyncio.run(service.upload_pdf(FakeUploadFile(content=b"not a pdf")))


def test_upload_pdf_rejects_oversized_file():
    service, _, _ = build_service(max_upload_bytes=8)

    with pytest.raises(UploadValidationError, match="size limit"):
        asyncio.run(service.upload_pdf(FakeUploadFile(content=b"%PDF-1.7\noversized")))


class SuccessfulUploadService:
    async def upload_pdf(self, file):
        return SimpleNamespace(
            id="doc-1",
            original_filename=file.filename,
            mime_type="application/pdf",
            size_bytes=14,
            status="uploaded",
            storage_bucket="documents",
            storage_key="documents/doc-1/statement.pdf",
            created_at=datetime.now(UTC),
        )


class ValidationFailureUploadService:
    async def upload_pdf(self, file):
        raise UploadValidationError("Only .pdf files are supported.")


def test_upload_document_endpoint(client: TestClient):
    client.app.dependency_overrides[get_document_upload_service] = lambda: SuccessfulUploadService()

    response = client.post(
        "/api/v1/documents",
        files={"file": ("statement.pdf", b"%PDF-1.7\nbody", "application/pdf")},
    )

    assert response.status_code == 201
    assert response.json()["id"] == "doc-1"
    assert response.json()["status"] == "uploaded"

    client.app.dependency_overrides.clear()


def test_upload_document_endpoint_validation_error(client: TestClient):
    client.app.dependency_overrides[get_document_upload_service] = (
        lambda: ValidationFailureUploadService()
    )

    response = client.post(
        "/api/v1/documents",
        files={"file": ("statement.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only .pdf files are supported."

    client.app.dependency_overrides.clear()
