from pathlib import Path
import requests
from typing import List
from src.config import config_provider
from src.entities import Fragment, RawFragment
from src.utils.raw_fragment_validators import validate_fragment_dict

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

        raw_data: List[RawFragment] = response.json()
        valid_fragments = tuple(
            raw_fragment
            for raw_fragment in raw_data
            if validate_fragment_dict(raw_fragment)
        )
            
        logger.debug(
            "Processed PDF file",
            extra={"file": file_path, "fragments_received": len(raw_data), "fragments_valid": len(valid_fragments)}
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
    