from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.config import Settings
from app.pdf.page_splitter import PdfPageSplittingService, PdfSplitError


class FakeImage:
    def __init__(self, *, width: int, height: int, payload: bytes) -> None:
        self.width = width
        self.height = height
        self.payload = payload

    def save(self, buffer, format: str) -> None:
        assert format == "PNG"
        buffer.write(self.payload)


class FakeStorage:
    def __init__(self) -> None:
        self.uploads = []

    def upload_bytes(
        self,
        *,
        bucket_name: str,
        object_key: str,
        content: bytes,
        content_type: str,
    ) -> None:
        self.uploads.append(
            {
                "bucket_name": bucket_name,
                "object_key": object_key,
                "content": content,
                "content_type": content_type,
            }
        )


class FakePageRepository:
    def __init__(self) -> None:
        self.pages = []

    def create(
        self,
        *,
        document_id: str,
        page_number: int,
        width: int,
        height: int,
        dpi: int,
        storage_bucket: str,
        storage_key: str,
        size_bytes: int,
    ):
        page = SimpleNamespace(
            document_id=document_id,
            page_number=page_number,
            width=width,
            height=height,
            dpi=dpi,
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            size_bytes=size_bytes,
        )
        self.pages.append(page)
        return page


def build_service() -> tuple[PdfPageSplittingService, FakePageRepository, FakeStorage]:
    repository = FakePageRepository()
    storage = FakeStorage()
    service = PdfPageSplittingService(
        settings=Settings(DOCUMENT_BUCKET="documents", PDF_SPLIT_DPI=150),
        page_repository=repository,
        storage=storage,
    )
    return service, repository, storage


def test_split_pdf_stores_page_images_and_persists_metadata():
    service, repository, storage = build_service()
    document = SimpleNamespace(id="doc-1")
    images = [
        FakeImage(width=100, height=200, payload=b"page-one"),
        FakeImage(width=300, height=400, payload=b"page-two"),
    ]

    with patch("app.pdf.page_splitter.convert_from_bytes", return_value=images) as converter:
        pages = service.split_pdf(document=document, pdf_content=b"%PDF-1.7\nbody")

    converter.assert_called_once()
    assert len(pages) == 2
    assert len(repository.pages) == 2
    assert len(storage.uploads) == 2
    assert storage.uploads[0]["content_type"] == "image/png"
    assert storage.uploads[0]["object_key"] == "documents/doc-1/pages/page-0001.png"
    assert pages[1].page_number == 2
    assert pages[1].width == 300
    assert pages[1].height == 400
    assert pages[1].dpi == 150


def test_split_pdf_wraps_conversion_errors():
    service, _, _ = build_service()
    document = SimpleNamespace(id="doc-1")

    with patch("app.pdf.page_splitter.convert_from_bytes", side_effect=RuntimeError("bad pdf")):
        with pytest.raises(PdfSplitError, match="Failed to split PDF"):
            service.split_pdf(document=document, pdf_content=b"invalid")
