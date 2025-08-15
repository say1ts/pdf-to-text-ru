from sqlalchemy.orm import Session
from src.database.models import RecognizedFragment as ORMRecognizedFragment
from src.entities import RecognizedFragment
from typing import Optional
from datetime import datetime

def create_recognized_fragment(session: Session, entity: RecognizedFragment) -> RecognizedFragment:
    orm_fragment = entity.to_orm(ORMRecognizedFragment)
    session.add(orm_fragment)
    session.flush()
    entity.recognized_fragment_id = orm_fragment.recognized_fragment_id
    return entity

def get_recognized_fragment_by_fragment_id(
    session: Session, fragment_id: int, recognizer: str
) -> Optional[RecognizedFragment]:
    orm_frag = session.query(ORMRecognizedFragment).filter(
        ORMRecognizedFragment.fragment_id == fragment_id,
        ORMRecognizedFragment.recognizer == recognizer
    ).first()
    return RecognizedFragment.from_orm(orm_frag) if orm_frag else None

def update_recognized_fragment(
    session: Session, entity: RecognizedFragment, recognized_text: str
) -> None:
    orm_frag = session.query(ORMRecognizedFragment).filter(
        ORMRecognizedFragment.recognized_fragment_id == entity.recognized_fragment_id
    ).first()
    if orm_frag:
        orm_frag.text = recognized_text
        orm_frag.recognized_at = datetime.utcnow()
        session.flush()
        