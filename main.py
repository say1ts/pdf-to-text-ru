from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.converters.pdf_to_page_images import get_all_pdf_files
from src.repository.documents import get_cut_documents, get_document_by_filename
from src.database.models import Base
from src.workflows.process_pdf import process_bulk_pdf
from src.workflows.recognize_fragments import recognize_bulk_fragments, recognize_single_document
from src.utils.reading_order import ReadingOrderService
from src.utils.docker_manager import managed_docker_container
from src.config import config_provider


def main():
    settings = config_provider.get_settings()
    logger = config_provider.get_logger("main")

    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    Base.metadata.create_all(engine)

    order_strategy = ReadingOrderService().get_reading_order

    docker_run_command = [
        "docker",
        "run",
        "--name",
        "pla",
        "--gpus",
        '"device=0"',
        "-p",
        "5060:5060",
        "--entrypoint",
        "./start.sh",
        "huridocs/pdf-document-layout-analysis:v0.0.24",
    ]

    with Session(engine) as session:
        try:
            pdf_files = get_all_pdf_files(settings.PDF_INPUT_DIR)
        except FileNotFoundError:
            logger.warning(f"No PDF files found in {settings.PDF_INPUT_DIR}")
            return None

        cut_docs = map(lambda doc: doc.filename + "." + doc.extension, get_cut_documents(session))
        docs_already_processed = all(pdf_file in cut_docs for pdf_file in pdf_files)

        if not docs_already_processed:
            with managed_docker_container(
                container_name="pla", run_command=docker_run_command, logger=logger
            ):
                documents = process_bulk_pdf(
                    pdf_files=pdf_files,
                    output_dir=settings.IMAGE_OUTPUT_DIR,
                    dpi=150,
                    session=session,
                    order_strategy=order_strategy,
                    logger=logger,
                )

                for doc in documents:
                    logger.info({"document": doc.filename, "id": doc.document_id})

        # 2 STAGE TEXT FRAGMENT RECOGNIZER
        document = get_document_by_filename(session, "test")
        recognize_single_document(
            document=document, session=session, logger=logger, recognizer_type="text"
        )
        # for doc in recognized_docs:
        #     logger.info({"recognized_document": doc.filename, "id": doc.document_id})


if __name__ == "__main__":
    main()
