from typing import Dict, Any
from src.config import config_provider
from src.entities import ContentType


logger = config_provider.get_logger(__name__)


def validate_fragment_dict(fragment: Dict[str, Any]) -> bool:
    """
    Валидирует сырые данные фрагмента из JSON.
    Проверяет наличие полей, тип ContentType и минимальные размеры.
    """
    try:
        ContentType(fragment["type"])
        if fragment["width"] >= 20 and fragment["height"] >= 10:
            return True
        logger.debug(
            "Fragment is NOT VALID by width or height",
            extra={"page": fragment["page_number"], "type": fragment["type"]},
        )
    except ValueError:
        return False
