import json
import logging
from collections import deque
from dataclasses import dataclass
from io import BytesIO

from PIL import Image

from app.core.config import Settings
from app.documents.models import DocumentObject, DocumentPage
from app.documents.repository import DocumentObjectRepository
from app.storage.service import ObjectStorageService

logger = logging.getLogger(__name__)


class PageSegmentationError(RuntimeError):
    pass


@dataclass(frozen=True)
class BoundingBox:
    x: int
    y: int
    width: int
    height: int

    def to_dict(self) -> dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    @property
    def area(self) -> int:
        return self.width * self.height


class PageSegmentationService:
    def __init__(
        self,
        *,
        settings: Settings,
        object_repository: DocumentObjectRepository,
        storage: ObjectStorageService,
    ) -> None:
        self.settings = settings
        self.object_repository = object_repository
        self.storage = storage

    def segment_page(self, *, page: DocumentPage) -> list[DocumentObject]:
        logger.info(
            "Segmenting page image into document objects",
            extra={
                "page_id": page.id,
                "document_id": page.document_id,
                "page_number": page.page_number,
            },
        )

        try:
            page_image_bytes = self.storage.get_object_bytes(
                bucket_name=page.storage_bucket,
                object_key=page.storage_key,
            )
            image = Image.open(BytesIO(page_image_bytes)).convert("RGB")
            boxes = self.detect_regions(image)
        except Exception as exc:
            logger.exception(
                "Page segmentation failed",
                extra={"page_id": page.id, "document_id": page.document_id},
            )
            raise PageSegmentationError("Failed to segment page image.") from exc

        objects: list[DocumentObject] = []
        for index, box in enumerate(boxes, start=1):
            object_id = f"object-{index:04d}"
            crop_bytes = self._crop_to_png_bytes(image, box)
            object_key = (
                f"documents/{page.document_id}/pages/"
                f"page-{page.page_number:04d}/objects/{object_id}.png"
            )
            self.storage.upload_bytes(
                bucket_name=page.storage_bucket,
                object_key=object_key,
                content=crop_bytes,
                content_type="image/png",
            )
            objects.append(
                self.object_repository.create(
                    page_id=page.id,
                    object_id=object_id,
                    bounding_box=box.to_dict(),
                    image_storage_bucket=page.storage_bucket,
                    image_storage_key=object_key,
                    processing_status="segmented",
                )
            )

        logger.info(
            "Page segmentation completed",
            extra={
                "page_id": page.id,
                "document_id": page.document_id,
                "object_count": len(objects),
                "detected_objects_json": self.to_json(objects),
            },
        )
        return objects

    def detect_regions(self, image: Image.Image) -> list[BoundingBox]:
        grayscale = image.convert("L")
        width, height = grayscale.size
        pixels = grayscale.load()
        visited: set[tuple[int, int]] = set()
        boxes: list[BoundingBox] = []

        for y in range(height):
            for x in range(width):
                if (x, y) in visited or pixels[x, y] > self.settings.segmentation_threshold:
                    continue

                box = self._flood_fill_box(
                    pixels=pixels,
                    start_x=x,
                    start_y=y,
                    width=width,
                    height=height,
                    visited=visited,
                )
                if box.area >= self.settings.segmentation_min_area:
                    boxes.append(box)

        boxes = self._merge_nearby_boxes(boxes, padding=self.settings.segmentation_merge_padding)
        boxes = [box for box in boxes if box.area >= self.settings.segmentation_min_area]
        return sorted(boxes, key=lambda box: (box.y, box.x))

    def detect_independent_regions(self, image: Image.Image) -> list[BoundingBox]:
        page_area = image.width * image.height
        boxes = self.detect_regions(image)
        return [
            box
            for box in boxes
            if box.area < page_area * 0.85
            and box.width < image.width * 0.95
            and box.height < image.height * 0.95
        ]

    def to_json(self, objects: list[DocumentObject]) -> str:
        payload = [
            {
                "page_id": item.page_id,
                "object_id": item.object_id,
                "bounding_box": item.bounding_box,
                "image_storage_key": item.image_storage_key,
                "processing_status": item.processing_status,
            }
            for item in objects
        ]
        return json.dumps(payload)

    def _flood_fill_box(
        self,
        *,
        pixels,
        start_x: int,
        start_y: int,
        width: int,
        height: int,
        visited: set[tuple[int, int]],
    ) -> BoundingBox:
        queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
        visited.add((start_x, start_y))
        min_x = max_x = start_x
        min_y = max_y = start_y

        while queue:
            x, y = queue.popleft()
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)

            for next_x, next_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if (
                    next_x < 0
                    or next_y < 0
                    or next_x >= width
                    or next_y >= height
                    or (next_x, next_y) in visited
                    or pixels[next_x, next_y] > self.settings.segmentation_threshold
                ):
                    continue
                visited.add((next_x, next_y))
                queue.append((next_x, next_y))

        return BoundingBox(
            x=min_x,
            y=min_y,
            width=max_x - min_x + 1,
            height=max_y - min_y + 1,
        )

    def _merge_nearby_boxes(self, boxes: list[BoundingBox], padding: int) -> list[BoundingBox]:
        merged: list[BoundingBox] = []
        for box in boxes:
            merged_box = box
            changed = True
            while changed:
                changed = False
                remaining: list[BoundingBox] = []
                for candidate in merged:
                    if self._boxes_touch(merged_box, candidate, padding):
                        merged_box = self._union(merged_box, candidate)
                        changed = True
                    else:
                        remaining.append(candidate)
                merged = remaining
            merged.append(merged_box)
        return merged

    def _boxes_touch(self, first: BoundingBox, second: BoundingBox, padding: int) -> bool:
        first_right = first.x + first.width
        first_bottom = first.y + first.height
        second_right = second.x + second.width
        second_bottom = second.y + second.height
        return not (
            first_right + padding < second.x
            or second_right + padding < first.x
            or first_bottom + padding < second.y
            or second_bottom + padding < first.y
        )

    def _union(self, first: BoundingBox, second: BoundingBox) -> BoundingBox:
        x = min(first.x, second.x)
        y = min(first.y, second.y)
        right = max(first.x + first.width, second.x + second.width)
        bottom = max(first.y + first.height, second.y + second.height)
        return BoundingBox(x=x, y=y, width=right - x, height=bottom - y)

    def _crop_to_png_bytes(self, image: Image.Image, box: BoundingBox) -> bytes:
        crop = image.crop((box.x, box.y, box.x + box.width, box.y + box.height))
        buffer = BytesIO()
        crop.save(buffer, format="PNG")
        return buffer.getvalue()
