from typing import Tuple

POINTS_PER_INCH = 72.0

def scale_coordinates(
    coords: Tuple[float, float, float, float], 
    dpi: int
) -> Tuple[int, int, int, int]:
    """
    Масштабирует координаты из пунктов (pt) в пиксели (px) с учетом DPI.

    Args:
        coords: Кортеж с координатами (left, top, width, height) в пунктах.
        dpi: Разрешение, с которым было создано изображение (точек на дюйм).

    Returns:
        Кортеж с целочисленными координатами (left, top, right, bottom) в пикселях.
    """
    left, top, width, height = coords
    scale_factor = dpi / POINTS_PER_INCH

    px_left = int(left * scale_factor)
    px_top = int(top * scale_factor)
    px_right = int((left + width) * scale_factor)
    px_bottom = int((top + height) * scale_factor)

    return (px_left, px_top, px_right, px_bottom)