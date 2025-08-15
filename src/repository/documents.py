from sqlalchemy.orm import Session
from src.database.models import Document as ORMDocument
from src.entities import Document
from typing import List, Optional

def create_document(session: Session, entity: Document) -> Document:
    orm_doc = entity.to_orm(ORMDocument)
    session.add(orm_doc)
    session.flush()
    entity.document_id = orm_doc.document_id
    return entity

def get_document_by_filename(session: Session, filename: str) -> Optional[Document]:
    orm_doc = session.query(ORMDocument).filter(ORMDocument.filename == filename).first()
    return Document.from_orm(orm_doc) if orm_doc else None

def get_cut_documents(session: Session) -> Optional[List[ORMDocument]]:
    return session.query(ORMDocument).filter(ORMDocument.is_success_processed).first()

def update_document_status(session: Session, entity: Document) -> None:
    orm_doc = session.query(ORMDocument).filter(ORMDocument.document_id == entity.document_id).first()
    if orm_doc:
        orm_doc.is_success_processed = entity.is_success_processed
        orm_doc.processed_at = entity.processed_at
        session.flush()