import logging
from io import BytesIO

from pdf2image import convert_from_bytes

from app.core.config import Settings
from app.documents.models import Document, DocumentPage
from app.documents.repository import DocumentPageRepository
from app.storage.service import ObjectStorageService

logger = logging.getLogger(__name__)


class PdfSplitError(RuntimeError):
    pass


class PdfPageSplittingService:
    def __init__(
        self,
        *,
        settings: Settings,
        page_repository: DocumentPageRepository,
        storage: ObjectStorageService,
    ) -> None:
        self.settings = settings
        self.page_repository = page_repository
        self.storage = storage

    def split_pdf(self, *, document: Document, pdf_content: bytes) -> list[DocumentPage]:
        logger.info(
            "Splitting PDF into page images",
            extra={
                "document_id": document.id,
                "pdf_size_bytes": len(pdf_content),
                "dpi": self.settings.pdf_split_dpi,
            },
        )

        try:
            images = convert_from_bytes(
                pdf_content,
                dpi=self.settings.pdf_split_dpi,
                fmt="png",
                poppler_path=self.settings.poppler_path or None,
            )
        except Exception as exc:
            logger.exception(
                "PDF page splitting failed",
                extra={"document_id": document.id},
            )
            raise PdfSplitError("Failed to split PDF into page images.") from exc

        pages: list[DocumentPage] = []
        for index, image in enumerate(images, start=1):
            image_bytes = self._image_to_png_bytes(image)
            object_key = f"documents/{document.id}/pages/page-{index:04d}.png"
            self.storage.upload_bytes(
                bucket_name=self.settings.document_bucket,
                object_key=object_key,
                content=image_bytes,
                content_type="image/png",
            )
            pages.append(
                self.page_repository.create(
                    document_id=document.id,
                    page_number=index,
                    width=image.width,
                    height=image.height,
                    dpi=self.settings.pdf_split_dpi,
                    storage_bucket=self.settings.document_bucket,
                    storage_key=object_key,
                    size_bytes=len(image_bytes),
                )
            )

        logger.info(
            "PDF page splitting completed",
            extra={
                "document_id": document.id,
                "page_count": len(pages),
            },
        )
        return pages

    def _image_to_png_bytes(self, image) -> bytes:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
