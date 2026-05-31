from io import BytesIO
from types import SimpleNamespace

from PIL import Image, ImageDraw

from app.core.config import Settings
from app.segmentation.service import PageSegmentationService


class FakeStorage:
    def __init__(self, page_image: bytes) -> None:
        self.page_image = page_image
        self.uploads = []

    def get_object_bytes(self, *, bucket_name: str, object_key: str) -> bytes:
        assert bucket_name == "documents"
        assert object_key == "documents/doc-1/pages/page-0001.png"
        return self.page_image

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


class FakeObjectRepository:
    def __init__(self) -> None:
        self.objects = []

    def create(
        self,
        *,
        page_id: str,
        object_id: str,
        bounding_box: dict[str, int],
        image_storage_bucket: str,
        image_storage_key: str,
        processing_status: str,
    ):
        document_object = SimpleNamespace(
            page_id=page_id,
            object_id=object_id,
            bounding_box=bounding_box,
            image_storage_bucket=image_storage_bucket,
            image_storage_key=image_storage_key,
            processing_status=processing_status,
        )
        self.objects.append(document_object)
        return document_object


def create_sample_page_with_two_document_regions() -> bytes:
    image = Image.new("RGB", (500, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 220, 260), outline="black", width=5)
    draw.rectangle((280, 40, 470, 240), outline="black", width=5)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def build_page():
    return SimpleNamespace(
        id="page-1",
        document_id="doc-1",
        page_number=1,
        storage_bucket="documents",
        storage_key="documents/doc-1/pages/page-0001.png",
    )


def test_segment_page_detects_multiple_document_regions_and_persists_crops():
    storage = FakeStorage(create_sample_page_with_two_document_regions())
    repository = FakeObjectRepository()
    service = PageSegmentationService(
        settings=Settings(
            DOCUMENT_BUCKET="documents",
            SEGMENTATION_MIN_AREA=1000,
            SEGMENTATION_MERGE_PADDING=8,
        ),
        object_repository=repository,
        storage=storage,
    )

    objects = service.segment_page(page=build_page())

    assert len(objects) == 2
    assert len(repository.objects) == 2
    assert len(storage.uploads) == 2
    assert storage.uploads[0]["content_type"] == "image/png"
    assert storage.uploads[0]["object_key"] == (
        "documents/doc-1/pages/page-0001/objects/object-0001.png"
    )
    assert objects[0].processing_status == "segmented"
    assert objects[0].bounding_box["x"] <= 22
    assert objects[0].bounding_box["y"] <= 22
    assert objects[0].bounding_box["width"] >= 198
    assert objects[0].bounding_box["height"] >= 238
    assert objects[1].bounding_box["x"] >= 278


def test_segment_page_produces_json_representation():
    storage = FakeStorage(create_sample_page_with_two_document_regions())
    repository = FakeObjectRepository()
    service = PageSegmentationService(
        settings=Settings(SEGMENTATION_MIN_AREA=1000, SEGMENTATION_MERGE_PADDING=8),
        object_repository=repository,
        storage=storage,
    )

    objects = service.segment_page(page=build_page())
    payload = service.to_json(objects)

    assert '"object_id": "object-0001"' in payload
    assert '"image_storage_key": "documents/doc-1/pages/page-0001/objects/object-0001.png"' in payload
    assert '"processing_status": "segmented"' in payload
