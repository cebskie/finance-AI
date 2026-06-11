from app.classification.service import PageClassificationService, UNKNOWN_DOCUMENT_TYPE
from app.core.config import Settings


def test_classifies_purchase_order_from_configured_keywords():
    service = PageClassificationService(settings=Settings())

    result = service.classify_page(
        text="Purchase Order PO Number 450001 Buyer Ship To Bill To",
        ocr_confidence=92,
    )

    assert result.document_type == "purchase_order"
    assert result.confidence > 0.8
    assert "purchase order" in result.metadata["matched_keywords"]


def test_classifies_unknown_when_confidence_is_low():
    service = PageClassificationService(settings=Settings(CLASSIFICATION_MIN_CONFIDENCE=0.8))

    result = service.classify_page(text="Invoice Number Amount Due", ocr_confidence=40)

    assert result.document_type == UNKNOWN_DOCUMENT_TYPE
    assert result.confidence == 0.0
