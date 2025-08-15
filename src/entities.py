from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple, TypedDict

class ContentType(Enum):
    SECTION_HEADER = "Section header"
    TITLE = "Title"
    PAGE_HEADER = "Page header"
    PAGE_FOOTER = "Page footer"
    TEXT = "Text"
    LIST_ITEM = "List item"
    CAPTION = "Caption"
    FOOTNOTE = "Footnote"
    FORMULA = "Formula"
    PICTURE = "Picture"
    TABLE = "Table"

@dataclass
class Document:
    document_id: Optional[int]
    filename: str
    extension: str
    is_success_processed: bool = False
    processed_at: Optional[datetime] = None

    def to_orm(self, orm_model):
        return orm_model(
            document_id=self.document_id,
            filename=self.filename,
            extension=self.extension,
            is_success_processed=self.is_success_processed,
            processed_at=self.processed_at
        )

    @classmethod
    def from_orm(cls, orm_doc):
        return cls(
            document_id=orm_doc.document_id,
            filename=orm_doc.filename,
            extension=orm_doc.extension,
            is_success_processed=orm_doc.is_success_processed,
            processed_at=orm_doc.processed_at
        )

@dataclass
class Page:
    page_id: Optional[int]
    document_id: int
    number: int
    dpi: int
    width: int
    height: int

    def to_orm(self, orm_model):
        return orm_model(
            page_id=self.page_id,
            document_id=self.document_id,
            number=self.number,
            dpi=self.dpi,
            width=self.width,
            height=self.height
        )

    @classmethod
    def from_orm(cls, orm_page):
        return cls(
            page_id=orm_page.page_id,
            document_id=orm_page.document_id,
            number=orm_page.number,
            dpi=orm_page.dpi,
            width=orm_page.width,
            height=orm_page.height
        )

class RawFragment(TypedDict):
    left: float
    top: float
    width: float
    height: float
    page_number: int
    page_width: int
    page_height: int
    type: str
    text: str | None

@dataclass
class Fragment:
    fragment_id: Optional[int]
    page_id: Optional[int]
    page_number: Optional[int]
    content_type: ContentType
    order_number: Optional[int]
    left: float
    top: float
    width: float
    height: float
    coord_type = Optional[str]
    text: Optional[str]
    created_at: Optional[datetime] = None
    cropped_at: Optional[datetime] = None

    def to_orm(self, orm_model):
        return orm_model(
            fragment_id=self.fragment_id,
            page_id=self.page_id,
            page_number=self.page_number,
            content_type=self.content_type.value,
            order_number=self.order_number,
            left=self.left,
            top=self.top,
            width=self.width,
            height=self.height,
            text=self.text,
            created_at=self.created_at or datetime.utcnow(),
            cropped_at=self.cropped_at
        )

    @classmethod
    def from_dict(cls, data: dict, coords: Tuple[int, int, int, int], page_id: int = None):
        return cls(
            fragment_id=None,
            page_id=page_id,
            page_number=data["page_number"],
            content_type=ContentType(data["type"]),
            order_number=None,
            left=coords[0],
            top=coords[1],
            width=coords[2],
            height=coords[3],
            text=data.get("text")
        )

    @classmethod
    def from_orm(cls, orm_fragment):
        return cls(
            fragment_id=orm_fragment.fragment_id,
            page_id=orm_fragment.page_id,
            page_number=orm_fragment.page_number,
            content_type=ContentType(orm_fragment.content_type),
            order_number=orm_fragment.order_number,
            left=orm_fragment.left,
            top=orm_fragment.top,
            width=orm_fragment.width,
            height=orm_fragment.height,
            text=orm_fragment.text,
            created_at=orm_fragment.created_at,
            cropped_at=orm_fragment.cropped_at
        )

@dataclass
class TextFragment(Fragment):
    pass

@dataclass
class TableFragment(Fragment):
    pass

@dataclass
class ImageFragment(Fragment):
    pass

@dataclass
class RecognizedFragment:
    recognized_fragment_id: Optional[int]
    fragment_id: int
    
    recognizer: str
    text: str
    confidence: Optional[float]

    def to_orm(self, orm_model):
        return orm_model(
            recognized_fragment_id=self.recognized_fragment_id,
            fragment_id=self.fragment_id,
            recognizer=self.recognizer,
            text=self.text,
            confidence=self.confidence
        )

    @classmethod
    def from_orm(cls, orm_recognized):
        return cls(
            recognized_fragment_id=orm_recognized.recognized_fragment_id,
            fragment_id=orm_recognized.fragment_id,
            recognizer=orm_recognized.recognizer,
            text=orm_recognized.text,
            confidence=orm_recognized.confidence
        )
        