import json
import logging
import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from app.classification.service import PageClassificationResult
from app.ocr.service import OcrResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtractionField:
    field_name: str
    value: str
    confidence: float
    source_page: int | None
    bounding_box: dict[str, int] | None
    extraction_method: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "value": self.value,
            "confidence": self.confidence,
            "source_page": self.source_page,
            "bounding_box": self.bounding_box,
            "extraction_method": self.extraction_method,
        }


@dataclass(frozen=True)
class StructuredExtractionResult:
    document_type: str
    classification_confidence: float
    extraction_confidence: float
    raw_ocr_text: str
    fields: list[ExtractionField]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_type": self.document_type,
            "classification_confidence": self.classification_confidence,
            "extraction_confidence": self.extraction_confidence,
            "raw_ocr_text": self.raw_ocr_text,
            "fields": [field.to_dict() for field in self.fields],
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)


class BaseDocumentExtractor:
    document_type: str = ""

    def __init__(self, *, rules: dict[str, Any], minimum_field_confidence: float) -> None:
        self.rules = rules
        self.minimum_field_confidence = minimum_field_confidence

    def extract(
        self,
        *,
        ocr: OcrResult,
        classification: PageClassificationResult,
        page_number: int | None = None,
    ) -> StructuredExtractionResult:
        fields: list[ExtractionField] = []
        for field_name, field_rules in self.rules.get("fields", {}).items():
            fields.extend(
                self._extract_field(
                    field_name=field_name,
                    field_rules=field_rules,
                    text=ocr.text,
                    ocr_confidence=ocr.confidence,
                    classification_confidence=classification.confidence,
                    page_number=page_number,
                )
            )

        extraction_confidence = self._result_confidence(fields)
        metadata = {
            "extractor": self.__class__.__name__,
            "method": "configurable_regex_rules",
            "field_count": len(fields),
            "ocr_confidence": round(ocr.confidence, 4),
            "source_ocr_engine": ocr.metadata.get("engine"),
            "rules_document_type": self.document_type,
        }
        return StructuredExtractionResult(
            document_type=self.document_type,
            classification_confidence=round(classification.confidence, 4),
            extraction_confidence=extraction_confidence,
            raw_ocr_text=ocr.text,
            fields=fields,
            metadata=metadata,
        )

    def _extract_field(
        self,
        *,
        field_name: str,
        field_rules: list[dict[str, Any]],
        text: str,
        ocr_confidence: float,
        classification_confidence: float,
        page_number: int | None,
    ) -> list[ExtractionField]:
        extracted: list[ExtractionField] = []
        seen_values: set[str] = set()
        for rule in field_rules:
            pattern = re.compile(rule["pattern"], re.IGNORECASE)
            for match in pattern.finditer(text):
                value = self._clean_value(match.group(1))
                if not value or value.lower() in seen_values:
                    continue
                confidence = self._field_confidence(
                    ocr_confidence=ocr_confidence,
                    classification_confidence=classification_confidence,
                    rule_weight=float(rule.get("confidence_weight", 0.75)),
                )
                if confidence < self.minimum_field_confidence:
                    continue
                extracted.append(
                    ExtractionField(
                        field_name=field_name,
                        value=value,
                        confidence=confidence,
                        source_page=page_number,
                        bounding_box=None,
                        extraction_method="configurable_regex",
                    )
                )
                seen_values.add(value.lower())
        return extracted

    def _field_confidence(
        self,
        *,
        ocr_confidence: float,
        classification_confidence: float,
        rule_weight: float,
    ) -> float:
        normalized_ocr_confidence = ocr_confidence / 100 if ocr_confidence > 1 else ocr_confidence
        confidence = normalized_ocr_confidence * classification_confidence * rule_weight
        return round(max(0.0, min(1.0, confidence)), 4)

    def _result_confidence(self, fields: list[ExtractionField]) -> float:
        if not fields:
            return 0.0
        return round(sum(field.confidence for field in fields) / len(fields), 4)

    def _clean_value(self, value: str) -> str:
        return value.strip(" \t\r\n:;,.")


class VendorInvoiceExtractor(BaseDocumentExtractor):
    document_type = "vendor_invoice"


class PurchaseOrderExtractor(BaseDocumentExtractor):
    document_type = "purchase_order"


class ApprovalExtractor(BaseDocumentExtractor):
    document_type = "approval"


class ReceiptExtractor(BaseDocumentExtractor):
    document_type = "receipt"


class StructuredExtractionService:
    extractor_classes = {
        "vendor_invoice": VendorInvoiceExtractor,
        "purchase_order": PurchaseOrderExtractor,
        "approval": ApprovalExtractor,
        "receipt": ReceiptExtractor,
    }

    def __init__(self, *, rules_path: str | None = None) -> None:
        self.rules_path = rules_path
        self.rules = self._load_rules()
        self.extractors = self._build_extractors()

    def extract(
        self,
        *,
        ocr: OcrResult,
        classification: PageClassificationResult,
        page_number: int | None = None,
    ) -> StructuredExtractionResult:
        extractor = self.extractors.get(classification.document_type)
        if not extractor:
            logger.info(
                "No structured extractor configured for document type",
                extra={"document_type": classification.document_type},
            )
            return StructuredExtractionResult(
                document_type=classification.document_type,
                classification_confidence=round(classification.confidence, 4),
                extraction_confidence=0.0,
                raw_ocr_text=ocr.text,
                fields=[],
                metadata={
                    "extractor": None,
                    "method": "unsupported_document_type",
                    "field_count": 0,
                    "ocr_confidence": round(ocr.confidence, 4),
                    "source_ocr_engine": ocr.metadata.get("engine"),
                },
            )
        return extractor.extract(
            ocr=ocr,
            classification=classification,
            page_number=page_number,
        )

    def extract_json(
        self,
        *,
        ocr: OcrResult,
        classification: PageClassificationResult,
        page_number: int | None = None,
    ) -> dict[str, Any]:
        return self.extract(
            ocr=ocr,
            classification=classification,
            page_number=page_number,
        ).to_dict()

    def _build_extractors(self) -> dict[str, BaseDocumentExtractor]:
        minimum_field_confidence = float(self.rules.get("minimum_field_confidence", 0.1))
        document_rules = self.rules.get("supported_document_types", {})
        extractors: dict[str, BaseDocumentExtractor] = {}
        for document_type, extractor_class in self.extractor_classes.items():
            rules = document_rules.get(document_type)
            if rules:
                extractors[document_type] = extractor_class(
                    rules=rules,
                    minimum_field_confidence=minimum_field_confidence,
                )
        return extractors

    def _load_rules(self) -> dict[str, Any]:
        rules_path = self._rules_source()
        with open(rules_path, encoding="utf-8") as rules_file:
            return json.load(rules_file)

    def _rules_source(self) -> str:
        if self.rules_path:
            return str(Path(self.rules_path))
        return str(files("app.extraction").joinpath("default_rules.json"))
