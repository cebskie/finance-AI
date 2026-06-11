from io import BytesIO
from types import SimpleNamespace

from PIL import Image

from app.core.config import Settings
from app.preprocessing.service import PagePreprocessingService


class FakeStorage:
    def __init__(self, image_bytes: bytes) -> None:
        self.image_bytes = image_bytes
        self.uploads = []

    def get_object_bytes(self, *, bucket_name: str, object_key: str) -> bytes:
        return self.image_bytes

    def upload_bytes(self, *, bucket_name: str, object_key: str, content: bytes, content_type: str):
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
        self.preprocessed = []

    def mark_preprocessed(self, *, page, preprocessed_storage_key: str, preprocessing_metadata: dict):
        page.preprocessed_storage_key = preprocessed_storage_key
        page.preprocessing_metadata = preprocessing_metadata
        self.preprocessed.append(page)
        return page


def image_bytes(width: int, height: int) -> bytes:
    image = Image.new("RGB", (width, height), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_preprocess_page_rotates_landscape_page_and_persists_optimized_image():
    storage = FakeStorage(image_bytes(400, 200))
    repository = FakePageRepository()
    service = PagePreprocessingService(
        settings=Settings(DOCUMENT_BUCKET="documents"),
        page_repository=repository,
        storage=storage,
    )
    page = SimpleNamespace(
        id="page-1",
        document_id="doc-1",
        page_number=1,
        storage_bucket="documents",
        storage_key="documents/doc-1/pages/page-0001.png",
    )

    result = service.preprocess_page(page=page)

    assert result.storage_key == "documents/doc-1/pages/page-0001-preprocessed.png"
    assert result.metadata["orientation_degrees"] == 90
    assert result.metadata["rotation_corrected"] is True
    assert len(storage.uploads) == 1
    assert storage.uploads[0]["content_type"] == "image/png"
    assert repository.preprocessed[0].preprocessed_storage_key == result.storage_key
