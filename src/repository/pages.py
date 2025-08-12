from sqlalchemy.orm import Session
from src.database.models import Page
from typing import List, Optional

def create_page(
    session: Session,
    document_id: int,
    page_number: int,
    dpi: int,
    width: Optional[int] = None,
    height: Optional[int] = None
) -> Page:
    """Create a new Page record in the database."""
    page = Page(
        document_id=document_id,
        number=page_number,
        dpi=dpi,
        width=width,
        height=height
    )
    session.add(page)
    session.flush()  # Ensure page_id is available
    return page

def get_pages_by_document_id(session: Session, document_id: int) -> List[Page]:
    """Retrieve all Pages for a given document_id."""
    return session.query(Page).filter(Page.document_id == document_id).all()
