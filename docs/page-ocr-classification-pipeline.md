# Page OCR and Classification Pipeline

## Scope

This stage implements the OCR-ready processing path for uploaded finance PDF packages:

`PDF upload -> page splitting -> page preprocessing -> full-page OCR -> page classification`

LLM extraction is intentionally out of scope for this iteration. The output of this stage is OCR text, OCR metadata, document type classification, confidence data, and optional segmentation fallback artifacts.

## Execution Flow

1. `DocumentUploadService` stores the original PDF and creates document metadata.
2. `PdfPageSplittingService` renders each PDF page into a full-page PNG.
3. `PageProcessingPipeline` processes every page independently:
   - `PagePreprocessingService` loads the page image, detects orientation, corrects rotation, applies deskew when OpenCV is available, and creates an OCR-optimized image.
   - `FullPageOcrService` runs Tesseract against the preprocessed full-page image.
   - `PageClassificationService` classifies the page from OCR text using externally loaded keyword rules.
   - `PageSegmentationService` is consulted only as a visual fallback. It segments the page only when multiple independent document regions are detected.
4. The document is marked `classification_ready` when all pages complete.

## Service Boundaries

- `app.pdf`: PDF rendering and page metadata creation.
- `app.preprocessing`: image normalization for OCR readiness.
- `app.ocr`: OCR engine integration and OCR confidence metadata.
- `app.classification`: configurable, deterministic page type classification.
- `app.segmentation`: optional visual segmentation fallback for multi-region pages.
- `app.pipeline`: orchestration across page-level services.

## Confidence Scoring

OCR confidence is calculated as the average Tesseract confidence across retained words. Empty words and negative-confidence artifacts are ignored.

Classification confidence is calculated from:

- rule score share of all positive candidate scores
- OCR confidence multiplier
- configured minimum confidence threshold

Pages below `CLASSIFICATION_MIN_CONFIDENCE` are classified as `unknown` and retain candidate scores plus matched keyword evidence in metadata.

## Fallback Strategy

The primary path is full-page OCR because production samples mostly represent one logical document per page.

Segmentation is optional and triggered only when `detect_independent_regions` finds at least `SEGMENTATION_FALLBACK_MIN_REGIONS` significant regions that do not cover nearly the whole page. This preserves segmentation for mixed-region edge cases without over-splitting normal PO, invoice, receipt, approval, system invoice, or internal record pages.

OCR fallback engines are not implemented in this step. The OCR metadata already includes retry fields so PaddleOCR, Azure OCR, and Google Vision OCR can be added behind the same result contract.

## Database Schema Updates

`document_pages` now stores page processing state:

- `preprocessed_storage_key`
- `preprocessing_metadata`
- `ocr_text`
- `ocr_metadata`
- `document_type`
- `classification_confidence`
- `classification_metadata`
- `segmentation_metadata`
- `processing_status`

`document_objects` remains the storage table for segmentation fallback crops.

Current schema creation uses SQLAlchemy `create_all`. Before production deployment, add explicit Alembic migrations for these columns.

## Classification Configuration

Default classification rules live in:

`backend/app/classification/default_rules.json`

Production deployments can override the rules file using `CLASSIFICATION_RULES_PATH`. Rules are JSON so admins can version them outside application code.

Supported page classes:

- `purchase_order`
- `vendor_invoice`
- `receipt`
- `approval`
- `system_invoice`
- `internal_record`
- `unknown`

## Testing Strategy With Production Samples

When production sample PDFs are available, create a non-committed fixture directory such as `backend/tests/fixtures/production_samples/` and run a golden-output test set:

1. Render each sample PDF into pages.
2. Persist expected page labels in a JSON manifest with filename, page number, expected document type, and notes.
3. Run preprocessing and OCR with Tesseract installed.
4. Assert:
   - preprocessed image exists and has plausible dimensions
   - OCR word count is above a sample-specific minimum
   - OCR confidence is captured
   - page classification matches expected label or becomes `unknown` only for explicitly ambiguous pages
   - segmentation fallback is not triggered for normal single-document pages
   - segmentation fallback triggers for known multi-region pages

Synthetic unit tests currently cover preprocessing persistence, mocked Tesseract OCR parsing, rule-based classification, upload orchestration, and fallback segmentation behavior.

## Risks

- Orientation detection is currently conservative and based on image geometry unless deeper OCR orientation support is added.
- OpenCV deskew is optional; environments without OpenCV still process pages but skip skew correction.
- Rule-based classification is explainable but less flexible than future LLM or ML classification.
- Tesseract quality depends on image DPI, installed language data, and document scan quality.
- Existing schema management needs Alembic before production rollout.
