from sqlalchemy.orm import Session
from src.database.models import Fragment as ORMFragment
from src.entities import Fragment as EntityFragment, TextFragment, TableFragment, ImageFragment, ContentType
from typing import List
from datetime import datetime

def create_fragment(session: Session, entity: EntityFragment) -> EntityFragment:
    orm_fragment = entity.to_orm(ORMFragment)
    session.add(orm_fragment)
    session.flush()
    entity.fragment_id = orm_fragment.fragment_id
    
    # Return appropriate subtype
    if entity.content_type == ContentType.TEXT:
        return TextFragment(**vars(entity))
    elif entity.content_type == ContentType.TABLE:
        return TableFragment(**vars(entity))
    elif entity.content_type == ContentType.PICTURE:
        return ImageFragment(**vars(entity))
    return entity

def get_fragments_by_page_id(session: Session, page_id: int) -> List[EntityFragment]:
    orm_fragments = session.query(ORMFragment).filter(ORMFragment.page_id == page_id).all()
    return [EntityFragment.from_orm(orm_fragment) for orm_fragment in orm_fragments]

def update_fragment_crop_status(session: Session, entity: EntityFragment, is_cropped: bool) -> None:
    orm_fragment = session.query(ORMFragment).filter(ORMFragment.fragment_id == entity.fragment_id).first()
    if orm_fragment:
        orm_fragment.is_cropped = is_cropped
        orm_fragment.cropped_at = datetime.utcnow() if is_cropped else None
        entity.is_cropped = is_cropped
        entity.cropped_at = orm_fragment.cropped_at
        session.flush()

def update_fragment_order(session: Session, entity: EntityFragment, order_number: int) -> None:
    orm_fragment = session.query(ORMFragment).filter(ORMFragment.fragment_id == entity.fragment_id).first()
    if orm_fragment:
        orm_fragment.order_number = order_number
        entity.order_number = order_number
        session.flush()