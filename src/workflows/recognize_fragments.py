from pathlib import Path
from typing import List, Dict
from sqlalchemy.orm import Session
from functools import reduce
import logging

from src.config import config_provider
from src.entities import Document, Fragment, RecognizedFragment
from src.repository import fragments as fragment_repo, pages as page_repo, recognized_fragments as recognized_repo
from src.recognizers.base_recognizer import BaseRecognizer
from src.recognizers.text_recognizer import TextRecognizer
from src.utils.image_saver import settings

logger = config_provider.get_logger(__name__)

RECOGNIZER_FACTORIES: Dict[str, callable] = {
    "text": lambda: TextRecognizer(),
    # "table": lambda: TableRecognizer(), 
    # "formula": lambda: TableRecognizer(), 
}

def get_recognizer_instance(recognizer_type: str) -> BaseRecognizer:
    factory = RECOGNIZER_FACTORIES.get(recognizer_type)
    if not factory:
        raise ValueError(f"Unknown recognizer type: {recognizer_type}")
    return factory()

def get_fragments_to_recognize(
    session: Session, document: Document, allowed_types: List[str]
) -> List[Fragment]:
    pages = page_repo.get_pages_by_document_id(session, document.document_id)
    all_fragments = [
        f for page in pages
        for f in fragment_repo.get_fragments_by_page_id(session, page.page_id)
        if f.content_type.value in allowed_types
    ]
    return all_fragments

def process_single_fragment(
    session: Session,
    fragment: Fragment,
    recognizer: BaseRecognizer,
    recognizer_name: str,
    output_dir: Path,
    filename: str
) -> bool:
    image_path = output_dir / settings.IMAGE_FRAGMENT_PATH_TEMPLATE.format(
        filename=filename,
        page_number=fragment.page_number,
        order_number=fragment.order_number or 0,
        fragment_id=fragment.fragment_id,
        content_type=fragment.content_type.value.lower(),
        extension=settings.IMAGE_FORMAT.lower()
    )
    try:
        existing = recognized_repo.get_recognized_fragment_by_fragment_id(
            session, fragment.fragment_id, recognizer_name)
        if existing:
            logger.info({"fragment_id": fragment.fragment_id, "msg": 'Already recognized by this tool.'})
            return False
        
        recognized_text = recognizer.recognize_image(image_path)
        if not recognized_text:
            return False

        new_entity = RecognizedFragment(
            recognized_fragment_id=None,
            fragment_id=fragment.fragment_id,
            recognizer=recognizer_name,
            text=recognized_text,
            confidence=None,
        )
        recognized_repo.create_recognized_fragment(session, new_entity)
        
        return True
    except Exception as e:
        logger.error({"fragment_id": fragment.fragment_id, "error": str(e)})
        return False

def recognize_single_document(
    document: Document,
    session: Session,
    logger: logging.LoggerAdapter,
    recognizer_type: str
) -> Document:
    allowed_types = settings.RECOGNIZER_ALLOWED_TYPES.get(recognizer_type, [])
    fragments = get_fragments_to_recognize(session, document, allowed_types)
    if not fragments:
        logger.info({"document": document.filename, "msg": "No fragments to recognize"})
        return document

    recognizer = get_recognizer_instance(recognizer_type)
    recognizer_name = f"{recognizer_type}-qwen2-vl-ocr-2b-instruct"

    results = map(
        lambda f: process_single_fragment(session, f, recognizer, recognizer_name, settings.IMAGE_OUTPUT_DIR, document.filename),
        fragments
    )
    successful = reduce(lambda acc, res: acc + (1 if res else 0), results, 0)

    logger.info({"document": document.filename, "recognized": successful, "total": len(fragments)})
    session.commit()
    return document

def recognize_bulk_fragments(
    documents: List[Document],
    session: Session,
    logger: logging.LoggerAdapter,
    recognizer_type: str
) -> List[Document]:
    return [recognize_single_document(doc, session, logger, recognizer_type) for doc in documents]