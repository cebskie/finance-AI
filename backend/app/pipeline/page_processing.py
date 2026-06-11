import logging
from dataclasses import dataclass
from io import BytesIO

from PIL import Image

from app.classification.service import PageClassificationService, PageClassificationResult
from app.core.config import Settings
from app.documents.models import DocumentPage
from app.documents.repository import DocumentPageRepository
from app.ocr.service import FullPageOcrService, OcrResult
from app.preprocessing.service import PagePreprocessingService, PagePreprocessingResult
from app.segmentation.service import PageSegmentationService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PageProcessingResult:
    page: DocumentPage
    preprocessing: PagePreprocessingResult
    ocr: OcrResult
    classification: PageClassificationResult
    segmentation_object_count: int


class PageProcessingPipeline:
    def __init__(
        self,
        *,
        settings: Settings,
        page_repository: DocumentPageRepository,
        preprocessor: PagePreprocessingService,
        ocr: FullPageOcrService,
        classifier: PageClassificationService,
        segmenter: PageSegmentationService,
    ) -> None:
        self.settings = settings
        self.page_repository = page_repository
        self.preprocessor = preprocessor
        self.ocr = ocr
        self.classifier = classifier
        self.segmenter = segmenter

    def process_page(self, *, page: DocumentPage) -> PageProcessingResult:
        preprocessing = self.preprocessor.preprocess_page(page=page)
        ocr_result = self.ocr.process_page(
            page=page,
            image_bytes=preprocessing.image_bytes,
        )
        classification = self.classifier.classify_page(
            text=ocr_result.text,
            ocr_confidence=ocr_result.confidence,
        )
        self.page_repository.mark_classified(
            page=page,
            document_type=classification.document_type,
            confidence=classification.confidence,
            classification_metadata=classification.metadata,
        )
        segmentation_object_count = self._run_segmentation_fallback_if_needed(
            page=page,
            image_bytes=preprocessing.image_bytes,
        )
        return PageProcessingResult(
            page=page,
            preprocessing=preprocessing,
            ocr=ocr_result,
            classification=classification,
            segmentation_object_count=segmentation_object_count,
        )

    def _run_segmentation_fallback_if_needed(
        self,
        *,
        page: DocumentPage,
        image_bytes: bytes,
    ) -> int:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        regions = self.segmenter.detect_independent_regions(image)
        should_segment = len(regions) >= self.settings.segmentation_fallback_min_regions
        metadata = {
            "strategy": "optional_visual_segmentation_fallback",
            "triggered": should_segment,
            "detected_region_count": len(regions),
            "minimum_region_count": self.settings.segmentation_fallback_min_regions,
            "regions": [region.to_dict() for region in regions],
        }
        if not should_segment:
            self.page_repository.mark_segmentation_fallback(
                page=page,
                segmentation_metadata=metadata,
            )
            return 0

        logger.info(
            "Running segmentation fallback for multi-region page",
            extra={
                "page_id": page.id,
                "document_id": page.document_id,
                "region_count": len(regions),
            },
        )
        objects = self.segmenter.segment_page(page=page)
        metadata["object_count"] = len(objects)
        self.page_repository.mark_segmentation_fallback(
            page=page,
            segmentation_metadata=metadata,
        )
        return len(objects)
