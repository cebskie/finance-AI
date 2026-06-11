import logging
from dataclasses import dataclass
from io import BytesIO

from PIL import Image

from app.core.config import Settings
from app.documents.models import DocumentPage
from app.documents.repository import DocumentPageRepository

logger = logging.getLogger(__name__)


class OcrPipelineError(RuntimeError):
    pass


@dataclass(frozen=True)
class OcrWord:
    text: str
    confidence: float
    bounding_box: dict[str, int]

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounding_box": self.bounding_box,
        }


@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float
    words: list[OcrWord]
    metadata: dict


class FullPageOcrService:
    def __init__(
        self,
        *,
        settings: Settings,
        page_repository: DocumentPageRepository,
    ) -> None:
        self.settings = settings
        self.page_repository = page_repository

    def process_page(
        self,
        *,
        page: DocumentPage,
        image_bytes: bytes,
        attempt: int = 1,
    ) -> OcrResult:
        logger.info(
            "Running full-page OCR",
            extra={
                "page_id": page.id,
                "document_id": page.document_id,
                "page_number": page.page_number,
                "engine": "tesseract",
                "attempt": attempt,
            },
        )

        try:
            result = self._run_tesseract(image_bytes=image_bytes, attempt=attempt)
            self.page_repository.mark_ocr_completed(
                page=page,
                text=result.text,
                ocr_metadata=result.metadata,
            )
        except Exception as exc:
            logger.exception(
                "Full-page OCR failed",
                extra={"page_id": page.id, "document_id": page.document_id},
            )
            raise OcrPipelineError("Failed to run full-page OCR.") from exc

        return result

    def _run_tesseract(self, *, image_bytes: bytes, attempt: int) -> OcrResult:
        try:
            import pytesseract
        except ImportError as exc:
            raise OcrPipelineError("pytesseract is required for OCR processing.") from exc

        if self.settings.tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = self.settings.tesseract_path

        image = Image.open(BytesIO(image_bytes))
        raw_data = pytesseract.image_to_data(
            image,
            lang=self.settings.ocr_language,
            output_type=pytesseract.Output.DICT,
            config="--psm 6",
        )
        words: list[OcrWord] = []
        text_parts: list[str] = []
        confidences: list[float] = []

        for index, raw_text in enumerate(raw_data.get("text", [])):
            text = str(raw_text).strip()
            confidence = self._parse_confidence(raw_data["conf"][index])
            if not text or confidence < 0:
                continue
            words.append(
                OcrWord(
                    text=text,
                    confidence=confidence,
                    bounding_box={
                        "x": int(raw_data["left"][index]),
                        "y": int(raw_data["top"][index]),
                        "width": int(raw_data["width"][index]),
                        "height": int(raw_data["height"][index]),
                    },
                )
            )
            text_parts.append(text)
            confidences.append(confidence)

        confidence = sum(confidences) / len(confidences) if confidences else 0.0
        metadata = {
            "engine": "tesseract",
            "language": self.settings.ocr_language,
            "page_segmentation_mode": 6,
            "confidence": round(confidence, 2),
            "confidence_threshold": self.settings.ocr_min_confidence,
            "word_count": len(words),
            "retry": {
                "attempt": attempt,
                "max_attempts": 1,
                "fallback_engine": None,
            },
            "words": [word.to_dict() for word in words],
        }
        return OcrResult(
            text=" ".join(text_parts),
            confidence=confidence,
            words=words,
            metadata=metadata,
        )

    def _parse_confidence(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return -1.0
