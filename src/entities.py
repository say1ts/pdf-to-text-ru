
# from dataclasses import dataclass
# from datetime import datetime
# from typing import List, Optional

from enum import Enum


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
    
# @dataclass
# class RecognizedFragment:
#     recognized_fragment_id: int
#     fragment_id: int
#     recognize_processor: str
#     result: Optional[str]
#     recognized_at: datetime

# @dataclass
# class Fragment:
#     fragment_id: int
#     order_number: Optional[int]
#     content_type: ContentType
    
#     left: float
#     top: float
#     width: float
#     height: float
    
#     text: Optional[str]
#     is_cropped: bool
#     created_at: datetime
#     cropped_at: Optional[datetime]
    
#     recognized_fragment: Optional[RecognizedFragment]
    
#     @property
#     def right(self) -> float:
#         return self.left + self.width

#     @property
#     def bottom(self) -> float:
#         return self.top + self.height

# @dataclass
# class Page:
#     page_id: int
#     original_file_id: int
    
#     number: int
#     dpi: int
#     width: int
#     height: int
    
#     fragments: List[Fragment]

# @dataclass
# class Document:
#     document_id: int
#     filename: str
#     extension: Optional[str]
#     is_success_processed: bool
#     processed_at: datetime
#     pages: List[Page]
    