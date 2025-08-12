from sqlalchemy.orm import Session
from src.database.models import Document
from typing import Optional

def create_document(session: Session, filename: str, extension: str) -> Document:
    """Create a new Document record in the database."""
    document = Document(
        filename=filename,
        extension=extension,
        is_success_processed=False,
        processed_at=None
    )
    session.add(document)
    session.flush()  # Ensure document_id is available
    return document

def get_document_by_filename(session: Session, filename: str) -> Optional[Document]:
    """Retrieve a Document by filename."""
    return session.query(Document).filter(Document.filename == filename).first()