import argparse
import json
import subprocess
import sys

from scripts.evaluate_extraction import evaluate, parse_expected_fields


def test_evaluate_reports_extracted_fields_confidence_and_missing_expected_fields():
    args = argparse.Namespace(
        ocr_text=(
            "Vendor: Acme Supplies Ltd Invoice Number INV-2026-001 "
            "Invoice Date 06/18/2026 Amount Due $1,250.75"
        ),
        ocr_file=None,
        classification_json=json.dumps(
            {
                "document_type": "vendor_invoice",
                "confidence": 0.93,
                "label": "Vendor Invoice Documents",
                "metadata": {"classifier": "keyword_rules"},
            }
        ),
        document_type=None,
        classification_confidence=1.0,
        ocr_confidence=91.0,
        expected_fields="invoice_numbers,totals_amounts,po_numbers",
        page_number=1,
        rules_path=None,
    )

    output = evaluate(args)
    field_names = {field["field_name"] for field in output["extracted_fields"]}

    assert output["document_type"] == "vendor_invoice"
    assert output["extraction_confidence"] > 0
    assert "invoice_numbers" in field_names
    assert "totals_amounts" in field_names
    assert output["missing_expected_fields"] == ["po_numbers"]
    assert output["raw_ocr_text"] == args.ocr_text


def test_parse_expected_fields_ignores_empty_values():
    assert parse_expected_fields("invoice_numbers, , totals_amounts,") == [
        "invoice_numbers",
        "totals_amounts",
    ]


def test_cli_outputs_json_for_inline_inputs():
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/evaluate_extraction.py",
            "--ocr-text",
            "Purchase Order PO Number PO-450001 Order Total USD 9,875.00",
            "--document-type",
            "purchase_order",
            "--classification-confidence",
            "0.9",
            "--ocr-confidence",
            "88",
            "--expected-fields",
            "po_numbers,dates",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    output = json.loads(completed.stdout)

    assert output["document_type"] == "purchase_order"
    assert output["extracted_fields"][0]["field_name"] == "po_numbers"
    assert output["missing_expected_fields"] == ["dates"]
