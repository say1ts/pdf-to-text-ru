from sqlalchemy.orm import Session
from src.database.models import Fragment as ORMFragment
from src.entities import Fragment
from typing import List


def create_fragment(session: Session, entity: Fragment) -> Fragment:
    orm_fragment = entity.to_orm(ORMFragment)
    session.add(orm_fragment)
    session.flush()
    entity.fragment_id = orm_fragment.fragment_id
    return entity


def get_fragments_by_page_id(session: Session, page_id: int) -> List[Fragment]:
    orm_fragments = session.query(ORMFragment).filter(ORMFragment.page_id == page_id).all()
    return [Fragment.from_orm(orm_fragment) for orm_fragment in orm_fragments]


def update_fragment_order(session: Session, entity: Fragment, order_number: int) -> None:
    orm_fragment = (
        session.query(ORMFragment).filter(ORMFragment.fragment_id == entity.fragment_id).first()
    )
    if orm_fragment:
        orm_fragment.order_number = order_number
        entity.order_number = order_number
        session.flush()
