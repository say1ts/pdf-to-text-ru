from pathlib import Path
from typing import List, Optional, Iterator, NamedTuple
from PIL import Image
from pdf2image import pdfinfo_from_path, convert_from_path


class PDFPageCountError(Exception):
    """Custom exception for PDF conversion errors."""
    pass

class PdfConversionError(Exception):
    """Custom exception for PDF conversion errors."""
    pass

class PageConversionResult(NamedTuple):
    """Result of converting a single PDF page."""
    page_number: int
    image: Optional[Image.Image]
    error: Optional[str]

def validate_pdf_folder(pdf_folder: str) -> Path:
    """Validates and returns the PDF folder path."""
    folder = Path(pdf_folder)
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"Directory {pdf_folder} does not exist or is not a directory")
    return folder

def get_first_pdf_file(pdf_folder: str) -> Path:
    """Returns the first PDF file found in the specified folder.

    Args:
        pdf_folder: Path to the folder containing PDF files.

    Returns:
        Path to the first PDF file.

    Raises:
        FileNotFoundError: If no PDF files are found in the folder.
        ValueError: If the folder is invalid.
    """
    folder = validate_pdf_folder(pdf_folder)
    for file_path in folder.glob("*.pdf"):
        return file_path
    raise FileNotFoundError(f"No PDF files found in {folder}")

def get_all_pdf_files(pdf_folder: str) -> List[Path]:
    """Returns a list of all PDF files in the specified folder.

    Args:
        pdf_folder: Path to the folder containing PDF files.

    Returns:
        List of Path objects for all PDF files.

    Raises:
        FileNotFoundError: If no PDF files are found in the folder.
        ValueError: If the folder is invalid.
    """
    folder = validate_pdf_folder(pdf_folder)
    pdf_files = list(folder.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {folder}")
    return pdf_files

def get_pdf_page_count(pdf_path: Path) -> int:
    """Returns the total number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Number of pages in the PDF.

    Raises:
        PdfConversionError: If unable to retrieve PDF information.
    """
    try:
        pdf_info = pdfinfo_from_path(pdf_path)
        return pdf_info["Pages"]
    except PDFPageCountError as e:
        raise PdfConversionError(f"Failed to get page count for {pdf_path}: {e}")

def convert_pdf_to_images(pdf_path: Path, max_pages: Optional[int] = None, dpi: int = 150) -> Iterator[PageConversionResult]:
    """Yields results of converting PDF pages to images.

    Args:
        pdf_path: Path to the PDF file.
        max_pages: Maximum number of pages to convert. If None, converts all pages.
        dpi: Resolution for conversion (default: 150).

    Yields:
        PageConversionResult for each page, containing the page number, image, and any error.

    Raises:
        PdfConversionError: If the PDF cannot be processed.
        ValueError: If invalid parameters are provided.
    """
    if dpi <= 0:
        raise ValueError("DPI must be a positive integer")
    if max_pages is not None and max_pages < 0:
        raise ValueError("max_pages must be non-negative")

    try:
        total_pages = get_pdf_page_count(pdf_path)
        pages_to_convert = min(total_pages, max_pages) if max_pages is not None else total_pages

        for page_num in range(1, pages_to_convert + 1):
            try:
                images = convert_from_path(
                    pdf_path,
                    dpi=dpi,
                    first_page=page_num,
                    last_page=page_num,
                    thread_count=1
                )
                yield PageConversionResult(page_number=page_num, image=images[0] if images else None, error=None)
                del images
            except Exception as e:
                yield PageConversionResult(page_number=page_num, image=None, error=str(e))
    except Exception as e:
        raise PdfConversionError(f"Failed to process {pdf_path}: {e}")
    