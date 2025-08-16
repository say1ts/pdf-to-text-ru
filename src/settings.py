from pathlib import Path
from typing import Dict, Any

from src.entities import ContentType

class Settings:
    """Application configuration."""
    
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    
    # Paths
    PDF_INPUT_DIR: Path = DATA_DIR / "input" / "pdfs"
    IMAGE_OUTPUT_DIR: Path = DATA_DIR / "images"
    LOG_DIR: Path = DATA_DIR / "logs"
    DB_PATH: Path = DATA_DIR / "db" / "database.db"
    
    # Image settings
    IMAGE_FORMAT: str = "PNG"
    IMAGE_QUALITY: int = 85
    IMAGE_FRAGMENT_PATH_TEMPLATE: str = "{filename}/frag_p{page_number}_o{order_number}_i{fragment_id}_{content_type}.{extension}"
    IMAGE_PAGE_PATH_TEMPLATE: str = "{filename}/page_{page_number}_i{page_id}.{extension}"
    
    # Database settings
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{DB_PATH}"
    
    # Layout analyzer settings
    LAYOUT_ANALYZER_URL: str = "http://localhost:5060"
    LAYOUT_ANALYZER_TIMEOUT: int = 300
    
    # Logging settings
    LOG_FILE: Path = LOG_DIR / "convert_pdf_to_pages.log"
    LOG_LEVEL: str = "DEBUG"
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Return settings as a dictionary."""
        return {
            "base_dir": str(cls.BASE_DIR),
            "pdf_input_dir": str(cls.PDF_INPUT_DIR),
            "image_output_dir": str(cls.IMAGE_OUTPUT_DIR),
            "log_dir": str(cls.LOG_DIR),
            "db_path": str(cls.DB_PATH),
            "image_format": cls.IMAGE_FORMAT,
            "image_quality": cls.IMAGE_QUALITY,
            "image_fragment_path_template": cls.IMAGE_FRAGMENT_PATH_TEMPLATE,
            "image_page_path_template": cls.IMAGE_PAGE_PATH_TEMPLATE,
            "sqlalchemy_database_uri": cls.SQLALCHEMY_DATABASE_URI,
            "layout_analyzer_url": cls.LAYOUT_ANALYZER_URL,
            "layout_analyzer_timeout": cls.LAYOUT_ANALYZER_TIMEOUT,
            "log_file": str(cls.LOG_FILE),
            "log_level": cls.LOG_LEVEL,
        }

    # Recognizer settings (общие)
    RECOGNIZER_ALLOWED_TYPES = {
        "text": [
            ContentType.CAPTION.value,
            ContentType.FOOTNOTE.value,
            ContentType.LIST_ITEM.value,
            ContentType.PAGE_FOOTER.value,
            ContentType.PAGE_HEADER.value,
            ContentType.SECTION_HEADER.value,
            ContentType.TEXT.value,
            ContentType.TITLE.value,
        ],
        "table": [...], 
        "formula": [...],
        "image": [...],
    }

    TEXT_RECOGNIZER_MODEL_NAME = "prithivMLmods/Qwen2-VL-OCR-2B-Instruct"
    TEXT_RECOGNIZER_PROMPT = (
        "Extract the exact text from the image in RUSSIAN ONLY. "
        "Do not add, complete, or invent any words, sentences, or punctuation. "
        "Output only the raw extracted text without any modifications or assumptions."
    )
    TEXT_RECOGNIZER_CACHE_DIR = DATA_DIR / "cache" / "qwen2-vl-ocr-2b-instruct"

settings = Settings()
