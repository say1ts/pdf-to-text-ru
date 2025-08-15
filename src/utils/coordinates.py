from typing import Tuple

POINTS_PER_INCH = 72.0

def correct_coord(coord: int, correction: int, max_val = float('inf')):
    new_coord = coord + correction
    if new_coord < 0:
        coord = 0
    if new_coord > max_val:
        coord = max_val
    return new_coord


def scale_coordinates_from_pt_to_px(
    left: float, 
    top: float,
    width: float, 
    height: float, 
    max_coord: Tuple[int, int],
    dpi: int,
) -> Tuple[int, int, int, int]:
    """
    Масштабирует координаты из пунктов (pt) в пиксели (px) с учетом DPI.

    Args:
        coords: Кортеж с координатами (left, top, width, height) в пунктах.
        dpi: Разрешение, с которым было создано изображение (точек на дюйм).

    Returns:
        Кортеж с целочисленными координатами (left, top, right, bottom) в пикселях.
    """
    scale_factor = dpi / POINTS_PER_INCH

    px_left = int(left * scale_factor)
    px_top = correct_coord(int(top * scale_factor), -4)        
    px_right = correct_coord(int((left + width) * scale_factor), 6, max_coord[0])
    px_bottom = correct_coord(int((top + height) * scale_factor), 4, max_coord[1])

    return (px_left, px_top, px_right, px_bottom)