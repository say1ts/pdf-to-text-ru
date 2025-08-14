from pathlib import Path
from typing import Dict, Any

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
    IMAGE_FRAGMENT_PATH_TEMPLATE: str = "{filename}/fragment_{page_number}_{order_id}_{fragment_id}_fragment_id.{extension}"
    IMAGE_PAGE_PATH_TEMPLATE: str = "{filename}/page_{page_number}_{page_id}_page_id.{extension}"
    
    # Database settings
    SQLALCHEMY_DATABASE_URI: str = f"sqlite:///{DB_PATH}"
    
    # Layout analyzer settings
    LAYOUT_ANALYZER_URL: str = "http://localhost:5060"
    LAYOUT_ANALYZER_TIMEOUT: int = 300
    
    # Logging settings
    LOG_FILE: Path = LOG_DIR / "convert_pdf_to_pages.log"
    LOG_LEVEL: str = "INFO"
    
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

settings = Settings()
