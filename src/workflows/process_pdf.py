from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Callable, Tuple
from sqlalchemy.orm import Session
from PIL import Image
import logging

from src.converters.pdf_to_page_images import get_all_pdf_files, convert_pdf_to_images, PdfConversionError, PageConversionResult
from src.repository import documents as doc_repo, pages as page_repo, fragments as fragment_repo
from src.recognizers.layout_analyzer import analyze_pdf, LayoutAnalyzerError
from src.utils.image_saver import save_page_image, save_fragment_image
from src.utils.coordinates import scale_coordinates_from_pt_to_px
from src.entities import Document, Fragment, Page, RawFragment


def group_fragments_by_page_number(fragments: List[RawFragment]) -> Dict[int, List[RawFragment]]:
    """Группирует фрагменты по номеру страницы (page_number из анализатора)."""
    pages: Dict[int, List[RawFragment]] = defaultdict(list)
    for fragment in fragments:
        pages[fragment['page_number']].append(fragment)
    return pages

def convert_raw_fragments_to_fragments(
    raw_page_fragments: List[RawFragment], dpi: int, image_size: Tuple[int, int]) -> List[Fragment]:
    page_fragments = []
    
    for raw_fr in raw_page_fragments:
        px_crop_box = scale_coordinates_from_pt_to_px(
            raw_fr['left'], 
            raw_fr['top'], 
            raw_fr['width'],
            raw_fr['height'],
            image_size,
            dpi
        )
        page_fragments.append(Fragment.from_dict(raw_fr, px_crop_box))
    return page_fragments
    

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
            raw_fragments = analyze_pdf(str(self.pdf_path))
            grouped_raw_fragments_by_page = group_fragments_by_page_number(raw_fragments)

            # 2. Конвертируем PDF в изображения и обрабатываем постранично
            for result in convert_pdf_to_images(self.pdf_path, dpi=self.dpi):
                self._process_page(result, grouped_raw_fragments_by_page)

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

    def _process_page(self, conv_result: PageConversionResult, all_fragments: Dict[int, List[RawFragment]]):
        """Обрабатывает одну страницу: сохраняет, создает сущности, нарезает фрагменты."""
        if conv_result.error or not conv_result.image:
            self.logger.error({"file": self.filename, "page": conv_result.page_number, "error": conv_result.error})
            return

        # 1. Создаем запись о странице в БД
        page = self._create_and_save_page(conv_result)

        # 2.1 Получаем фрагменты для текущей страницы
        raw_fragments = all_fragments.get(page.number, [])
        if not raw_fragments:
            return

        # 2.2 Преобразовываем сырые фрагменты
        page_fragments = convert_raw_fragments_to_fragments(
            raw_fragments, self.dpi, conv_result.image._size)
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
                save_fragment_image(
                    page_image=page_image,
                    output_dir=self.output_dir,
                    filename=self.filename,
                    page_number=page_number,
                    fragment=fragment,
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
