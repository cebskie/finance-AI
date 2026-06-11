from types import SimpleNamespace
from unittest.mock import patch
import sys

from app.core.config import Settings
from app.ocr.service import FullPageOcrService


class FakePageRepository:
    def __init__(self) -> None:
        self.ocr_calls = []

    def mark_ocr_completed(self, *, page, text: str, ocr_metadata: dict):
        self.ocr_calls.append(
            {
                "page": page,
                "text": text,
                "ocr_metadata": ocr_metadata,
            }
        )
        return page


def test_full_page_ocr_parses_words_confidence_and_bounding_boxes():
    repository = FakePageRepository()
    service = FullPageOcrService(
        settings=Settings(TESSERACT_PATH=""),
        page_repository=repository,
    )
    page = SimpleNamespace(id="page-1", document_id="doc-1", page_number=1)
    raw_data = {
        "text": ["Invoice", "", "123"],
        "conf": ["95", "-1", "85"],
        "left": [10, 0, 100],
        "top": [20, 0, 25],
        "width": [80, 0, 30],
        "height": [20, 0, 20],
    }

    fake_pytesseract = SimpleNamespace(
        Output=SimpleNamespace(DICT="dict"),
        image_to_data=lambda *args, **kwargs: raw_data,
        pytesseract=SimpleNamespace(tesseract_cmd=""),
    )

    with patch.dict(sys.modules, {"pytesseract": fake_pytesseract}), patch(
        "app.ocr.service.Image.open"
    ):
        result = service.process_page(page=page, image_bytes=b"png")

    assert result.text == "Invoice 123"
    assert result.confidence == 90
    assert len(result.words) == 2
    assert result.metadata["engine"] == "tesseract"
    assert repository.ocr_calls[0]["text"] == "Invoice 123"
