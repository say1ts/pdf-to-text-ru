from sqlalchemy.orm import Session
from src.database.models import Page as ORMPage
from src.entities import Page
from typing import List


def create_page(session: Session, entity: Page) -> Page:
    orm_page = entity.to_orm(ORMPage)
    session.add(orm_page)
    session.flush()
    entity.page_id = orm_page.page_id
    return entity


def get_pages_by_document_id(session: Session, document_id: int) -> List[Page]:
    orm_pages = session.query(ORMPage).filter(ORMPage.document_id == document_id).all()
    return [Page.from_orm(orm_page) for orm_page in orm_pages]
