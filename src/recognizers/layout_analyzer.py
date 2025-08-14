from pathlib import Path
import requests
import logging
from typing import List, Dict, Any
from src.config import config_provider
from src.entities import Fragment, ContentType

settings = config_provider.get_settings()
logger = config_provider.get_logger(__name__)

class LayoutAnalyzerError(Exception):
    pass

class FileNotFoundError(LayoutAnalyzerError):
    pass

class ServerError(LayoutAnalyzerError):
    pass

class InvalidJsonError(LayoutAnalyzerError):
    pass

def validate_json_fragment(fragment: Dict[str, Any]) -> bool:
    required_fields = {"left", "top", "width", "height", "page_number", "page_width", "page_height", "type"}
    if not all(field in fragment for field in required_fields):
        return False
    try:
        ContentType(fragment["type"])
        return fragment["width"] >= 20 and fragment["height"] >= 10
    except ValueError:
        return False

def analyze_pdf(file_path: str) -> List[Fragment]:
    try:
        if not Path(file_path).is_file():
            raise FileNotFoundError(f"File {file_path} not found")
            
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'application/pdf')}
            response = requests.post(
                settings.LAYOUT_ANALYZER_URL,
                files=files,
                timeout=settings.LAYOUT_ANALYZER_TIMEOUT
            )
        response.raise_for_status()
        
        # Здесь нужно сделать typed_dict или named_tuple
        data = response.json()
        
        # ПОЧЕМУ ЗДЕСЬ НЕ DICT со страницами в качестве индексов
        valid_fragments = [Fragment.from_dict(fragment, page_id=fragment["page_number"]) for fragment in data if validate_json_fragment(fragment)]
        logger.debug(
            "Processed PDF file",
            extra={"file": file_path, "fragments_received": len(data), "fragments_valid": len(valid_fragments)}
        )
        return valid_fragments
    except FileNotFoundError as e:
        logger.error("File not found", extra={"file": file_path, "error": str(e)})
        raise FileNotFoundError(f"File {file_path} not found")
    except requests.HTTPError as e:
        logger.error("HTTP error occurred", extra={"file": file_path, "error": str(e)})
        raise ServerError(f"HTTP error: {e}")
    except requests.RequestException as e:
        logger.error("Server request failed", extra={"file": file_path, "error": str(e)})
        raise ServerError(f"Server error: {e}")
    except ValueError as e:
        logger.error("Invalid JSON response", extra={"file": file_path, "error": str(e)})
        raise InvalidJsonError(f"Invalid JSON: {e}")
    