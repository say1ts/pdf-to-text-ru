from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Callable
from sqlalchemy.orm import Session
from PIL import Image
import logging

from icecream import ic

from src.converters.pdf_to_page_images import get_all_pdf_files, convert_pdf_to_images, PdfConversionError, PageConversionResult
from src.repository import documents as doc_repo, pages as page_repo, fragments as fragment_repo
from src.recognizers.layout_analyzer import analyze_pdf, LayoutAnalyzerError
from src.utils.image_saver import save_page_image, save_fragment_image
from src.utils.coordinates import scale_coordinates
from src.entities import Document, Page, Fragment


def group_fragments_by_page_number(fragments: List[Fragment]) -> Dict[int, List[Fragment]]:
    """Группирует фрагменты по номеру страницы (page_number из анализатора)."""
    pages: Dict[int, List[Fragment]] = defaultdict(list)
    for fragment in fragments:
        pages[fragment.page_number].append(fragment)
    return pages

class PdfProcessor:
    """
    Инкапсулирует логику обработки одного PDF-документа.
    """
    def __init__(
        self,
        pdf_path: Path,
        output_dir: Path,
        dpi: int,
        session: Session,
        logger: logging.LoggerAdapter,
        order_strategy: Callable[[List[Fragment]], List[int]]
    ):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.dpi = dpi
        self.session = session
        self.logger = logger
        self.order_strategy = order_strategy
        self.filename = pdf_path.stem
        self.extension = pdf_path.suffix.lstrip(".")
        self.document: Optional[Document] = None

    def process(self) -> Optional[Document]:
        """Основной метод, запускающий пайплайн обработки."""
        if not self._get_or_create_document():
            self.logger.info({"file": self.filename, "status": "skipped"})
            return None

        try:
            # 1. Анализируем разметку документа
            fragments = analyze_pdf(str(self.pdf_path))
            fragments_by_page = group_fragments_by_page_number(fragments)

            # 2. Конвертируем PDF в изображения и обрабатываем постранично
            for result in convert_pdf_to_images(self.pdf_path, dpi=self.dpi):
                self._process_page(result, fragments_by_page)

            # 3. Завершаем обработку
            self._finalize_processing(success=True)
            return self.document

        except (LayoutAnalyzerError, PdfConversionError) as e:
            self.logger.error({"file": self.filename, "error": str(e)})
            self._finalize_processing(success=False)
            return None

    def _get_or_create_document(self) -> bool:
        """Получает документ из БД или создает новый. Возвращает False, если документ уже успешно обработан."""
        doc = doc_repo.get_document_by_filename(self.session, self.filename)
        if doc and doc.is_success_processed:
            return False

        if not doc:
            doc = Document(document_id=None, filename=self.filename, extension=self.extension)
            doc_repo.create_document(self.session, doc)

        self.document = doc
        return True

    def _process_page(self, conv_result: PageConversionResult, all_fragments: Dict[int, List[Fragment]]):
        """Обрабатывает одну страницу: сохраняет, создает сущности, нарезает фрагменты."""
        if conv_result.error or not conv_result.image:
            self.logger.error({"file": self.filename, "page": conv_result.page_number, "error": conv_result.error})
            return

        # 1. Создаем запись о странице в БД
        page = self._create_and_save_page(conv_result)

        # 2.1 Получаем фрагменты для текущей страницы
        page_fragments = all_fragments.get(page.number, [])
        if not page_fragments:
            return

        # 2.2 Определяем и сохраняем порядок чтения
        self._set_fragments_order(page_fragments)
        
        # 3. Создаем записи о фрагментах в БД и нарезаем фрагменты по координатам
        self._create_fragments(page, page_fragments)
        self._crop_and_save_fragments(conv_result.image, page.number, page_fragments)
        
        self.logger.info({"page": page.number, "fragments_created": len(page_fragments)})


    def _create_and_save_page(self, conv_result: PageConversionResult) -> Page:
        page_entity = Page(
            page_id=None,
            document_id=self.document.document_id,
            number=conv_result.page_number,
            dpi=self.dpi,
            width=conv_result.image.width,
            height=conv_result.image.height
        )
        page_repo.create_page(self.session, page_entity)
        save_page_image(conv_result.image, self.output_dir, self.document.filename, page_entity.number, page_entity.page_id)
        self.logger.info({"page": page_entity.number, "status": "processed"})
        return page_entity

    def _create_fragments(self, page: Page, fragments: List[Fragment]):
        for frag in fragments:
            frag.page_id = page.page_id  # Теперь устанавливаем только здесь
            fragment_repo.create_fragment(self.session, frag)

    def _crop_and_save_fragments(self, page_image: Image.Image, page_number: int, fragments: List[Fragment]):
        for fragment in fragments:
            try:
                pt_coords = (fragment.left, fragment.top, fragment.width, fragment.height)
                px_crop_box = scale_coordinates(pt_coords, self.dpi, page_image._size)
                save_fragment_image(
                    page_image=page_image,
                    output_dir=self.output_dir,
                    filename=self.filename,
                    page_number=page_number,
                    fragment=fragment,
                    crop_box=px_crop_box
                )
            except Exception as e:
                self.logger.error({
                    "msg": "Failed to crop fragment image",
                    "page": page_number,
                    "fragment_id": fragment.fragment_id,
                    "error": str(e)
                })

    def _set_fragments_order(self, fragments: List[Fragment]):
        if not fragments:
            return
        ordered_indices = self.order_strategy(fragments)
        for order_num, original_index in enumerate(ordered_indices):
            fragments[original_index].order_number = order_num
            
        # self.logger.info({"page": fragments[0].page_id, "fragments_ordered": len(ordered_indices)})/


    def _finalize_processing(self, success: bool):
        if self.document:
            self.document.is_success_processed = success
            self.document.processed_at = datetime.utcnow()
            doc_repo.update_document_status(self.session, self.document)

        if success:
            self.session.commit()
            self.logger.info({"file": self.filename, "status": "successfully_processed"})
        else:
            self.session.rollback()
            self.logger.error({"file": self.filename, "status": "processing_failed"})         

def process_single_pdf(
    pdf_path: Path,
    output_dir: Path,
    dpi: int,
    session: Session,
    logger: logging.LoggerAdapter,
    order_strategy: Callable[[List[Fragment]], List[int]]
) -> Optional[Document]:
    """
    Создает экземпляр PdfProcessor и запускает обработку для одного файла.
    """
    processor = PdfProcessor(pdf_path, output_dir, dpi, session, logger, order_strategy)
    return processor.process()


def process_bulk_pdf(
    pdf_folder: Path,
    output_dir: Path,
    dpi: int,
    session: Session,
    logger: logging.LoggerAdapter,
    order_strategy: Callable[[List[Fragment]], List[int]]
) -> List[Document]:
    """
    Обрабатывает все PDF-файлы в указанной директории.
    """
    try:
        pdf_files = get_all_pdf_files(pdf_folder)
    except FileNotFoundError:
        logger.warning(f"No PDF files found in {pdf_folder}")
        return []

    processed_docs = []
    for pdf_path in pdf_files:
        logger.info(f"Starting processing for {pdf_path.name}")
        document = process_single_pdf(pdf_path, output_dir, dpi, session, logger, order_strategy)
        if document:
            processed_docs.append(document)
    return processed_docs
