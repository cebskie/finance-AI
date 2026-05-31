from sqlalchemy.orm import Session

from app.documents.models import Document, DocumentPage


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        document_id: str,
        original_filename: str,
        mime_type: str,
        size_bytes: int,
        storage_bucket: str,
        storage_key: str,
    ) -> Document:
        document = Document(
            id=document_id,
            original_filename=original_filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_bucket=storage_bucket,
            storage_key=storage_key,
        )
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def update_status(self, *, document: Document, status: str) -> Document:
        document.status = status
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document


class DocumentPageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        document_id: str,
        page_number: int,
        width: int,
        height: int,
        dpi: int,
        storage_bucket: str,
        storage_key: str,
        size_bytes: int,
    ) -> DocumentPage:
        page = DocumentPage(
            document_id=document_id,
            page_number=page_number,
            width=width,
            height=height,
            dpi=dpi,
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            size_bytes=size_bytes,
        )
        self.session.add(page)
        self.session.commit()
        self.session.refresh(page)
        return page
