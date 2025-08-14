import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.workflows.process_pdf import process_single_pdf
from src.entities import Document, Page, TextFragment, ContentType
from src.converters.pdf_to_page_images import PageConversionResult
from src.utils.reading_order import get_default_order, ReadingOrderService
from PIL import Image
from sqlalchemy.orm import Session

@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)

@pytest.fixture
def mock_image():
    image = MagicMock(spec=Image.Image)
    image.width = 800
    image.height = 600
    return image

@patch("src.workflows.process_pdf.get_document_by_filename")
@patch("src.workflows.process_pdf.create_document")
@patch("src.workflows.process_pdf.create_page")
@patch("src.workflows.process_pdf.create_fragment")
@patch("src.workflows.process_pdf.save_page_image")
@patch("src.workflows.process_pdf.save_fragment_image")
@patch("src.workflows.process_pdf.convert_pdf_to_images")
@patch("src.workflows.process_pdf.analyze_pdf")
@patch("src.workflows.process_pdf.update_document_status")
@patch("src.workflows.process_pdf.update_fragment_crop_status")
@patch("src.workflows.process_pdf.update_fragment_order")
def test_process_single_pdf_success(
    mock_update_fragment_order,
    mock_update_fragment_crop_status,
    mock_update_status,
    mock_analyze_pdf,
    mock_convert_pdf,
    mock_save_fragment_image,
    mock_save_page_image,
    mock_create_fragment,
    mock_create_page,
    mock_create_document,
    mock_get_document,
    mock_session,
    mock_image
):
    pdf_path = Path("test.pdf")
    output_dir = Path("data/images")
    dpi = 150
    logger = MagicMock()
    
    mock_get_document.return_value = None
    entity_doc = Document(document_id=1, filename="test", extension="pdf")
    mock_create_document.return_value = entity_doc
    entity_page = Page(page_id=1, document_id=1, number=1, dpi=150, width=800, height=600)
    mock_create_page.return_value = entity_page
    entity_fragment = TextFragment(fragment_id=1, page_id=1, content_type=ContentType.TEXT, order_number=None, left=10.0, top=20.0, width=100.0, height=50.0, text="Sample text")
    mock_create_fragment.return_value = entity_fragment
    mock_save_page_image.return_value = Path("data/images/test/page_1_1.png")
    mock_save_fragment_image.return_value = Path("data/images/test/fragment_1_0_1.png")
    mock_convert_pdf.return_value = [
        PageConversionResult(page_number=1, image=mock_image, error=None)
    ]
    mock_analyze_pdf.return_value = [
        {
            "left": 10.0,
            "top": 20.0,
            "width": 100.0,
            "height": 50.0,
            "page_number": 1,
            "page_width": 595,
            "page_height": 842,
            "type": "text",
            "text": "Sample text"
        }
    ]
    
    document = process_single_pdf(pdf_path, output_dir, dpi, mock_session, logger, order_strategy=get_default_order)
    
    assert document == entity_doc
    mock_get_document.assert_called_once_with(mock_session, "test")
    mock_create_document.assert_called_once()
    mock_create_page.assert_called_once()
    mock_create_fragment.assert_called_once()
    mock_save_page_image.assert_called_once()
    mock_save_fragment_image.assert_called_once()
    mock_update_fragment_crop_status.assert_called_once()
    mock_update_fragment_order.assert_called_once()
    mock_update_status.assert_called_once()
    mock_session.commit.assert_called_once()

@patch("src.workflows.process_pdf.get_document_by_filename")
@patch("src.workflows.process_pdf.create_document")
@patch("src.workflows.process_pdf.create_page")
@patch("src.workflows.process_pdf.create_fragment")
@patch("src.workflows.process_pdf.save_page_image")
@patch("src.workflows.process_pdf.save_fragment_image")
@patch("src.workflows.process_pdf.convert_pdf_to_images")
@patch("src.workflows.process_pdf.analyze_pdf")
@patch("src.workflows.process_pdf.update_document_status")
@patch("src.workflows.process_pdf.update_fragment_crop_status")
@patch("src.workflows.process_pdf.update_fragment_order")
def test_process_single_pdf_with_reading_order(
    mock_update_fragment_order,
    mock_update_fragment_crop_status,
    mock_update_status,
    mock_analyze_pdf,
    mock_convert_pdf,
    mock_save_fragment_image,
    mock_save_page_image,
    mock_create_fragment,
    mock_create_page,
    mock_create_document,
    mock_get_document,
    mock_session,
    mock_image
):
    pdf_path = Path("test.pdf")
    output_dir = Path("data/images")
    dpi = 150
    logger = MagicMock()
    
    mock_get_document.return_value = None
    entity_doc = Document(document_id=1, filename="test", extension="pdf")
    mock_create_document.return_value = entity_doc
    entity_page = Page(page_id=1, document_id=1, number=1, dpi=150, width=800, height=600)
    mock_create_page.return_value = entity_page
    entity_fragment = TextFragment(fragment_id=1, page_id=1, content_type=ContentType.TEXT, order_number=None, left=10.0, top=20.0, width=100.0, height=50.0, text="Sample text")
    mock_create_fragment.return_value = entity_fragment
    mock_save_page_image.return_value = Path("data/images/test/page_1_1.png")
    mock_save_fragment_image.return_value = Path("data/images/test/fragment_1_0_1.png")
    mock_convert_pdf.return_value = [
        PageConversionResult(page_number=1, image=mock_image, error=None)
    ]
    mock_analyze_pdf.return_value = [
        {
            "left": 10.0,
            "top": 20.0,
            "width": 100.0,
            "height": 50.0,
            "page_number": 1,
            "page_width": 595,
            "page_height": 842,
            "type": "text",
            "text": "Sample text"
        }
    ]
    
    order_strategy = ReadingOrderService().get_reading_order
    document = process_single_pdf(pdf_path, output_dir, dpi, mock_session, logger, order_strategy=order_strategy)
    
    assert document == entity_doc
    mock_update_fragment_order.assert_called_once()

@patch("src.workflows.process_pdf.get_document_by_filename")
def test_process_single_pdf_invalid_fragments(mock_get_document, mock_session):
    pdf_path = Path("test.pdf")
    logger = MagicMock()
    
    with patch("src.workflows.process_pdf.analyze_pdf") as mock_analyze_pdf:
        mock_analyze_pdf.return_value = [
            {
                "left": 10.0,
                "top": 20.0,
                "width": 10.0,
                "height": 5.0,
                "page_number": 1,
                "page_width": 595,
                "page_height": 842,
                "type": "text"
            }
        ]
        document = process_single_pdf(pdf_path, Path("data/images"), 150, mock_session, logger, get_default_order)
        
        assert document is not None
        logger.debug.assert_called_with({"file": str(pdf_path), "fragments_received": 1, "fragments_valid": 0})
        