from pathlib import Path
from PIL import Image
from src.settings import settings

def save_page_image(
    image: Image.Image,
    output_dir: Path,
    filename: str,
    page_number: int,
    page_id: int
) -> Path:
    """Save a page image to the specified path."""
    extension = settings.IMAGE_FORMAT.lower()
    image_path = output_dir / settings.IMAGE_PAGE_PATH_TEMPLATE.format(
        filename=filename,
        page_number=page_number,
        page_id=page_id,
        extension=extension
    )
    
    # Ensure directory exists
    image_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save image
    image.save(image_path, format=settings.IMAGE_FORMAT, quality=settings.IMAGE_QUALITY)
    return image_path