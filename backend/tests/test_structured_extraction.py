import json

from app.classification.service import PageClassificationResult
from app.extraction.service import StructuredExtractionService
from app.ocr.service import OcrResult, OcrWord


def production_ocr(text: str, confidence: float = 91.5) -> OcrResult:
    words = [
        OcrWord(
            text=word,
            confidence=confidence,
            bounding_box={"x": index * 12, "y": 20, "width": 10, "height": 12},
        )
        for index, word in enumerate(text.split())
    ]
    return OcrResult(
        text=text,
        confidence=confidence,
        words=words,
        metadata={
            "engine": "tesseract",
            "language": "eng",
            "page_segmentation_mode": 6,
            "confidence": confidence,
            "retry": {"attempt": 1, "max_attempts": 1, "fallback_engine": None},
            "words": [word.to_dict() for word in words],
        },
    )


def classified(document_type: str, confidence: float = 0.92) -> PageClassificationResult:
    return PageClassificationResult(
        document_type=document_type,
        label=document_type,
        confidence=confidence,
        metadata={"classifier": "keyword_rules"},
    )


def fields_by_name(result):
    fields = {}
    for field in result.fields:
        fields.setdefault(field.field_name, []).append(field.value)
    return fields


def test_extracts_vendor_invoice_fields_and_preserves_raw_ocr_text():
    text = (
        "Vendor: Acme Supplies Ltd Invoice Number INV-2026-001 "
        "Invoice Date 06/18/2026 PO Number PO-7788 Amount Due $1,250.75"
    )
    service = StructuredExtractionService()

    result = service.extract(
        ocr=production_ocr(text),
        classification=classified("vendor_invoice"),
        page_number=2,
    )
    fields = fields_by_name(result)

    assert result.document_type == "vendor_invoice"
    assert result.raw_ocr_text == text
    assert result.extraction_confidence > 0.7
    assert fields["vendor_names"] == ["Acme Supplies Ltd"]
    assert fields["invoice_numbers"] == ["INV-2026-001"]
    assert fields["po_numbers"] == ["PO-7788"]
    assert fields["dates"] == ["06/18/2026"]
    assert fields["totals_amounts"] == ["1,250.75"]
    assert all(field.confidence > 0 for field in result.fields)
    assert all(field.source_page == 2 for field in result.fields)


def test_extracts_purchase_order_fields_from_ocr_output():
    text = (
        "Purchase Order PO Number PO-450001 Order Date 05/30/2026 "
        "Supplier: Northwind Traders Ship To Jakarta Order Total USD 9,875.00"
    )
    service = StructuredExtractionService()

    result = service.extract(
        ocr=production_ocr(text, confidence=88.0),
        classification=classified("purchase_order", confidence=0.9),
        page_number=1,
    )
    fields = fields_by_name(result)

    assert fields["po_numbers"] == ["PO-450001"]
    assert fields["dates"] == ["05/30/2026"]
    assert fields["vendor_names"] == ["Northwind Traders"]
    assert fields["totals_amounts"] == ["9,875.00"]


def test_extracts_approval_fields_from_ocr_output():
    text = (
        "Approval Number APR-2026-77 Approved Date June 1, 2026 "
        "Payee: Delta Consulting Invoice Number DC-991 PO Number PO-123 "
        "Approved Amount IDR 25.000.000"
    )
    service = StructuredExtractionService()

    result = service.extract(
        ocr=production_ocr(text, confidence=86.0),
        classification=classified("approval", confidence=0.87),
        page_number=3,
    )
    fields = fields_by_name(result)

    assert fields["document_numbers"] == ["APR-2026-77"]
    assert fields["dates"] == ["June 1, 2026"]
    assert fields["vendor_names"] == ["Delta Consulting"]
    assert fields["invoice_numbers"] == ["DC-991"]
    assert fields["po_numbers"] == ["PO-123"]
    assert fields["totals_amounts"] == ["25.000.000"]


def test_extracts_receipt_fields_and_returns_json_serializable_result():
    text = (
        "Receipt No RCP-888 Paid Date 06/03/2026 Merchant: City Hotel "
        "Transaction ID TX-777 Amount Paid $410.00 Invoice No INV-710"
    )
    service = StructuredExtractionService()

    result_json = service.extract_json(
        ocr=production_ocr(text, confidence=93.0),
        classification=classified("receipt", confidence=0.91),
        page_number=4,
    )
    encoded = json.dumps(result_json)
    fields = {}
    for field in result_json["fields"]:
        fields.setdefault(field["field_name"], []).append(field["value"])

    assert encoded
    assert result_json["raw_ocr_text"] == text
    assert result_json["extraction_confidence"] > 0.7
    assert "RCP-888" in fields["document_numbers"]
    assert "TX-777" in fields["document_numbers"]
    assert fields["vendor_names"] == ["City Hotel"]
    assert fields["invoice_numbers"] == ["INV-710"]
    assert fields["totals_amounts"] == ["410.00"]


def test_unsupported_document_type_preserves_ocr_text_without_fields():
    text = "System generated accounting document GL Account 6100"
    service = StructuredExtractionService()

    result = service.extract(
        ocr=production_ocr(text),
        classification=classified("system_invoice", confidence=0.8),
        page_number=1,
    )

    assert result.fields == []
    assert result.extraction_confidence == 0.0
    assert result.raw_ocr_text == text
    assert result.metadata["method"] == "unsupported_document_type"
