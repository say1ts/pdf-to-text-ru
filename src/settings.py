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
            
            ContentType.FORMULA.value,
        ],
        "table": [...], 
        "formula": [ContentType.FORMULA.value],
        "image": [...],
    }

    TEXT_RECOGNIZER_MODEL_NAME = "prithivMLmods/Qwen2-VL-OCR-2B-Instruct"
    TEXT_RECOGNIZER_PROMPT = (
        "Extract the exact text from the image in RUSSIAN ONLY. "
        "Do not add, complete, or invent any words, sentences, or punctuation. "
        "Output only the raw extracted text without any modifications or assumptions."
    )
    TEXT_RECOGNIZER_CACHE_DIR = DATA_DIR / "cache" / "qwen2-vl-ocr-2b-instruct"
    
    # Formula recognizer settings
    FORMULA_RECOGNIZER_MODEL_BACKEND: str = "onnx"
    FORMULA_RECOGNIZER_MODEL_DIR: Path = DATA_DIR / "cache" / "pix2text-mfr-onnx"
    
settings = Settings()
