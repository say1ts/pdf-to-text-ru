from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.database.models import Base
from src.workflows.process_pdf import process_bulk_pdf
from src.utils.reading_order import ReadingOrderService, get_default_order
from src.config import config_provider
from src.utils.docker_manager import managed_docker_container

def main():
    settings = config_provider.get_settings()
    logger = config_provider.get_logger("main")

    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    Base.metadata.create_all(engine)

    order_strategy = ReadingOrderService().get_reading_order # get_default_order  # or ReadingOrderService().get_reading_order

    docker_run_command = [
        "docker", "run", "--name", "pla", "--gpus", '"device=0"',
        "-p", "5060:5060", "--entrypoint", "./start.sh", "huridocs/pdf-document-layout-analysis:v0.0.24"
    ]

    with Session(engine) as session:
        with managed_docker_container(
            container_name="pla",
            run_command=docker_run_command,
            logger=logger
        ):
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