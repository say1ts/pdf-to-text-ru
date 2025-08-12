from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.database.models import Base
from src.workflows.process_pdf import process_bulk_pdf
from src.settings import settings
import logging

def main():
    # Ensure directories exist
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(settings.LOG_FILE),
            logging.StreamHandler()
        ]
    )
    
    # Set up database
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    Base.metadata.create_all(engine)
    
    # Process PDFs
    with Session(engine) as session:
        documents = process_bulk_pdf(
            pdf_folder=settings.PDF_INPUT_DIR,
            output_dir=settings.IMAGE_OUTPUT_DIR,
            dpi=150,
            session=session
        )
        
        for doc in documents:
            print(f"Processed document: {doc.filename} (ID: {doc.document_id})")

if __name__ == "__main__":
    main()
    