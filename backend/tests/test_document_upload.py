import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from app.api.dependencies import (
    get_document_object_repository,
    get_document_page_repository,
    get_document_repository,
    get_document_upload_service,
)
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
        self.objects = {}

    def upload_pdf(self, *, bucket_name: str, object_key: str, content: bytes) -> None:
        self.uploads.append(
            {
                "bucket_name": bucket_name,
                "object_key": object_key,
                "content": content,
            }
        )
        self.objects[(bucket_name, object_key)] = content

    def get_object_bytes(self, *, bucket_name: str, object_key: str) -> bytes:
        return self.objects[(bucket_name, object_key)]


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

    def update_status(self, *, document, status: str):
        document.status = status
        return document


class FakePageSplitter:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls = []

    def split_pdf(self, *, document, pdf_content: bytes):
        self.calls.append({"document": document, "pdf_content": pdf_content})
        if self.should_fail:
            raise RuntimeError("split failed")
        return [
            SimpleNamespace(
                id="page-1",
                document_id=document.id,
                page_number=1,
                storage_bucket="documents",
                storage_key=f"documents/{document.id}/pages/page-0001.png",
            )
        ]


class FakePagePipeline:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls = []

    def process_page(self, *, page):
        self.calls.append(page)
        if self.should_fail:
            raise RuntimeError("page pipeline failed")
        return SimpleNamespace(segmentation_object_count=1)


def build_service(
    *,
    max_upload_bytes: int = 1024,
    page_splitter_should_fail: bool = False,
    page_pipeline_should_fail: bool = False,
) -> tuple[DocumentUploadService, FakeRepository, FakeStorage, FakePageSplitter, FakePagePipeline]:
    settings = Settings(
        DOCUMENT_BUCKET="documents",
        MAX_UPLOAD_BYTES=max_upload_bytes,
    )
    repository = FakeRepository()
    storage = FakeStorage()
    page_splitter = FakePageSplitter(should_fail=page_splitter_should_fail)
    page_pipeline = FakePagePipeline(should_fail=page_pipeline_should_fail)
    service = DocumentUploadService(
        settings=settings,
        repository=repository,
        storage=storage,
        page_splitter=page_splitter,
        page_pipeline=page_pipeline,
    )
    return service, repository, storage, page_splitter, page_pipeline


def test_upload_pdf_stores_file_persists_metadata_splits_and_processes_pages():
    service, repository, storage, page_splitter, page_pipeline = build_service()

    document = asyncio.run(service.upload_pdf(FakeUploadFile()))

    assert document.status == "classification_ready"
    assert document.mime_type == "application/pdf"
    assert document.storage_bucket == "documents"
    assert document.storage_key.startswith(f"documents/{document.id}/")
    assert len(storage.uploads) == 1
    assert len(repository.documents) == 1
    assert len(page_splitter.calls) == 1
    assert len(page_pipeline.calls) == 1
    assert page_splitter.calls[0]["pdf_content"] == b"%PDF-1.7\ncontent"


def test_upload_pdf_marks_document_failed_when_page_splitting_fails():
    service, _, _, page_splitter, page_pipeline = build_service(page_splitter_should_fail=True)

    document = asyncio.run(service.upload_pdf(FakeUploadFile()))

    assert document.status == "page_processing_failed"
    assert len(page_splitter.calls) == 1
    assert len(page_pipeline.calls) == 0


def test_upload_pdf_marks_document_failed_when_page_pipeline_fails():
    service, _, _, page_splitter, page_pipeline = build_service(
        page_pipeline_should_fail=True,
    )

    document = asyncio.run(service.upload_pdf(FakeUploadFile()))

    assert document.status == "page_processing_failed"
    assert len(page_splitter.calls) == 1
    assert len(page_pipeline.calls) == 1


def test_upload_pdf_rejects_non_pdf_extension():
    service, _, _, _, _ = build_service()

    with pytest.raises(UploadValidationError, match="Only .pdf files"):
        asyncio.run(service.upload_pdf(FakeUploadFile(filename="statement.txt")))


def test_upload_pdf_rejects_invalid_magic_bytes():
    service, _, _, _, _ = build_service()

    with pytest.raises(UploadValidationError, match="not a valid PDF"):
        asyncio.run(service.upload_pdf(FakeUploadFile(content=b"not a pdf")))


def test_upload_pdf_rejects_oversized_file():
    service, _, _, _, _ = build_service(max_upload_bytes=8)

    with pytest.raises(UploadValidationError, match="size limit"):
        asyncio.run(service.upload_pdf(FakeUploadFile(content=b"%PDF-1.7\noversized")))


class SuccessfulUploadService:
    async def upload_pdf(self, file):
        return SimpleNamespace(
            id="doc-1",
            original_filename=file.filename,
            mime_type="application/pdf",
            size_bytes=14,
            status="classification_ready",
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
    assert response.json()["status"] == "classification_ready"

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


class FakeReportDocumentRepository:
    def __init__(self, document=None) -> None:
        self.document = document

    def get_by_id(self, *, document_id: str):
        return self.document


class FakeReportPageRepository:
    def __init__(self, pages) -> None:
        self.pages = pages

    def list_by_document_id(self, *, document_id: str):
        return self.pages


class FakeReportObjectRepository:
    def __init__(self, counts) -> None:
        self.counts = counts

    def count_by_page_ids(self, *, page_ids: list[str]):
        return {page_id: self.counts.get(page_id, 0) for page_id in page_ids}


def test_processing_report_endpoint_returns_page_debug_summary(client: TestClient):
    document = SimpleNamespace(id="doc-1", original_filename="statement.pdf")
    pages = [
        SimpleNamespace(
            id="page-1",
            page_number=1,
            document_type="vendor_invoice",
            classification_confidence=91,
            ocr_text="Invoice total 100",
            classification_metadata={
                "extraction_json": {
                    "document_type": "vendor_invoice",
                    "fields": [{"name": "total", "value": "100"}],
                }
            },
            ocr_metadata=None,
            preprocessing_metadata=None,
            segmentation_metadata=None,
        ),
        SimpleNamespace(
            id="page-2",
            page_number=2,
            document_type=None,
            classification_confidence=None,
            ocr_text=None,
            classification_metadata=None,
            ocr_metadata=None,
            preprocessing_metadata=None,
            segmentation_metadata=None,
        ),
    ]

    client.app.dependency_overrides[get_document_repository] = lambda: FakeReportDocumentRepository(
        document
    )
    client.app.dependency_overrides[get_document_page_repository] = lambda: FakeReportPageRepository(
        pages
    )
    client.app.dependency_overrides[get_document_object_repository] = (
        lambda: FakeReportObjectRepository({"page-1": 3})
    )

    response = client.get("/api/v1/documents/doc-1/processing-report")

    assert response.status_code == 200
    assert response.json() == {
        "document_id": "doc-1",
        "original_filename": "statement.pdf",
        "page_count": 2,
        "pages": [
            {
                "page_number": 1,
                "document_type": "vendor_invoice",
                "classification_confidence": 91,
                "ocr_text_length": 17,
                "segmentation_object_count": 3,
                "extraction_json": {
                    "document_type": "vendor_invoice",
                    "fields": [{"name": "total", "value": "100"}],
                },
            },
            {
                "page_number": 2,
                "document_type": None,
                "classification_confidence": None,
                "ocr_text_length": 0,
                "segmentation_object_count": 0,
                "extraction_json": None,
            },
        ],
    }

    client.app.dependency_overrides.clear()


def test_processing_report_endpoint_returns_404_for_unknown_document(client: TestClient):
    client.app.dependency_overrides[get_document_repository] = lambda: FakeReportDocumentRepository()
    client.app.dependency_overrides[get_document_page_repository] = lambda: FakeReportPageRepository(
        []
    )
    client.app.dependency_overrides[get_document_object_repository] = (
        lambda: FakeReportObjectRepository({})
    )

    response = client.get("/api/v1/documents/missing/processing-report")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."

    client.app.dependency_overrides.clear()
