from pathlib import Path
from typing import Tuple
from PIL import Image
from src.config import config_provider
from src.entities import Fragment

settings = config_provider.get_settings()

def save_page_image(image: Image.Image, output_dir: Path, filename: str, page_number: int, page_id: int) -> Path:
    extension = settings.IMAGE_FORMAT.lower()
    image_path = output_dir / settings.IMAGE_PAGE_PATH_TEMPLATE.format(
        filename=filename, page_number=page_number, page_id=page_id, extension=extension
    )
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(image_path, format=settings.IMAGE_FORMAT, quality=settings.IMAGE_QUALITY)
    return image_path

def save_fragment_image(
    page_image: Image.Image,
    output_dir: Path,
    filename: str,
    page_number: int,
    fragment: Fragment,
    crop_box: Tuple[int, int, int, int]
) -> Path:
    """
    Вырезает и сохраняет изображение фрагмента, используя готовые координаты в пикселях.
    """
    fragment_image = page_image.crop(crop_box)

    extension = settings.IMAGE_FORMAT.lower()
    image_path = output_dir / settings.IMAGE_FRAGMENT_PATH_TEMPLATE.format(
        filename=filename,
        page_number=page_number,
        order_id=fragment.order_number or 0,
        fragment_id=fragment.fragment_id,
        extension=extension
    )
    image_path.parent.mkdir(parents=True, exist_ok=True)
    fragment_image.save(image_path, format=settings.IMAGE_FORMAT, quality=settings.IMAGE_QUALITY)
    return image_path