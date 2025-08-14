from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.database.models import Base
from src.workflows.process_pdf import process_bulk_pdf
from src.utils.reading_order import get_default_order
from src.config import config_provider

def main():
    settings = config_provider.get_settings()
    logger = config_provider.get_logger("main")
    
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    Base.metadata.create_all(engine)
    
    order_strategy = get_default_order # get_reading_order  # or get_default_order
    with Session(engine) as session:
        documents = process_bulk_pdf(
            pdf_folder=settings.PDF_INPUT_DIR,
            output_dir=settings.IMAGE_OUTPUT_DIR,
            dpi=150,
            session=session,
            order_strategy=order_strategy,
            logger=logger
        )
        
        for doc in documents:
            logger.info({"document": doc.filename, "id": doc.document_id})

if __name__ == "__main__":
    main()
    