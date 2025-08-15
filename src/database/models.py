from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = 'document'

    document_id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, nullable=False, unique=True)
    extension = Column(String)
    is_success_processed = Column(Boolean, nullable=False, default=False)
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    pages = relationship("Page", back_populates="document")

    __table_args__ = (
        Index('ix_document_filename', 'filename'),
    )

class Page(Base):
    __tablename__ = 'page'
    page_id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('document.document_id'), nullable=False)
    number = Column(Integer, nullable=False)
    dpi = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    document = relationship("Document", back_populates="pages")
    fragments = relationship("Fragment", back_populates="page")

    __table_args__ = (
        Index('ix_page_document_id', 'document_id'),
        Index('ix_page_number', 'number'),
    )

class Fragment(Base):
    __tablename__ = 'fragment'

    fragment_id = Column(Integer, primary_key=True, autoincrement=True)
    content_type = Column(String, nullable=False)
    order_number = Column(Integer, nullable=True)
    left = Column(Float, nullable=False)
    top = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    page_id = Column(Integer, ForeignKey('page.page_id'), nullable=False)
    page_number = Column(Integer, nullable=False)
    text = Column(String)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    cropped_at = Column(DateTime)
    page = relationship("Page", back_populates="fragments")
    recognized_fragments = relationship("RecognizedFragment", back_populates="fragment")

    __table_args__ = (
        Index('ix_fragment_page_id', 'page_id'),
    )

class RecognizedFragment(Base):
    __tablename__ = 'recognized_fragment'

    recognized_fragment_id = Column(Integer, primary_key=True, autoincrement=True)
    fragment_id = Column(Integer, ForeignKey('fragment.fragment_id'), nullable=False)
    text = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    recognized_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    fragment = relationship("Fragment", back_populates="recognized_fragments")

    __table_args__ = (
        Index('ix_recognized_fragment_fragment_id', 'fragment_id'),
    )