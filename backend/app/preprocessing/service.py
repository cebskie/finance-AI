import logging
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageEnhance, ImageOps

from app.core.config import Settings
from app.documents.models import DocumentPage
from app.documents.repository import DocumentPageRepository
from app.storage.service import ObjectStorageService

logger = logging.getLogger(__name__)


class PagePreprocessingError(RuntimeError):
    pass


@dataclass(frozen=True)
class PagePreprocessingResult:
    image_bytes: bytes
    storage_key: str
    metadata: dict


class PagePreprocessingService:
    def __init__(
        self,
        *,
        settings: Settings,
        page_repository: DocumentPageRepository,
        storage: ObjectStorageService,
    ) -> None:
        self.settings = settings
        self.page_repository = page_repository
        self.storage = storage

    def preprocess_page(self, *, page: DocumentPage) -> PagePreprocessingResult:
        logger.info(
            "Preprocessing page for full-page OCR",
            extra={
                "page_id": page.id,
                "document_id": page.document_id,
                "page_number": page.page_number,
            },
        )

        try:
            source_bytes = self.storage.get_object_bytes(
                bucket_name=page.storage_bucket,
                object_key=page.storage_key,
            )
            source_image = Image.open(BytesIO(source_bytes)).convert("RGB")
            orientation_degrees = self.detect_orientation(source_image)
            rotated_image = self.correct_rotation(source_image, orientation_degrees)
            deskewed_image, deskew_angle = self.deskew(rotated_image)
            optimized_image = self.optimize_for_ocr(deskewed_image)
            image_bytes = self._image_to_png_bytes(optimized_image)
            storage_key = self._preprocessed_key(page.storage_key)
            metadata = {
                "source_storage_key": page.storage_key,
                "preprocessed_storage_key": storage_key,
                "orientation_degrees": orientation_degrees,
                "rotation_corrected": orientation_degrees != 0,
                "deskew_angle_degrees": deskew_angle,
                "deskew_applied": abs(deskew_angle) >= 0.1,
                "ocr_optimization": {
                    "grayscale": True,
                    "autocontrast": True,
                    "contrast_factor": 1.4,
                },
                "engine": "pillow",
            }
            self.storage.upload_bytes(
                bucket_name=page.storage_bucket,
                object_key=storage_key,
                content=image_bytes,
                content_type="image/png",
            )
            self.page_repository.mark_preprocessed(
                page=page,
                preprocessed_storage_key=storage_key,
                preprocessing_metadata=metadata,
            )
        except Exception as exc:
            logger.exception(
                "Page preprocessing failed",
                extra={"page_id": page.id, "document_id": page.document_id},
            )
            raise PagePreprocessingError("Failed to preprocess page image.") from exc

        return PagePreprocessingResult(
            image_bytes=image_bytes,
            storage_key=storage_key,
            metadata=metadata,
        )

    def detect_orientation(self, image: Image.Image) -> int:
        width, height = image.size
        if width > height * 1.25:
            return 90
        return 0

    def correct_rotation(self, image: Image.Image, orientation_degrees: int) -> Image.Image:
        if orientation_degrees == 0:
            return image
        return image.rotate(-orientation_degrees, expand=True, fillcolor="white")

    def deskew(self, image: Image.Image) -> tuple[Image.Image, float]:
        try:
            import cv2
            import numpy as np
        except ImportError:
            return image, 0.0

        grayscale = np.array(ImageOps.grayscale(image))
        inverted = cv2.bitwise_not(grayscale)
        thresholded = cv2.threshold(
            inverted,
            0,
            255,
            cv2.THRESH_BINARY | cv2.THRESH_OTSU,
        )[1]
        coordinates = np.column_stack(np.where(thresholded > 0))
        if coordinates.size == 0:
            return image, 0.0

        angle = cv2.minAreaRect(coordinates)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if abs(angle) < 0.1 or abs(angle) > 15:
            return image, 0.0

        height, width = grayscale.shape[:2]
        center = (width // 2, height // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            np.array(image),
            matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return Image.fromarray(rotated), float(round(angle, 2))

    def optimize_for_ocr(self, image: Image.Image) -> Image.Image:
        grayscale = ImageOps.grayscale(image)
        normalized = ImageOps.autocontrast(grayscale)
        enhanced = ImageEnhance.Contrast(normalized).enhance(1.4)
        return enhanced.convert("RGB")

    def _preprocessed_key(self, source_key: str) -> str:
        if source_key.lower().endswith(".png"):
            return f"{source_key[:-4]}{self.settings.preprocessed_image_suffix}"
        return f"{source_key}{self.settings.preprocessed_image_suffix}"

    def _image_to_png_bytes(self, image: Image.Image) -> bytes:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
