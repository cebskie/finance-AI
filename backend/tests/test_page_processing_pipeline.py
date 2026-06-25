from dataclasses import dataclass
from io import BytesIO
from types import SimpleNamespace

from PIL import Image, ImageDraw

from app.classification.service import PageClassificationResult
from app.core.config import Settings
from app.ocr.service import OcrResult
from app.pipeline.page_processing import PageProcessingPipeline
from app.preprocessing.service import PagePreprocessingResult
from app.segmentation.service import PageSegmentationService


class FakePageRepository:
    def __init__(self) -> None:
        self.classified = []
        self.segmentation = []

    def mark_classified(self, *, page, document_type: str, confidence: float, classification_metadata: dict):
        self.classified.append(
            {
                "document_type": document_type,
                "confidence": confidence,
                "classification_metadata": classification_metadata,
            }
        )
        return page

    def mark_segmentation_fallback(self, *, page, segmentation_metadata: dict):
        self.segmentation.append(segmentation_metadata)
        return page


class FakePreprocessor:
    def __init__(self, image_bytes: bytes) -> None:
        self.image_bytes = image_bytes

    def preprocess_page(self, *, page):
        return PagePreprocessingResult(
            image_bytes=self.image_bytes,
            storage_key="preprocessed.png",
            metadata={},
        )


class FakeOcr:
    def process_page(self, *, page, image_bytes: bytes):
        return OcrResult(text="Invoice Number 123 Amount Due", confidence=90, words=[], metadata={})


class FakeClassifier:
    def classify_page(self, *, text: str, ocr_confidence: float):
        return PageClassificationResult(
            document_type="vendor_invoice",
            label="Vendor Invoice Documents",
            confidence=0.9,
            metadata={"rule": "invoice_keyword"},
        )


class FakeExtractor:
    def __init__(self) -> None:
        self.calls = []

    def extract_json(self, *, ocr: OcrResult, classification: PageClassificationResult, page_number: int):
        self.calls.append(
            {
                "ocr_text": ocr.text,
                "document_type": classification.document_type,
                "page_number": page_number,
            }
        )
        return {
            "document_type": classification.document_type,
            "extraction_confidence": 0.8,
            "fields": [],
            "raw_ocr_text": ocr.text,
        }


class FakeObjectRepository:
    def __init__(self) -> None:
        self.objects = []

    def create(self, **kwargs):
        item = SimpleNamespace(**kwargs)
        self.objects.append(item)
        return item


class FakeStorage:
    def __init__(self, image_bytes: bytes) -> None:
        self.image_bytes = image_bytes
        self.uploads = []

    def get_object_bytes(self, *, bucket_name: str, object_key: str) -> bytes:
        return self.image_bytes

    def upload_bytes(self, *, bucket_name: str, object_key: str, content: bytes, content_type: str):
        self.uploads.append(content)


def multi_region_image_bytes() -> bytes:
    image = Image.new("RGB", (500, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 220, 260), outline="black", width=5)
    draw.rectangle((280, 40, 470, 240), outline="black", width=5)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_pipeline_runs_segmentation_only_when_multiple_regions_are_detected():
    image_bytes = multi_region_image_bytes()
    page_repository = FakePageRepository()
    extractor = FakeExtractor()
    segmenter = PageSegmentationService(
        settings=Settings(SEGMENTATION_MIN_AREA=1000, SEGMENTATION_MERGE_PADDING=8),
        object_repository=FakeObjectRepository(),
        storage=FakeStorage(image_bytes),
    )
    pipeline = PageProcessingPipeline(
        settings=Settings(SEGMENTATION_FALLBACK_MIN_REGIONS=2, SEGMENTATION_MIN_AREA=1000),
        page_repository=page_repository,
        preprocessor=FakePreprocessor(image_bytes),
        ocr=FakeOcr(),
        classifier=FakeClassifier(),
        extractor=extractor,
        segmenter=segmenter,
    )
    page = SimpleNamespace(
        id="page-1",
        document_id="doc-1",
        page_number=1,
        storage_bucket="documents",
        storage_key="documents/doc-1/pages/page-0001.png",
    )

    result = pipeline.process_page(page=page)

    assert result.classification.document_type == "vendor_invoice"
    assert result.extraction["document_type"] == "vendor_invoice"
    assert page_repository.classified == [
        {
            "document_type": "vendor_invoice",
            "confidence": 0.9,
            "classification_metadata": {
                "rule": "invoice_keyword",
                "extraction_json": {
                    "document_type": "vendor_invoice",
                    "extraction_confidence": 0.8,
                    "fields": [],
                    "raw_ocr_text": "Invoice Number 123 Amount Due",
                },
            },
        }
    ]
    assert extractor.calls == [
        {
            "ocr_text": "Invoice Number 123 Amount Due",
            "document_type": "vendor_invoice",
            "page_number": 1,
        }
    ]
    assert result.segmentation_object_count == 2
    assert page_repository.segmentation[0]["triggered"] is True
