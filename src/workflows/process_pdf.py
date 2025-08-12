from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from src.database.models import Document
from src.converters.pdf_to_page_images import get_first_pdf_file, convert_pdf_to_images, PdfConversionError
from src.repository.documents import create_document, get_document_by_filename
from src.repository.pages import create_page
from src.utils.image_saver import save_page_image
from src.settings import settings
import logging

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def process_pdf(pdf_path: Path, output_dir: Path, dpi: int, session: Session) -> Optional[Document]:
    """Process a single PDF file, convert pages to images, and save metadata."""
    try:
        # Extract filename and extension
        filename = pdf_path.stem
        extension = pdf_path.suffix
        
        # Check if document already exists
        if get_document_by_filename(session, filename):
            logger.warning(f"Document {filename} already exists in database, skipping")
            return None
            
        # Create document record
        document = create_document(session, filename, extension)
        logger.info(f"Created document: {filename} (ID: {document.document_id})")
        
        # Convert PDF to images
        for result in convert_pdf_to_images(pdf_path, dpi=dpi):
            try:
                # Create page record
                width = result.image.width if result.image else None
                height = result.image.height if result.image else None
                page = create_page(
                    session=session,
                    document_id=document.document_id,
                    page_number=result.page_number,
                    dpi=dpi,
                    width=width,
                    height=height
                )
                
                if result.error:
                    logger.error(
                        f"Failed to convert page {result.page_number} of {filename}: {result.error}"
                    )
                elif result.image:
                    # Save image
                    image_path = save_page_image(
                        image=result.image,
                        output_dir=output_dir,
                        filename=filename,
                        page_number=result.page_number,
                        page_id=page.page_id
                    )
                    logger.info(f"Saved page {result.page_number} to {image_path}")
                
                session.commit()
            except Exception as e:
                logger.error(
                    f"Error processing page {result.page_number} of {filename}: {e}"
                )
                session.rollback()
                continue
                
        return document
        
    except PdfConversionError as e:
        logger.error(f"Failed to process PDF {pdf_path}: {e}")
        session.rollback()
        return None

def process_bulk_pdf(pdf_folder: Path, output_dir: Path, dpi: int, session: Session) -> List[Document]:
    """Process all PDF files in the specified folder."""
    from src.converters.pdf_to_page_images import get_all_pdf_files
    
    documents = []
    try:
        pdf_files = get_all_pdf_files(pdf_folder)
        logger.info(f"Found {len(pdf_files)} PDF files in {pdf_folder}")
        
        for pdf_path in pdf_files:
            document = process_pdf(pdf_path, output_dir, dpi, session)
            if document:
                documents.append(document)
                
        return documents
        
    except Exception as e:
        logger.error(f"Error in bulk processing: {e}")
        return documents
    