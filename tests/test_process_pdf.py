import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.workflows.process_pdf import process_pdf
from src.database.models import Document, Page
from src.converters.pdf_to_page_images import PageConversionResult
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
@patch("src.workflows.process_pdf.save_page_image")
@patch("src.workflows.process_pdf.convert_pdf_to_images")
def test_process_pdf_success(
    mock_convert_pdf,
    mock_save_image,
    mock_create_page,
    mock_create_document,
    mock_get_document,
    mock_session,
    mock_image
):
    # Arrange
    pdf_path = Path("test.pdf")
    output_dir = Path("data/images")
    dpi = 150
    
    mock_get_document.return_value = None
    mock_document = Document(document_id=1, filename="test", extension=".pdf")
    mock_create_document.return_value = mock_document
    mock_page = Page(page_id=1, document_id=1, number=1, dpi=150, width=800, height=600)
    mock_create_page.return_value = mock_page
    mock_save_image.return_value = Path("data/images/test/1_1_1.png")
    mock_convert_pdf.return_value = [
        PageConversionResult(page_number=1, image=mock_image, error=None)
    ]
    
    # Act
    document = process_pdf(pdf_path, output_dir, dpi, mock_session)
    
    # Assert
    assert document == mock_document
    mock_get_document.assert_called_once_with(mock_session, "test")
    mock_create_document.assert_called_once_with(mock_session, "test", ".pdf")
    mock_create_page.assert_called_once_with(
        mock_session, document_id=1, page_number=1, dpi=150, width=800, height=600
    )
    mock_save_image.assert_called_once_with(
        image=mock_image,
        output_dir=output_dir,
        filename="test",
        page_number=1,
        page_id=1
    )
    mock_session.commit.assert_called()