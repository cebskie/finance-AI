import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.classification.service import PageClassificationResult
from app.extraction.service import StructuredExtractionService
from app.ocr.service import OcrResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate structured extraction from OCR text and classification output.",
    )
    ocr_input = parser.add_mutually_exclusive_group(required=True)
    ocr_input.add_argument("--ocr-text", help="Raw OCR text to evaluate.")
    ocr_input.add_argument("--ocr-file", help="Path to a UTF-8 text file containing raw OCR text.")

    classification_input = parser.add_mutually_exclusive_group(required=True)
    classification_input.add_argument(
        "--classification-json",
        help=(
            "Classification JSON. Expected keys: document_type, confidence, "
            "and optionally label and metadata."
        ),
    )
    classification_input.add_argument(
        "--document-type",
        choices=["vendor_invoice", "purchase_order", "approval", "receipt"],
        help="Classified document type.",
    )

    parser.add_argument(
        "--classification-confidence",
        type=float,
        default=1.0,
        help="Classification confidence used with --document-type. Defaults to 1.0.",
    )
    parser.add_argument(
        "--ocr-confidence",
        type=float,
        default=100.0,
        help="OCR confidence from 0-100 or 0-1. Defaults to 100.",
    )
    parser.add_argument(
        "--expected-fields",
        default="",
        help="Comma-separated expected field names, for example invoice_numbers,totals_amounts.",
    )
    parser.add_argument(
        "--page-number",
        type=int,
        default=None,
        help="Optional source page number to include in extracted fields.",
    )
    parser.add_argument(
        "--rules-path",
        default=None,
        help="Optional extraction rules JSON path.",
    )
    return parser


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    ocr_text = load_ocr_text(args)
    classification = load_classification(args)
    ocr = OcrResult(
        text=ocr_text,
        confidence=args.ocr_confidence,
        words=[],
        metadata={"engine": "evaluation_input"},
    )
    result = StructuredExtractionService(rules_path=args.rules_path).extract(
        ocr=ocr,
        classification=classification,
        page_number=args.page_number,
    )
    extracted_fields = result.to_dict()["fields"]
    extracted_field_names = {field["field_name"] for field in extracted_fields}
    expected_fields = parse_expected_fields(args.expected_fields)

    return {
        "document_type": result.document_type,
        "extraction_confidence": result.extraction_confidence,
        "classification_confidence": result.classification_confidence,
        "extracted_fields": extracted_fields,
        "missing_expected_fields": [
            field_name for field_name in expected_fields if field_name not in extracted_field_names
        ],
        "raw_ocr_text": result.raw_ocr_text,
        "metadata": result.metadata,
    }


def load_ocr_text(args: argparse.Namespace) -> str:
    if args.ocr_file:
        return Path(args.ocr_file).read_text(encoding="utf-8")
    return args.ocr_text


def load_classification(args: argparse.Namespace) -> PageClassificationResult:
    if args.classification_json:
        raw = json.loads(args.classification_json)
        document_type = raw["document_type"]
        confidence = float(raw.get("confidence", 1.0))
        label = raw.get("label", document_type)
        metadata = raw.get("metadata", {})
    else:
        document_type = args.document_type
        confidence = args.classification_confidence
        label = document_type
        metadata = {"source": "cli_document_type"}

    return PageClassificationResult(
        document_type=document_type,
        label=label,
        confidence=confidence,
        metadata=metadata,
    )


def parse_expected_fields(value: str) -> list[str]:
    return [field.strip() for field in value.split(",") if field.strip()]


def main() -> None:
    args = build_parser().parse_args()
    print(json.dumps(evaluate(args), indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
